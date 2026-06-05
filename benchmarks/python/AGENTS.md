# Agent Guide

Scope: composable, bottom-up benchmark scenarios for Green Metrics Tool.

## Scenario Layout

- `usage_scenario-*.yml`: one primitive benchmark per file.
- `benchmark.py`: shared benchmark harness used by most scenarios.
- `benchmark_server.py`: local HTTP server for request and asset benchmarks.
- `Dockerfile`: shared runtime image for all scenarios in this directory.

## Agent Notes

- Keep benchmarks narrowly scoped: one dominant scaling variable per scenario.
- Prefer local services over external network access so runs stay reproducible.
- Emit work units through `custom_metrics` so GMT can normalize energy by the amount of work performed.
