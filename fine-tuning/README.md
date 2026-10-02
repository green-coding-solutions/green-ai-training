# Fine-Tuning

This folder is for fine-tuning the model with LoRA and unsloth.

## Installation

```bash
python3.12 -m venv venv
pip install -r requirements.txt
```


## Run

```bash
python3 train_unsloth.py --model 'unsloth/Qwen2.5-Coder-0.5B-Instruct' --dataset training_data.json
```


## Fusing

After training it is recommended to fuse the model which makes it easier to evaluate it.

```bash
mlx_lm.fuse \
  --model unsloth/Qwen2.5-Coder-7B-Instruct \
  --adapter-path lora-adapter \
  --save-path ./fused-model
```

This is only needed if training with Apple MLX.

The result can then be evaluate. See the `../evaluation` folder for details
