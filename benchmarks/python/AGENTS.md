# Agent Guide

Scope: composable, bottom-up benchmark scenarios for Green Metrics Tool.

## Scenario Layout

- `usage_scenario-*.yml`: one primitive benchmark per file.

## Agent Notes

- Keep benchmarks narrowly scoped: one dominant scaling variable per scenario.
- Prefer local services over external network access so runs stay reproducible.
- Emit work units through `custom_metrics` so GMT can normalize energy by the amount of work performed.
