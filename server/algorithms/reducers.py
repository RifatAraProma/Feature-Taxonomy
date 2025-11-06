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
    # Convert y to (x, y) pairs if necessary
    y_arr = np.asarray(y, dtype=float)
    x_arr = np.arange(len(y_arr))
    data_pairs = list(zip(x_arr, y_arr))
    
    # Handle class-based algorithms with special logic
    if method == "EveryNthPoint":
        from plotly_resampler.aggregation import EveryNthPoint
        step = params.get("step", 2)
        # EveryNthPoint works with indices directly
        idxs = list(range(0, len(data_pairs), step))
        return [float(y_arr[i]) for i in idxs if i < len(y_arr)]
    
    elif method == "Fpcs":
        from .vendor.fpcs.fpcs_sampling import Fpcs
        rate = params.get("rate", 2)
        fpcs = Fpcs(rate)
        output = []
        for node in data_pairs:
            emitted = fpcs.push_data(node)
            if emitted:
                output.extend(emitted)
        return [float(pair[1]) for pair in output]
    
    elif method in ["LTTBDownsampler", "M4Downsampler", "MinMaxDownsampler", "MinMaxLTTBDownsampler"]:
        from tsdownsample.downsamplers import LTTBDownsampler, M4Downsampler, MinMaxDownsampler, MinMaxLTTBDownsampler
        
        output_length = params.get("output_length", 5)
        if output_length >= len(data_pairs):
            return y_arr.tolist()
            
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
                    return y_arr.tolist()  # Fallback for small data
            downsampler = M4Downsampler()
        elif method == "MinMaxDownsampler":
            # MinMax requires even number and minimum 2
            adjusted_length = max(2, ((output_length + 1) // 2) * 2)
            if adjusted_length > len(data_pairs):
                adjusted_length = (len(data_pairs) // 2) * 2
                if adjusted_length < 2:
                    return y_arr.tolist()  # Fallback for small data
            downsampler = MinMaxDownsampler()
        elif method == "LTTBDownsampler":
            adjusted_length = max(3, output_length)  # LTTB minimum is 3
            downsampler = LTTBDownsampler()
        elif method == "MinMaxLTTBDownsampler":
            adjusted_length = max(3, output_length)  # MinMaxLTTB minimum is 3  
            downsampler = MinMaxLTTBDownsampler()
        
        # Additional safety check
        if adjusted_length >= len(data_pairs):
            return y_arr.tolist()
        
        idxs = downsampler.downsample(x, y, n_out=adjusted_length)
        return [float(y[i]) for i in idxs]
    
    # Handle the reclassified window-based selection filters
    elif method == "median_filter_reducer":
        from .vendor.data_reducer_algorithms import median_filter_reducer
        window_size = params.get("window_size", 3)
        result_pairs = median_filter_reducer(data_pairs, window_size)
        return [float(pair[1]) for pair in result_pairs]
    
    elif method == "min_filter_reducer":
        from .vendor.data_reducer_algorithms import min_filter_reducer  
        window_size = params.get("window_size", 3)
        result_pairs = min_filter_reducer(data_pairs, window_size)
        return [float(pair[1]) for pair in result_pairs]
        
    elif method == "max_filter_reducer":
        from .vendor.data_reducer_algorithms import max_filter_reducer
        window_size = params.get("window_size", 3)  
        result_pairs = max_filter_reducer(data_pairs, window_size)
        return [float(pair[1]) for pair in result_pairs]
    
    # Handle function-based algorithms (existing logic)
    if method in CALLS:
        result_pairs = CALLS[method](data_pairs, **params)
        # Extract y values from result
        if isinstance(result_pairs, list) and len(result_pairs) > 0:
            if isinstance(result_pairs[0], tuple):
                return [float(pair[1]) for pair in result_pairs]
        return np.asarray(result_pairs).tolist()
    
    raise ValueError(f"Unknown reducer method: {method}")
