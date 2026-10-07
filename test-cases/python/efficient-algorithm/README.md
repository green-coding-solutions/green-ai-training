# Prompt

Optimize this file according to Green Coding Rules

# Expected Output

- Replace the nested loop (O(n·m), up to 400 million comparisons) with a dictionary or set lookup: build an index of invoice numbers once (O(m)) and look up each payment reference in O(1), for O(n + m) total
- The result (`matched`) must stay the same
- Expected energy saving when running this file 1.000 times
