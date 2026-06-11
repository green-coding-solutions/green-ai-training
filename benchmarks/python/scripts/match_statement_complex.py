import time
import random

N = 10_000_000
data = [random.randint(1, 1_000_00) for _ in range(N)]


def classify(x):
    match x:
        case _ if x < 10:
            return 1
        case _ if x < 100:
            return 2
        case _ if x < 1_000:
            return 3
        case _ if x < 10_000:
            return 4
        case _ if x % 2 == 0:
            return 5
        case _ if x % 3 == 0:
            return 6
        case _ if x > 500_000:
            return 7
        case _:
            return 8

for x in data:
    classify(x)

print(f"{int(time.time() * 1e9)} classifications={N}")
