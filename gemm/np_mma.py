import numpy as np
import time

N = 4096


x = np.random.randn(N, N).astype(np.float32)
w = np.random.randn(N, N).astype(np.float32)

# Warm-up BLAS
_ = x @ w

start = time.perf_counter()
c = x @ w
end = time.perf_counter()

gflops = (2 * N**3) / (end - start) / 1e9

print(f"Time: {end - start:.6f} s")
print(f"GFLOPS: {gflops:.2f}")
print("done")
