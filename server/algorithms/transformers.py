# Wrappers for transformer algorithms (smoothers) from vendor
from .vendor import data_transformer_algorithms as v
import numpy as np

# Map canonical names to callables (adjust to your vendor API)
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
    
    # try vendor
    if method in CALLS:
        result_pairs = CALLS[method](data_pairs, **params)
        # Extract y values from result
        if isinstance(result_pairs, list) and len(result_pairs) > 0:
            if isinstance(result_pairs[0], tuple):
                return [float(pair[1]) for pair in result_pairs]
        return np.asarray(result_pairs).tolist()