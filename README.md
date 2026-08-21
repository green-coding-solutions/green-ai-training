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


# Purpose and gains

The basic energy information about programming language primitives as well as infrastructure decisions shall
aid human and AI developers in creating more energy efficient code.

Please read details in [CONCEPT.md](/CONCEPT.md)


# Results

The results are online in the [Green Metrics Tool Cluster Dashboard](https://metrics.green-coding.io/runs.html?&uri=green-ai-training&show_archived=false&show_other_users=true)

Measurement data is constantly updated, but for easy viewing all data in a table you can see this
[data snapshot from 12th June 2026](https://metrics.green-coding.io/compare-simple.html?ids=bf7da9ad-390d-4522-9efe-637d2d84de33%2C7f2a2410-7de8-4c41-8549-4d1bf6f76c06%2C67365d1b-2ff4-4501-a1ca-eaebc13e4e67%2C308ded0b-5342-4f94-8a6e-45deca7aeca4%2Ce940138a-16aa-42e1-8a4f-af570f2e731a%2C168daf0d-865d-49f1-94c9-aba10eaa7bf9%2C26bae94a-54ca-423b-9890-0fd29ca51a15%2C82dba456-b7c1-4551-bc56-13ec416d5763%2Ca1f7dde2-6c93-4f0c-be58-60afc5280cf8%2C0ea9e29d-6934-4d5c-930d-c74a96332a17%2Cc2e43427-2191-4e8a-85bb-c009fb5d2529%2Ca0e9521c-40df-4c8d-8be2-cef9ec1582f9%2Ccc578ba3-3f81-4f93-be02-9259b30bbe97%2C27276e38-026f-4fbb-919c-f2669de5d944%2Cb738e7b5-c5e8-43f7-8f53-2925c8d65418%2C6eada168-e871-4894-a1eb-dd7da6aeee18%2C54c8433e-2ce5-4937-a945-fe91ed0caa07%2C4a2085fd-6f43-4f26-a3ee-2a6fcd7db594%2C58ee50a2-7110-4418-beea-df6ffba5425a%2C93744ee5-31e6-4c06-ac16-faab8d0bdff6%2C6d24c0eb-91ef-416a-8298-d37e57845d29%2Ccbafe025-7fc2-4967-bb11-700ef16fe74e%2C24038a7d-f5e2-484d-a9b6-3b37845083d4%2Ce3185fd1-c310-4ac7-b18b-a7cf88b4ee12%2C01dcb1c9-8746-457f-8cc7-bc24b1e00818%2Cc8b7a64c-25a9-49c2-9706-d103e51e3790%2C57163e60-dc9e-4a38-aae0-3f041e62baf5%2Ccccd6121-0b69-4735-9a6b-54e683e64fc7%2C669071d8-9273-4523-aff3-c1d44511f05c%2C6db1e251-b7b6-4ae1-96df-393a833dc730%2C11c00aa6-5d67-497f-a934-52e9df617fec%2Cf88accba-5864-4d56-baca-0a1903656ccd%2C8543fcf5-f92f-47c3-ac93-5c0cc689b1c8%2Cac1f3351-3fe3-4582-a7e0-14da2492e580%2Cf4e8135a-04de-44fd-bc27-83742417d37f%2C28d92c15-79d7-44ca-8f43-a733fe2e265a%2C1644f237-a289-4bb2-b79c-de7cbabcac65%2Ca9533378-71f0-49df-bd5f-1e5f27cda9c2%2C84899848-09c6-48d4-a691-cb367400ff41%2C1ded9ca6-6232-467d-a1b1-3f362be9a001%2C4acbc4bf-0eb8-4487-a166-ee80fe8dfa5e%2C2b5917ea-8237-46e3-8cd0-5fa5ca47f8de%2C8151346a-dde7-43fb-9126-7966bd780e2c%2C7921e61c-2db3-4322-9cea-703a5e77e76c%2C81a932bc-04da-443b-93cf-d4d8468de247%2C54102c15-25be-4283-9688-024ecef3f205%2C59acd135-b276-4a25-82f9-3a57bd7a0d9c%2Cea3e2364-dcd6-4837-ba13-74909a99d075%2Cc038dec4-76d6-4efa-8390-5cd1c0888cbb%2Ca57f1820-884a-4c5f-bb18-a2b63690f323%2Cf25bb603-8904-43a5-bae9-1d4db05fdb59%2Cf8dd6a6c-193c-4b2e-8a54-3d081a81412b%2Ca0976832-3020-4e8d-ab9d-afff114ac269%2Cb31ca361-1745-4fac-8e6b-a97ec99bf476%2Cb3db38a3-f77e-49f8-a013-e5ea275aa39e%2C4464055e-5cde-4f35-847d-8390b32f89a2%2C4bde5059-6cef-48a2-82ae-1199035ad287%2Cd77a7951-be7f-4d01-b021-e488b1969361%2C352798c6-d90f-458e-ad13-f0d849da37ab%2C6851ecdc-7a86-4d73-b34e-a422bdae5461%2Ce8f8a428-098b-483a-bfb7-9bdb4168c093%2C3de5c7f2-7d81-4d92-95f5-cdd2136966f7&metrics=cpu_utilization_procfs_system%2Ccpu_energy_rapl_msr_component%2Ccpu_power_rapl_msr_component%2Cmemory_power_rapl_msr_component%2Cphase_time_syscall_system)

## Structured Data

Structured Data in JSON format is available through the individual run endpoints

- Example for [Bash Quoting - Double](https://metrics.green-coding.io/stats.html?id=26bae94a-54ca-423b-9890-0fd29ca51a15): https://api.green-coding.io/v1/phase_stats/single/26bae94a-54ca-423b-9890-0fd29ca51a15

## Badge Linking

If you want to cite some benchmarks for the training data used here you can also badge-link the results.

- Example for [Bash Quoting - Double](https://metrics.green-coding.io/stats.html?id=26bae94a-54ca-423b-9890-0fd29ca51a15) CPU Package Energy:
                    <img src="https://api.green-coding.io/v1/badge/single/26bae94a-54ca-423b-9890-0fd29ca51a15?metric=cpu_energy_rapl_msr_component" loading="lazy" onerror="this.parentNode.parentNode.remove(); console.log('Could not render cpu_energy_rapl_msr_component badge - Likely due to non public visibility of the run.')">

You can find the badges under the "Badges" tab to copy & paste.

# Running a scenario

Scenarios are executed via the Green Metrics Tool CLI. Example for a single Python scenario:

```bash
green-metrics-tool run python/usage_scenario-sort.yml
```

Refer to the [GMT documentation](https://docs.green-coding.io) for installation and full usage instructions.

For simple test cases all files can also be run directly by calling the Python scripts in the `scripts` folder or executing the bash files directly.

# Test Cases

To validate the AI model we have pre-created test cases.

## In-Sample Test Cases

You cna find those including their **planned prompts** as well as **expected outputs** in [test-cases](/test-cases)

## Out-of-Sample Test Cases

- https://github.com/shldigital/promprint-data-wrangling
    - **Example Prompt**: Look at the repository in https://github.com/shldigital/promprint-data-wrangling and
    please optimize it according to green coding standards.
    - **Expected output**: Optimized code with annotations or additional output file that states expected energy and carbon savings

- https://github.com/shldigital/promprint-data-wrangling
    - **Example Prompt**: Look at the repository in https://github.com/shldigital/promprint-data-wrangling and
    please optimize it according to green coding standards.
    - **Expected output**: Optimized code with annotations or additional output file that states expected energy and carbon savings


# TODOS

- AI Model Training ⭕️
- AI Model evaluation ⭕️

# Organizational

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
grant - UKRI grant number UKRI569.
