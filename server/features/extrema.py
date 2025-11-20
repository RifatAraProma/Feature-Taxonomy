import numpy as np

def find_extrema(y):
    """
    Find local extrema in time series.
    
    Returns:
        Tuple of (minima, maxima, all_extrema) - already time-ordered
    """
    y = np.asarray(y, dtype=float)
    minima, maxima = [], []
    for t in range(1, len(y)-1):
        if y[t-1] < y[t] > y[t+1]:
            maxima.append({"t": t+1, "y": float(y[t]), "type": "max"})
        if y[t-1] > y[t] < y[t+1]:
            minima.append({"t": t+1, "y": float(y[t]), "type": "min"})
    
    # Return separate lists to avoid redundant filtering
    all_extrema = maxima + minima
    return minima, maxima, all_extrema
