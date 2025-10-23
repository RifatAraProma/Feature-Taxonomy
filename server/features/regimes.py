import numpy as np

def simple_regimes(y, w=20, delta=0.5):
    y = np.asarray(y, dtype=float)
    if len(y) < w*2:  # not enough data to segment
        return [{"a":1,"b":len(y),"baseline":float(np.mean(y))}], []
    cpts = []
    a = 1
    i = w
    while i < len(y)-w:
        left = np.mean(y[i-w:i])
        right = np.mean(y[i:i+w])
        if abs(right - left) > delta:
            cpts.append({"t": int(i+1), "fromBaseline": float(left), "toBaseline": float(right)})
        i += w//2
    # Build regimes from cpts
    regs = []
    starts = [1] + [c["t"] for c in cpts]
    ends = [c["t"]-1 for c in cpts] + [len(y)]
    for a,b in zip(starts, ends):
        baseline = float(np.mean(y[a-1:b]))
        regs.append({"a": int(a), "b": int(b), "baseline": baseline})
    return regs, cpts
