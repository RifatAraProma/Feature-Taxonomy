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
    # Check if y is already pairs (list of tuples) or just y values
    if isinstance(y, list) and len(y) > 0 and isinstance(y[0], tuple):
        # Already have (x, y) pairs
        data_pairs = y
    else:
        # Convert y to (x, y) pairs
        y_arr = np.asarray(y, dtype=float)
        x_arr = np.arange(len(y_arr))
        data_pairs = list(zip(x_arr, y_arr))
    
    if method in CALLS:
        result_pairs = CALLS[method](data_pairs, **params)
        # Return as (x, y) tuples to be authentic to the algorithm
        if isinstance(result_pairs, list) and len(result_pairs) > 0:
            if isinstance(result_pairs[0], tuple):
                return [(float(pair[0]), float(pair[1])) for pair in result_pairs]
        return [(float(i), float(val)) for i, val in enumerate(result_pairs)]
    raise ValueError(f"Unknown aggregator method: {method}")
