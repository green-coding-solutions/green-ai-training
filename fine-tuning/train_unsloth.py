import os

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["UNSLOTH_DISABLE_STATISTICS"] = "1"   # skips a telemetry README fetch
os.environ["UNSLOTH_DISABLE_UPDATE_CHECK"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import argparse
import math
from unsloth import FastLanguageModel, is_bfloat16_supported
from unsloth.chat_templates import train_on_responses_only
from unsloth.device_type import is_mlx_available
import torch
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig
from transformers import TrainerCallback


class EvalAfterFirstStep(TrainerCallback):
    # The MLX trainer has no eval_on_start. Step 1 runs at 1/warmup_steps of the learning rate,
    # so this eval is close to the untrained baseline.
    def on_step_end(self, args, state, control, **kwargs):
        if state.global_step == 1:
            control.should_evaluate = True
        return control

def train_model(model_name, target_modules, dataset_path, output_dir, split_and_evaluate,
                eval_dataset_path=None, epochs=3, learning_rate=2e-4, rank=16, max_seq_length=2048, quantize_4bit=False,
                batch_size=2, gradient_accumulation_steps=None):

    # Load the model
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,

        # Setting load_in_4bit = False and load_in_16bit=True can help with training speed if the model is not in 4bit.
        # We have seen 15-25% improvement unsloth/Qwen2.5-Coder-7B-Instruct which has BF16 tensors
        # => Always both parameter have to be set with each value inverse to the other!
        # Using 4-bit might use less memory, but can degrade the model if not already in 4bit
        load_in_4bit=quantize_4bit,
        load_in_16bit=not quantize_4bit,
    )

    # Add LoRA adapters.
    model = FastLanguageModel.get_peft_model(
        model,
        r=rank,
        lora_alpha=rank,
        lora_dropout=0,
        target_modules=target_modules,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    dataset = load_dataset(
        "json",
        data_files=dataset_path,
        split="train",
        )

    train_dataset = dataset
    eval_dataset = None

    if eval_dataset_path:
        # ../dataset/out/eval.jsonl is a fixed held-out split, no need to cut the train set
        eval_dataset = load_dataset("json", data_files=eval_dataset_path, split="train")
    elif split_and_evaluate:
        dataset = dataset.train_test_split(
            test_size=0.1,
            seed=3407,
        )
        train_dataset = dataset["train"]
        eval_dataset = dataset["test"]

    def format_example(example):
        # ../dataset/out/*.jsonl uses a "messages" list (multi-turn, optional system prompt)
        messages = example.get("messages") or [
            {
                "role": "user",
                "content": example["prompt"],
            },
            {
                "role": "assistant",
                "content": example["response"],
            },
        ]

        template_kwargs = {}
        if "enable_thinking" in tokenizer.get_chat_template():
            template_kwargs["enable_thinking"] = False

        return {
            "text": tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
                **template_kwargs
            )
        }

    train_dataset = train_dataset.map(format_example)
    if eval_dataset:
        eval_dataset = eval_dataset.map(format_example)

    # Keep the effective batch at 8 by default, so a smaller batch only saves memory
    # and does not change the number of optimizer steps or the warmup
    if gradient_accumulation_steps is None:
        gradient_accumulation_steps = max(1, 8 // batch_size)
    # Warm up over 10% of all optimizer steps. Passed as a whole number because the MLX trainer
    # ignores fractional warmup_steps and would start at the full learning rate.
    total_steps = math.ceil(len(train_dataset) / (batch_size * gradient_accumulation_steps)) * epochs
    warmup_steps = max(1, int(total_steps * 0.1))

    if total_steps < 100:
        raise RuntimeError(f"Total Steps is very small ({total_steps}). It should be at least a couple hundreds to a few thousands. Read the README on which params to tune.")

    use_mlx = is_mlx_available()

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        args=SFTConfig(
            output_dir=output_dir,
            dataset_text_field="text",
            max_length=max_seq_length,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            num_train_epochs=epochs,
            learning_rate=learning_rate,
            lr_scheduler_type="cosine",
            warmup_steps=warmup_steps,
            weight_decay=0.01,
            logging_steps=1,
            # Save a checkpoint after an eval only if the eval loss improved. Without an eval
            # dataset there is no loss to compare, so fall back to one checkpoint per epoch.
            save_strategy="best" if eval_dataset is not None else "epoch",
            metric_for_best_model="eval_loss" if eval_dataset is not None else None,
            greater_is_better=False,
            save_total_limit=2,
            bf16=is_bfloat16_supported(),
            fp16=not is_bfloat16_supported(),
            # We could also use adamw_torch_fused when training on CUDA as it is faster and does not quantize
            # But sadly we have seen OOM doing this on 32 GB shared memory MLX Training
            optim="adamw_8bit",
            seed=3407,
            report_to="none",
            # Evaluate every 50 optimizer steps to see where in an epoch the eval loss turns
            eval_strategy="steps" if eval_dataset is not None else "no",
            eval_steps=50,
            # Baseline val loss of the untrained model, to compare the later evals against.
            # MLXTrainingConfig rejects this kwarg, MLX uses EvalAfterFirstStep instead.
            **({"eval_on_start": eval_dataset is not None} if not use_mlx else {}),
        ),
    )

    # Loss only on the assistant turns. Otherwise the model also learns to reproduce the user
    # prompts and the system prompt. Instruction/response markers are detected from the chat template.
    trainer = train_on_responses_only(trainer)

    if eval_dataset is not None and use_mlx:
        trainer.add_callback(EvalAfterFirstStep())

    trainer.train()

    # Saves the LoRA adapter, not a complete copy of the model.
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

def main():
    parser = argparse.ArgumentParser(description="Run inference with an Unsloth language model.")

    parser.add_argument("--model", help=f"Model name/path (e.g.: unsloth/Qwen2.5-Coder-7B-Instruct)", required=True)
    parser.add_argument("--dataset", help=f"Dataset to use for fine-tuning of model", required=True)
    parser.add_argument("--output", help=f"Output directory for LoRA adapter", default="./lora-adapter")
    parser.add_argument("--split-and-evaluate", help=f"Split Dataset in Training and Evaluation and evaluate", action="store_true")
    parser.add_argument("--eval-dataset", help="Separate evaluation dataset (e.g. ../dataset/out/eval.jsonl), replaces --split-and-evaluate", default=None)
    parser.add_argument("--epochs", help="Number of training epochs", type=float, default=3)
    parser.add_argument("--learning-rate", help="Learning rate", type=float, default=2e-4)
    parser.add_argument("--rank", help="LoRA rank (lora_alpha is set to the same value)", type=int, default=16)
    parser.add_argument("--batch-size", help="Conversations per forward pass. Lower it to save memory", type=int, default=2)
    parser.add_argument("--gradient-accumulation-steps", help="Batches per optimizer step (default: 8 / batch size, so the effective batch stays 8)", type=int, default=None)
    parser.add_argument("--max-seq-length", help="Maximum tokens per conversation, longer ones are truncated", type=int, default=2048)
    # These layers should ONLY be the language layers. Not the vision layers (like vision_model.XXX or vision.q_proj etc.)
    parser.add_argument("--target-modules", help="Comma-separated LoRA language layer target modules (gate_proj,up_proj,down_proj are typically 'knowledge' and 'q_proj,k_proj,v_proj,o_proj 'behaviour and capabilities')", default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj")
    parser.add_argument("--quantize-4bit", help="Force 4-bit quantization. Helpful if you have limited memory. Might reduce training speed and model accuracy in not already 4-bit models.", action="store_true")

    args = parser.parse_args()

    target_modules = [module.strip() for module in args.target_modules.split(",") if module.strip()]


    print(f"Loading model: {args.model}")
    print(f"Target modules: {target_modules}")

    train_model(args.model, target_modules, args.dataset, args.output, args.split_and_evaluate,
                args.eval_dataset, args.epochs, args.learning_rate, args.rank, args.max_seq_length, args.quantize_4bit,
                args.batch_size, args.gradient_accumulation_steps)

if __name__ == "__main__":
    main()