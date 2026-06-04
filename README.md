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


The benchmarks are designed for the the [Green Metrics Tool (GMT)](https://www.green-coding.io/projects/green-metrics-tool/)
but when extracted from their *YAML* files can be run in any linux environment.

## Purpose and gains

The basic energy information about progamming language primitives as well as infrastructure decisions shall
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
- **Reproducibility** — all services are local; no external network dependencies unless explicitely intended


## Funding Notice

The work for this repository was funded by the [BRAID - Sustainable AI futures](https://www.bathspa.ac.uk/news-and-events/news/ai-research-grant/)
grant.
