#!/usr/bin/env python3
"""Builds the training files from verified examples.

Runs verify (cached) over all examples, keeps the passing ones and writes:
  out/train.jsonl, out/eval.jsonl   {"id", "category", "messages": [{"role", "content"}, ...]}
  out/stats.json                    counts per category / pattern / language

Most examples carry no system prompt, so the green behavior becomes the model's default. A small share gets a
neutral system prompt (never mentioning sustainability), so the behavior also holds when an app sets one.

Usage:
  python scripts/build.py
  python scripts/build.py --eval-ratio 0.1 --system-ratio 0.15
  python scripts/build.py --format prompt-response   # single-turn only, for the old {"prompt","response"} trainer
"""

import argparse
import hashlib
import json
import random
import sys
from collections import Counter

from common import OUT_DIR, load_examples
from verify import summarize, verify_all

NEUTRAL_SYSTEM_PROMPTS = [
    "You are a helpful assistant.",
    "You are a helpful coding assistant.",
    "You are an expert software engineer. Answer precisely.",
    "You are a senior developer helping a colleague.",
    "You are a programming assistant integrated into a chat window. Use Markdown for code.",
]


def stable_fraction(text):
    return int(hashlib.sha1(text.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--eval-ratio", type=float, default=0.1, help="Share of examples held out per category")
    parser.add_argument("--system-ratio", type=float, default=0.15, help="Share of examples with a neutral system prompt")
    parser.add_argument("--format", choices=["messages", "prompt-response"], default="messages")
    parser.add_argument("--no-exec", action="store_true", help="Skip execution checks (not recommended)")
    parser.add_argument("--seed", type=int, default=3407)
    args = parser.parse_args()

    report = verify_all(no_exec=args.no_exec, quiet=True)
    (OUT_DIR / "verify-report.json").write_text(json.dumps(report, indent=1))
    summarize(report)
    failed = [k for k, v in report.items() if v["status"] == "fail"]
    if failed:
        print(f"\nSkipping {len(failed)} failing examples (see out/verify-report.json): {', '.join(failed[:10])}"
              + (" ..." if len(failed) > 10 else ""))

    rng = random.Random(args.seed)
    train, evals, skipped_multi = [], [], 0
    for _, ex in load_examples():
        if report.get(ex["id"], {}).get("status") != "pass":
            continue
        messages = [{"role": m["role"], "content": m["content"].rstrip() + "\n"} for m in ex["messages"]]
        if rng.random() < args.system_ratio:
            messages = [{"role": "system", "content": rng.choice(NEUTRAL_SYSTEM_PROMPTS)}] + messages

        if args.format == "prompt-response":
            convo = [m for m in messages if m["role"] != "system"]
            if len(convo) != 2:
                skipped_multi += 1
                continue
            record = {"id": ex["id"], "category": ex["category"], "prompt": convo[0]["content"],
                      "response": convo[1]["content"]}
        else:
            record = {"id": ex["id"], "category": ex["category"], "messages": messages}

        (evals if stable_fraction(ex["id"]) < args.eval_ratio else train).append(record)

    rng.shuffle(train)
    OUT_DIR.mkdir(exist_ok=True)
    for name, records in (("train.jsonl", train), ("eval.jsonl", evals)):
        with open(OUT_DIR / name, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    passed = [v for v in report.values() if v["status"] == "pass"]
    stats = {
        "train": len(train), "eval": len(evals), "failed": len(failed),
        "categories": Counter(v["category"] for v in passed),
        "patterns": Counter(p for v in passed for p in v["patterns"]),
        "languages": Counter(v.get("language") for v in passed),
        "verified": Counter(lvl for v in passed for lvl in v["verified"]),
    }
    (OUT_DIR / "stats.json").write_text(json.dumps(stats, indent=1))
    print(f"\nWrote {len(train)} train / {len(evals)} eval examples to {OUT_DIR}"
          + (f" (skipped {skipped_multi} multi-turn for prompt-response)" if skipped_multi else ""))
    sys.exit(0)


if __name__ == "__main__":
    main()
