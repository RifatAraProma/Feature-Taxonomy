from .asap.asap import asap_smoother


def asap_aggregator(data: list[tuple], max_window: int) -> list[tuple]:
    return asap_smoother(data, max_window)


def bin_average_aggregator(data: list[tuple], bins: int) -> list[tuple]:
    """
    Basic bin aggregation by contiguous chunks; returns mean x and mean y per bin.
    - data: list of (x, y) pairs
    - bins: desired number of output bins (clamped to [1, len(data)])
    """
    if not data:
        return []
    n = len(data)
    bins = max(1, min(bins, n))
    chunk = (n + bins - 1) // bins  # ceil(n / bins)

    out: list[tuple] = []
    for start in range(0, n, chunk):
        end = min(start + chunk, n)
        count = end - start
        sx = sy = 0.0
        for i in range(start, end):
            x, y = data[i]
            sx += float(x)
            sy += float(y)
        out.append((sx / count, sy / count))
    return out