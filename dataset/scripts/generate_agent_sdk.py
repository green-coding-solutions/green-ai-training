#!/usr/bin/env python3
"""Same as generate.py, but runs the teacher through the Claude Agent SDK (the Claude Code engine) instead of the API.

With the Agent SDK the requests use the account that Claude Code is logged in with, so a Claude Pro/Max subscription
works and no API credits are needed. Usage counts against the subscription's usage limits.

Setup (once):
  venv/bin/pip install claude-agent-sdk
  claude          # log in with your Claude account (/login), then exit
  unset ANTHROPIC_API_KEY   # otherwise the API key is used and billed instead of the subscription

Steps:
  python scripts/generate_agent_sdk.py plan --n 300
  python scripts/generate_agent_sdk.py run --limit 10     # test run first, review the output
  python scripts/generate_agent_sdk.py run                # the rest, stops when the usage limit is reached
  python scripts/verify.py examples/generated
  python scripts/generate_agent_sdk.py repair             # one repair attempt for failing generated examples

`run` skips jobs that already have a file in examples/generated/, so after a usage limit simply run it again later.
There is no batch mode: batches are an API feature.
"""

import argparse
import asyncio
import json
import os
import random
import sys
import time

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKError,
    CLINotFoundError,
    RateLimitEvent,
    ResultMessage,
    TextBlock,
    query,
)

from common import OUT_DIR, load_spec_text
from generate import (
    DEFAULT_MODEL,
    JOBS_FILE,
    REPAIR_TEMPLATE,
    TEACHER_INTRO,
    build_user_prompt,
    load_reference_examples,
    pending_jobs,
    plan_jobs,
    save_example,
)


class UsageLimitReached(Exception):
    pass


def agent_options(model, effort):
    return ClaudeAgentOptions(
        system_prompt=TEACHER_INTRO + "\n\n" + load_spec_text(),  # replaces the Claude Code system prompt
        model=model,
        effort=effort,
        thinking={"type": "adaptive"},
        tools=[],               # plain text generation, no file or shell access
        max_turns=1,
        setting_sources=[],     # ignore CLAUDE.md, user/project settings, hooks
        cwd=str(OUT_DIR),
    )


async def ask(prompt, options):
    """Returns (text, cost_usd). text is None on errors."""
    text, cost = [], None
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            if message.error:
                print(f"  ! {message.error}")
            text += [b.text for b in message.content if isinstance(b, TextBlock)]
        elif isinstance(message, RateLimitEvent):
            info = message.rate_limit_info
            if info.status == "rejected":
                resets = time.strftime("%H:%M", time.localtime(info.resets_at)) if info.resets_at else "later"
                raise UsageLimitReached(f"usage limit reached, resets at {resets}")
            if info.status == "allowed_warning" and info.utilization:
                print(f"  ! {info.utilization:.0%} of the usage limit used")
        elif isinstance(message, ResultMessage):
            cost = message.total_cost_usd
            if message.is_error:
                print(f"  ! result: {message.subtype} {message.result or ''}"[:300])
                return None, cost
    return "".join(text) or None, cost


async def run_all(items, work, workers):
    """Runs work(item) with at most `workers` in parallel. Stops starting new items after a usage limit."""
    semaphore = asyncio.Semaphore(workers)
    stop = asyncio.Event()
    totals = {"ok": 0, "failed": 0, "cost": 0.0}

    async def guarded(item):
        async with semaphore:
            if stop.is_set():
                return
            try:
                ok, cost = await work(item)
            except UsageLimitReached as e:
                if not stop.is_set():
                    print(f"■ {e}. Run the same command again after the reset to continue.")
                stop.set()
                return
            except CLINotFoundError:
                sys.exit("Claude Code CLI not found. Reinstall claude-agent-sdk (it bundles the CLI).")
            except ClaudeSDKError as e:
                print(f"  ✗ {e}"[:300])
                ok, cost = False, None
            totals["ok" if ok else "failed"] += 1
            totals["cost"] += cost or 0

    await asyncio.gather(*(guarded(i) for i in items))
    # On a subscription nothing is billed per request. The CLI still reports what the tokens would cost on the API.
    print(f"Done: {totals['ok']} ok, {totals['failed']} failed (API-equivalent cost ~${totals['cost']:.2f})")


def run(jobs, model, effort, workers):
    options = agent_options(model, effort)
    by_category, by_pattern = load_reference_examples()
    rng = random.Random(0)
    prompts = {j["id"]: build_user_prompt(j, by_category, by_pattern, rng) for j in jobs}

    async def work(job):
        text, cost = await ask(prompts[job["id"]], options)
        path = save_example(job["id"], job["category"], text) if text else None
        print(f"  {'✓' if path else '✗'} {job['id']}")
        return bool(path), cost

    asyncio.run(run_all(jobs, work, workers))


def repair(model, effort, workers):
    report_path = OUT_DIR / "verify-report.json"
    if not report_path.exists():
        sys.exit("Run scripts/verify.py examples/generated first.")
    report = json.loads(report_path.read_text())
    targets = [(k, v) for k, v in report.items()
               if v["status"] == "fail" and "/generated/" in v["file"]
               and not any(e.startswith("duplicates:") or e.startswith("contamination:") for e in v["errors"])]
    print(f"Repairing {len(targets)} examples (one attempt each)")
    options = agent_options(model, effort)

    async def work(item):
        ex_id, entry = item
        with open(entry["file"], encoding="utf-8") as f:
            example = f.read()
        prompt = REPAIR_TEMPLATE.format(errors="\n".join(f"- {e}" for e in entry["errors"]), example=example)
        text, cost = await ask(prompt, options)
        ok = bool(text and save_example(ex_id, entry["category"], text))
        print(f"  {'✓ repaired' if ok else '✗ could not repair'} {ex_id}")
        return ok, cost

    asyncio.run(run_all(targets, work, workers))
    print("Now run: python scripts/verify.py examples/generated  (delete what still fails)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_plan = sub.add_parser("plan", help="Sample a job matrix into out/jobs.jsonl (same as generate.py plan)")
    p_plan.add_argument("--n", type=int, default=300)
    p_plan.add_argument("--seed", type=int, default=1)
    p_run = sub.add_parser("run", help="Generate examples for pending jobs")
    p_run.add_argument("--limit", type=int)
    p_rep = sub.add_parser("repair", help="One repair attempt for failing generated examples")
    for p in (p_run, p_rep):
        p.add_argument("--workers", type=int, default=2)
        p.add_argument("--model", default=DEFAULT_MODEL, help="model id or alias (opus, sonnet)")
        p.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    args = parser.parse_args()

    if args.cmd in ("run", "repair") and os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is set, so requests would be billed to the API instead of your subscription.\n"
                 "Run `unset ANTHROPIC_API_KEY` first (or use generate.py for API runs).")

    OUT_DIR.mkdir(exist_ok=True)
    if args.cmd == "plan":
        jobs = plan_jobs(args.n, args.seed)
        with open(JOBS_FILE, "w") as f:
            for j in jobs:
                f.write(json.dumps(j) + "\n")
        print(f"Planned {len(jobs)} jobs in {JOBS_FILE}")
    elif args.cmd == "run":
        jobs = pending_jobs(args.limit)
        print(f"{len(jobs)} pending jobs")
        if jobs:
            run(jobs, args.model, args.effort, args.workers)
    elif args.cmd == "repair":
        repair(args.model, args.effort, args.workers)


if __name__ == "__main__":
    main()
