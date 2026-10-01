# Evaluation

This dir is for evaluation of the LLM fine tuning.

It needs it's own `venv` and own folder as we install different `pip` package versions.

## Installation

```bash
python3.14 -m venv venv
pip install -r requirements.txt
```

## Safeguard

You are advised to create a new user that does not have write rights to the whole system and setup firewall
rules if necessary

A typical way on macOS to do this is install LittleSnitch and also setup a new user that has no permission
to read the home folder of your main user.
Put all files in a folder in this users `Public` folder and then symlink it to your main user.
The main user should then create a git that is non readable or writeable to the new user.

## Running

```bash
HF_ALLOW_CODE_EVAL=1 lm_eval \
  --model hf \
  --model_args "pretrained=Qwen/Qwen2.5-7B-Instruct,peft=/Users/code-runner/Public/Sites/green-coding/green-ai-training/fine-tuning/lora-adapter" \
  --tasks mbpp_plus \
  --batch_size 1 \
  --output_path results/base \
--apply_chat_template \
  --confirm_run_unsafe_code \
  --device mps
```
