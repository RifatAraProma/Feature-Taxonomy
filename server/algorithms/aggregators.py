# Wrappers for aggregator algorithms from vendor
from .vendor import data_aggregator_algorithms as v
import numpy as np

CALLS = {}
for name in dir(v):
    if name.startswith("_"): continue
    fn = getattr(v, name)
    if callable(fn):
        CALLS[name] = fn

def apply(method: str, y, **params):
    # Convert y to (x, y) pairs if necessary
    y_arr = np.asarray(y, dtype=float)
    x_arr = np.arange(len(y_arr))
    data_pairs = list(zip(x_arr, y_arr))
    
    if method in CALLS:
        result_pairs = CALLS[method](data_pairs, **params)
        # Extract y values from result
        if isinstance(result_pairs, list) and len(result_pairs) > 0:
            if isinstance(result_pairs[0], tuple):
                return [float(pair[1]) for pair in result_pairs]
        return np.asarray(result_pairs).tolist()
    raise ValueError(f"Unknown aggregator method: {method}")
