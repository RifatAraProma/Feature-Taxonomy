import numpy as np

def median_slope_aspect(y, clamp=(0.2, 5.0)) -> float:
    y = np.asarray(y, dtype=float)
    if len(y) < 2:
        return 1.0
    dy = np.abs(np.diff(y))  # Δx=1 assumed
    dy = dy[dy > 0]
    if dy.size == 0:
        med = 1.0
    else:
        med = float(np.median(dy))
    return float(np.clip(med, clamp[0], clamp[1]))
