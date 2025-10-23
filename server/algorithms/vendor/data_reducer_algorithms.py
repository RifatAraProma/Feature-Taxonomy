import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from plotly_resampler.aggregation import EveryNthPoint
from tsdownsample.downsamplers import M4Downsampler, MinMaxDownsampler, MinMaxLTTBDownsampler, LTTBDownsampler
from .douglas_peucker.douglas_peucker import rdp_iter_count
from .topology.topolines import filter_tda_threshold_indices
from .fpcs.fpcs_sampling import Fpcs

# ---- helpers ----
def _xy_from_pairs(data:list[tuple]):
    arr = np.asarray(data)
    if arr.ndim != 2 or arr.shape[1] != 2:
        raise ValueError("data must be an array-like of (x, y) pairs")
    return arr[:, 0], arr[:, 1]

def _pairs_from_indices(x: np.ndarray, y: np.ndarray, idxs: np.ndarray) -> list[tuple]:
    return [(x[i], y[i]) for i in idxs.astype(int)]


# ===========================
# DOWNSAMPLERS
# ===========================


def m4_downsample(data: list[tuple], output_length: int) -> list[tuple]:
    """
    Robust wrapper for tsdownsample M4Downsampler.

    Behavior:
      - If data is empty -> return []
      - If output_length is None or >= len(data) -> return data (no downsampling)
      - Ensure n_out is a multiple of 4 and >= 8 (tsdownsample requirement).
        Round requested output_length up to the next valid multiple of 4,
        clamp to len(data), and require >= 8.
      - If dataset length < 8 -> fallback to returning original (safe).
    """
    if not data:
        return []

    n = len(data)
    # if no downsampling requested or output_length >= length, return original
    if output_length is None or output_length >= n:
        return data

    # If dataset is too short for M4 internals, don't call tsdownsample
    if n < 8:
        # fallback policy: return the original sequence for tiny inputs
        return data

    # Compute safe n_out:
    #  - at least 8
    #  - at most n
    #  - a multiple of 4 (round up)
    requested = int(output_length)
    safe_n = max(8, requested)
    if safe_n > n:
        safe_n = n
    # round up to multiple of 4
    if safe_n % 4 != 0:
        safe_n = ((safe_n + 3) // 4) * 4
        if safe_n > n:
            safe_n = n

    # final guard: safe_n must be >= 8 to avoid Rust panic
    if safe_n < 8:
        return list(data)

    # perform downsample using tsdownsample API
    x_m4 = np.array([p[0] for p in data])
    y_m4 = np.array([p[1] for p in data])
    m4_tsd = M4Downsampler()
    idx = m4_tsd.downsample(x_m4, y_m4, n_out=safe_n)
    return _pairs_from_indices(x_m4, y_m4, idx)

 
def minmaxlttb_downsample(data: list[tuple], output_length: int, minmax_ratio: int = 4) -> list[tuple] :
    """
    Downsample a sequence of (x, y) pairs using MinMaxLTTB.
    Returns a list of (x, y) pairs (same type as input ordering).
    
    """
    
    if output_length is None or output_length < 3:
        return data
        
    if len(data) <= output_length:
        return data
    else:
        # Convert input data into separate x and y arrays
        x, y = _xy_from_pairs(data)
        # ensure contiguous 1-D float64 arrays expected by tsdownsample
        x = np.ascontiguousarray(np.asarray(x).ravel(), dtype=float)
        y = np.ascontiguousarray(np.asarray(y).ravel(), dtype=float)

        minmaxlttb_tsd = MinMaxLTTBDownsampler()
        
        # n_out here is the number of datapoints in output
        # minmax_ratio 4 is default value
        # parallel is related to optimizing processing time.
        
        downsampled_indices  = minmaxlttb_tsd.downsample(
            x,
            y,
            n_out = output_length, 
            minmax_ratio = 4, 
            parallel = True
        )

    return _pairs_from_indices(x, y, np.array(downsampled_indices))


def lttb_downsample(data: list[tuple], output_length: int) -> list[tuple] :
    """
    Downsample a sequence of (x, y) pairs using LTTB.
    Returns a list of (x, y) pairs (same type as input ordering).
    
    """
    
    if output_length is None or output_length < 3:
        return data
        
    if len(data) <= output_length:
        return data
    else:
        # Convert input data into separate x and y arrays
        x, y = _xy_from_pairs(data)
        # ensure contiguous 1-D float64 arrays expected by tsdownsample
        x = np.ascontiguousarray(np.asarray(x).ravel(), dtype=float)
        y = np.ascontiguousarray(np.asarray(y).ravel(), dtype=float)
        lttb_tsd = LTTBDownsampler()
        
        # n_out here is the number of datapoints in output
        # minmax_ratio 4 is default value
        # parallel is related to optimizing processing time.
        
        downsampled_indices  = lttb_tsd.downsample(
            x,
            y,
            n_out = output_length, 
            parallel = True
        )

    return _pairs_from_indices(x, y, np.array(downsampled_indices))


def uniform_subsample_downsample(data: list[tuple], output_length: int) -> list[tuple]:
    """
    Uniformly select `output_length` points (including endpoints) from (x,y).
    Returns a reduced list of (x,y) pairs.
    """
    if output_length is None or output_length < 2:
        raise ValueError("output_length must be >= 2")
    input_length = len(data)
    if output_length >= input_length:
        return data

    x, y = _xy_from_pairs(data)
    # Places output_length evenly spaced fractional indices over [0, N-1], then rounds to nearest integer sample index.
    # (Note: NumPy uses bankers rounding, i.e., .5 goes to the nearest even integer. That’s fine, but be aware.
    idxs = np.linspace(0, input_length - 1, output_length).round().astype(int)
    #Force include endpoints explicitly
    idxs[0], idxs[-1] = 0, input_length - 1
    # Ensure uniqueness; if collisions happen, pad with evenly spaced extras
    idxs = np.unique(idxs)
    
    # If duplicates reduced the count, this loop tops up with a simple evenly spaced arithmetic progression over 
    # (0, N-1) (excluding the last index so you don’t duplicate the endpoint), then unique again to remove any 
    # collisions with existing picks. The loop repeats until you have exactly output_length unique indices.
    while len(idxs) < output_length:
        need = output_length - len(idxs)
        step = max(1, (input_length - 1) // (need + 1))
        extras = np.arange(step, input_length - 1, step, dtype=int)[:need]
        idxs = np.unique(np.concatenate([idxs, extras]))
        
    return _pairs_from_indices(x, y, idxs)


def rdp_downsample(data: list[tuple], output_length: int) -> list[tuple]:
    """
    Ramer–Douglas–Peucker reduction to a target number of points (>= 2).
    Operates on true (x,y) geometry and returns a reduced subset of original points.
    """
    if output_length is None or output_length < 2:
        raise ValueError("output_length must be >= 2")
    
    # RDP uses pldist(point, start, end) with a 2-D cross product
    # Therefore we need each point to be a 2-D vector- (x,y)
    arr = np.asarray(data, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 2:
        raise ValueError("data must be (x, y) pairs")
    if output_length >= len(arr):
        return [(row[0], row[1]) for row in arr]

    reduced = rdp_iter_count(arr, output_length)  # returns Nx2 array of (x,y)
   
    return [(row[0], row[1]) for row in reduced]


def tda_downsample(data: list[tuple], threshold: float) -> list[tuple]:
    """
    TDA smoothing (full-length) using topology.filter_tda_count with a slider in [0, 1].

    Parameters
    ----------
    data : list[(x, y)]
        Input series as (x, y) pairs.
    threshold : float in [0, 1]
        Slider controlling how many topological features (peak–valley pairs) are kept.
        - threshold = 0.0  -> keep *fewest* pairs (only the most persistent) -> **strongest smoothing**.
        - threshold = 1.0  -> keep *all* pairs (including tiny wiggles)     -> **least smoothing**.

    Returns
    -------
    list[(x, y_smoothed)]
       returns points that survive the threshold cut-off.

   
    """
    if threshold is None or not (0.0 <= float(threshold) <= 1.0):
        raise ValueError(" threshold must be between 0 to 1")
    
    x, y = _xy_from_pairs(data)
    idxs = filter_tda_threshold_indices(y, threshold)
    idxs_arr = np.asarray(idxs, dtype=int).ravel()
    
    return _pairs_from_indices(x, y, idxs_arr)


def fpcs_downsample(data: list[tuple], rate: int) -> list[tuple]:
    """
    Downsample (x,y) using the authors' FPCS algorithm with its native parameter `rate`.

    Parameters
    ----------
    data : list[(x,y)]
        Input series in order.
    rate : int >= 1
        Sampling interval R controlling how many incoming points are considered
        between emitted extrema. Smaller R → more emitted points; larger R → fewer.
        R = 1
        Meaning: FPCS checks extrema after every single sample.
        In practice this produces the densest possible output (many extrema emitted, little reduction).
        
        R = N (length of the input series) is the extreme upper bound.
        Meaning: FPCS will only check extrema once at the very end, so very few points (basically only the most persistent extrema + endpoints) will survive.

    Returns
    -------
    list[(x,y)]
        Points emitted by FPCS (no forced endpoints; mirrors paper code).
    """
    if not data:
        return []
    if rate < 1:
        raise ValueError("rate must be >= 1")

    fpcs = Fpcs(rate)
    output: list[tuple] = []
    for node in data:
        emitted = fpcs.push_data(node)
        if emitted:
            output.extend(emitted)
    return output
