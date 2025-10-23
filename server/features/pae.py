import numpy as np

# Lightweight placeholder PAE (not pixel-based; swap with your own if desired)
def pixel_approx_entropy(y, m=2, r_ratio=0.2):
    y = np.asarray(y, dtype=float)
    if len(y) < m + 2:
        return 0.0
    sd = np.std(y)
    r = r_ratio * sd if sd > 0 else 0.1
    def _phi(m):
        X = np.array([y[i:i+m] for i in range(len(y)-m+1)])
        C = np.mean([np.mean(np.max(np.abs(X - x), axis=1) <= r) for x in X])
        return np.log(C + 1e-12)
    return float(_phi(m) - _phi(m+1))
