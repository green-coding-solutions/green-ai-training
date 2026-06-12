import time

N = 1_000_000
CHUNK = "x"

result = ""
for _ in range(N):
    result += CHUNK

print(f"{time.time_ns()} string_concatenations={N}")
