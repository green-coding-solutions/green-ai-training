import time
import random

N = 10_000_000
data = [random.randint(1, 1_000_00) for _ in range(N)]


def classify(x):
    if x < 10:
        return 1
    elif x < 100:
        return 2
    elif x < 1_000:
        return 3
    elif x < 10_000:
        return 4
    elif x % 2 == 0:
        return 5
    elif x % 3 == 0:
        return 6
    elif x > 500_000:
        return 7
    else:
        return 8

for x in data:
    classify(x)

print(f"{int(time.time() * 1e9)} classifications={N}")
