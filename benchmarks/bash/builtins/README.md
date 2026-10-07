# Bash Builtins Benchmark

Benchmark for `test-cases/bash/builtins`. All three variants summarize the same static 20,000-line access log
(`log.txt` in this folder) and print identical output.

| Scenario | Variant | Metric |
|---|---|---|
| `usage_scenario-subprocess.yml` | `script-subprocess.sh`, copy of the test case: `$(echo \| cut)` and `$(expr)` per line, about 10 processes per line | `log_lines` |
| `usage_scenario-builtins.yml` | `script-builtins.sh`: `read -r` field splitting, `$(( ))`, `case`, no subprocess per line | `log_lines` |
| `usage_scenario-awk.yml` | `script-awk.sh`: one `awk` pass over the file | `log_lines` |

Local check (not GMT, 3,000 lines): subprocess ~11 s, builtins ~40 ms, awk ~4 ms.
