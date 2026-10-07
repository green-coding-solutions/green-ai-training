# Prompt

Optimize this file according to Green Coding Rules

# Expected Output

- Replace the hand-written loops with built-in functions that run in C: `sum(temperatures)` for the total, `max(temperatures)` for the highest value, and `any(t < 0 for t in temperatures)`, which also stops at the first frost reading instead of scanning the whole list
- Count readings per station with `collections.Counter(stations)` instead of a manual dict loop
- Get the busiest station with `Counter.most_common(1)` or `max(..., key=...)` instead of sorting all stations to take the first one
- The results must stay the same. Exception: since Python 3.12, `sum()` of floats uses compensated summation, so the total can differ from the manual loop in the last digits (the `sum()` result is the more accurate one)
- Expected energy saving when running this file 1.000 times
