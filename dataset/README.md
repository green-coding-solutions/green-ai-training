# Green Coding SFT Dataset

Instruction dataset for LoRA fine-tuning a chat model (Gemma 3/4, Qwen2.5-Coder) so that it picks energy-efficient solutions by default
when writing, reviewing or refactoring code, knows when a pattern does *not* pay off, and never invents energy numbers.

The behavior is taught through conversations, not through the rule texts. The rules in `spec/` are only given to the
teacher (a human author or `generate.py`). The training data has no system prompt that mentions green coding.

## Layout

```
spec/
  gsf-green-code-skill.md   GSF rules (MIT, Green Software Foundation), teacher input only
  house-rules.md            target behavior, caveats, numbers policy, response formats (wins over GSF)
  measured-facts.md         GMT measurements from ../data/green-coding-measurement-data.csv, the only allowed figures
  taxonomy.yaml             categories + mix, pattern ids, languages, domains
examples/                   conversation sources (YAML, several documents per file)
  generated/                output of generate.py
scripts/
  verify.py                 automatic checks, writes out/verify-report.json
  build.py                  verified examples -> out/train.jsonl, out/eval.jsonl, out/stats.json
  generate.py               teacher-model generation via the Anthropic API (batch or sync)
  generate_agent_sdk.py     same via the Claude Agent SDK (Claude subscription instead of API credits)
out/                        build output
```

## Setup

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

## Workflow

```bash
venv/bin/python scripts/verify.py              # check all examples (cached, re-runs on change)
venv/bin/python scripts/build.py               # write out/train.jsonl and out/eval.jsonl

cd ../fine-tuning
python3 train_unsloth.py --model unsloth/Qwen2.5-Coder-7B-Instruct \
  --dataset ../dataset/out/train.jsonl --eval-dataset ../dataset/out/eval.jsonl
```

Scaling up with a teacher model (costs API credits, `ANTHROPIC_API_KEY` or `ant auth login`):

```bash
venv/bin/python scripts/generate.py plan --n 1500        # job matrix following taxonomy.yaml weights
venv/bin/python scripts/generate.py run --mode sync --limit 10   # small test run first, review the output
venv/bin/python scripts/generate.py run --mode batch     # the rest, Message Batches API (half price)
venv/bin/python scripts/generate.py collect              # when the batch has finished
venv/bin/python scripts/verify.py examples/generated
venv/bin/python scripts/generate.py repair               # one repair attempt per failing example
```

With a Claude Pro/Max subscription instead of API credits, use `generate_agent_sdk.py` (Claude Agent SDK, uses the
account Claude Code is logged in with; no batch mode, counts against the subscription's usage limits):

```bash
claude                                   # log in once (/login), then exit
unset ANTHROPIC_API_KEY                  # otherwise the API key is billed
venv/bin/python scripts/generate_agent_sdk.py plan --n 300
venv/bin/python scripts/generate_agent_sdk.py run --limit 10
venv/bin/python scripts/generate_agent_sdk.py run      # stops at the usage limit, rerun after the reset
venv/bin/python scripts/verify.py examples/generated
venv/bin/python scripts/generate_agent_sdk.py repair
```

Read a sample of generated examples before training on them. The verifier catches broken code and policy violations,
not subtle wrong advice.

Verification executes the code from the examples. For generated examples, run it in a container or as a user without
access to anything important (see `../evaluation/README.md`).

## Example format

```yaml
id: refactor-py-new-customers-001
category: refactor              # see taxonomy.yaml
language: python
patterns: [set-membership]      # taxonomy pattern ids
facts: [F-MEMB]                 # required if the assistant quotes a measured figure
messages:
  - role: user
    content: |
      ...
  - role: assistant
    content: |
      ...
verify:                         # optional
  test: |                       # asserts run after the answer's code
  equivalence: {driver: ...}    # original (user code) and answer print the same output
  benchmark: {driver: ..., min_speedup: 3}   # answer must use measurably less CPU time
  sql: {setup: ..., compare: true}           # run in SQLite, compare result sets
  static_only: "reason"         # code that needs network, GPUs or unavailable tools
```

`verify.py` docstring lists all options (`module`, `setup`, `green_block`, `original_code`, `lang`, ...).

## What verify.py checks

- **Schema:** known categories and pattern ids, alternating roles, ends with the assistant.
- **Style:** Green Notes in generation/refactor answers, severity headers in reviews, *no* Green Notes or
  sustainability talk in general answers, language tags on code blocks, no leaked spec or fact ids.
- **Numbers:** every energy, percentage or multiplier figure in an answer must appear in a cited fact or in the
  user's own message.
- **URLs:** GSF pattern links must be in the taxonomy. Green Metrics Tool and benchmark links
  (`metrics.green-coding.io`, `github.com/green-coding-solutions`) must be copied verbatim from a cited fact.
- **Syntax:** Python, JavaScript, bash, JSON, YAML, SQLite.
- **Execution:** tests, output equivalence between original and answer, CPU-time benchmarks.
- **Contamination:** user code must not be a near copy of `../test-cases` (the evaluation set).
- **Duplicates:** near-identical prompts across the dataset.

Dockerfiles, HTML/CSS, Go, Java, TypeScript and nginx configs are only reviewed by hand (`static-only`).
