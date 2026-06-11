import time

N = 10_000_000

# Realistic scenario: data arrives as a list, then converted to set for lookups
haystack_list = list(range(N))
haystack_set = set(haystack_list)  # O(n) creation cost included deliberately

# Needle is absent — O(1) hash lookup regardless
needle = N + 1

found = needle in haystack_set

print(f"{time.time_ns()} elements_checked={N}")
