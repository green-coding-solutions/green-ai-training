import time

N = 1_000_000
CHUNK = "x"

parts = []
for _ in range(N):
    parts.append(CHUNK)
result = "".join(parts)

print(f"{time.time_ns()} string_concatenations={N}")
