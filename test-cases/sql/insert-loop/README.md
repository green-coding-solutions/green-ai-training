# Prompt

Optimize this file according to Green Coding Rules

# Expected Output

- Replace the row-by-row INSERT loop with `executemany()` or a COPY command to send all rows in a single database operation, reducing per-row round-trip and commit overhead
- Expected energy saving when running this file 1.000 times
