import os

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import argparse
import json
from pathlib import Path
from transformers import AutoTokenizer

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "dataset" / "examples"


def to_messages(record):
    # Same fallback as format_example in train_unsloth.py
    return record.get("messages") or [
        {"role": "user", "content": record["prompt"]},
        {"role": "assistant", "content": record["response"]},
    ]

def count_tokens(tokenizer, record):
    template_kwargs = {}
    if "enable_thinking" in tokenizer.get_chat_template():
        template_kwargs["enable_thinking"] = False

    # Same text train_unsloth.py feeds to the trainer, so the counts match what max_seq_length is compared against
    text = tokenizer.apply_chat_template(to_messages(record), tokenize=False, add_generation_prompt=False, **template_kwargs)
    return len(tokenizer(text, add_special_tokens=False)["input_ids"])

def percentile(sorted_lengths, q):
    return sorted_lengths[min(len(sorted_lengths) - 1, int(q * len(sorted_lengths)))]

def source_file(example_id):
    # dataset/out/*.jsonl is rebuilt by dataset/scripts/build.py, the source YAML is what survives a rebuild
    matches = list(EXAMPLES_DIR.rglob(f"{example_id}.yaml")) if example_id else []
    return matches[0] if matches else None

def analyze(tokenizer, dataset_path, threshold, delete):
    lines = Path(dataset_path).read_text(encoding="utf-8").splitlines()
    lengths = []
    too_long = []

    for line_number, line in enumerate(lines):
        if not line.strip():
            continue
        record = json.loads(line)
        length = count_tokens(tokenizer, record)
        lengths.append(length)
        if threshold is not None and length > threshold:
            too_long.append((line_number, record.get("id"), length))

    lengths.sort()
    print(f"\n{dataset_path}")
    print(f"  examples={len(lengths)} mean={sum(lengths) // len(lengths)} p50={percentile(lengths, 0.5)} "
          f"p90={percentile(lengths, 0.9)} p95={percentile(lengths, 0.95)} p99={percentile(lengths, 0.99)} max={lengths[-1]}")
    for limit in (1024, 2048, 3072, 4096, 8192):
        print(f"  > {limit}: {sum(length > limit for length in lengths)}")

    # Round up to a multiple of 64, a GPU friendly size that still has no truncation
    print(f"  Suggested --max-seq-length (no truncation): {-(-lengths[-1] // 64) * 64}")

    if threshold is None:
        return

    print(f"\n  {len(too_long)} examples above {threshold} tokens:")
    for line_number, example_id, length in sorted(too_long, key=lambda item: -item[2]):
        source = source_file(example_id)
        print(f"    {length:>6} tokens  line {line_number + 1:<6} {example_id}  {source or '(no source YAML found)'}")

    if not delete or not too_long:
        return

    answer = input(f"\n  Delete these {len(too_long)} examples from {dataset_path} and their source YAMLs? [y/N] ")
    if answer.strip().lower() != "y":
        print("  Nothing deleted")
        return

    drop = {line_number for line_number, _, _ in too_long}
    kept = [line for line_number, line in enumerate(lines) if line_number not in drop]
    Path(dataset_path).write_text("\n".join(kept) + "\n", encoding="utf-8")
    print(f"  Deleted {len(drop)} examples, {len(kept)} remain")

    # Without the source YAML the next dataset/scripts/build.py run would bring the example back
    for _, example_id, _ in too_long:
        source = source_file(example_id)
        if source:
            source.unlink()
            print(f"  Deleted {source}")

def main():
    parser = argparse.ArgumentParser(description="Show token lengths of a dataset to choose --max-seq-length for train_unsloth.py.")

    parser.add_argument("--model", help="Model name/path whose tokenizer and chat template to use (e.g.: unsloth/Qwen2.5-Coder-7B-Instruct)", required=True)
    parser.add_argument("--dataset", help="One or more JSONL datasets (e.g.: ../dataset/out/train.jsonl ../dataset/out/eval.jsonl)", nargs="+", required=True)
    parser.add_argument("--threshold", help="List the examples with more tokens than this", type=int, default=None)
    parser.add_argument("--delete", help="Delete the examples above --threshold from the dataset file (asks before)", action="store_true")

    args = parser.parse_args()

    if args.delete and args.threshold is None:
        parser.error("--delete needs --threshold")

    tokenizer = AutoTokenizer.from_pretrained(args.model)

    for dataset_path in args.dataset:
        analyze(tokenizer, dataset_path, args.threshold, args.delete)

if __name__ == "__main__":
    main()
