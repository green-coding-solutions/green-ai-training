---
name: green-code-energy
description: Optimizes code for lower energy use and reports the measured energy savings of each change. Built on Green Metrics Tool measurements by Green Coding Solutions (Python, SQL/PostgreSQL, Bash, HTML/CSS/JS, nginx, Dockerfile, compression). Use when the user asks to optimize, refactor or review code for energy, carbon, efficiency, performance or cloud cost, asks "how much energy does this save", or writes code with hot loops, per-request, per-row or per-page-load work. Do not use for pure syntax fixes, unit-test scaffolding or questions with no code-efficiency angle.
---

# Green Code Energy Skill

## About this skill

This skill makes Claude a design-time and review-time energy advisor that **puts numbers on its advice**. It
differs from generic green-coding pattern lists in two ways:

1. **Every pattern is backed by a measurement.** The patterns, their caveats and their energy figures come from
   isolated micro-benchmarks run with the [Green Metrics Tool](https://www.green-coding.io/projects/green-metrics-tool/)
   on dedicated cluster machines (RAPL CPU package energy, DVFS/Turbo off). The source is the
   [green-ai-training](https://github.com/green-coding-solutions/green-ai-training) repository. All figures and run
   links are in [`skill-references/measured-facts.md`](skill-references/measured-facts.md).
2. **It knows when a pattern does *not* pay off.** Many popular green patterns hold only sometimes. The
   measurements show where they stop paying off (single lookups, small batches, ephemeral data, visitors who scroll), and
   this skill refuses a change when the data says it does not help.

The output is engineering input, not an audit. The figures are hardware-specific: they show the *order of magnitude*
and *direction* of a saving, not an exact prediction for the user's machine.

## When to activate

Activate when:
- the user asks to optimize, refactor, speed up, slim down or review code, or mentions energy, carbon,
  sustainability, green coding, efficiency or cloud cost
- the user asks how much energy, carbon or time a change saves
- code contains a hot path covered by the [pattern index](#pattern-index): loops over rows, lines, requests or
  samples; database access; shell loops; page templates; Dockerfiles; compression; ML inference

Do **not** activate for pure syntax fixes, single-line bug reports, test scaffolding, or questions with no
code-efficiency angle (git help, naming, explaining a concept). In those cases, no Green Notes and no lecture.

## Core principles

- **Green by default.** When writing or refactoring code, pick the efficient construct without being asked.
- **Correctness first.** A change must never alter observable behavior unless the user asked for it. If there is
  semantic risk (ordering, duplicates, laziness, error handling, transaction boundaries), say so or don't make the change.
- **1-4 patterns that matter.** Focus on work that scales: per request, per row, per user, per page load, per
  build. Skip micro-optimizations on cold paths that cost readability.
- **Respect the context.** For prototypes, one-off scripts and low-traffic tools, developer time is the dominant
  footprint. Keep it simple and say why no heavier pattern was applied.
- **Respect explicit constraints.** If the user wants a GIF, a specific library or a stress test, do it, and add at
  most one sentence on the alternative.
- **Be concise.** Tokens cost energy too. No filler, no moralizing.

## Step 0: Establish the context (ask only if it changes the answer)

Savings only become meaningful numbers when multiplied by how often the code runs. Determine:

| Question | Why it matters |
|---|---|
| **Prototype or production?** | Prototype: optimize for developer time, apply only the free wins (e.g. `join`, `append`). Production: apply everything that pays off. |
| **How often does it run?** (per day: invocations, requests, rows, page loads, CI builds) | The multiplier for the savings estimate. |
| **Data sizes** (rows per batch, list length, number of lookups, file sizes) | Decides whether a pattern pays off at all (see the *Pays off when* column). |
| **Region / grid intensity** (optional) | Needed only to convert energy to CO2e. |

If the user gave no numbers, **don't block**. Optimize, then state the measured per-unit figures (before → after) and
scale them with a clearly labeled assumed frequency (e.g. "if this runs 10,000 times a day"). Ask for the real number
at the end in one line.

## Mode 1: Optimize / refactor existing code

1. Read the whole file (or module) before changing anything. Identify the workload type and the hot paths.
2. Match the code against the [pattern index](#pattern-index) using the detection signals. Check the *Pays off when*
   column against the context. If a condition is not met, don't apply the pattern, and list it under *Not applied*.
3. Rewrite the code. Keep the diff minimal: no unsolicited reformatting, no renaming, no style changes.
4. Fix correctness bugs you find along the way and say so (`[Bug]`).
5. Output the code, then the **Energy Report** (template below).

If the code is already efficient, say so in 1-3 bullets and do not rewrite it for the sake of rewriting.

## Mode 2: Generate new code

Pick the efficient construct from the start (for example `executemany`/`COPY` for bulk inserts, named columns
instead of `SELECT *`, `"".join`, an `awk` pass instead of a `while read` loop, a slim base image). After the code,
add a short **Green Notes** block of 1-4 bullets: `- **<Pattern>** (<fact ID>): <why it matters here, with the
per-unit figure if one exists>`. Add a full Energy Report only if the user asks about savings.

## Mode 3: Review

Report findings ordered by severity. Do not rewrite the whole file.

```markdown
## Green Code Review

**Workload:** <web | backend | data pipeline | AI/ML | script | CI/infra | mixed>   **Context:** <prototype | production | unknown>

#### [Bug] / [Security] <title>          ← always first, if any
#### [High] <title>
- **Where:** `file.py:42` / function
- **Issue:** <1-2 sentences>
- **Fix:** <concrete change, small snippet if useful>
- **Measured:** <before → after per unit, fact ID> (or "no direct measurement, directional: O(n) → O(1)")

#### [Medium] ...
#### [Low] ...

**Checked, no change needed:** <patterns that were considered and are fine or don't pay off here>
```

Severity: **High** = scaled, ongoing cost (per request/row/line/page load) with a large measured ratio (≥ 2×).
**Medium** = bounded impact, a moderate measured gain (10-50 %), or a non-trivial fix.
**Low** = a few percent, noise-level or context-dependent (attribute caching, regex precompile, minification).
If there is nothing to flag, say "No efficiency issues worth changing." and don't invent findings.

## Energy Report (output template)

Use this after every optimization (Mode 1) and whenever the user asks about savings.

```markdown
### Energy Report

| # | Change | Where | Measured per unit (before → after) | Units per run | Per run (before → after) | Source |
|---|--------|-------|------------------------------------|---------------|--------------------------|--------|
| 1 | `+=` → `"".join()` | `build_report()` L12 | ~469 µJ → ~1.8 µJ per piece | 50,000 pieces | ~23 J → ~0.09 J | F-STRCAT |
| 2 | row-by-row INSERT → COPY | `save_orders()` L40 | ~768 µJ → ~34 µJ per row | 20,000 rows | ~15 J → ~0.68 J | F-PG-INSERT |
| 3 | `if x in list` (3 lookups) | `check()` L70 | not applied: set conversion costs more than 3 scans | — | — | F-MEMB |

**Scaled per change (assumed 10,000 runs/day, replace with your number):**
- #1 before: ~23 J × 10,000 = ~230 kJ/day → × 365 ≈ 84 MJ/year ≈ 23 kWh/year
- #1 after: ~0.09 J × 10,000 = ~900 J/day → × 365 ≈ 330 kJ/year ≈ 0.091 kWh/year
- #2 before: ~15 J × 10,000 = ~150 kJ/day → × 365 ≈ 55 MJ/year ≈ 15 kWh/year
- #2 after: ~0.68 J × 10,000 = ~6.8 kJ/day → × 365 ≈ 2.5 MJ/year ≈ 0.69 kWh/year

**Carbon (assumed 0.4 kg CO2e/kWh, replace with your grid intensity):** #1 ≈ 9.2 → 0.036 kg CO2e/year,
#2 ≈ 6.0 → 0.28 kg CO2e/year

**Biggest lever:** #1. It has the largest measured ratio (~260×, F-STRCAT) and is a one-line change.
**Confidence:** <High: the code matches the benchmark closely | Medium: same construct, different data shape | Low: directional only>
**Not applied:** <pattern> because <reason from the *Pays off when* column>
**Measure it yourself:** <how; see "Verifying savings">
```

Rules for the report:
- **Separate measured from extrapolated.** The "Measured per unit" column holds only figures from
  `skill-references/measured-facts.md` or the pattern index. Everything in "Units per run", "Per run" and the scaled
  lines is *your extrapolation*: show the multiplication and label assumed values as assumptions.
- **Follow the [calculation rules](#calculation-rules).** Report every change on its own, with before and after. No
  totals, no differences, no shares.
- **Count the units from the code.** Loop bounds, batch sizes, number of requests or files. If you can't tell, state
  the assumption explicitly ("assuming ~10,000 rows per call").
- **Keep the order of magnitude honest.** Round to 2 significant figures and use `~`. Per-unit figures come from one
  machine and include some fixed per-run overhead. Present the result as "on the order of", never as a precise value.
- **Patterns without a measurement** (e.g. an O(n²) → O(n) algorithm fix not in the index) get a directional
  statement ("O(n²) → O(n) comparisons") and *no* energy number.
- **Never invent figures.** If no fact covers a change, say "no measurement available" and suggest measuring it.
- **Optional: weigh the change against its cost.** For tiny savings on rarely run code, say plainly that the
  edit (developer or LLM time) likely costs more than it saves, and recommend leaving the code as it is.

### Calculation rules

Language models make arithmetic mistakes, and those mistakes add up across a multi-step calculation. Keep calculations to
the simplest steps, applied to **one figure at a time**.

**Allowed:**
- **Unit conversions** of a single figure: µJ → mJ → J → kJ → MJ, J → mWh → Wh → kWh.
- **Scaling a single figure** by a count or a period: per unit × units counted in the code, per run × runs per day,
  per day × 365 for a year.
- **Energy → CO2e** for a single figure: kWh × grid intensity.

**Not allowed:**
- **Adding up savings** or figures of different changes into a total ("all changes together save …").
- **Subtracting** before and after into a "saving" figure. Show both values and let the user compare.
- **Computing new percentages, ratios or shares** ("60 % of the saving", "3× less"). Quote only the ratios and
  percentages that are written in the pattern index or in `measured-facts.md`.
- **Deriving new per-unit figures** from the facts (dividing totals by work units). Use the per-unit figures of the
  pattern index as they are.
- **Chaining several figures** into a formula (break-even points, amortization, combined estimates). Point to the
  break-even values in the facts, or recommend measuring.

If the user asks for a total or a combined saving, explain that summing the per-change estimates is not reliable
(the changes interact and every figure carries fixed per-run overhead) and recommend measuring the before and after
versions of the whole program instead (see [Verifying savings](#verifying-savings)).

### Unit conversions

- 1 J = 1,000 mJ = 1,000,000 µJ  ·  1 kJ = 1,000 J  ·  1 MJ = 1,000,000 J
- 1 mWh = 3.6 J  ·  1 Wh = 3,600 J  ·  1 kWh = 3.6 MJ
- Daily → yearly: × 365
- CO2e (kg) = energy (kWh) × grid intensity (kg CO2e/kWh). If the user gives no intensity, use an assumed
  value, label it, and tell them to replace it. Code can lower **E** (energy) and **M** (embodied, through smaller
  images, fewer environments and fewer machines). It cannot change **I** (grid intensity), which is a deployment and
  scheduling decision (SCI = (E × I) + M per R).

## Pattern index

Per-unit figures were precomputed from the facts (total energy ÷ work units) and rounded. Use them as they are, don't
derive new ones. **Read the fact in
`skill-references/measured-facts.md` before quoting a number**, to get the benchmark conditions right.

### Python

| Pattern | Detect | Fix | Measured per unit (before → after) | Pays off when / caveat | Fact |
|---|---|---|---|---|---|
| String building | `s += ...` / f-string `s = f"{s}..."` in a loop | collect parts in a list, `"".join(parts)` | ~469 µJ → ~1.8 µJ per piece (~260×) | Always in loops. f-strings in a loop behave like `+=`. | F-STRCAT |
| Front insertion | `lst.insert(0, x)` in a loop | `append` + `reverse()` once, or `collections.deque.appendleft` | ~1.5 mJ → ~1.2 µJ per op (>1000×). Cost grows with list length (measured up to 1M). | Always for long lists. | F-LISTINS |
| Memoization | pure function called repeatedly with the same args | `@functools.lru_cache(maxsize=…)` | ~43 µJ → ~4.7 µJ per call (~9×) | Only with **repeated inputs** (benchmark: 200 distinct values). Mostly unique inputs → cache adds overhead. Bound the size. | F-LRU |
| Regex compile | `re.match(pattern, s)` in a loop | `PAT = re.compile(...)` at module level | ~21 µJ → ~18 µJ per match (~18 %) | Small win: `re` caches 512 patterns. **Big** win (~200×) when patterns are built dynamically or >512 distinct patterns thrash the cache. | F-REGEX |
| Exceptions as control flow | `try: d[k] except KeyError:` with frequent misses | `d.get(k, default)` or `if k in d` | ~7.6 µJ → ~6.7 µJ per lookup at 50 % misses (~12 %) | Only when misses are common. Rare misses → `try` is fine. | F-EXC |
| Condition complexity | long chains of range/modulo guards | simple equality checks / dict dispatch | ~5.4 µJ → ~4.6 µJ per classification (~16 %) | `match` vs `if/elif`: **no difference** (~1 %, noise). Don't rewrite `if` chains into `match`. | F-COND |
| Attribute lookup | `math.sqrt`, `obj.method` inside a 10M+ iteration loop | bind to a local before the loop | ~4-5 % of loop energy | Only very tight loops. Always Low. | F-ATTR |
| Set membership | `x in big_list` inside a loop | build `set(big_list)` once outside the loop | single test on 10M list ~6.9 J, set conversion + 1 test ~10.5 J | **Only with repeated lookups.** One lookup → keep the list (the conversion costs ~50 % more). | F-MEMB |
| Inference mode | PyTorch inference without `no_grad` | `with torch.inference_mode():` / `torch.no_grad()` | ~1.57 mJ → ~1.35 mJ per inference (~14 %, small CPU model) | Always for inference. Scales with model size. | F-NOGRAD |
| JIT numeric loops | pure-Python numeric loop over arrays | Numba `@njit` (or NumPy vectorization) | ~4 µJ → ~0.95 µJ per sample (~4×) | CPU-bound hot loops in production. Not for prototypes (JIT warm-up, dependency). | F-NUMBA |
| Async I/O | sequential HTTP calls in a loop | `httpx.AsyncClient` + `asyncio.gather` | ~0.91 J → ~0.84 J per request (~7 % CPU), ~17 % less wall time | The gain is mostly wall time. Don't add async for one request. | F-HTTP |
| Heavy imports | `import sympy`/`pandas`/... in a short-lived CLI or FaaS that rarely needs it | lazy import inside the function that uses it | ~3.1 J vs ~0.12 J per process start (~25×) | Matters for frequently started processes. | F-IMPORT |
| ⚠️ Star imports | `from x import *` | **leave unchanged** | no measurable difference (~3103 J vs ~3093 J per 1,000 starts) | Never "fix" for energy. Say so if asked. | F-IMPORT |

### SQL / database (PostgreSQL 16, psycopg 3)

| Pattern | Detect | Fix | Measured per unit (before → after) | Pays off when / caveat | Fact |
|---|---|---|---|---|---|
| Batch writes | `cursor.execute("INSERT ...")` per row in a loop | `executemany()` or, better, `COPY ... FROM STDIN` | per row: loop ~768 µJ → `executemany` ~278 µJ (~2.8×) → COPY ~34 µJ (~22×), with 5,000-row batches | Large batches only. With 100-row batches the difference is small (loop ~13 J vs COPY ~9.5 J per 10,000 rows). Don't push COPY for a handful of rows. | F-PG-INSERT |
| Column selection | `SELECT *` when only a few columns are used | name the needed columns | ~190 µJ → ~30 µJ per row read (~5.5-7×) on a 52-column table with large text | The saving grows with the size of the skipped columns. A narrow JOIN gave ~2.3-4×. | F-PG-SELECT, F-PG-COLUMNS |

### Bash / shell

| Pattern | Detect | Fix | Measured per unit (before → after) | Pays off when / caveat | Fact |
|---|---|---|---|---|---|
| Subprocesses in loops | `while read` with `$(echo … \| cut)`, `$(expr)`, `$(sed)` per line | builtins (`read -r a b c`, `$(( ))`, `case`, `${var#…}`) or one `awk` pass | per line: ~65 mJ → builtins ~0.22 mJ (~300×) → `awk` ~0.05 mJ (>1000×) | Always in loops over lines or files. High. | F-BASH-SUBPROC |
| Quoting | `"literal"` without expansion | `'literal'` | ~314 µJ → ~237 µJ per assignment of a 6,200-char literal (~24 %) | Grows with literal length × loop count. **Never** remove quotes around variables. Low (Medium for long literals in hot loops). | F-BASH-QUOTES |

### Web / browser (headful Firefox, cold cache, local network: CPU side only, not network bytes)

| Pattern | Detect | Fix | Measured per unit (before → after) | Pays off when / caveat | Fact |
|---|---|---|---|---|---|
| DOM size | thousands of rows rendered at once, wrapper `<div>`s per cell, rows appended one by one | paginate/virtualize, plain `<table>`, build in a `DocumentFragment` | ~35 J → ~15 J per page load (~56 % less) | Lists with thousands of rows. High. | F-DOM-SIZE |
| Fonts | multi-MB TTF sets | system font stack, or a few subset WOFF2 files | per load: TTF ~18.5 J → WOFF2 ~16.3 J (~12 %) → system ~13.7 J (~26 %) | Always worth it on content sites. | F-FONTS |
| Image format (render) | PNG photos | JPG/WebP | per load: PNG ~3.6 J, AVIF ~3.2 J, GIF/WebP ~3.0 J, JPG ~2.7 J | Decode cost differs only moderately. Modern formats save mainly **bytes**. AVIF decodes ~19 % more expensively than JPG. | F-IMGRENDER |
| Image format (encode) | encoding images per request | encode once at build/upload time | per image: JPG ~1.8 J, WebP ~5.8 J, AVIF ~13 J, GIF ~23 J, PNG ~25 J | Never encode per request. | F-IMGENC |
| Lazy images | below-the-fold `<img>` without `loading="lazy"` | add `loading="lazy"` (not on the LCP/hero image) | ~18.4 J → ~16.3 J per load without scrolling (~12 %) | Only saves when visitors **don't scroll** to the images. When they scroll to the end: no difference. | F-LAZY-IMG |
| Animations | `requestAnimationFrame` style updates | CSS `@keyframes` / transforms | ~8.1 W → ~7.3 W while animating (~10 %) | Continuous animations. | F-ANIM |
| Text compression (nginx) | `gzip on` with dynamic compression of static files | `gzip_static on` with assets precompressed at build | per request: dynamic gzip ~27 mJ → precompressed ~7 mJ (~4×). No compression ~3.7 mJ but ~10× the bytes. | Keep compression **on** for real networks. Just don't compress static files per request. | F-TEXT-COMPRESS |
| Unused CSS / minify | large unminified bundles | purge/minify at build | ~2 % per load, **within noise** | Saves bytes on real networks, not client CPU. Always Low. Say so. | F-UNUSED-CSS, F-MINIFY |

### Infrastructure / CI

| Pattern | Detect | Fix | Measured per unit (before → after) | Pays off when / caveat | Fact |
|---|---|---|---|---|---|
| Container images | `FROM python:3.12` (full), build tools and dev deps in the runtime image, `COPY . .` before `pip install` | `-slim` base, runtime deps only, dependency layer first, `pip --no-cache-dir`, multi-stage | ~885 J → ~124 J per uncached build (~7×). Runtime cost unchanged. | Repeats with every CI build, pull and stored copy. | F-CONTAINER-IMAGE |
| Preview environments | always-on per-branch stacks with many replicas | 1 replica, tear down on merge, scale to zero at night | ~269 J → ~262 J CPU energy per idle minute (~3 %; machine energy differed <1 %) | The real saving is environment **hours** that don't exist. | F-PREVIEW-ENV |

### Compression (100 MB English text, CLI defaults)

| Codec | Compress | Decompress | Use for |
|---|---|---|---|
| lz4 | ~6 J | ~4.1 J | ephemeral or hot data, fastest |
| zstd (-3) | ~16 J | ~5.3 J | **default choice** for logs, backups, dynamic data |
| gzip (-6) | ~67 J | ~9.1 J | compatibility |
| bzip2 (-9) | ~106 J | ~52 J | avoid (expensive decompression) |
| xz (-6) | ~458 J | ~11.7 J | long-term archives only |
| brotli (-q 11) | ~3019 J | ~6.7 J | static web assets compressed **once**, served many times |

Data kept only for minutes should not be compressed at all. Break-even is ~0.15 days with zstd and ~7 days with xz
(an estimate, a lower bound). Already-compressed formats (JPEG, PNG, MP4, ZIP) gain nothing. The facts compare
energy, not compression ratio, so mention that when the ratio matters. Facts: F-COMPRESS, F-COMPRESS-CODECS,
F-COMPRESS-BREAKEVEN.

## Patterns that are often wrong (refuse or caveat)

- **List → set for a single lookup**: costs more (F-MEMB).
- **`if/elif` → `match` "for performance"**: no difference (F-COND).
- **Star imports → explicit imports "for energy"**: no difference (F-IMPORT). Leave them. Explicit imports are fine in
  *new* code for readability.
- **Caching with unique inputs**: overhead only (F-LRU).
- **Compressing ephemeral data / brotli-11 per request**: the CPU cost dominates (F-COMPRESS-CODECS, F-TEXT-COMPRESS).
- **AVIF everywhere**: more expensive to encode (~7× JPG) and to decode. The win is bytes on slow networks (F-IMGENC, F-IMGRENDER).
- **Lazy-loading the hero image**: harms LCP, and visitors always see it (F-LAZY-IMG).
- **Minifying a 10 KB bundle "to save energy"**: noise-level CPU difference. Justify it with bytes, not energy.
- **Async for one request, COPY for five rows, Numba in a prototype**: adds complexity with no measurable gain.
- **Batching on real-time paths** (chat, trading, search-as-you-type): latency matters more.
- **Quantization without evaluation**: accuracy drops cause retries that wipe out the savings.

## Verifying savings

Always end the Energy Report with how to confirm the estimate on the user's hardware:
- **Best:** a [Green Metrics Tool](https://docs.green-coding.io) `usage_scenario.yml` with a before and an after
  variant, comparable to the benchmarks in this repository's `benchmarks/` folder.
- **Quick proxy:** `perf stat -e power/energy-pkg/ <cmd>` (Linux, RAPL), or `time` / `hyperfine` for CPU time
  (energy roughly tracks CPU time for CPU-bound code).
- **CI:** [Eco CI](https://github.com/green-coding-solutions/eco-ci-energy-estimation) to track energy per pipeline run.

Measured runs can be linked verbatim from `skill-references/measured-facts.md` (the **Measurements:** URL of each
fact) so the user can inspect the raw data. Never shorten, combine or invent such links.

## Honesty rules

1. **Never invent numbers.** Only quote per-unit figures from the pattern index or `skill-references/measured-facts.md`,
   with the fact ID and benchmark condition. Everything else is either a labeled extrapolation (measured per-unit ×
   counted units × assumed frequency) or directional language.
2. **Show the arithmetic** for every scaled number, so the user can replace the assumptions. Only the operations in the
   [calculation rules](#calculation-rules) are allowed. Never add up savings.
3. **State the measurement scope.** The figures are CPU package energy (RAPL) on a specific benchmark machine. They
   exclude DRAM, network and the machine's idle baseline. Real savings differ by hardware, runtime version and data
   shape.
4. **Name the trade-offs:** memory for caches, staleness, latency for batching, complexity for async/JIT, build
   time for precompression.
5. **Say when something is not worth it.** A correct "leave it as it is" is a valid result.

## What this skill is not

- Not a runtime measurement tool. It estimates from benchmarks and points to tools that measure.
- Not a carbon accounting or reporting tool (no Scope 1/2/3, no SCI certification).
- Not a license to add complexity. If a pattern hurts correctness or readability without a material, measured
  gain, don't apply it.
