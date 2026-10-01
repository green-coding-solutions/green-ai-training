import os

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["UNSLOTH_DISABLE_STATISTICS"] = "1"   # skips a telemetry README fetch
os.environ["UNSLOTH_DISABLE_UPDATE_CHECK"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import argparse
import torch
from unsloth import FastLanguageModel
from peft import PeftModel


# unsloth/Qwen2.5-Coder-0.5B-Instruct any good?
#    - Quick. Takes 0:16
#    - But no optimization actually applied 😢
# distilbert/distilbert-base-uncased can do more than 1/0 ?

# unsloth/Qwen2.5-Coder-7B-Instruct better?
#    - Good Takes around 1:22 to complete in Ollama and 1:04 in PyTorch
# unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit better?

def generate_output(model_name_or_lora_folder, prompt, verbose):
    # Load the model
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name_or_lora_folder,
        max_seq_length=4096,
        load_in_4bit=True,
    )

    # Optimize the model for inference
    FastLanguageModel.for_inference(model)


    if tokenizer.chat_template:
        if verbose:
            print('Using chat template: ', tokenizer.chat_template)

        messages = [{"role": "user","content": prompt}]
        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        )

    else:
        print("Model has no Chat Template configured. ", "\n", "Falling back to direct prompt.")

        inputs = tokenizer(prompt, return_tensors="pt")["input_ids"]

    with torch.inference_mode():
        outputs = model.generate(
            input_ids=inputs,
            max_new_tokens=8192,
            do_sample=False,
            # If more output variation is wanted temperature can be set, but top_p should
            # also be considered and do_sample must be True
            # temperature=0.7,
            # top_p=0.9,
            # do_sample=True
        )

    # Only decode the generated portion
    generated = outputs[0][inputs.shape[-1]:]

    return tokenizer.decode(generated, skip_special_tokens=True)

def main():
    parser = argparse.ArgumentParser(description="Run inference with an Unsloth language model.")

    parser.add_argument("--model", help=f"Model name/path (e.g.: unsloth/Qwen2.5-Coder-7B-Instruct) or LoRA adapater folder", required=True)
    parser.add_argument('--verbose', help="Show debug output", action="store_true")

    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument(
        "--prompt",
        action="append",
        help="One or more prompts to send to the model. "
             "Each prompt is executed in a fresh context.",
    )
    prompt_group.add_argument("--prompt-file", help="Path to a file containing the prompt.")

    args = parser.parse_args()

    if args.prompt is not None:
        prompts = args.prompt
    else:
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompts = [f.read()]

    print(f"Loading model: {args.model}")

    for prompt in prompts:
        print("\n" + "=" * 80)
        print(f"Prompt: {prompt}")
        print("=" * 80)

        output = generate_output(args.model, prompt, args.verbose)

        print(output)

if __name__ == "__main__":
    main()