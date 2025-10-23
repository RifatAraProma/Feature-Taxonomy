# asap_nb.py
# A direct port of the notebook's smooth_ASAP function with minimal adaptations.

import math
from typing import List, Sequence, Tuple
import numpy as np


# --- SMA (same semantics as notebook/JS) ---
def SMA(values: Sequence[float], window_size: int, slide_size: int) -> np.ndarray:
    """
    Simple moving average with explicit window_size and slide_size.
    NaNs treated as 0 (to mirror the JS impl).
    Emits when the window first reaches 'window_size', then advances by 'slide_size'.
    """
    if window_size <= 0 or slide_size <= 0:
        raise ValueError("window_size and slide_size must be >= 1")

    arr = np.asarray(values, dtype=float).copy()
    arr[np.isnan(arr)] = 0.0

    n = arr.size
    if n == 0:
        return np.array([], dtype=float)

    window_start = 0
    s = 0.0
    count = 0
    out = []

    for i in range(n):
        if i - window_start >= window_size:
            out.append(s / count if count > 0 else 0.0)
            old_start = window_start
            # advance the start by slide_size steps
            while window_start < n and (window_start - old_start) < slide_size:
                s -= arr[window_start]
                count -= 1
                window_start += 1
        s += arr[i]
        count += 1

    # emit final if exactly full
    if count == window_size:
        out.append(s / count if count > 0 else 0.0)

    return np.asarray(out, dtype=float)


# --- Metrics used by ASAP (same formulas as notebook/JS) ---
class Metrics:
    def __init__(self, values: Sequence[float]) -> None:
        self.values = np.asarray(values, dtype=float)
        self.len = int(self.values.size)
        self.m = self.values.mean() if self.len else 0.0

    def kurtosis(self) -> float:
        if self.len == 0:
            return float("nan")
        dif = self.values - self.m
        u4 = float(np.sum(dif**4))
        var = float(np.sum(dif**2))
        if var == 0.0:
            return float("inf")
        # Pearson’s kurtosis (no -3), population moments
        return self.len * u4 / (var**2)

    def roughness(self) -> float:
        if self.len <= 1:
            return 0.0
        d = np.diff(self.values)
        # population std (divide by N)
        return float(np.sqrt(np.sum((d - d.mean())**2) / max(1, d.size)))


# --- ACF (autocorrelation) as in JS/nb, with peak picking ---
class ACF:
    CORR_THRESH = 0.2

    def __init__(self, values: Sequence[float], max_lag: int) -> None:
        self.values = np.asarray(values, dtype=float)
        self.max_lag = max(2, int(max_lag))
        self.mean = float(self.values.mean()) if self.values.size else 0.0

        # correlations[0] left at 0.0 (not used by peak logic)
        self.correlations = np.zeros(self.max_lag, dtype=float)
        self.max_acf = 0.0  # track maximum correlation among peaks

        # for parity with notebook usage:
        m = Metrics(self.values)
        self.kurtosis = m.kurtosis()
        self.roughness = m.roughness()

        self._calculate()
        self.peaks = self._find_peaks()

    def _next_pow2_greater(self, n: int) -> int:
        if n <= 1:
            return 2
        p = int(np.floor(np.log2(n))) + 1
        return 1 << p

    def _calculate(self) -> None:
        n = self.values.size
        if n == 0:
            return
        L = self._next_pow2_greater(n)
        xr = np.zeros(L, dtype=float)
        xr[:n] = self.values - self.mean

        X = np.fft.fft(xr)
        power = (X.real * X.real) + (X.imag * X.imag)
        R = np.fft.ifft(power).real

        denom = R[0] if R[0] != 0 else 1.0
        for i in range(1, self.max_lag):
            self.correlations[i] = R[i] / denom

    def _find_peaks(self) -> List[int]:
        peaks: List[int] = []
        if self.max_lag <= 1:
            return peaks

        positive = self.correlations[1] > self.correlations[0]
        max_idx = 1
        for i in range(2, self.max_lag):
            c = self.correlations[i]
            if not positive and c > self.correlations[i - 1]:
                max_idx = i
                positive = True
            elif positive and c > self.correlations[max_idx]:
                max_idx = i
            elif positive and c < self.correlations[i - 1]:
                if max_idx > 1 and self.correlations[max_idx] > self.CORR_THRESH:
                    peaks.append(max_idx)
                    if self.correlations[max_idx] > self.max_acf:
                        self.max_acf = self.correlations[max_idx]
                positive = False

        # Fallback: try all lags if no useful peaks
        if len(peaks) <= 1:
            for i in range(2, self.max_lag):
                peaks.append(i)
        return peaks


# --- Binary search refinement (same signature/logic as notebook) ---
def binary_search(head: int, tail: int,
                  data: Sequence[float],
                  min_obj: float,
                  original_kurt: float,
                  window_size: int) -> int:
    head = int(head)
    tail = int(tail)
    best_w = int(window_size)
    best_obj = float(min_obj)

    while head <= tail:
        w = int((head + tail) // 2)
        smoothed = SMA(data, w, 1)
        m = Metrics(smoothed)
        if m.kurtosis() >= original_kurt:
            r = m.roughness()
            if r < best_obj:
                best_obj = r
                best_w = w
            head = w + 1
        else:
            tail = w - 1
    return best_w


# --- Main function: exactly the notebook’s structure/variables ---
def smooth_ASAP(data, max_window: int = 5, resolution: int | None = None):
    """
    Notebook-style ASAP entry point.

    Parameters
    ----------
    data : 1-D sequence (y-values)
    max_window : int (default 5)
        Used to bound the search: ACF max_lag = len(data) / max_window,
        and tail = len(data) / max_window.
    resolution : int or None
        If provided and len(data) >= 2*resolution, pre-aggregate by
        SMA(range=len/rez, slide=len/rez).

    Returns
    -------
    (window_size, slide_size)
        window_size : int chosen by ASAP
        slide_size  : int pre-aggregation slide (1 if no pre-aggregation)
    """
    data = np.asarray(data, dtype=float)

    # Preaggregate according to resolution
    slide_size = 1
    window_size = 1
    if resolution and data.size >= 2 * int(resolution):
        slide_size = int(max(1, data.size // int(resolution)))
        data = SMA(data, slide_size, slide_size)

    # ACF with max_lag = len(data) / max_window  (note notebook uses division)
    max_lag = max(2, int(data.size // int(max_window)))
    acf = ACF(data, max_lag=max_lag)
    peaks = acf.peaks
    orig_kurt = acf.kurtosis
    min_obj = acf.roughness
    lb = 1
    largest_feasible = -1
    tail = max(1, int(data.size // int(max_window)))

    # Scan peaks backward
    for i in range(len(peaks) - 1, -1, -1):
        w = int(peaks[i])

        if w < lb or w == 1:
            break
        elif math.sqrt(max(0.0, 1 - acf.correlations[w])) * window_size > \
             math.sqrt(max(0.0, 1 - acf.correlations[window_size])) * w:
            continue

        smoothed = SMA(data, w, 1)
        metrics = Metrics(smoothed)
        if metrics.roughness() < min_obj and metrics.kurtosis() >= orig_kurt:
            min_obj = metrics.roughness()
            window_size = w
            # lb update as in notebook:
            num = (acf.max_acf - 1.0)
            den = (acf.correlations[w] - 1.0)
            if den != 0.0:
                scale = math.sqrt(max(0.0, num / den))
                lb = round(max(w * scale, lb))
            # NOTE: the notebook code sets largest_feasible but the provided cell
            # didn’t show the assignment. If needed, uncomment:
            # if largest_feasible < 0: largest_feasible = i

    if largest_feasible > 0:
        if largest_feasible < len(peaks) - 2:
            tail = int(peaks[largest_feasible + 1])
        lb = max(lb, int(peaks[largest_feasible] + 1))

    window_size = binary_search(lb, tail, data, min_obj, orig_kurt, window_size)
    return window_size, slide_size


# --- Optional helper to actually smooth (x,y) with the chosen window ---
def asap_smoother(data: list[tuple],
                      max_window: int = 5,
                      resolution: int | None = None) -> list[tuple]:
    """
    Apply notebook-style ASAP smoothing to (x,y) and return aggregated output.
    x is aligned to the right edge of each window: x_out[k] = x[w-1+k].
    """
    if not data:
        return []
    arr = np.asarray(data, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 2:
        raise ValueError("data must be (x,y) pairs")
    x = arr[:, 0]
    y = arr[:, 1]

    # Ignore trailing NaN (matches JS/nb behavior)
    if np.isnan(y[-1]):
        y = y[:-1]
        x = x[:-1]

    w, slide = smooth_ASAP(y, max_window=max_window, resolution=resolution)
    y_s = SMA(y, w, 1)
    x_out = x[w - 1:]
    L = min(len(x_out), len(y_s))
    return list(map(tuple, np.column_stack((x_out[:L], y_s[:L]))))
