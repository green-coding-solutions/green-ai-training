import time
import random
import math

N = 10_000_000
data = [random.uniform(1.0, 1000.0) for _ in range(N)]

for x in data:
    math.sqrt(x)

print(f"{time.time_ns()} iterations={N}")
