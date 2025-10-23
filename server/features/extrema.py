import numpy as np

def find_extrema(y):
    y = np.asarray(y, dtype=float)
    maxima, minima = [], []
    for t in range(1, len(y)-1):
        if y[t-1] < y[t] > y[t+1]:
            maxima.append({"t": t+1, "y": float(y[t]), "type": "max"})
        if y[t-1] > y[t] < y[t+1]:
            minima.append({"t": t+1, "y": float(y[t]), "type": "min"})
    return maxima + minima
