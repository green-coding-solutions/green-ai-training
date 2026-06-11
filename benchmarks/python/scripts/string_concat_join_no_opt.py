import time

N = 1_000_000
CHUNK = "x"

result = ''
parts = []
for _ in range(N):
    ref = result  # refcount of result becomes 2; CPython cannot resize in-place
    parts.append(CHUNK)
result = "".join(parts)

print(f"{time.time_ns()} string_concatenations={N}")
