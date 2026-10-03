import os

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["UNSLOTH_DISABLE_STATISTICS"] = "1"   # skips a telemetry README fetch
os.environ["UNSLOTH_DISABLE_UPDATE_CHECK"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import argparse
from unsloth import FastLanguageModel
import torch
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig


# unsloth/Qwen2.5-Coder-0.5B-Instruct any good?
#    - Quick. Takes 0:16
#    - But no optimization actually applied 😢
# distilbert/distilbert-base-uncased can do more than 1/0 ?

# unsloth/Qwen2.5-Coder-7B-Instruct better?
#    - Good Takes around 1:22 to complete in Ollama and 1:04 in PyTorch
# unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit better?

def train_model(model_name, target_modules, dataset_path, output_dir, split_and_evaluate):

    # Load the model
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=4096,
        load_in_4bit=True,
    )

    # Add LoRA adapters.
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=16,
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

    if split_and_evaluate:
        dataset = dataset.train_test_split(
            test_size=0.1,
            seed=3407,
        )
        train_dataset = dataset["train"]
        eval_dataset = dataset["test"]

    def format_example(example):
        messages = [
            {
                "role": "user",
                "content": example["prompt"],
            },
            {
                "role": "assistant",
                "content": example["response"],
            },
        ]

        return {
            "text": tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False,
            )
        }

    train_dataset = train_dataset.map(format_example)
    if eval_dataset:
        eval_dataset = eval_dataset.map(format_example)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        dataset_text_field="text",
        max_seq_length=4096,
        args=SFTConfig(
            output_dir=output_dir,
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            num_train_epochs=10,
            learning_rate=2e-4,
            logging_steps=10,
            save_steps=100,
            fp16=True,
            optim="adamw_8bit",
            report_to="none",
            # Validation loss - Works only if eval_dataset != None
            eval_strategy="steps",
            eval_steps=50,
        ),
    )

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
    parser.add_argument("--target-modules", help="Comma-separated LoRA target modules (gate_proj,up_proj,down_proj are typically 'knowledge' and 'q_proj,k_proj,v_proj,o_proj 'behaviour and capabilities')", default="gate_proj,up_proj,down_proj")

    args = parser.parse_args()

    target_modules = [module.strip() for module in args.target_modules.split(",") if module.strip()]


    print(f"Loading model: {args.model}")
    print(f"Target modules: {target_modules}")

    train_model(args.model, args.target_modules, args.dataset, args.output, args.split_and_evaluate)

if __name__ == "__main__":
    main()