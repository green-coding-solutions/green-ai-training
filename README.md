# Green AI Training

This repository contains minimal benchmarks designed to capture energy costs of minimal code and
infrastructure building blocks.

This includes:
- Programming language primitives like variable assignments, loops, incrementation etc
- Typical code functionality like executing network requests, loading libraries, etc.
- Specific language building blocks like memory cost for DOM nodes, rendering and download cost of images in a web-page etc.
- System level building blocks like the cost of running a full additional core, idling a system, running unthrottled downloads etc.

In summary scenarios isolate primitive workloads so that measured energy can be attributed to specific code
constructs and mapped back to source-level operations.

The benchmarks are designed for the [Green Metrics Tool (GMT)](https://www.green-coding.io/projects/green-metrics-tool/)
but when extracted from their *YAML* files can be run in any linux environment.

## Benchmark Index

### Python — `benchmarks/python/`

| Pattern / Case | Scenarios | Status |
|---|---|---|
| **Caching / Memoization** — `functools.lru_cache` vs repeated computation | `usage_scenario-repeated-computation*.yml` | ✅ |
| **Attribute Lookup** — cached local variable vs repeated `obj.method` in hot loop | `usage_scenario-attr-lookup-*.yml` | ✅ |
| **String Concatenation** — `+=` vs `''.join()` vs f-string | `usage_scenario-string-concat-*.yml` | ✅ |
| **Regex** — precompiled vs inline (Python cache active) vs forced recompile per call | `usage_scenario-regex-*.yml` | ✅ |
| **Membership Testing** — `if x in list` O(n) vs `if x in set` O(1) | `usage_scenario-membership-*.yml` | ✅ |
| **Import Styles** — `from module import name` (namespace) vs `from module import *` (star) | `usage_scenario-import-*.yml` | ✅ |
| **HTTP Requests** — synchronous (`urllib`) vs asynchronous (`httpx`) | `usage_scenario-http-requests-*.yml` | ✅ |
| **Conditionals** — chain of `if/elif` (20 branches) vs `match` statement | `usage_scenario-if-statement.yml`, `usage_scenario-match-statement.yml` | ✅ |
| **Exception Flow as Control** — `try/except KeyError` vs `dict.get()` vs `if key in dict` | `usage_scenario-exception-flow-*.yml` | ✅ |
| **List Operations** — `.append()` vs `.insert(0, ...)` | `usage_scenario-list-append.yml`, `usage_scenario-list-insert.yml` | ✅ |
| **PyTorch Inference** — with `torch.no_grad()` vs without | `usage_scenario-pytorch-*.yml` | ✅ |
| **Quantization** — pure NumPy loop vs Numba JIT-compiled | `usage_scenario-quantize-*.yml` | ✅ |

### SQL — `benchmarks/sql/`

| Pattern / Case | Scenarios | Status |
|---|---|---|
| **SELECT column selection** — `SELECT *` vs named columns vs extra unused columns | `usage_scenario-select-*.yml` | ✅ |
| **INSERT batching** — single-row loop vs bulk insert | `usage_scenario-insert-*.yml` | ✅ |

### Bash — `benchmarks/bash/`

| Pattern / Case | Scenarios | Status |
|---|---|---|
| **Quote style** — single quotes (no substitution scan) vs double quotes | `usage_scenario-single-quotes.yml`, `usage_scenario-double-quotes.yml` | ✅ |

### Browser / JavaScript — `benchmarks/browser/animation/`

| Pattern / Case | Scenarios | Status |
|---|---|---|
| **Animation approach** — CSS animations vs JavaScript-driven animations | `usage_scenario-css.yml`, `usage_scenario-js.yml` | ✅ |

### Image Formats — `benchmarks/image-formats/`

| Pattern / Case | Scenarios | Status |
|---|---|---|
| **Rendering cost** — PNG / WebP / GIF / JPG / AVIF in headful and headless browser | `usage_scenario-headful.yml`, `usage_scenario-headless.yml` | ✅ |
| **Encoding cost** — converting between formats via ImageMagick (CPU only) | `usage_scenario-encoding.yml` | ✅ |
| **Download / network transfer cost** — format file size impact on bandwidth energy | — | ⭕️ planned |

### Sample Code — `benchmarks/sample-code/` and `sample-code/`

| Pattern / Case | Scenarios | Status |
|---|---|---|
| **Order processing baseline** — unoptimized reference implementation | `usage_scenario-run.yml` | ✅ |
| **AI-optimized** — same code after generic Claude AI optimization | `usage_scenario-run-ai-optimized.yml` | ✅ |
| **Green AI-optimized** — same code after energy-aware Green AI optimization | `usage_scenario-run-green-ai-optimized.yml` | ✅ |

### Planned / Not Yet Implemented

| Pattern / Case | Notes |
|---|---|
| **JS → Rust recompilation** | Cost per line of code + amortization breakeven point |
| **Carbon-aware job scheduling** | Delay non-critical jobs to low-carbon windows via an internal queue |


## Purpose and gains

The basic energy information about programming language primitives as well as infrastructure decisions shall
aid human and AI developers in creating more energy efficient code.

Please read details in [CONCEPT.md](/CONCEPT.md)


## Results

The results are online in the [Green Metrics Tool Cluster Dashboard](https://metrics.green-coding.io/runs.html?&uri=green-ai-training&show_archived=false&show_other_users=true)

## Running a scenario

Scenarios are executed via the Green Metrics Tool CLI. Example for a single Python scenario:

```bash
green-metrics-tool run python/usage_scenario-sort.yml
```

Refer to the [GMT documentation](https://docs.green-coding.io) for installation and full usage instructions.

## Design principles

- **Isolation** — one primitive operation per scenario, no side effects
- **Composability** — scenarios are independent and can be combined if needed
- **Normalization** — all scenarios report work units so energy measurements are comparable across hardware
- **Reproducibility** — all services are local; no external network dependencies unless explicitly intended

## Sources

- https://patterns.greensoftware.foundation/
- https://github.com/green-code-initiative/creedengo-rules-specifications/blob/main/RULES.md
- https://s2group.cs.vu.nl/AwesomeAndDarkTactics
- https://arxiv.org/html/2506.08790v1

## Possible future sources

- https://github.com/green-code-initiative/creedengo-python/issues/154

## Funding Notice

The work for this repository was funded by the [BRAID - Sustainable AI futures](https://www.bathspa.ac.uk/news-and-events/news/ai-research-grant/)
grant.
