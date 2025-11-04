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


# def paa_aggregator(data: list[tuple], segments: int) -> list[tuple]:
#     """
#     Piecewise Aggregate Approximation (PAA) - divides time series into equal segments
#     and replaces each segment with its mean value.
#     
#     Parameters:
#     - data: list of (x, y) pairs representing the time series
#     - segments: number of equal-length segments to divide the series into
#     
#     Returns:
#     - list of (x, y) pairs where each point represents the mean of a segment
#     """
#     if not data:
#         return []
#     
#     n = len(data)
#     segments = max(1, min(segments, n))  # clamp segments to valid range
#     
#     # Calculate segment size
#     segment_size = n / segments
#     
#     out: list[tuple] = []
#     
#     for i in range(segments):
#         # Calculate start and end indices for this segment
#         start_idx = int(i * segment_size)
#         end_idx = int((i + 1) * segment_size)
#         
#         # Handle last segment to include any remaining points
#         if i == segments - 1:
#             end_idx = n
#             
#         # Calculate mean x and y for this segment
#         segment_count = end_idx - start_idx
#         if segment_count > 0:
#             sum_x = sum_y = 0.0
#             for j in range(start_idx, end_idx):
#                 x, y = data[j]
#                 sum_x += float(x)
#                 sum_y += float(y)
#             
#             mean_x = sum_x / segment_count
#             mean_y = sum_y / segment_count
#             out.append((mean_x, mean_y))
#     
#     return out