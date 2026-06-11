import time

N = 1_000_000
CHUNK = "x"

result = ""
for _ in range(N):
    ref = result  # refcount of result becomes 2; CPython cannot resize in-place
    result = f"{result}{CHUNK}"

print(f"{time.time_ns()} string_concatenations={N}")
