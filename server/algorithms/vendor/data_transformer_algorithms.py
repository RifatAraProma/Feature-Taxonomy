import numpy as np
import scipy.ndimage as scind
import scipy.signal as scisig
import scipy.fftpack as scifft

# ---- helpers ----
def _xy_from_pairs(data:list[tuple]):
    arr = np.asarray(data)
    if arr.ndim != 2 or arr.shape[1] != 2:
        raise ValueError("data must be an array-like of (x, y) pairs")
    return arr[:, 0], arr[:, 1]

def _pairs(x, y):
    return list(zip(x, y))
    if not (0 <= filter_level <= 1):
        raise ValueError("filter_level must be in [0, 1]")

def _check_cutoff_frequency(cutoff_freq_normalized: float):
    if not (0 < cutoff_freq_normalized < 1):
        raise ValueError("cutoff_freq_normalized must be in (0, 1)")

def _ensure_odd_window(window_size: int) -> int:
    """Convert window size to nearest odd number if even."""
    return window_size + 1 if window_size % 2 == 0 else window_size

# ===========================
# WINDOW-BASED FILTERS
# Mean, Median, Min, Max, Savitzky-Golay (sliding window operations)
# ===========================

def mean_filter(data: list[tuple], window_size: int) -> list[tuple]:
    """
    Simple moving average (mean) filter on y with given window_size (samples).
    Preserves all original data points while applying smoothing.
    
    How it works:
    1. Pad the data at edges to preserve output length (mode='edge')
    2. Slide a window of size `window_size` across the data
    3. Compute the average (mean) of values in each window
    4. Result maintains the same number of points as input
    
    Parameters:
    - window_size: Size of the averaging window (samples)
                   window_size = 1: No smoothing, returns input data unchanged
                   window_size = 2: Light smoothing
                   window_size = N: Heavy smoothing (larger N = more blur)
    
    Returns:
        Smoothed data as list of (x, y) tuples with same length as input
        
    Example:
        Input:  [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]
        window_size=2: [(0, 1.0), (1, 1.75), (2, 2.5), (3, 3.5), (4, 4.5)]
        window_size=3: [(0, 1.5), (1, 2.0), (2, 3.0), (3, 4.0), (4, 4.5)]
    """
    if not data:
        return []
    
    if window_size < 1:
        raise ValueError("window_size must be >= 1")
    if window_size > len(data):
        raise ValueError(f"window_size must be <= {len(data)}")
    
    x, y = _xy_from_pairs(data)
    
    # Pad the data at edges
    pad_pre = window_size // 2
    pad_post = window_size - 1 - pad_pre
    y_pad = np.pad(y, (pad_pre, pad_post), mode='edge')
    
    # Apply moving average via convolution
    kernel = np.ones((window_size,)) / window_size
    y_f = np.convolve(y_pad, kernel, mode='valid')
    
    # Return pairs with same length as input
    return _pairs(x, y_f)


def median_filter(data: list[tuple], window_size: int) -> list[tuple]:
    """
    Apply a median filter on y values, keeping x unchanged.
    Preserves all original data points while smoothing noise.
    
    Parameters:
    - window_size: Size of the median filter window (must be >= 1)
    
    How it works:
    1. Slide a window of size `window_size` across the data
    2. For each window position, compute the median of values in that window
    3. Replace the center value with the median (smooth noise while preserving edges via 'nearest' mode)
    4. Result maintains the same number of points as input
    
    Use case: Non-linear smoothing that removes spikes while preserving edges
    """
    x, y = _xy_from_pairs(data)
    if window_size < 1:
        raise ValueError("window_size must be >= 1")
    if window_size > len(y):
        raise ValueError(f"window_size must be <= {len(y)}")
    
    y_med = scind.median_filter(y, size=window_size, mode='nearest')
    return _pairs(x, y_med)


def min_filter(data: list[tuple], window_size: int) -> list[tuple]:
    """
    Apply a minimum filter on y values, keeping x unchanged.
    Extracts local minimum values within sliding windows.
    
    Parameters:
    - window_size: Size of the minimum filter window (must be >= 1)
    
    How it works:
    1. Slide a window of size `window_size` across the data
    2. For each window position, find the minimum value in that window
    3. Replace the center value with the minimum (smoothing via local minima)
    4. Result maintains the same number of points as input
    
    Use case: Finding baseline, removing positive outliers, morphological operations
    """
    x, y = _xy_from_pairs(data)
    if window_size < 1:
        raise ValueError("window_size must be >= 1")
    if window_size > len(y):
        raise ValueError(f"window_size must be <= {len(y)}")
    
    y_min = scind.minimum_filter(y, size=window_size, mode='nearest')
    return _pairs(x, y_min)


def max_filter(data: list[tuple], window_size: int) -> list[tuple]:
    """
    Apply a maximum filter on y values, keeping x unchanged.
    Extracts local maximum values within sliding windows.
    
    Parameters:
    - window_size: Size of the maximum filter window (must be >= 1)
    
    How it works:
    1. Slide a window of size `window_size` across the data
    2. For each window position, find the maximum value in that window
    3. Replace the center value with the maximum (smoothing via local maxima)
    4. Result maintains the same number of points as input
    
    Use case: Finding peaks, removing negative outliers, morphological operations
    """
    x, y = _xy_from_pairs(data)
    if window_size < 1:
        raise ValueError("window_size must be >= 1")
    if window_size > len(y):
        raise ValueError(f"window_size must be <= {len(y)}")
    
    y_max = scind.maximum_filter(y, size=window_size, mode='nearest')
    return _pairs(x, y_max)


def savitzky_golay_filter(data: list[tuple], window_size:int, polyorder: int = 2) -> list[tuple]:
    """
    Savitzky–Golay smoothing on y via sliding window polynomial fitting.
    window_size will be converted to nearest odd number if even.
    min window_size is 3
    max window_size is the length of the input data
    """
    x, y = _xy_from_pairs(data)
    if window_size < 3:
        raise ValueError("window_size must be >= 3")
    
    # ensure odd window and check against polyorder
    window_size = _ensure_odd_window(window_size)
    if window_size <= int(polyorder):
        raise ValueError("window_size must be > polyorder")
        
    y_f = scisig.savgol_filter(y, window_size, polyorder, mode='nearest')
    return _pairs(x, y_f)

# ===========================
# CONVOLUTION-BASED FILTERS
# Gaussian kernel smoothing
# ===========================

def gaussian_filter(data: list[tuple], sigma: float) -> list[tuple]:
    """
    Gaussian smoothing on y with given sigma (in samples).
    sigma : float
        Standard deviation of the Gaussian kernel. 
        - Small values (≈1–5) → light smoothing.  
        - Larger values (≥ len(data)/10) → heavy smoothing, trend only.  
    """
    x, y = _xy_from_pairs(data)
    y_f = scind.gaussian_filter1d(y, sigma=float(sigma), mode='nearest')
    return _pairs(x, y_f)

# ===========================
# FREQUENCY-DOMAIN FILTERS
# FFT-based (direct frequency domain cutoff)
# ===========================

def fft_cutoff_filter(data: list[tuple], cutoff_freq: int) -> list[tuple]:
    """
    Frequency-domain low-pass filter.
    
    Converts signal to frequency domain (FFT), keeps only the lowest frequencies up to
    cutoff_freq, zeros out the rest, then converts back to time domain.
    
    Parameters:
    - cutoff_freq: Number of frequency components to keep (integer)
        - 2 → keep only 2 frequencies (maximum smoothing, trend only)
        - Higher values → less smoothing
        - len(data) → keep all frequencies (no smoothing, identity)
    
    Result: Frequencies above the cutoff are zeroed out, producing a smoothed signal.
    
    Note: The mapping from level to cutoff_freq using LineSmooth's logarithmic approach
    should be done in the precomputation script, not here.
    """
    x, y = _xy_from_pairs(data)
    
    # Clamp cutoff to valid range [2, len(y)]
    cutoff_freq = max(2, min(int(cutoff_freq), len(y)))
    
    # Convert to frequency domain (returns positive frequencies only)
    fft = scifft.rfft(y)
    
    # Zero out all frequencies above cutoff
    fft[cutoff_freq:] = 0
    
    # Convert back to time domain
    y_f = scifft.irfft(fft, n=len(y))
    return _pairs(x, y_f)

# ===========================
# IIR FILTERS
# Butterworth, Chebyshev, Elliptical (infinite impulse response, frequency-domain design)
# ===========================

def butterworth_filter(data: list [tuple], cutoff_freq_normalized: float, order: int = 2) -> list[tuple]:
    """
    Butterworth low-pass on y.
    cutoff_freq_normalized in (0,1), order >= 1. Uses lfilter (phase lag like your original).
    cutoff_freq_normalized is given in normalized frequency units, relative to the Nyquist frequency (half the sampling rate).

    cutoff = 1.0 → keep all frequencies (no smoothing).

    cutoff = 0.5 → only keep frequencies up to half of Nyquist → moderate smoothing.

    cutoff = 0.1 → only keep very low frequencies → very heavy smoothing (trend only).
    
    the order is the degree of the filter’s polynomial — basically, it controls how steeply the filter transitions from “pass” (keep) 
    to “stop” (attenuate).
    
    Low order = dull knife → transition is gradual, smoothing is “soft”.

    High order = sharp knife → transition is abrupt, like a brick wall.
    """
    x, y = _xy_from_pairs(data)
    _check_cutoff_frequency(cutoff_freq_normalized)
    b, a = scisig.butter(order, float(cutoff_freq_normalized), btype='low')
    y_f = scisig.lfilter(b, a, y)
    return _pairs(x, y_f)


def chebyshev_filter(data: list [tuple], cutoff_freq_normalized: float, order: int = 2, ripple_db: float = 0.001)-> list[tuple]:
    """
    Chebyshev Type I low-pass on y.
    cutoff_freq_normalized ∈ (0, 1)
    Normalized to Nyquist (0.5·Fs).

    Lower cutoff → more smoothing. You keep only low frequencies (trend), remove more wiggles.

    Higher cutoff → less smoothing. More detail passes.

    order (integer ≥ 1)
    Controls transition steepness at the cutoff.

    Higher order → sharper transition (attenuates above-cutoff content more strongly) → appears smoother for the same cutoff.

    Very high orders can introduce ringing and be numerically touchy.

    ripple_db (> 0) (passband ripple)
    Chebyshev I trades flatness in the passband for a steeper roll-off.

    Larger ripple_db (e.g., 1 dB) → allows steeper roll-off for a given order → tends to smooth more (cuts highs harder) but the passband undulates a bit (small amplitude variations).

    Smaller ripple_db (e.g., 0.1 dB) → flatter passband (less undulation) but gentler roll-off → a bit less smoothing at the same cutoff/order.
    """
    x, y = _xy_from_pairs(data)
    _check_cutoff_frequency(cutoff_freq_normalized)
    
    # b = numerator polynomial coefficients (feed-forward part).
    # a = denominator polynomial coefficients (feedback part).
    b, a = scisig.cheby1(order, ripple_db, cutoff_freq_normalized, btype='low')
    
    # applies the IIR filter (defined by coefficients b and a) to your signal y.
    y_f = scisig.lfilter(b, a, y)
    return _pairs(x, y_f)


def elliptical_filter(data: list [tuple], cutoff_freq_normalized: float, order: int, ripple_db: float, max_atten_db: float):
    """
    Elliptic (Cauer) low-pass on y.
    cutoff_freq_normalized ∈ (0, 1)
        Normalized cutoff (relative to Nyquist).

        Lower cutoff → more smoothing (keeps only very low frequencies / trend).

        Higher cutoff → less smoothing (more detail passes).

    order (int ≥ 1)
        Controls the steepness of the transition at the cutoff.

        Higher order → sharper roll-off → for the same cutoff, more high-frequency removal ⇒ smoother output.

        Very high orders can cause ringing/instability (use sos form if you go high).

    ripple_db (> 0, passband ripple)
        Elliptic filters allow ripple in the passband to achieve a very steep roll-off.

        Larger ripple (e.g., 1 dB) → permits a steeper transition for a given order ⇒ tends to smooth more (cuts highs harder) but introduces small amplitude undulations in the kept band.

        Smaller ripple (e.g., 0.1 dB) → flatter passband (cleaner amplitudes) but gentler transition ⇒ slightly less smoothing at the same cutoff/order.

    max_atten_db (> ripple_db, stopband attenuation)
        Required attenuation in the stopband (how much you suppress high frequencies).

        Higher stopband attenuation (e.g., 60–80 dB) → stronger suppression of highs ⇒ perceived as more smoothing (less residual high-freq noise).

        Tightening this while keeping order fixed often forces a sharper transition (or a higher realized order internally), which can increase ringing risk.
    """
    x, y = _xy_from_pairs(data)
    _check_cutoff_frequency(cutoff_freq_normalized)
    b, a = scisig.ellip(order, ripple_db, max_atten_db, cutoff_freq_normalized, btype='low')
    y_f = scisig.lfilter(b, a, y)
    return _pairs(x, y_f)

