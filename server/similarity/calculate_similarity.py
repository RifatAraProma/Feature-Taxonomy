import numpy as np
from typing import Sequence, Dict, Tuple

# ---------------------------
# 1) Interpolation utilities
# ---------------------------

def _linspace01(n: int) -> np.ndarray:
    """Normalized domain [0, 1] with n samples."""
    if n <= 0:
        raise ValueError("Length must be positive.")
    return np.linspace(0.0, 1.0, n)

def interpolate_to_length(y: Sequence[float], n_target: int) -> np.ndarray:
    """Resample 1D series y to target length using linear interpolation."""
    y = np.asarray(y, dtype=float)
    if len(y) == n_target:
        return y.copy()
    x_src = _linspace01(len(y))
    x_tgt = _linspace01(n_target)
    return np.interp(x_tgt, x_src, y)

def align_series(y1: Sequence[float], y2: Sequence[float]) -> Tuple[np.ndarray, np.ndarray]:
    """Make y1 and y2 equal-length by interpolating the shorter one."""
    y1, y2 = np.asarray(y1, float), np.asarray(y2, float)
    n1, n2 = len(y1), len(y2)
    if n1 == 0 or n2 == 0:
        raise ValueError("Both series must be non-empty.")
    if n1 == n2:
        return y1, y2
    if n1 > n2:
        return y1, interpolate_to_length(y2, n1)
    else:
        return interpolate_to_length(y1, n2), y2

# ---------------------------
# 2) Metric functions
# ---------------------------

def L_1(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """
    Average-case error (L1 norm): mean absolute deviation.
    """
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    if len(y_true) != len(y_pred):
        raise ValueError("Input lengths must match.")
    return float(np.mean(np.abs(y_true - y_pred)))

def L_inf(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """
    Worst-case error (L-infinity norm): maximum absolute deviation.
    """
    y_true, y_pred = np.asarray(y_true, float), np.asarray(y_pred, float)
    if len(y_true) != len(y_pred):
        raise ValueError("Input lengths must match.")
    return float(np.max(np.abs(y_true - y_pred)))

# ---------------------------
# 3) High-level comparison
# ---------------------------

def compare_levels(y1: Sequence[float], y2: Sequence[float]) -> Dict[str, float]:
    """
    Compare vertical-level preservation between two series.
    - Resamples shorter series to match length.
    - Computes L1 (average-case) and L_inf (worst-case) metrics.
    - Returns both raw and normalized values.
    """
    y1a, y2a = align_series(y1, y2)
    yrange = np.max(y1a) - np.min(y1a) + 1e-12

    avg_err = L_1(y1a, y2a)
    worst_err = L_inf(y1a, y2a)

    return {
        "Average-case (L1)": avg_err,
        "Worst-case (L_inf)": worst_err,
        "Normalized L1": avg_err / yrange,
        "Normalized L_inf": worst_err / yrange,
    }

# ---------------------------
# Example
# ---------------------------

if __name__ == "__main__":
    y_orig = [1, 2, 3, 5, 7, 9]
    y_simpl = [1.1, 2.2, 2.8, 5.3]  # shorter → will be interpolated
    metrics = compare_levels(y_orig, y_simpl)
    for k, v in metrics.items():
        print(f"{k}: {v:.6f}")
