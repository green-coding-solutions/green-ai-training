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

### Choosing parameters

#### Choosing --max-seq-length

`token_lengths.py` counts the tokens per example with the model's chat template and suggests a `--max-seq-length`
that truncates nothing. `--threshold` lists the longer examples with their source YAML, `--delete` removes them from
the JSONL and deletes their source YAML in `../dataset/examples` after a y/N prompt, so a rebuild does not bring them back.

```bash
python3 token_lengths.py --model 'unsloth/Qwen2.5-Coder-7B-Instruct' \
  --dataset ../dataset/out/train.jsonl ../dataset/out/eval.jsonl \
  --threshold 2048 --delete
```

#### Choosing epochs

A typical value is 2.
If you get too few steps from this it is rather recommended to increase the amount of samples you have then to
increase epochs.
A value of 3-4 is howver also acceptable if you want the model not to learn a concept so much, but to memorize stronger.

#### Choosing --batch-size

A value of at least 2 is preferred as it makes evaluating loss easier. Loss does jump quite a bit if *batch-size* is
only 1 and you can see a trend only over longer times rather than step-to-step.

Howver in low-memory situations you often have to set --batch-size to 1. It is no quality loss, but be aware
of the loss evaluation quirk.

#### Choosing --gradient-accumulation-steps

This is by far the most tricky param.
If you set it too low the the training loss will jump around quite a bit.
Setting it too high will result in too few steps. We recommend having at least 100 steps if you have a very tight
knit sample set. If you sample set is quite diverse having hundreds to thousand steps is more apt as you need to
train quite a bit of concept into the model.

If you steps get too low when you increase this value you also can compensate with epochs a bit but be aware of the
issues said above. In the end adding samples is often the best approach. Be aware that they should complement one
another and not duplicate.

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
