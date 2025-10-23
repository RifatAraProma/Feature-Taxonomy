import numpy as np

def highpass_energy(y, cutoff_ratio=0.25):
    y = np.asarray(y, dtype=float)
    Y = np.fft.rfft(y - np.mean(y))
    freqs = np.fft.rfftfreq(len(y), d=1.0)
    cutoff = cutoff_ratio * np.max(freqs) if len(freqs) else 0.0
    mask = freqs >= cutoff
    return float(np.sum(np.abs(Y[mask])**2))
