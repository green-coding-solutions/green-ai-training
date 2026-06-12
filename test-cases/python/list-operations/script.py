import time

N = 1_000_000

lst = []
for _ in range(N):
    lst.insert(0, 42)

print(f"{time.time_ns()} list_operations={N}")
