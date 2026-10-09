# Fine-Tuning

This folder is for fine-tuning the model with LoRA and unsloth.

## Installation

```bash
python3.12 -m venv venv
pip install -r requirements.txt
```


## Run

```bash
python3 train_unsloth.py --model 'unsloth/Qwen2.5-Coder-7B-Instruct' --dataset ../data/green-coding-talk-questions.csv
```

With the green coding conversation dataset (build it first, see `../dataset/README.md`):

```bash
python3 train_unsloth.py --model 'unsloth/Qwen2.5-Coder-7B-Instruct' \
  --dataset ../dataset/out/train.jsonl \
  --eval-dataset ../dataset/out/eval.jsonl \
  --output ./lora-adapter-green-code
```

Loss is computed on the assistant turns only. Defaults: all attention and MLP projections as LoRA targets, rank 16,
3 epochs, learning rate 2e-4 with cosine decay. Watch the eval loss per epoch: if it rises while the train loss keeps
falling, the model is memorizing, so use fewer epochs (`--epochs 2`).


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
