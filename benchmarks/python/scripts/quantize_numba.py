import time
import numpy as np
from numba import njit

@njit
def quantize(x):
    n = x.size
    y = np.zeros(n)
    error = np.zeros(n + 1)
    qe = 0.0

    for i in range(n):
        qe += x[i]
        y[i] = 1.0 if qe > 0 else -1.0
        qe -= y[i]

    return y

N = 10_000_000
rng = np.random.default_rng(42)
x = rng.uniform(-0.5, 0.5, N).astype(np.float64)

# warm-up call to trigger JIT compilation before the timed run
quantize(x[:1])

quantize(x)

print(f"{time.time_ns()} samples={N}")
