#!/usr/bin/env python3
"""Generates synthetic training examples with a teacher model (Claude, via the Anthropic API).

The teacher gets the spec (house rules + measured facts + taxonomy) as a cached system prompt and a job
(category, pattern, language, domain, user style) plus hand-written examples of the same category as format
reference. It returns one example in the YAML source format, which lands in examples/generated/ and then must
pass verify.py like every hand-written example.

Steps:
  python scripts/generate.py plan --n 1500              # sample a job matrix -> out/jobs.jsonl
  python scripts/generate.py run --mode batch           # submit all pending jobs as a Message Batch (50% cheaper)
  python scripts/generate.py collect                    # fetch finished batch results into examples/generated/
  python scripts/generate.py run --mode sync --limit 10 # small synchronous test run
  python scripts/verify.py examples/generated
  python scripts/generate.py repair                     # one repair attempt for failing generated examples

Credentials: ANTHROPIC_API_KEY, or a profile from `ant auth login`.
"""

import argparse
import json
import random
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic
import yaml
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

from common import EXAMPLES_DIR, OUT_DIR, dump_yaml, load_examples, load_spec_text, load_taxonomy

DEFAULT_MODEL = "claude-opus-5-5"
GENERATED_DIR = EXAMPLES_DIR / "generated"
JOBS_FILE = OUT_DIR / "jobs.jsonl"
BATCH_STATE = OUT_DIR / "batches.json"
MAX_TOKENS = 16000

TEACHER_INTRO = """You create supervised fine-tuning examples for a small open-weight coding assistant (4B-7B class, e.g. Gemma or Qwen2.5-Coder).
The goal: the student model writes, reviews and refactors code with the most energy-efficient solution by default,
knows when a green pattern does NOT apply, and never invents energy numbers.

The student is trained WITHOUT any system prompt, so the conversation itself must demonstrate the behavior.
The user never mentions these rules. The user usually does not mention "green" or "energy" at all.

Below are the spec files. Follow house-rules.md for behavior and response formats, use only facts from
measured-facts.md for figures (and list their IDs in `facts:`). Quote figures without links: no measurement,
benchmark or pattern catalog URLs in answers.
Never mention the spec files, fact IDs, or that you are generating training data inside the conversation.

Scope: the dataset only teaches what was measured. Every example is about the case a fact in measured-facts.md
measured, in one of the languages taxonomy.yaml lists for its pattern:
- The user's code contains exactly the inefficiency the benchmark measured (or, for no-change, the case where the
  fact says it does not pay off). Do not invent other refactorings or optimizations.
- Do not add findings or Green Notes for anything without a fact in measured-facts.md (no caching layers, N+1
  queries, polling, algorithm rewrites, other languages' idioms, ...). Review findings beyond the pattern are limited to
  real bugs and security problems.
- List the backing fact ids in `facts:`. Every example needs at least one fact.

## Output format

Return exactly one YAML document inside a ```yaml fence and nothing else. Schema:

```yaml
id: <given id>
category: <given category>
language: <main language>
patterns: [<pattern ids from the taxonomy>]
facts: [<fact ids backing the pattern, required>]
sql_dialect: postgres            # only if SQL is not SQLite-compatible
messages:
  - role: user
    content: |
      <realistic user message, pasted code in fenced blocks>
  - role: assistant
    content: |
      <ideal answer following house-rules.md>
verify:                          # strongly preferred for python and javascript
  module: true                   # import answer code as a module (use when it has a __main__ block)
  green_block: 0                 # index of the code block in the final answer to test (default: last)
  test: |                        # asserts appended after the answer code
  equivalence:                   # refactor/review: original (first user block) vs answer, same stdout
    driver: |
  benchmark:                     # optional, CPU time original vs answer, only for clear algorithmic wins
    driver: |
    min_speedup: 1.5
  sql: {setup: "<CREATE TABLE ...; INSERT ...>", compare: true}   # SQL: run in SQLite, compare results
  static_only: "<reason>"        # when code needs network, GPUs or packages beyond stdlib + numpy
```

Quality bar:
- The code must be correct and runnable. Equivalence drivers must print deterministic output.
- Realistic, varied user messages. Pasted code should look like real code from the given domain, not a textbook
  toy, and hide the inefficiency naturally among other code. 10-60 lines are typical.
- Answers are concise. Green Notes have 1-4 bullets. No filler, no moralizing.
- Plain, simple English. Short sentences."""

JOB_TEMPLATE = """Create one training example.

- id: {id}
- category: {category} ({category_description})
- pattern focus: {patterns}
- language: {language}
- domain: {domain}
- user style: {user_style}
{extra}
Scenarios that already exist for this pattern (do something clearly different):
{existing}

Format reference (hand-written examples of the same category):
{few_shots}"""


def client():
    return anthropic.Anthropic()


# ---------------------------------------------------------------- plan

def fill_categories(taxonomy, oversample):
    """Categories needed so that existing + new examples match the target mix without removing any."""
    have, by_pattern = defaultdict(int), defaultdict(int)
    for _, ex in load_examples():
        have[ex.get("category")] += 1
        for p in ex.get("patterns") or []:
            by_pattern[p] += 1
    weights = {c: v["weight"] for c, v in taxonomy["categories"].items()}
    total = max(have[c] / w for c, w in weights.items())
    need = {c: max(0, round(total * w) - have[c]) for c, w in weights.items()}
    print(f"Existing {sum(have.values())} examples, target {round(total)}. "
          f"New per category (before x{oversample} for failures): {need}")
    return [c for c, k in need.items() for _ in range(round(k * oversample))], by_pattern


def plan_jobs(n, seed, fill=False, oversample=1.3):
    taxonomy = load_taxonomy()
    rng = random.Random(seed)
    cats = list(taxonomy["categories"])
    weights = [taxonomy["categories"][c]["weight"] for c in cats]
    patterns = [p for p in taxonomy["patterns"] if p["languages"]]
    by_pattern = defaultdict(int)
    if fill:
        planned = fill_categories(taxonomy, oversample)
        rng.shuffle(planned[0])
        planned, by_pattern = planned
        n = len(planned)

    def pick_pattern(pool):
        # thin patterns first: weight by 1 / (1 + examples that already have the pattern)
        choice = rng.choices(pool, [1 / (1 + by_pattern[p["id"]]) for p in pool])[0] if fill else rng.choice(pool)
        by_pattern[choice["id"]] += 1
        return choice

    jobs = []
    for i in range(n):
        category = planned[i] if fill else rng.choices(cats, weights)[0]
        if category == "conceptual":
            pats, language = [pick_pattern(patterns)["id"]], "text"
        else:
            primary = pick_pattern(patterns)
            pats = [primary["id"]]
            if category in ("review", "refactor") and rng.random() < 0.4:
                second = rng.choice([p for p in patterns if set(p["languages"]) & set(primary["languages"])])
                if second["id"] != primary["id"]:
                    pats.append(second["id"])
            if category == "no-change" and rng.random() < 0.5:
                pats.append("context-tradeoff")
            language = rng.choice(primary["languages"])
        jobs.append({
            "id": f"gen-{seed}-{i:05d}-{category}",
            "category": category,
            "patterns": pats,
            "language": language,
            "domain": rng.choice(taxonomy["domains"]),
            "user_style": rng.choice(taxonomy["user_styles"]),
        })
    return jobs


# ---------------------------------------------------------------- prompts

def system_blocks():
    return [{"type": "text", "text": TEACHER_INTRO + "\n\n" + load_spec_text(),
             "cache_control": {"type": "ephemeral"}}]


def build_user_prompt(job, by_category, by_pattern, rng):
    taxonomy = load_taxonomy()
    shots = by_category.get(job["category"], [])
    shots = rng.sample(shots, min(2, len(shots)))
    few_shots = "\n\n".join("```yaml\n" + dump_yaml(ex) + "```"
                            for ex in shots) or "(none)"
    existing = []
    for p in job["patterns"]:
        existing += by_pattern.get(p, [])
    existing = "\n".join(f"- {line}" for line in existing[:25]) or "- (none yet)"
    extra = ""
    if job["category"] == "no-change":
        extra = "- make the reason concrete: already-efficient code, or a context where the pattern would not pay off\n"
    if job["category"] == "multi-turn":
        extra = "- 2-3 user turns; the user pushes back or changes requirements, the assistant adapts without nagging\n"
    return JOB_TEMPLATE.format(
        id=job["id"], category=job["category"],
        category_description=taxonomy["categories"][job["category"]]["description"],
        patterns=", ".join(job["patterns"]), language=job["language"], domain=job["domain"],
        user_style=job["user_style"], extra=extra, existing=existing, few_shots=few_shots)


def load_reference_examples():
    by_category, by_pattern = defaultdict(list), defaultdict(list)
    for path, ex in load_examples():
        first_line = ex["messages"][0]["content"].strip().splitlines()[0][:120]
        for p in ex.get("patterns") or []:
            by_pattern[p].append(first_line)
        if GENERATED_DIR not in path.parents:
            by_category[ex["category"]].append(ex)
    return by_category, by_pattern


def request_params(model, effort, user_prompt):
    return {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": system_blocks(),
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": effort},
        "messages": [{"role": "user", "content": user_prompt}],
    }


# ---------------------------------------------------------------- parse / save

def text_of(message):
    return "".join(b.text for b in message.content if b.type == "text")


def save_example(job_id, category, text):
    m = re.search(r"```ya?ml\n(.*?)\n```\s*$", text, re.DOTALL) or re.search(r"```ya?ml\n(.*)```", text, re.DOTALL)
    raw = m.group(1) if m else text
    try:
        ex = yaml.safe_load(raw)
        if not isinstance(ex, dict) or "messages" not in ex:
            raise ValueError("not an example mapping")
    except (yaml.YAMLError, ValueError) as e:
        fail_dir = OUT_DIR / "generate-failures"
        fail_dir.mkdir(parents=True, exist_ok=True)
        (fail_dir / f"{job_id}.txt").write_text(text)
        print(f"  ✗ {job_id}: could not parse YAML ({e}); raw output in {fail_dir}")
        return None
    ex["id"] = job_id
    ex["category"] = category
    path = GENERATED_DIR / category / f"{job_id}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml(ex))
    return path


def done_ids():
    return {p.stem for p in GENERATED_DIR.rglob("*.yaml")} if GENERATED_DIR.exists() else set()


def pending_jobs(limit=None):
    if not JOBS_FILE.exists():
        sys.exit("No jobs planned yet. Run: python scripts/generate.py plan --n 1500")
    submitted = set()
    if BATCH_STATE.exists():
        for b in json.loads(BATCH_STATE.read_text()).values():
            if not b.get("collected"):
                submitted.update(b["job_ids"])
    jobs = [json.loads(line) for line in JOBS_FILE.read_text().splitlines() if line.strip()]
    finished = done_ids()
    jobs = [j for j in jobs if j["id"] not in finished and j["id"] not in submitted]
    return jobs[:limit] if limit else jobs


# ---------------------------------------------------------------- run

def call_sync(c, params):
    """Streaming call with server-side refusal fallback. Returns text or None."""
    with c.beta.messages.stream(**params, betas=["server-side-fallback-2026-07-01"], fallbacks="default") as stream:
        message = stream.get_final_message()
    if message.stop_reason == "refusal":
        return None, message
    return text_of(message), message


def run_sync(jobs, model, effort, workers):
    c = client()
    by_category, by_pattern = load_reference_examples()
    rng = random.Random(0)
    prompts = {j["id"]: build_user_prompt(j, by_category, by_pattern, rng) for j in jobs}
    usage = defaultdict(int)

    def work(job):
        try:
            text, message = call_sync(c, request_params(model, effort, prompts[job["id"]]))
        except anthropic.RateLimitError:
            time.sleep(30)
            text, message = call_sync(c, request_params(model, effort, prompts[job["id"]]))
        return job, text, message

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(work, j) for j in jobs]
        for fut in as_completed(futures):
            try:
                job, text, message = fut.result()
            except anthropic.APIStatusError as e:
                print(f"  ✗ API error {e.status_code}: {e.message}")
                continue
            except anthropic.APIConnectionError as e:
                print(f"  ✗ connection error: {e}")
                continue
            for k in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"):
                usage[k] += getattr(message.usage, k, 0) or 0
            if text is None:
                print(f"  ✗ {job['id']}: refused ({message.stop_details})")
                continue
            if message.stop_reason == "max_tokens":
                print(f"  ✗ {job['id']}: hit max_tokens")
                continue
            path = save_example(job["id"], job["category"], text)
            if path:
                print(f"  ✓ {path.relative_to(EXAMPLES_DIR.parent)}")
    print("usage: " + ", ".join(f"{k}={v}" for k, v in usage.items()))


def run_batch(jobs, model, effort):
    c = client()
    by_category, by_pattern = load_reference_examples()
    rng = random.Random(0)
    requests = [
        Request(custom_id=j["id"],
                params=MessageCreateParamsNonStreaming(**request_params(model, effort,
                                                                        build_user_prompt(j, by_category,
                                                                                          by_pattern, rng))))
        for j in jobs
    ]
    batch = c.messages.batches.create(requests=requests)
    state = json.loads(BATCH_STATE.read_text()) if BATCH_STATE.exists() else {}
    state[batch.id] = {"job_ids": [j["id"] for j in jobs],
                       "categories": {j["id"]: j["category"] for j in jobs}, "collected": False}
    BATCH_STATE.write_text(json.dumps(state, indent=1))
    print(f"Submitted batch {batch.id} with {len(jobs)} requests. Collect later with: generate.py collect")


def collect():
    if not BATCH_STATE.exists():
        sys.exit("No batches submitted.")
    c = client()
    state = json.loads(BATCH_STATE.read_text())
    for batch_id, info in state.items():
        if info.get("collected"):
            continue
        batch = c.messages.batches.retrieve(batch_id)
        if batch.processing_status != "ended":
            counts = batch.request_counts
            print(f"{batch_id}: {batch.processing_status} (processing={counts.processing}, "
                  f"succeeded={counts.succeeded})")
            continue
        saved = 0
        for result in c.messages.batches.results(batch_id):
            job_id = result.custom_id
            if result.result.type != "succeeded":
                print(f"  ✗ {job_id}: {result.result.type}")
                continue
            message = result.result.message
            if message.stop_reason in ("refusal", "max_tokens"):
                print(f"  ✗ {job_id}: {message.stop_reason}")
                continue
            if save_example(job_id, info["categories"][job_id], text_of(message)):
                saved += 1
        info["collected"] = True
        print(f"{batch_id}: saved {saved}/{len(info['job_ids'])} examples to {GENERATED_DIR}")
    BATCH_STATE.write_text(json.dumps(state, indent=1))


# ---------------------------------------------------------------- repair

REPAIR_TEMPLATE = """This training example failed automatic verification. Fix it so that all checks pass while keeping
the scenario. If the problem is in the answer's code, fix the code (and the explanation if needed). If the
verification block is wrong, fix the verification block. Return the complete corrected YAML document in a
```yaml fence and nothing else.

Errors:
{errors}

Example:
```yaml
{example}
```"""


def repair(model, effort, workers):
    report_path = OUT_DIR / "verify-report.json"
    if not report_path.exists() or not report_path.stat().st_size:
        sys.exit("Run scripts/verify.py examples/generated first.")
    report = json.loads(report_path.read_text())
    targets = [(k, v) for k, v in report.items()
               if v["status"] == "fail" and "/generated/" in v["file"]
               and not any(e.startswith("duplicates:") or e.startswith("contamination:") for e in v["errors"])]
    print(f"Repairing {len(targets)} examples (one attempt each)")
    c = client()

    def work(item):
        ex_id, entry = item
        with open(entry["file"], encoding="utf-8") as f:
            example = f.read()
        prompt = REPAIR_TEMPLATE.format(errors="\n".join(f"- {e}" for e in entry["errors"]), example=example)
        text, message = call_sync(c, request_params(model, effort, prompt))
        return ex_id, entry, text

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for fut in as_completed([pool.submit(work, t) for t in targets]):
            ex_id, entry, text = fut.result()
            if text and save_example(ex_id, entry["category"], text):
                print(f"  ✓ repaired {ex_id}")
            else:
                print(f"  ✗ could not repair {ex_id}")
    print("Now run: python scripts/verify.py examples/generated  (delete what still fails)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_plan = sub.add_parser("plan", help="Sample a job matrix into out/jobs.jsonl")
    p_plan.add_argument("--n", type=int, default=1500)
    p_plan.add_argument("--seed", type=int, default=1)
    p_plan.add_argument("--fill", action="store_true",
                        help="Plan only what is missing for the target mix (thin patterns first), ignores --n")
    p_plan.add_argument("--oversample", type=float, default=1.3,
                        help="With --fill: plan this many times the gap, because some generated examples fail verify")
    p_run = sub.add_parser("run", help="Generate examples for pending jobs")
    p_run.add_argument("--mode", choices=["batch", "sync"], default="batch")
    p_run.add_argument("--limit", type=int)
    p_run.add_argument("--workers", type=int, default=4)
    sub.add_parser("collect", help="Fetch finished batches")
    p_rep = sub.add_parser("repair", help="One repair attempt for failing generated examples")
    p_rep.add_argument("--workers", type=int, default=4)
    for p in (p_run, p_rep):
        p.add_argument("--model", default=DEFAULT_MODEL)
        p.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    args = parser.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    if args.cmd == "plan":
        jobs = plan_jobs(args.n, args.seed, args.fill, args.oversample)
        with open(JOBS_FILE, "w") as f:
            for j in jobs:
                f.write(json.dumps(j) + "\n")
        print(f"Planned {len(jobs)} jobs in {JOBS_FILE}")
    elif args.cmd == "run":
        jobs = pending_jobs(args.limit)
        print(f"{len(jobs)} pending jobs")
        if jobs:
            (run_batch if args.mode == "batch" else
             lambda j, m, e: run_sync(j, m, e, args.workers))(jobs, args.model, args.effort)
    elif args.cmd == "collect":
        collect()
    elif args.cmd == "repair":
        repair(args.model, args.effort, args.workers)


if __name__ == "__main__":
    main()
