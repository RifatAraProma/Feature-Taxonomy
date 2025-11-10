from .asap.asap import asap_smoother


def asap_aggregator(data: list[tuple], resolution: int) -> list[tuple]:
    """
    ASAP aggregator with resolution-based pre-aggregation.
    
    The resolution parameter controls the output length via pre-aggregation:
    - High resolution (close to data length): minimal aggregation, more points
    - Low resolution (e.g., 10-50): heavy aggregation, fewer points
    
    ASAP will automatically select the optimal smoothing window after pre-aggregation.
    """
    # Use max_window=5 as default (ASAP will auto-select optimal window)
    # Resolution controls the actual output length via pre-aggregation
    return asap_smoother(data, max_window=5, resolution=resolution)


def bin_average_aggregator(data: list[tuple], bins: int) -> list[tuple]:
    """
    Basic bin aggregation by contiguous chunks; returns interpolated x and mean y per bin.
    X-coordinates are linearly interpolated to span [x_min, x_max], ensuring points at both endpoints.
    - data: list of (x, y) pairs
    - bins: desired number of output bins (clamped to [1, len(data)])
    """
    if not data:
        return []
    n = len(data)
    bins = max(1, min(bins, n))

    # Get the full x-range - ensure we always have points at start and end
    x_min = data[0][0]
    x_max = data[-1][0]

    out: list[tuple] = []
    
    # Calculate bin boundaries using float division for exact spacing
    for bin_idx in range(bins):
        # Calculate the range of data indices for this bin
        start_idx = int(bin_idx * n / bins)
        end_idx = int((bin_idx + 1) * n / bins)
        
        # Calculate interpolated x-coordinate to span full range
        # This ensures first point is at x_min and last point is at x_max
        if bins == 1:
            bin_x = (x_min + x_max) / 2.0  # center for single bin
        else:
            # Map bin_idx to range [x_min, x_max]
            # bin_idx=0 → x_min, bin_idx=bins-1 → x_max
            bin_x = x_min + (bin_idx / (bins - 1)) * (x_max - x_min)
        
        # Calculate mean y-value for the bin
        sy = 0.0
        count = end_idx - start_idx
        for i in range(start_idx, end_idx):
            _, y = data[i]
            sy += float(y)
        
        out.append((bin_x, sy / count))
    
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