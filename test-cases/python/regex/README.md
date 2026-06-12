# Prompt

Optimize this file according to Green Coding Rules

# Expected Output

- Precompile the regex pattern once outside the loop using `re.compile()` and reuse the compiled pattern object instead of recompiling (and purging the cache) on every iteration
- Expected energy saving when running this file 1.000 times
