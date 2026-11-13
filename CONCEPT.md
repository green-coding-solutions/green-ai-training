# Concept

**In short:** today's coding models already *know* most green coding patterns, but they don't *use* them unless asked.
They fall back to the most common solution in their training data. We fine-tune small open models so that the
energy-efficient choice becomes their default, and we back every recommendation with real energy measurements
instead of rules of thumb.

**Contents**

- [Goal](#goal)
- [The problem](#the-problem)
- [Why not just give the model a skill file?](#why-not-just-give-the-model-a-skill-file)
- [Our approach: fine-tune the habit](#our-approach-fine-tune-the-habit)
- [Green patterns are often true, but not always](#green-patterns-are-often-true-but-not-always)
- [What current models get right and wrong](#what-current-models-get-right-and-wrong)
- [Open problems and future work](#open-problems-and-future-work)
- [Related work](#related-work)

---

## Goal

A **carbon-optimizing** coding model: when it writes new code, it picks the leaner construct by default. When it
reviews or refactors code, it suggests greener alternatives. It covers two scenarios:

- **Manual:** helping a developer who writes or audits code.
- **Automated / agents:** engineering the greenest code for a task without a human asking for it.

It should also know when a "green" pattern *doesn't* pay off, and say so.

A second idea, a **carbon-aware** model, is not implemented yet. See [future work](#open-problems-and-future-work).

## The problem

**Models default to the average solution.** Modern models have a lot of knowledge, but they write the code they
have seen most often. Energy-efficient variants are rarer in the training data, so they rarely come out by default.

- A [2026 study](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ESEM.2026.29) shows this is still true for
  current models. Their code is generally good, but it doesn't target energy savings unless prompted to.
- [Earlier research](https://fount.aucegypt.edu/etds/2799/) found that models only produce really green code when the
  prompt contains the right keywords (e.g. *optimize*) and says *what* to optimize. That means the developer
  already has to know the patterns, which usually isn't the case.
- [Older models](https://arxiv.org/html/2506.08790v1) even suggested officially discouraged solutions, such as
  outdated Oracle data types or memory-inefficient string building.

## Why not just give the model a skill file?

A skill file (instructions loaded into the prompt) can nudge a model in the right direction. We provide one too:
[`SKILL.md`](SKILL.md). But it has real limits, especially for small local models:

- **Models still drift back to the average.** Even with a skill loaded, models often don't apply it. The weight
  of the "average" solution in their training data pulls them back.
- **Skills are heavy.** The [Green Software Foundation skill](https://github.com/Green-Software-Foundation/reference-implementations/blob/main/tools/gsf/green-code-skill/AGENTS.md)
  is already very compact and still takes about 2,000 tokens.
  - Small models for 8 GB of VRAM, such as CodeGemma 7B, have only an 8k context window. With the skill loaded,
    you get two or three iterations on a normal-sized code file before the model forgets earlier context.
  - Mid-size models for 16 GB of VRAM have bigger windows (128k for Gemma 4 E4B, Llama 3.1 8B or Qwen2.5-Coder 7B).
    But a large skill file fills that window with mostly irrelevant rules, and models get worse at using information
    the more of it they have to search through ([Lost in the Middle, Liu et al.](https://arxiv.org/abs/2307.03172)).
- **Rules fade over long sessions.** Even large models that fit big skill files follow the rules less strictly as the
  conversation grows and the system prompt or skill moves further back in the context.

**Our solution:** fine-tune the green behavior into the model. The behavior is more consistent, and no context is spent on
instructions, which also saves compute, KV cache and the energy that goes with them.

## Our approach: fine-tune the habit

### Why LoRA fits

The base models already know that `str.join` beats `+=`, that set lookups are O(1) and that WebP files are smaller than
GIFs. Our baseline tests confirmed this for every model we tried. What they lack is the **habit** of picking those
options without being asked.

LoRA fine-tuning is good at shifting habits and style, and weak at adding new facts. That is exactly the gap we need to close.

### What the dataset looks like

Q&A pairs like *"What is the 'cache static data' pattern?"* don't build a habit. The model needs to see the behavior
applied hundreds of times, in realistic situations. Our [dataset](dataset/README.md) is therefore made of conversations
in which a user asks for ordinary coding help and **never mentions energy**:

| Category | Share | What the model learns |
|---|---|---|
| Generation | 35 % | write green code by default |
| Review | 22 % | find inefficiencies next to normal bugs |
| Refactor | 18 % | rewrite code with the greener construct |
| No change | 9 % | say when code is already fine or a pattern doesn't apply |
| Conceptual | 6 % | explain trade-offs briefly and conditionally |
| Estimate | 6 % | answer "how much does this save?" without inventing numbers |
| Multi-turn | 4 % | handle pushback (deadlines, readability) without nagging |

Every pattern in the dataset is backed by one of our [benchmarks](benchmarks/). The current build has 1,683 training
and 201 evaluation conversations.

Planned are two model lines:

- **Measured patterns** (published): our patterns for which we have energy measurements.
- **GSF patterns** (planned): the patterns of the [Green Software Foundation catalog](https://patterns.greensoftware.foundation/),
  reworked into the same conversation format.

### Numbers: quote, don't calculate

Models are bad at counting and arithmetic ([EMNLP 2025](https://aclanthology.org/2025.emnlp-main.681/)), so we never
let the model compute energy figures:

- The model may only quote the **rounded, sourced figures** in [`measured-facts.md`](dataset/spec/measured-facts.md),
  together with their test conditions. It never scales them to the user's workload.
  [`verify.py`](dataset/scripts/verify.py) rejects every training example with a number that isn't in a cited fact.
- Anything that needs real calculation (savings for *your* workload, fresh measurement data) comes from outside the model:
  - **Function calling:** works well when you control the harness and run the model locally (Ollama, vLLM).
    A first experiment is in [`llm-tools/`](llm-tools/).
  - **Retrieval (RAG):** either as a tool in the harness, through an Ollama `Modelfile` without a dev environment,
    or as a skill that makes a plain API request.
  - **Skill file:** [`SKILL.md`](SKILL.md) gives general-purpose LLMs the same facts, plus a labeled estimate format.

## Green patterns are often true, but not always

Many public green coding catalogs
([GSF patterns](https://patterns.greensoftware.foundation/),
[green-codex rules](https://github.com/Institut-du-Numerique-Responsable/green-codex/blob/main/green-codex/references/rules.md),
[green-claude](https://github.com/Institut-du-Numerique-Responsable/green-claude),
[skill-nr](https://github.com/Institut-du-Numerique-Responsable/skill-nr))
list rules that are *often* true, but not always. The model has to know the edge cases:

- **"Use compiled languages."** Only true for production code. For a prototype, the developer's time is the main
  energy and carbon cost, so optimize for development speed.
- **"Cache static data."** If the data is rarely accessed, a cache (and maybe a caching service) can cost more energy
  than the occasional re-fetch.
- **"Compress stored data."** [Compression costs energy](https://metrics.green-coding.io/stats.html?id=addc5f5e-55da-47f8-956d-240d06304e4e).
  It only pays off if the data is stored long enough. Data kept for minutes should not be compressed at all, and data that
  is read often also pays the decompression cost every time. Compression is common because storage is billed by the MB,
  so it often saves money without saving energy. Our estimate for a 100 MB file:
  - **zstd** (100 MB → 30 MB, ~3.2 mWh): the file has to be stored for about **0.15 days** before compression pays off.
  - **xz** (~151 mWh): the break-even is about **7 days**.

<details>
<summary>Break-even calculation</summary>

Assumptions: a 1 TB SSD with 10 W constant power, 30 kg CO₂e embodied carbon (Datavizta), a 4-year lifetime and a grid
intensity of 0.3 kg CO₂e per kWh. A 100 MB file uses 1/10,000 of the disk.

- Embodied carbon per second for the file: 30 / 4 / 365 / 24 / 3600 / 10,000 = 2.378 × 10⁻¹¹ kg,
  which is 2.378 × 10⁻¹¹ / 0.3 = 7.927 × 10⁻¹¹ kWh equivalent per second
- Power share per second: 10 W / 10,000 / 1000 / 3600 = 2.778 × 10⁻¹⁰ kWh per second
- Compression removes 70 MB, so it saves 70 % of that: (7.927 × 10⁻¹¹ + 2.778 × 10⁻¹⁰) × 0.7 = 2.499 × 10⁻¹⁰ kWh per second
- zstd: 0.0000032 kWh / 2.499 × 10⁻¹⁰ / 86,400 ≈ **0.148 days**
- xz: 0.00015086 kWh / 2.499 × 10⁻¹⁰ / 86,400 ≈ **7 days**

The compression energy we measured later (fact `F-COMPRESS-CODECS`) is higher than this estimate assumed, so treat these
break-even times as lower bounds.

</details>

## What current models get right and wrong

As of mid-2026, frontier models (Claude Opus 4.8, ChatGPT 5.x) give good green advice on **well-known topics**, but
are vague or wrong on **niche topics**, and they still don't apply green patterns by default.

**Well-known topic: Docker vs. VM.** Asked about the energy overhead of a VM compared to a container, ChatGPT 5.4
explained why containers are leaner (shared kernel, no guest OS, less RAM pressure, better consolidation) and estimated
about 5–30 % more energy per workload for VMs. This matches our
[measurements of Docker vs. VMs](https://metrics.green-coding.io/compare.html?ids=68fb8502-4a61-40b8-a5cd-14bb7affda4b,e9289785-98bf-4e81-8069-b494fdaa00ba,98265e98-8126-4f72-8f1b-bc7ecd1892c5,cd83a76e-fa24-4317-a107-50e84d5a5cc7,0ddc51b2-e75b-45c7-9b73-34611063d8e6,d4d4441b-b1a8-426b-8ce9-c6636640853f,d1c4f8b0-0093-40b6-a27e-47f9056f0569&force_mode=usage_scenarios).

**Niche topic: image decoding cost.** Asked to rank image formats by browser decode cost, Claude Opus 4.8 (high effort)
answered from theory. Our [measurement](https://metrics.green-coding.io/stats.html?id=b31ca361-1745-4fac-8e6b-a97ec99bf476)
disagrees:

| Rank | Model's answer (cheapest first) | Measured (50 page loads, CPU energy) |
|---|---|---|
| 1 | BMP | JPG, ~134 J |
| 2 | GIF | WebP, ~150 J |
| 3 | PNG | GIF, ~151 J |
| 4 | JPEG | AVIF, ~159 J |
| 5 | WebP | PNG, ~181 J |
| 6 | AVIF | – |

The model ranked PNG as cheap and JPEG as more expensive. In our measurement JPG was the cheapest and PNG the most
expensive.

**Default behavior.** Asked to *generate* code (e.g. "a portfolio website with 10 pictures, 5 above the fold"), or to
*optimize* code they are given, models usually pick the statistically most likely solution, not the leanest one.

## Open problems and future work

- **Carbon-aware behavior.** The idea is to query a grid intensity API and adapt to it, for example by suggesting that a
  large refactoring run later, when the grid is cleaner, or by asking more questions first instead of producing a large edit.
  Not implemented.
- **Prototype vs. production mode.** For prototypes, write the smallest working code, skip caching and similar best
  practices, and keep answers short to save tokens. For production, spend the effort on the leanest code. The training data
  already teaches the model to respect this context. An explicit mode switch does not exist yet.
- **Savings for your workload.** Ideally, developers get "this change saves x mWh per execution, so x mWh per year at
  10,000 FaaS invocations a day", plus the total for applying *all* recommendations to a file, so they can weigh it against
  the cost of the change. The fine-tuned model deliberately doesn't calculate this. The [skill file](SKILL.md) gives a
  labeled estimate. A calculation tool is future work.
- **Multi-step calculations.** Questions like the compression break-even above still trip up every model we tested
  somewhere in the formula. Only a tool or RAG for that specific kind of calculation would solve it reliably.
- **Choosing between options without data.** Faced with several possible optimizations for a web page (optimize images,
  HTTP/2, lazy loading, CSS instead of JS animations) and only one allowed, a model needs measurements to rank them.
  More benchmarks, such as the software comparisons in [Energy ID](https://www.green-coding.io/products/energy-id/), could
  feed future training rounds.
- **Predicting total energy.** [EnCode](https://sa4s-serc.github.io/encode) predicts the energy of static code. It gives
  no heuristics for how constructs behave with varying input, but it could be combined with this model for full estimates.

## Related work

**Alternative approaches**

- [A Generative AI Tool for Constructing Web Frontend with Integration of Quality Feedback Loop](https://dl.acm.org/doi/full/10.1145/3816713.3818803):
  the harness checks generated code with non-AI checks (heuristics, pattern matching) after generation. It's a good
  addition, but we left it out because it is an engineering challenge, not a research question.

**Evaluations of how green LLM-written code is**

- [Balancing Green and Clean Code: Prompting for LLM-Based Refactoring (ESEM 2026)](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ESEM.2026.29)
- [Green Code or Costly Code? Evaluating the Energy Costs of Iterative LLM-Based Code Optimizations (replication package)](https://zenodo.org/records/23598170)
