# Bottom Up Benchmarks

This directory contains simple Green Metrics Tool scenarios for bottom-up energy estimation.

Each `usage_scenario-*.yml` isolates one primitive workload so measured energy can later be mapped back to source code blocks such as:

- loops
- arithmetic-heavy code
- dictionary lookups
- JSON parsing and serialization
- sorting
- subprocess calls
- local HTTP request handling
- page and image asset transfer

The scenarios share a single image and benchmark harness:

- `benchmark.py`
- `benchmark_server.py`
- `Dockerfile`

All scenarios emit work units through `custom_metrics` so a run can be normalized by the amount of work performed.
