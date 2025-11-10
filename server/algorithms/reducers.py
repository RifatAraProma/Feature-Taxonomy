# Wrappers for reducer algorithms from vendor
from .vendor import data_reducer_algorithms as v
import numpy as np

CALLS = {}
for name in dir(v):
    if name.startswith("_"): continue
    fn = getattr(v, name)
    if callable(fn):
        CALLS[name] = fn

def _xy_from_pairs(data):
    """Helper function to extract x, y arrays from data pairs"""
    arr = np.asarray(data)
    if arr.ndim != 2 or arr.shape[1] != 2:
        raise ValueError("data must be an array-like of (x, y) pairs")
    return arr[:, 0], arr[:, 1]

def _pairs_from_indices(x, y, idxs):
    """Helper function to create pairs from indices"""
    return [(x[i], y[i]) for i in idxs.astype(int)]

def apply(method: str, y, **params):
    # Check if y is already pairs (list of tuples) or just y values
    if isinstance(y, list) and len(y) > 0 and isinstance(y[0], tuple):
        # Already have (x, y) pairs
        data_pairs = y
        x_arr = np.array([pair[0] for pair in data_pairs], dtype=float)
        y_arr = np.array([pair[1] for pair in data_pairs], dtype=float)
    else:
        # Convert y to (x, y) pairs
        y_arr = np.asarray(y, dtype=float)
        x_arr = np.arange(len(y_arr))
        data_pairs = list(zip(x_arr, y_arr))
    
    # Handle class-based algorithms with special logic
    if method == "EveryNthPoint":
        from plotly_resampler.aggregation import EveryNthPoint
        step = params.get("step", 2)
        # EveryNthPoint works with indices directly
        idxs = list(range(0, len(data_pairs), step))
        # Return as (x, y) tuples
        return [(float(x_arr[i]), float(y_arr[i])) for i in idxs if i < len(y_arr)]
    
    elif method == "Fpcs":
        from .vendor.fpcs.fpcs_sampling import Fpcs
        rate = params.get("rate", 2)
        fpcs = Fpcs(rate)
        output = []
        for node in data_pairs:
            emitted = fpcs.push_data(node)
            if emitted:
                output.extend(emitted)
        # Output already contains tuples, ensure they're floats
        return [(float(pair[0]), float(pair[1])) for pair in output]
    
    elif method in ["LTTBDownsampler", "M4Downsampler", "MinMaxDownsampler", "MinMaxLTTBDownsampler"]:
        from tsdownsample.downsamplers import LTTBDownsampler, M4Downsampler, MinMaxDownsampler, MinMaxLTTBDownsampler
        
        output_length = params.get("output_length", 5)
        if output_length >= len(data_pairs):
            # Return as (x, y) tuples
            return [(float(x_arr[i]), float(y_arr[i])) for i in range(len(y_arr))]
            
        x, y = _xy_from_pairs(data_pairs)
        x = np.ascontiguousarray(x, dtype=float)
        y = np.ascontiguousarray(y, dtype=float)
        
        # Adjust output_length for specific algorithm requirements
        if method == "M4Downsampler":
            # M4 requires multiple of 4 and minimum 8
            adjusted_length = max(8, ((output_length + 3) // 4) * 4)
            if adjusted_length > len(data_pairs):
                adjusted_length = len(data_pairs)
                if adjusted_length % 4 != 0:
                    adjusted_length = (adjusted_length // 4) * 4
                if adjusted_length < 8:
                    # Return as (x, y) tuples
                    return [(float(x_arr[i]), float(y_arr[i])) for i in range(len(y_arr))]
            downsampler = M4Downsampler()
        elif method == "MinMaxDownsampler":
            # MinMax requires even number and minimum 2
            adjusted_length = max(2, ((output_length + 1) // 2) * 2)
            if adjusted_length > len(data_pairs):
                adjusted_length = (len(data_pairs) // 2) * 2
                if adjusted_length < 2:
                    # Return as (x, y) tuples
                    return [(float(x_arr[i]), float(y_arr[i])) for i in range(len(y_arr))]
            downsampler = MinMaxDownsampler()
        elif method == "LTTBDownsampler":
            adjusted_length = max(3, output_length)  # LTTB minimum is 3
            downsampler = LTTBDownsampler()
        elif method == "MinMaxLTTBDownsampler":
            adjusted_length = max(3, output_length)  # MinMaxLTTB minimum is 3  
            downsampler = MinMaxLTTBDownsampler()
        
        # Additional safety check
        if adjusted_length >= len(data_pairs):
            # Return as (x, y) tuples
            return [(float(x_arr[i]), float(y_arr[i])) for i in range(len(y_arr))]
        
        idxs = downsampler.downsample(x, y, n_out=adjusted_length)
        # Return as (x, y) tuples
        return [(float(x[i]), float(y[i])) for i in idxs]
    
    # Handle function-based algorithms (existing logic)
    if method in CALLS:
        result_pairs = CALLS[method](data_pairs, **params)
        # Result should already be pairs, ensure they're floats
        if isinstance(result_pairs, list) and len(result_pairs) > 0:
            if isinstance(result_pairs[0], tuple):
                return [(float(pair[0]), float(pair[1])) for pair in result_pairs]
        # If not tuples, convert to array and return
        return np.asarray(result_pairs).tolist()
    
    raise ValueError(f"Unknown reducer method: {method}")
