import time
import random

N = 1_000_000

random.seed(42)
data = {str(i): i * 2 for i in range(1000)}
keys = [str(random.randint(0, 1999)) for _ in range(N)]

total = 0
for key in keys:
    if key in data:
        total += data[key]

print(f"{time.time_ns()} dict_lookups={N}")
