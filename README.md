# Green AI Training

This repository contains minimal benchmarks designed to capture energy costs of minimal code and
infrastructure building blocks.

This includes:
- Programming language primitives like variable assignments, loops, incrementation etc
- Typical code functionality like executing network requests, loading libraries, etc.
- Specific language building blocks like memory cost for DOM nodes, rendering and download cost of images in a web-page etc.
- Infrastructure building blocks like the cost of overhead from VMs vs. native level (Docker)
- System level building blocks like the cost of running a full additional core, idling a system, running unthrottled downloads etc.

In summary scenarios isolate primitive workloads so that measured energy can be attributed to specific code
constructs and mapped back to source-level operations.


The benchmarks are designed for the the [Green Metrics Tool (GMT)](https://www.green-coding.io/projects/green-metrics-tool/)
but when extracted from their *YAML* files can be run in any linux environment.

## Repository layout

```
green-ai-training/
├── python/          # Python bottom-up benchmark scenarios
└── system/          # System-level benchmark scenarios
```

## python/

Contains a shared benchmark harness and ten independent GMT usage scenarios, each targeting a single operation type:

| Scenario | What it measures |
|---|---|
| `idle` | Baseline energy while sleeping |
| `empty-loop` | Loop overhead with no body |
| `integer-arithmetic` | Arithmetic-heavy computation |
| `memory-sequential` | Sequential read/write over buffers |
| `dict-lookup` | Hash table lookups |
| `json-roundtrip` | JSON encode/decode |
| `sort` | In-memory sort |
| `subprocess-spawn` | Process creation overhead |
| `http-requests` | Local HTTP request/response cycle |
| `page-assets` | Web asset transfer (HTML + images) |

Each scenario:
- Runs inside a Docker container with defined CPU/memory limits
- Scales across multiple input sizes to reveal complexity trends
- Emits work units via `custom_metrics` for energy-per-unit normalization
- Includes cooldown sleeps between steps for thermal stabilization

See [`python/README.md`](python/README.md) for details on the harness files.

## system/

System-level scenarios that benchmark CPU, memory, disk, network, idle time, wakeups, and syscalls at the OS layer.

| File | Target |
|---|---|
| `usage_scenario.yml` | Standard container environment |
| `usage_scenario_vm.yml` | Kata container / VM environment |

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
