# Green AI Training

**A coding assistant that writes energy-efficient code, trained on real energy measurements.**

Most "green coding" advice comes from rules of thumb. Some are true, some only true sometimes, and some are wrong.
This repository takes a different approach:

1. We write small benchmarks that each isolate one coding decision (e.g. `+=` vs `"".join()` in Python,
   `SELECT *` vs named columns in SQL, single vs double quotes in Bash).
2. We measure their energy use on dedicated lab machines with the
   [Green Metrics Tool (GMT)](https://www.green-coding.io/products/green-metrics-tool/).
3. We turn those measurements into training conversations and fine-tune open coding models on them.

The result is a family of models that pick the energy-efficient option by default, know when an optimization
is *not* worth it, and only quote energy numbers that were actually measured.

**Contents**

- [Try the models](#try-the-models)
  - [Online playground](#online-playground)
  - [Run locally with Ollama](#run-locally-with-ollama)
- [Use the skill file with Claude, ChatGPT & co.](#use-the-skill-file-with-claude-chatgpt--co)
- [Where the energy numbers come from](#where-the-energy-numbers-come-from)
- [Explore the data yourself: Energy ID](#explore-the-data-yourself-energy-id)
- [Benchmark index](#benchmark-index)
- [Measurement results](#measurement-results)
- [Running a benchmark yourself](#running-a-benchmark-yourself)
- [Training your own model](#training-your-own-model)
- [Test cases](#test-cases)
- [Background](#background)

---

# Try the models

All models are published on Hugging Face: **https://huggingface.co/green-coding**

| Model | Base model | Quantization | Download size |
|---|---|---|---|
| [Green-Coding-Qwen2.5-Coder-7B-Q4_K_M](https://huggingface.co/green-coding/Green-Coding-Qwen2.5-Coder-7B-Q4_K_M) | Qwen2.5-Coder 7B Instruct | Q4_K_M | 4.7 GB |
| [Green-Coding-Qwen2.5-Coder-7B-Q6_K](https://huggingface.co/green-coding/Green-Coding-Qwen2.5-Coder-7B-Q6_K) | Qwen2.5-Coder 7B Instruct | Q6_K | 6.3 GB |
| [Green-Coding-Gemma4-12B-Q4_K_M](https://huggingface.co/green-coding/Green-Coding-Gemma4-12B-Q4_K_M) | Gemma 4 12B | Q4_K_M | 7.4 GB |
| [Green-Coding-Gemma4-12B-Q6_K](https://huggingface.co/green-coding/Green-Coding-Gemma4-12B-Q6_K) | Gemma 4 12B | Q6_K | 9.8 GB |
| [Green-Coding-Qwen2.5-Coder-14B-Q4_K_M](https://huggingface.co/green-coding/Green-Coding-Qwen2.5-Coder-14B-Q4_K_M) | Qwen2.5-Coder 14B Instruct | Q4_K_M | 9.0 GB |
| [Green-Coding-Qwen2.5-Coder-14B-Q6_K](https://huggingface.co/green-coding/Green-Coding-Qwen2.5-Coder-14B-Q6_K) | Qwen2.5-Coder 14B Instruct | Q6_K | 12.1 GB |

**Which one should I pick?** `Q4_K_M` files are smaller and faster. `Q6_K` files are closer to the full-precision
model. If you're unsure, start with the **7B Q4_K_M** model. It runs on most laptops with 8 GB of free RAM.
Use the 12B / 14B models if you have 16 GB or more.

## Online playground

Want to try it without installing anything? Use the playground at **https://www.green-coding.ai**

> [!NOTE]
> **Be patient. The playground is slow on purpose.**
> It runs on low-energy infrastructure that is switched off when nobody uses it.
> - If the machine is already running, a typical answer takes **about 2 minutes**.
> - If the machine has to boot and load the model first, the first answer can take **about 20 minutes**.
> - You can check the status of the machine the model runs on the [Green Metrics Tool - Cluster Status Page](https://metrics.green-coding.io/cluster-status.html)
>     - Look out for the *ML/AI Benchmarking - GTX-1080* machine
>
> Later requests are fast again as long as the machine stays up.

## Run locally with Ollama

[Ollama](https://ollama.com/download) is the easiest way to run the models on your own computer.

Ollama can pull every model straight from Hugging Face. One command downloads and starts it:

```bash
ollama run hf.co/green-coding/Green-Coding-Qwen2.5-Coder-7B-Q4_K_M
```

The first start downloads the model (4.7 GB to 12.1 GB). After that it starts right away. The chat template comes along
automatically.

All models:

```bash
ollama run hf.co/green-coding/Green-Coding-Qwen2.5-Coder-7B-Q4_K_M
ollama run hf.co/green-coding/Green-Coding-Qwen2.5-Coder-7B-Q6_K
ollama run hf.co/green-coding/Green-Coding-Gemma4-12B-Q4_K_M
ollama run hf.co/green-coding/Green-Coding-Gemma4-12B-Q6_K
ollama run hf.co/green-coding/Green-Coding-Qwen2.5-Coder-14B-Q4_K_M
ollama run hf.co/green-coding/Green-Coding-Qwen2.5-Coder-14B-Q6_K
```

Once the `>>>` prompt appears, set the recommended temperature (see below) and ask something, for example:

```
>>> /set parameter temperature 0.2
>>> Review this Python function for energy efficiency:
    def build(items):
        s = ""
        for i in items:
            s += str(i)
        return s
```

`ollama pull hf.co/green-coding/<model>` only downloads a model, and `ollama list` shows what you have.

### Recommended setting: temperature 0.2

We recommend a **temperature of 0.2**. A low temperature keeps answers focused and consistent, which matters
for code and for quoting measured figures correctly. The models don't set it themselves, so set it in one of these ways:

- **Inside an interactive `ollama run` session** (applies until you exit):
  ```
  >>> /set parameter temperature 0.2
  ```
- **Permanently, as your own model name:** save the setting once in a `Modelfile`:
  ```
  FROM hf.co/green-coding/Green-Coding-Qwen2.5-Coder-7B-Q4_K_M
  PARAMETER temperature 0.2
  ```
  ```bash
  ollama create green-coding -f Modelfile
  ollama run green-coding
  ```
  The examples below use this name `green-coding`. If you skip this step, use the full `hf.co/…` name instead.
- **Through the Ollama API:**
  ```bash
  curl http://localhost:11434/api/chat -d '{
    "model": "green-coding",
    "messages": [{"role": "user", "content": "Is a set faster than a list for membership tests in Python?"}],
    "options": {"temperature": 0.2},
    "stream": false
  }'
  ```
- **From Python** (`pip install ollama`):
  ```python
  import ollama
  response = ollama.chat(
      model='green-coding',
      messages=[{'role': 'user', 'content': 'Optimize this SQL query for energy: SELECT * FROM orders'}],
      options={'temperature': 0.2},
  )
  print(response['message']['content'])
  ```
- **In tools that use Ollama** (Open WebUI, Continue, …): look for a *temperature* field in the model settings.

---

# Use the skill file with Claude, ChatGPT & co.

If you don't want to run one of our models, you can give the same knowledge to a general-purpose LLM instead.
[`SKILL.md`](SKILL.md) is a skill file. It holds the measured patterns of this repository, when each one pays off,
and a fixed output format for energy savings. It reads the figures from
[`skill-references/measured-facts.md`](skill-references/measured-facts.md), a copy of
[`dataset/spec/measured-facts.md`](dataset/spec/measured-facts.md).

| | Fine-tuned models | Skill file |
|---|---|---|
| Runs on | your machine (Ollama) or green-coding.ai | any capable LLM: Claude, ChatGPT, … |
| Green behavior | built in, no prompt needed | loaded as instructions with each task |
| Savings output | measured figures, not scaled to your code | measured figures **plus** a labeled estimate per run and per year |
| Updating the facts | retrain | edit or re-copy one Markdown file |

> **Using your own local model?** The [Ollama RAG chat](llm-tools/README.md) works with any Ollama model that
> supports tool calling, with no fine-tuning and without the full skill. The model looks up the matching measurement
> through a tool call and quotes the figures straight from it, so the numbers stay true to the measurements.

## How to use it

Always keep `SKILL.md` and the `skill-references/` folder together. The skill reads the facts from there.

**Claude Code**

```bash
mkdir -p ~/.claude/skills/green-code-energy
cp -r SKILL.md skill-references ~/.claude/skills/green-code-energy/
```

To use it in a single project only, copy the files to `<project>/.claude/skills/green-code-energy/` instead.
Claude loads the skill automatically when you ask it to optimize or review code, or to estimate energy savings.
You can also call it directly with `/green-code-energy`.

**Claude apps (claude.ai, Desktop)**

Package the skill as a ZIP file and upload it under *Settings → Capabilities → Skills*:

```bash
mkdir green-code-energy && cp -r SKILL.md skill-references green-code-energy/
zip -r green-code-energy.zip green-code-energy
```

**ChatGPT and other LLMs**

These tools don't read the skill format natively, but the files are plain Markdown, so they work as instructions:

- **ChatGPT:** create a *Project* or *Custom GPT*. Paste the content of `SKILL.md` into its instructions and upload
  `skill-references/measured-facts.md` as a file.
- **Any other chat or API:** send `SKILL.md` as the system prompt and add `measured-facts.md` to the context.
- **Coding agents that read `AGENTS.md`:** add a line pointing to `SKILL.md`, for example
  *"For optimization and code review tasks, follow `SKILL.md`."*

Then ask as usual, for example:

```
Optimize test-cases/sample-code/run.py. It runs about 1,000 times a day in production.
```

## What output to expect

The skill works in three modes:

- **Optimize / refactor:** you get the rewritten code with a minimal diff, then an **Energy Report**.
- **Generate:** you get new code that uses the efficient construct from the start, followed by short **Green Notes**.
- **Review:** you get findings ranked `[Bug]` / `[Security]` / `[High]` / `[Medium]` / `[Low]`, each with
  location, issue, fix and the measured figure, plus a list of patterns that were checked and need no change.

The Energy Report looks like this:

```markdown
| # | Change | Where | Measured per unit (before → after) | Saving per unit | Units per run | Saving per run | Source |
|---|--------|-------|------------------------------------|-----------------|---------------|----------------|--------|
| 1 | `+=` → `"".join()` | `build_report()` L12 | ~469 µJ → ~1.8 µJ per piece | ~467 µJ | 50,000 pieces | ~23 J | F-STRCAT |
| 2 | row-by-row INSERT → COPY | `save_orders()` L40 | ~768 µJ → ~34 µJ per row | ~734 µJ | 20,000 rows | ~15 J | F-PG-INSERT |
| 3 | `if x in list` (3 lookups) | `check()` L70 | not applied: set conversion costs more than 3 scans | — | — | — | F-MEMB |

**Total per run:** ~38 J (~0.011 Wh) of CPU energy
**Scaled (assumed 10,000 runs/day):** ~380 kJ/day ≈ 0.11 kWh/day ≈ 38 kWh/year
**Carbon (assumed 0.4 kg CO2e/kWh, replace with your grid intensity):** ≈ 15 kg CO2e/year
```

It also names the change with the largest saving, a confidence level, the patterns it deliberately did *not* apply
(and why), and how to measure the real saving yourself. "Measured per unit" is always taken from a fact. Everything
to its right is an estimate: the model multiplies the measured figure by the units it counted in your code and by
the run frequency you gave (or an assumed one, which it labels). It shows the calculation so you can plug in your
own numbers.

If you don't say how often the code runs or how big the data is, the model makes an assumption and labels it rather
than blocking. You get better estimates if you mention prototype vs. production, runs per day and data sizes
right away.

## Limitations

- **It does not show the model's own energy use.** The report covers only what your code saves when it runs. The
  energy the LLM uses to read your code and write the answer (inference) is not included, and a skill file cannot
  measure it. To see the energy of the inference itself, run the model through the
  [Green Metrics Tool](https://www.green-coding.io/products/green-metrics-tool/) yourself or use
  **https://www.green-coding.ai**, which reports the inference energy. For small
  savings on rarely run code, the inference can cost more energy than the change will ever save.
- **The estimates are extrapolations.** The per-unit figures come from micro-benchmarks on one lab machine, as
  CPU package energy (RAPL) only: no RAM, disk, network or idle baseline. Your hardware, runtime version and data
  shape will differ. Treat the result as an order of magnitude, and measure if the decision matters.
- **Only benchmarked patterns get numbers.** Changes outside the
  [benchmark index](#benchmark-index), such as a better algorithm, are described in direction only
  (e.g. "O(n²) → O(n)"), without an energy figure.
- **The model can still make mistakes.** A skill file is instructions, not a guarantee. General-purpose models can
  quote a figure wrongly or get the arithmetic wrong, which happens most often in multi-step calculations. Check the
  numbers against `measured-facts.md` (every figure carries a fact ID) before you report them.
- **It adds context.** `SKILL.md` and the facts file together are about 44 KB (roughly 10,000 tokens), which adds
  energy and cost to every request that loads them.
- **The facts are a snapshot.** `skill-references/measured-facts.md` is a copy of the export from October 2026.
  Re-copy it when `dataset/spec/measured-facts.md` changes.
- **It is not a measurement or carbon accounting tool.** For real numbers, measure with the Green Metrics Tool,
  or with [Eco CI](https://github.com/green-coding-solutions/eco-ci-energy-estimation) in CI pipelines.

---

# Where the energy numbers come from

The model is told never to make up energy figures. Every number it quotes comes from a real measurement:

```
benchmarks/  ──►  Green Metrics Tool  ──►  data/*.csv  ──►  dataset/spec/measured-facts.md  ──►  training examples  ──►  model
(scenarios)       (lab machines)          (raw export)      (31 rounded, sourced facts)          (cite facts by ID)
```

1. **Benchmarks.** Each folder in [`benchmarks/`](benchmarks/) holds GMT `usage_scenario` files that run one coding
   variant at a time and report how much work was done (iterations, rows, page loads, …).
2. **Measurement.** The scenarios run on the
   [GMT measurement cluster](https://metrics.green-coding.io/cluster-status.html): dedicated bare-metal
   machines tuned for repeatable results. The Micro Benchmarking machine, for example, has TurboBoost, Hyper-Threading
   and DVFS switched off. Click the (ℹ︎) icon on the cluster page for each machine's specs and configuration.
3. **Export.** [`data/query.sql`](data/query.sql) pulls the latest run of every benchmark from the GMT database into
   [`data/green-coding-measurement-data.csv`](data/green-coding-measurement-data.csv) (export of October 2026).
4. **Facts.** The raw values are condensed into
   [`dataset/spec/measured-facts.md`](dataset/spec/measured-facts.md): 31 facts, each with rounded figures, the test
   conditions, a link to the GMT measurement and a link to the benchmark code.
5. **Training data.** Training conversations in [`dataset/examples/`](dataset/examples/) may only quote numbers
   from these facts, and must list the fact IDs they use. [`dataset/scripts/verify.py`](dataset/scripts/verify.py)
   rejects any example with an energy, percentage or multiplier figure that is not in a cited fact. The current
   build has 1,683 training and 201 evaluation conversations.

### Which energy does the model talk about?

Unless an answer says otherwise, the figures are **CPU energy measured with Intel RAPL**
(GMT metric `cpu_energy_rapl_msr_component`). RAPL reports the energy of the **whole CPU package**: the cores plus the
on-chip parts such as caches and memory controller. It does **not** include RAM (DRAM), disks, network,
GPU or the power supply.

A few facts also quote **machine energy**: the whole server, measured at the wall socket with an AC power meter
(GMT metric `psu_energy_ac_mcp_machine`). The model labels these as machine energy.

Keep in mind that the figures describe *our* benchmark on *our* lab machine. They show which option is cheaper and
by roughly how much. They are not a prediction for your workload, which is why the model doesn't scale them to
your code. To know the saving in your setup, measure it, for example with the Green Metrics Tool.

---

# Explore the data yourself: Energy ID

Many of these measurements, and many more for popular open-source software, can be browsed in the online
**Energy ID** database: **https://www.green-coding.io/products/energy-id/**

Energy ID lists software by *tasks* (a typical use case) and shows energy, CO₂ and the SCI score for each, with links
to the full GMT measurement. Here are three examples. The first two are part of the model's training data. The third
is additional data that could go into future training rounds.

## Example 1: Bash single vs. double quotes

Bash scans text in double quotes for `$`, backticks and backslashes. Text in single quotes is taken as it is.
The benchmark assigns a 6,200-character string in a loop, once with `"…"` and once with `'…'`.

Results on the *Micro Benchmarking* machine (CPU package energy, RAPL):

| Loop iterations | Double quotes `"…"` | Single quotes `'…'` | Saving |
|---|---|---|---|
| 10,000 | 3.70 J (3,702,875 µJ) | 3.19 J (3,185,342 µJ) | **14.0 %** |
| 100,000 | 31.91 J (31,909,778 µJ) | 24.36 J (24,356,357 µJ) | **23.7 %** |
| 1,000,000 | 313.73 J (313,731,454 µJ) | 236.88 J (236,883,261 µJ) | **24.5 %** |

A second machine (*High Performance Benchmarking*) confirms it: over the whole run, 593.82 J with double quotes vs.
453.73 J with single quotes, **23.6 %** less.

**Takeaway:** use single quotes for any string that doesn't need variable expansion. The absolute saving is small
for a script that runs once and grows with string length and loop count. This is fact `F-BASH-QUOTES` in the
training data.

**Sources:**
- Energy ID: [Bash](https://www.green-coding.io/products/energy-id/detail/?id=44&name=Bash)
- GMT measurements: [double quotes](https://metrics.green-coding.io/stats.html?id=dd9bbb4e-b056-4067-8ad2-7b1818a86f10),
  [single quotes](https://metrics.green-coding.io/stats.html?id=b265ef9b-adb9-4b56-a14b-ae34fdaa7247),
  [comparison of all four runs (both machines)](https://metrics.green-coding.io/compare-simple.html?ids=dd9bbb4e-b056-4067-8ad2-7b1818a86f10,b265ef9b-adb9-4b56-a14b-ae34fdaa7247,28d92c15-79d7-44ca-8f43-a733fe2e265a,a9533378-71f0-49df-bd5f-1e5f27cda9c2)
- Benchmark code: [`benchmarks/bash/`](benchmarks/bash/)

## Example 2: PostgreSQL INSERT, row by row vs. batched

A Python client (psycopg 3) inserts rows into PostgreSQL 16 in 100 batches, with one commit per batch. Three
variants are compared: one `execute()` per row (loop), `executemany()`, and `COPY … FROM STDIN`.

Results on the *Micro Benchmarking* machine (CPU package energy, RAPL):

| Batch size (total rows) | Loop: one `INSERT` per row | `executemany()` | `COPY` |
|---|---|---|---|
| 100 rows (10,000) | 13.36 J | 15.32 J | **9.51 J** |
| 1,000 rows (100,000) | 90.15 J | 32.70 J | **17.26 J** |
| 5,000 rows (500,000) | 384.06 J, 60.2 s | 138.57 J, 17.7 s | **17.33 J, 3.1 s** |

With batches of 5,000 rows, `COPY` used **22× less energy** than the loop and 8× less than `executemany()`, which in
turn used 2.8× less than the loop. With batches of 1,000 rows, `COPY` used 5.2× less than the loop.

With batches of only 100 rows the picture changes. `COPY` still saves 28.8 %, but `executemany()` used 14.7 % *more*
energy than the plain loop, because the fixed cost of each batch outweighs the per-row work.

**Takeaway:** batch writes pay off when there are many rows per batch. For a handful of rows the simple loop is fine.
Knowing when an optimization is *not* worth it is just as much part of the training as recommending one. This is
fact `F-PG-INSERT` in the training data.

**Sources:**
- Energy ID: [PostgreSQL](https://www.green-coding.io/products/energy-id/detail/?id=9&name=PostgreSQL)
- GMT measurements: [loop](https://metrics.green-coding.io/stats.html?id=8e80b599-3332-432f-8c7e-1cfb93a3a354),
  [executemany](https://metrics.green-coding.io/stats.html?id=8b4c205d-5fb1-40af-ab77-0427ca572f4e),
  [COPY](https://metrics.green-coding.io/stats.html?id=adff4e53-2f1a-4d88-9c0d-dd681d02923f),
  [comparison of all three](https://metrics.green-coding.io/compare-simple.html?ids=8e80b599-3332-432f-8c7e-1cfb93a3a354,8b4c205d-5fb1-40af-ab77-0427ca572f4e,adff4e53-2f1a-4d88-9c0d-dd681d02923f)
- Benchmark code: [`benchmarks/sql/`](benchmarks/sql/)

## Example 3: KeyDB vs. other key-value stores (Memtier benchmark), candidate for future training

[memtier_benchmark](https://github.com/RedisLabs/memtier_benchmark) sends as many requests as it can to a
key-value store for about a minute. The same benchmark was run against KeyDB, Redis, Valkey, DragonflyDB and
Memcached on the *High Performance Benchmarking* machine.

| Store | CPU energy (RAPL) | Operations served | Energy per operation |
|---|---|---|---|
| **KeyDB** | 3,030.39 J | 14,309,718 | **211.8 µJ** |
| Memcached | 3,023.43 J | 14,465,827 | 209.0 µJ |
| DragonflyDB | 2,965.24 J | 11,040,565 | 268.6 µJ |
| Redis | 2,376.28 J | 8,061,985 | 294.8 µJ |
| Valkey | 2,330.70 J | 7,830,341 | 297.7 µJ |

Looking only at total energy, KeyDB seems the *worst* choice: it used 27.5 % more CPU energy than Redis. But in the
same time it served 77.5 % more operations. Per operation, KeyDB needed **28.2 % less energy than Redis**
(211.8 µJ vs. 294.8 µJ) and 28.9 % less than Valkey.

**Takeaway:** always compare energy *per unit of useful work*, not just total energy. A faster system can use more power
and still be the more efficient one. Every benchmark in this repository reports its work units for that reason.

> This example is not yet part of the training data: it comes from Energy ID's broader software database, not from
> the 31 facts in `measured-facts.md`. Measurements like this one (whole software products compared on the same
> workload) are additional data that could be added in future training rounds, so the model could also advise on
> choosing between tools, not only on code constructs.

**Sources:**
- Energy ID: [KeyDB](https://www.green-coding.io/products/energy-id/detail/?id=36&name=KeyDB) (the detail page also
  lists the comparable stores)
- GMT measurements: [KeyDB](https://metrics.green-coding.io/stats.html?id=925ce3e1-babd-4c67-8989-3c5bb55e3fab),
  [Redis](https://metrics.green-coding.io/stats.html?id=ac1e53b3-80b0-4736-a703-81efc89e7748),
  [Valkey](https://metrics.green-coding.io/stats.html?id=c1bc4ba2-a1e9-4e27-b3f3-f539d4d38cac),
  [DragonflyDB](https://metrics.green-coding.io/stats.html?id=cad72ec3-2daa-42f1-9fa2-c4ef731f63f8),
  [Memcached](https://metrics.green-coding.io/stats.html?id=8bbf92c3-2156-4dcf-9f38-aafd487b6ce3),
  [side-by-side comparison](https://metrics.green-coding.io/compare-simple.html?ids=925ce3e1-babd-4c67-8989-3c5bb55e3fab,ac1e53b3-80b0-4736-a703-81efc89e7748,c1bc4ba2-a1e9-4e27-b3f3-f539d4d38cac,cad72ec3-2daa-42f1-9fa2-c4ef731f63f8,8bbf92c3-2156-4dcf-9f38-aafd487b6ce3)
- Benchmark code: [KV-Bench / memtier](https://github.com/green-coding-solutions/KV-Bench/tree/main/benchmarks/memtier)

---

# Benchmark index

Each benchmark isolates one decision, so the measured energy difference can be traced to one specific code
construct. The scenarios are written for the Green Metrics Tool, but the scripts inside them run on any Linux machine.

### Python: [`benchmarks/python/`](benchmarks/python/)

| Pattern | What is compared | Scenarios |
|---|---|---|
| Caching / memoization | `functools.lru_cache` vs repeated computation | `usage_scenario-repeated-computation*.yml` |
| Attribute lookup | cached local variable vs repeated `obj.method` in a hot loop | `usage_scenario-attr-lookup-*.yml` |
| Built-in functions | `sum()` / `max()` / `any()` vs hand-written loops | `usage_scenario-builtin-functions-*.yml` |
| Efficient algorithm | dict lookup vs nested loops | `usage_scenario-efficient-algorithm-*.yml` |
| String concatenation | `+=` vs `''.join()` vs f-string | `usage_scenario-string-concat-*.yml` |
| Regex | precompiled vs inline vs forced recompile per call | `usage_scenario-regex-*.yml` |
| Membership testing | `x in list` vs `x in set` | `usage_scenario-membership-*.yml` |
| Import styles | `import module` vs `from module import *` | `usage_scenario-import-*.yml` |
| HTTP requests | synchronous `urllib` vs asynchronous `httpx` | `usage_scenario-http-requests-*.yml` |
| Conditionals | `if/elif` chain vs `match` statement | `usage_scenario-if-statement.yml`, `usage_scenario-match-statement.yml` |
| Exceptions as control flow | `try/except KeyError` vs `dict.get()` vs `if key in dict` | `usage_scenario-exception-flow-*.yml` |
| List operations | `.append()` vs `.insert(0, …)` | `usage_scenario-list-append.yml`, `usage_scenario-list-insert.yml` |
| PyTorch inference | with vs without `torch.no_grad()` | `usage_scenario-pytorch-*.yml` |
| Quantization | pure NumPy loop vs Numba JIT | `usage_scenario-quantize-*.yml` |

### SQL: [`benchmarks/sql/`](benchmarks/sql/)

| Pattern | What is compared | Scenarios |
|---|---|---|
| Column selection | `SELECT *` vs named columns vs number of columns | `usage_scenario-select-*.yml` |
| Insert batching | one `INSERT` per row vs `executemany()` vs `COPY` | `usage_scenario-insert-*.yml` |

### Bash: [`benchmarks/bash/`](benchmarks/bash/)

| Pattern | What is compared | Scenarios |
|---|---|---|
| Quote style | single quotes vs double quotes | `usage_scenario-single-quotes.yml`, `usage_scenario-double-quotes.yml` |
| Subprocesses | a subprocess per field vs shell builtins vs one `awk` pass | `builtins/usage_scenario-*.yml` |

### Web and browser: [`benchmarks/web/`](benchmarks/web/), [`benchmarks/browser/`](benchmarks/browser/), [`benchmarks/image-formats/`](benchmarks/image-formats/)

| Pattern | What is compared | Folder |
|---|---|---|
| Animations | CSS vs JavaScript-driven | `browser/animation/` |
| Image formats, rendering | PNG / WebP / GIF / JPG / AVIF in headful and headless browsers | `image-formats/` |
| Image formats, encoding | converting between formats with ImageMagick | `image-formats/` |
| DOM size | 10,000 rows vs paginated | `web/dom-size/` |
| Web fonts | TTF vs WOFF2 subsets vs system font stack | `web/fonts/` |
| Lazy images | eager vs `loading="lazy"` | `web/lazy-images/` |
| Minification | source vs minified JavaScript | `web/minify/` |
| Text compression | none vs gzip per request vs precompressed | `web/text-compression/` |
| Unused CSS | full stylesheet vs purged | `web/unused-css/` |

See [`benchmarks/web/README.md`](benchmarks/web/README.md) for details.

### Infrastructure: [`benchmarks/infra/`](benchmarks/infra/)

| Pattern | What is compared | Folder |
|---|---|---|
| Container images | unoptimized Dockerfile vs slim, layered image | `infra/container-image/` |
| Preview environments | full stack per branch vs minimal | `infra/minimize-environments/` |

### Sample code: [`benchmarks/sample-code/`](benchmarks/sample-code/)

| Variant | Scenario |
|---|---|
| Order processing baseline (unoptimized) | `usage_scenario-run.yml` |
| Same code after generic AI optimization | `usage_scenario-run-ai-optimized.yml` |
| Same code after energy-aware Green AI optimization | `usage_scenario-run-green-ai-optimized.yml` |

### Planned

| Pattern | Notes |
|---|---|
| Image download / network transfer cost | Impact of file size on network energy |
| JS → Rust recompilation | Cost per line of code and break-even point |
| Carbon-aware job scheduling | Delay non-critical jobs to low-carbon windows |

---

# Measurement results

- **All runs:** [Green Metrics Tool dashboard](https://metrics.green-coding.io/runs.html?&uri=green-ai-training&show_archived=false&show_other_users=true)
  (constantly updated)
- **Facts used for training:** [`dataset/spec/measured-facts.md`](dataset/spec/measured-facts.md), each with a link to
  its measurement
- **Raw export:** [`data/green-coding-measurement-data.csv`](data/green-coding-measurement-data.csv)
- **Older table view:** [data snapshot from 12 June 2026](https://metrics.green-coding.io/compare-simple.html?ids=bf7da9ad-390d-4522-9efe-637d2d84de33%2C7f2a2410-7de8-4c41-8549-4d1bf6f76c06%2C67365d1b-2ff4-4501-a1ca-eaebc13e4e67%2C308ded0b-5342-4f94-8a6e-45deca7aeca4%2Ce940138a-16aa-42e1-8a4f-af570f2e731a%2C168daf0d-865d-49f1-94c9-aba10eaa7bf9%2C26bae94a-54ca-423b-9890-0fd29ca51a15%2C82dba456-b7c1-4551-bc56-13ec416d5763%2Ca1f7dde2-6c93-4f0c-be58-60afc5280cf8%2C0ea9e29d-6934-4d5c-930d-c74a96332a17%2Cc2e43427-2191-4e8a-85bb-c009fb5d2529%2Ca0e9521c-40df-4c8d-8be2-cef9ec1582f9%2Ccc578ba3-3f81-4f93-be02-9259b30bbe97%2C27276e38-026f-4fbb-919c-f2669de5d944%2Cb738e7b5-c5e8-43f7-8f53-2925c8d65418%2C6eada168-e871-4894-a1eb-dd7da6aeee18%2C54c8433e-2ce5-4937-a945-fe91ed0caa07%2C4a2085fd-6f43-4f26-a3ee-2a6fcd7db594%2C58ee50a2-7110-4418-beea-df6ffba5425a%2C93744ee5-31e6-4c06-ac16-faab8d0bdff6%2C6d24c0eb-91ef-416a-8298-d37e57845d29%2Ccbafe025-7fc2-4967-bb11-700ef16fe74e%2C24038a7d-f5e2-484d-a9b6-3b37845083d4%2Ce3185fd1-c310-4ac7-b18b-a7cf88b4ee12%2C01dcb1c9-8746-457f-8cc7-bc24b1e00818%2Cc8b7a64c-25a9-49c2-9706-d103e51e3790%2C57163e60-dc9e-4a38-aae0-3f041e62baf5%2Ccccd6121-0b69-4735-9a6b-54e683e64fc7%2C669071d8-9273-4523-aff3-c1d44511f05c%2C6db1e251-b7b6-4ae1-96df-393a833dc730%2C11c00aa6-5d67-497f-a934-52e9df617fec%2Cf88accba-5864-4d56-baca-0a1903656ccd%2C8543fcf5-f92f-47c3-ac93-5c0cc689b1c8%2Cac1f3351-3fe3-4582-a7e0-14da2492e580%2Cf4e8135a-04de-44fd-bc27-83742417d37f%2C28d92c15-79d7-44ca-8f43-a733fe2e265a%2C1644f237-a289-4bb2-b79c-de7cbabcac65%2Ca9533378-71f0-49df-bd5f-1e5f27cda9c2%2C84899848-09c6-48d4-a691-cb367400ff41%2C1ded9ca6-6232-467d-a1b1-3f362be9a001%2C4acbc4bf-0eb8-4487-a166-ee80fe8dfa5e%2C2b5917ea-8237-46e3-8cd0-5fa5ca47f8de%2C8151346a-dde7-43fb-9126-7966bd780e2c%2C7921e61c-2db3-4322-9cea-703a5e77e76c%2C81a932bc-04da-443b-93cf-d4d8468de247%2C54102c15-25be-4283-9688-024ecef3f205%2C59acd135-b276-4a25-82f9-3a57bd7a0d9c%2Cea3e2364-dcd6-4837-ba13-74909a99d075%2Cc038dec4-76d6-4efa-8390-5cd1c0888cbb%2Ca57f1820-884a-4c5f-bb18-a2b63690f323%2Cf25bb603-8904-43a5-bae9-1d4db05fdb59%2Cf8dd6a6c-193c-4b2e-8a54-3d081a81412b%2Ca0976832-3020-4e8d-ab9d-afff114ac269%2Cb31ca361-1745-4fac-8e6b-a97ec99bf476%2Cb3db38a3-f77e-49f8-a013-e5ea275aa39e%2C4464055e-5cde-4f35-847d-8390b32f89a2%2C4bde5059-6cef-48a2-82ae-1199035ad287%2Cd77a7951-be7f-4d01-b021-e488b1969361%2C352798c6-d90f-458e-ad13-f0d849da37ab%2C6851ecdc-7a86-4d73-b34e-a422bdae5461%2Ce8f8a428-098b-483a-bfb7-9bdb4168c093%2C3de5c7f2-7d81-4d92-95f5-cdd2136966f7&metrics=cpu_utilization_procfs_system%2Ccpu_energy_rapl_msr_component%2Ccpu_power_rapl_msr_component%2Cmemory_power_rapl_msr_component%2Cphase_time_syscall_system)

### Structured data (JSON)

Every run has a JSON endpoint. Example for
[Bash double quotes](https://metrics.green-coding.io/stats.html?id=26bae94a-54ca-423b-9890-0fd29ca51a15):
https://api.green-coding.io/v1/phase_stats/single/26bae94a-54ca-423b-9890-0fd29ca51a15

### Badges

To cite a measurement, you can embed a live badge. Example for the CPU package energy of
[Bash double quotes](https://metrics.green-coding.io/stats.html?id=26bae94a-54ca-423b-9890-0fd29ca51a15):

![CPU energy badge](https://api.green-coding.io/v1/badge/single/26bae94a-54ca-423b-9890-0fd29ca51a15?metric=cpu_energy_rapl_msr_component)

On every run page, the *Badges* tab has the snippets ready to copy and paste.

---

# Running a benchmark yourself

With the [Green Metrics Tool installed](https://docs.green-coding.io/docs/installation/), point the runner at this
repository and pick a scenario file:

```bash
python3 runner.py --uri /path/to/green-ai-training \
  --filename benchmarks/python/usage_scenario-string-concat-join.yml \
  --name "String concat join"
```

See the [GMT documentation](https://docs.green-coding.io) for all options.

For a quick test without GMT you can also run the scripts directly: the Python scripts in the `scripts` folders and
the shell scripts are plain programs.

---

# Training your own model

The full pipeline lives in this repository:

| Step | Folder | Guide |
|---|---|---|
| 1. Build the training dataset | [`dataset/`](dataset/) | [`dataset/README.md`](dataset/README.md) |
| 2. Fine-tune with LoRA (unsloth) | [`fine-tuning/`](fine-tuning/) | [`fine-tuning/README.md`](fine-tuning/README.md) |
| 3. Evaluate the model | [`evaluation/`](evaluation/) | [`evaluation/README.md`](evaluation/README.md) |

Logs of the published training runs are in [`training-logs/`](training-logs/).

> [!IMPORTANT]
> Use **Python 3.12** for the whole training pipeline. As of 2026 there are
> [open bugs](https://github.com/huggingface/datasets/issues/8373) that make it unusable in Python 3.14 and likely
> also in Python 3.13.

---

# Test cases

We use these test cases to check the model.

### In-sample

[`test-cases/`](test-cases/) contains code for each benchmarked pattern, together with **example prompts** and the
**expected output**.

### Out-of-sample

- https://github.com/shldigital/promprint-data-wrangling
  - **Example prompt:** *Look at the repository in https://github.com/shldigital/promprint-data-wrangling and please
    optimize it according to green coding standards.*
  - **Expected output:** Optimized code with annotations, or an additional file stating the expected energy and
    carbon savings.

---

# Background

## Why this project?

Energy measurements of programming primitives and infrastructure decisions help human and AI developers write more
energy-efficient code. Many popular green coding rules are only true under certain conditions. For example, compressing
data costs energy, so it only pays off if the data is stored long enough. Read the full reasoning in
[CONCEPT.md](CONCEPT.md).

## Design principles

- **Isolation:** one operation per scenario, no side effects
- **Composability:** scenarios are independent and can be combined
- **Normalization:** every scenario reports work units, so results can be compared across hardware
- **Reproducibility:** all services run locally, with no external network dependencies unless intended

## Sources

- https://patterns.greensoftware.foundation/
- https://github.com/green-code-initiative/creedengo-rules-specifications/blob/main/RULES.md
- https://s2group.cs.vu.nl/AwesomeAndDarkTactics
- https://arxiv.org/html/2506.08790v1

Possible future sources:

- https://github.com/green-code-initiative/creedengo-python/issues/154

## Funding

The work for this repository was funded by the
[BRAID - Sustainable AI futures](https://www.bathspa.ac.uk/news-and-events/news/ai-research-grant/) grant
(UKRI grant number UKRI569).
