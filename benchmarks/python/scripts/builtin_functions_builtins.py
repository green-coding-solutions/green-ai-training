import random
import time
from collections import Counter

N = 1_000_000

random.seed(42)
temperatures = [round(random.uniform(-20.0, 40.0), 1) for _ in range(N)]
stations = [f"station-{random.randint(0, 99)}" for _ in range(N)]

total = sum(temperatures)
average = total / len(temperatures)

highest = max(temperatures)

has_frost = any(t < 0 for t in temperatures)

readings_per_station = Counter(stations)

busiest = readings_per_station.most_common(1)[0]

print(f"{time.time_ns()} readings_processed={N}")
