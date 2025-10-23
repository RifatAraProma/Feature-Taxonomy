import numpy as np

def periodogram(y):
    y = np.asarray(y, dtype=float)
    Y = np.fft.rfft(y - np.mean(y))
    freqs = np.fft.rfftfreq(len(y), d=1.0)
    mag = np.abs(Y)
    # ignore zero freq for dominant
    if len(mag) > 1:
        idx = np.argmax(mag[1:]) + 1
        fstar = float(freqs[idx])
        A = float(mag[idx])
    else:
        fstar, A = 0.0, 0.0
    return {"freqs": freqs.tolist(), "mag": mag.tolist(), "fStar": fstar, "amplitude": A}
