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

"""
min window_size is 1, which will return the input data
max window_size is the length of the input data which will do more aggressive filtering
"""
def _check_window_size(window_size: int, max_len: int):
    if window_size < 1:
        raise ValueError("window_size must be >= 1")
    if window_size > max_len:
        raise ValueError(f"window_size must be <= {max_len}")
    
    
def _check_cutoff_frequency(cutoff_freq_normalized: float):
    if not (0 < cutoff_freq_normalized <= 1):
        raise ValueError("cutoff_norm must be in (0, 1]")

def _ensure_odd_window(window_size: int) -> int:
    """Convert window size to nearest odd number if even."""
    return window_size + 1 if window_size % 2 == 0 else window_size

# ===========================
# CONVOLUTIONAL FILTERS
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


def mean_filter(data: list[tuple], window_size: int) -> list[tuple]:
    """
    Simple moving average on y with given window_size (samples).
    min window_size is 1, which will return the input data
    max window_size is the length of the input data which will do more aggressive filtering
    """
    x, y = _xy_from_pairs(data)
    _check_window_size(window_size, len(y))
    
    pad_pre = window_size // 2
    pad_post = window_size - 1 - pad_pre
    y_pad = np.pad(y, (pad_pre, pad_post), mode='edge')
    y_f = np.convolve(y_pad, np.ones((window_size,)) / window_size, mode='valid')
    return _pairs(x, y_f)


def savitzky_golay_filter(data: list[tuple], window_size:int, polyorder: int = 2) -> list[tuple]:
    """
    Savitzky–Golay smoothing on y.
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
# FREQUENCY-DOMAIN / IIR LOW-PASS
# ===========================

def fft_cutoff_filter(data: list[tuple], cutoff_freq_normalized: float) -> list[tuple]:
    """
    Frequency-domain hard low-pass on y using rFFT.
    cutoff_freq_normalized: normalized cutoff in (0,1], where 1.0 ~ keep all, 0.5 ~ Nyquist/2, etc.
    The Nyquist frequency is a concept from signal processing.

        -If your data is sampled at a rate of Fs samples per second (sampling frequency),
        then the Nyquist frequency = Fs / 2.

        - It’s the highest frequency you can represent without aliasing (distortions that happen when higher frequencies “fold” into lower ones).
    """
    x, y = _xy_from_pairs(data)
    _check_cutoff_frequency(cutoff_freq_normalized)
    
    #frequency-domain representation (positive frequencies only).
    fft = scifft.rfft(y)
    
    #number of available frequency bins (≈ half of your time-domain length, +1)
    nfft = fft.shape[0]              # = N//2 + 1
    
    # keep bins up to k_keep (inclusive), zero the rest
    # cutoff_freq_normalized * (nfft - 1) gives the index of the last frequency bin you want to keep.
    k_keep = int(round(cutoff_freq_normalized * (nfft - 1))) 
    
    # ensures k_keep is valid
    # min(k_keep, nfft) → avoids indexing past the FFT array
    # max(2, ...) → makes sure at least the DC bin (0 Hz) and the first frequency bin are preserved.
    k_keep = max(2, min(k_keep, nfft))
    
    # zero out everything above cutoff
    fft[k_keep:] = 0
    y_f = scifft.irfft(fft, n=len(y))
    return _pairs(x, y_f)


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
    
    Think of order like the sharpness of the knife at the cutoff frequency.

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
