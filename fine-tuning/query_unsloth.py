import argparse

from unsloth import FastLanguageModel
import torch
import mlx.core as mx

# unsloth/Qwen2.5-Coder-0.5B-Instruct any good?
#    - Quick. Takes 0:16
#    - But no optimization actually applied 😢
# distilbert/distilbert-base-uncased can do more than 1/0 ?

# unsloth/Qwen2.5-Coder-7B-Instruct better?
#    - Good Takes around 1:22 to complete in Ollama and 1:04 in PyTorch
# unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit better?

def generate_output(model_name, prompt, lora_adapter_folder):
    # Load the model
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=4096,
        load_in_4bit=True,
    )

    if lora_adapter_folder:
        model.load_adapter(lora_adapter_folder)

    # Optimize the model for inference
    FastLanguageModel.for_inference(model)


    if tokenizer.chat_template:
        print('Using chat template: ', tokenizer.chat_template)

        messages = [{"role": "user","content": prompt}]
        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="np",
        )

    else:
        print("Model has no Chat Template configured. ", "\n", "Falling back to direct prompt.")

        inputs = tokenizer(prompt, return_tensors="np")["input_ids"]

    with torch.inference_mode():
        outputs = model.generate(
            input_ids=mx.array(inputs),
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

    parser.add_argument("--model", help=f"Model name/path (e.g.: unsloth/Qwen2.5-Coder-7B-Instruct)", required=True)

    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt", help="Prompt to send to the model.")
    prompt_group.add_argument("--prompt-file", help="Path to a file containing the prompt.")

    parser.add_argument("--lora-adapter", help="Add additional LoRA adapter from directory")

    args = parser.parse_args()

    if args.prompt is not None:
        prompt = args.prompt
    else:
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read()

    print(f"Loading model: {args.model}")

    output = generate_output(args.model, prompt, args.lora_adapter)

    print(output)

if __name__ == "__main__":
    main()