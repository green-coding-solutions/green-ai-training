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

All scenarios emit work units through `custom_metrics` so a run can be normalized by the amount of work performed.

## Scenarios

| Scenario file | What is compared | Metric |
|---|---|---|
| `usage_scenario-if-statement.yml` | Simple equality `if-elif` vs complex range/modulo dispatch | `classifications` |
| `usage_scenario-match-statement.yml` | Simple vs complex `match` dispatch | `classifications` |
| `usage_scenario-attr-lookup-repeated.yml` | Repeated attribute lookup through dotted path | `lookups` |
| `usage_scenario-attr-lookup-cached.yml` | Attribute cached in local variable before loop | `lookups` |
| `usage_scenario-membership-list.yml` | Membership test in a `list` | `checks` |
| `usage_scenario-membership-set.yml` | Membership test in a `set` | `checks` |
| `usage_scenario-list-insert-vs-append.yml` | `list.insert(0, …)` vs `list.append(…)` | `operations` |
| `usage_scenario-string-concat-plus.yml` | String concatenation with `+` | `concatenations` |
| `usage_scenario-string-concat-join.yml` | String concatenation with `str.join` | `concatenations` |
| `usage_scenario-string-concat-fstring.yml` | String concatenation with f-string | `concatenations` |
| `usage_scenario-regex-inline.yml` | `re.match` with inline pattern string (cache active) | `regex_matches` |
| `usage_scenario-regex-precompiled.yml` | `re.compile` once, reuse compiled pattern | `regex_matches` |
| `usage_scenario-regex-recompile.yml` | Pattern recompiled on every iteration | `regex_matches` |
| `usage_scenario-repeated-computation.yml` | Repeated expensive computation with no caching | `computations` |
| `usage_scenario-repeated-computation-lru-cache.yml` | Same computation memoized with `@lru_cache` | `computations` |
| `usage_scenario-exception-flow-exception.yml` | Control flow via `try/except` | `operations` |
| `usage_scenario-exception-flow-branch.yml` | Same control flow via `if` branch | `operations` |
| `usage_scenario-exception-flow-dict-get.yml` | Same control flow via `dict.get` default | `operations` |
| `usage_scenario-import-star.yml` | `from module import *` | `imports` |
| `usage_scenario-import-namespace.yml` | `import module` (namespace import) | `imports` |
| `usage_scenario-http-requests-sync.yml` | Synchronous HTTP requests with `requests` | `http_requests` |
| `usage_scenario-http-requests-async.yml` | Asynchronous HTTP requests with `aiohttp` | `http_requests` |
| `usage_scenario-pytorch-without-no-grad.yml` | PyTorch inference **without** `torch.no_grad()` (10k and 100k passes) | `inferences` |
| `usage_scenario-pytorch-no-grad.yml` | PyTorch inference **with** `torch.no_grad()` (10k and 100k passes) | `inferences` |
| `usage_scenario-quantize-numpy.yml` | 1-bit sigma-delta quantization — pure Python loop over NumPy array | `samples` |
| `usage_scenario-quantize-numba.yml` | Same quantization loop compiled to native code with Numba `@njit` | `samples` |
