import time
import random
from functools import lru_cache

N = 1_000_000
UNIQUE_N = 200
data = [random.randint(0, UNIQUE_N - 1) for _ in range(N)]

@lru_cache(maxsize=UNIQUE_N)
def compute(n):
    total = 0
    for i in range(1, n + 2):
        total += i * i
    return total

for x in data:
    compute(x)

print(f"{time.time_ns()} computations={N}")
