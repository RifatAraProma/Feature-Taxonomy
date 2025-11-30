"""
Centralized algorithm display names configuration.

Maps internal algorithm identifiers to polished, human-readable names
for use in visualizations, UI labels, and reports.
"""

# Algorithm display names - polished versions for UI/plots
ALGORITHM_NAMES = {
    # Transformers (Filters)
    'gaussian_filter': 'Gaussian Filter',
    'median_filter': 'Median Filter',
    'mean_filter': 'Mean Filter',
    'min_filter': 'Min Filter',
    'max_filter': 'Max Filter',
    'savitzky_golay_filter': 'Savitzky-Golay',
    'butterworth_filter': 'Butterworth',
    'fft_cutoff_filter': 'FFT Cutoff',
    'chebyshev_filter': 'Chebyshev',
    'elliptical_filter': 'Elliptical',
    
    # Reducers (Downsamplers)
    'lttb_downsample': 'LTTB',
    'm4_downsample': 'M4',
    'rdp_downsample': 'Douglas-Peucker',
    'minmaxlttb_downsample': 'MinMaxLTTB',
    'uniform_subsample': 'Uniform Subsample',
    'fpcs_downsample': 'FPCS',
    'tda_downsample': 'TopoLines',
    
    # Aggregators
    'asap_aggregator': 'ASAP',
    'bin_average_aggregator': 'PAA',
}


def get_algorithm_name(algorithm_id: str) -> str:
    """
    Get the polished display name for an algorithm.
    
    Args:
        algorithm_id: Internal algorithm identifier (e.g., 'gaussian_filter')
    
    Returns:
        Polished display name (e.g., 'Gaussian Filter')
        Falls back to title-cased version if not found.
    """
    return ALGORITHM_NAMES.get(algorithm_id, algorithm_id.replace('_', ' ').title())


def get_all_names() -> dict:
    """
    Get all algorithm name mappings.
    
    Returns:
        Dictionary mapping algorithm IDs to display names
    """
    return ALGORITHM_NAMES.copy()


# Reverse mapping: display name -> algorithm ID (for lookups)
NAME_TO_ID = {v: k for k, v in ALGORITHM_NAMES.items()}


def get_algorithm_id(display_name: str) -> str:
    """
    Get the internal algorithm ID from a display name.
    
    Args:
        display_name: Polished display name (e.g., 'Gaussian Filter')
    
    Returns:
        Internal algorithm ID (e.g., 'gaussian_filter')
        Returns the input if not found.
    """
    return NAME_TO_ID.get(display_name, display_name.lower().replace(' ', '_'))
