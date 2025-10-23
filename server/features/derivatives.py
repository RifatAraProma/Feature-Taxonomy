import numpy as np

def slope(y):
    y = np.asarray(y, dtype=float)
    return np.diff(y)

def curvature(y):
    y = np.asarray(y, dtype=float)
    return y[2:] - 2*y[1:-1] + y[:-2]

def roughness(y):
    dy = slope(y)
    return float(np.std(dy))
