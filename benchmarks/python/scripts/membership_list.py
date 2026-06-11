import time

N = 10_000_000

# Realistic scenario: data arrives as a list (e.g. loaded from a file or DB)
haystack = list(range(N))

# Needle is absent — forces the list to scan every element (worst case O(n))
needle = N + 1

found = needle in haystack

print(f"{time.time_ns()} elements_checked={N}")
