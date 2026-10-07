import random
import time

N = 1_000_000

random.seed(42)
temperatures = [round(random.uniform(-20.0, 40.0), 1) for _ in range(N)]
stations = [f"station-{random.randint(0, 99)}" for _ in range(N)]

total = 0.0
for t in temperatures:
    total = total + t
average = total / len(temperatures)

highest = temperatures[0]
for t in temperatures:
    if t > highest:
        highest = t

has_frost = False
for t in temperatures:
    if t < 0:
        has_frost = True

readings_per_station = {}
for s in stations:
    if s in readings_per_station:
        readings_per_station[s] = readings_per_station[s] + 1
    else:
        readings_per_station[s] = 1

busiest = sorted(readings_per_station.items(), key=lambda kv: kv[1], reverse=True)[0]

print(f"{time.time_ns()} readings_processed={N}")
