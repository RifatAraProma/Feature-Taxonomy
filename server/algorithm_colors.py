"""
Algorithm color mapping - centralized configuration.
This mirrors the frontend colors defined in web/src/constants/algorithmColors.ts
to ensure consistent visualization across the entire application.
"""

# Algorithm color map - matches frontend exactly
ALGORITHM_COLORS = {
    'gaussian_filter': '#4B0082',        
    'median_filter': '#7B68EE',         
    'mean_filter': '#00008B',          
    'min_filter': '#4169E1',             
    'max_filter': '#1b9e77',                     
    'savitzky_golay_filter': '#00FFFF',  
    'butterworth_filter': '#006400',   
    'fft_cutoff_filter': '#66a61e',   
    'chebyshev_filter': '#00FF7F',    
    'elliptical_filter': '#a6761d',   

    # Reducers (7 algorithms) - Next 7 colors
    'lttb_downsample': '#e6ab02',        
    'm4_downsample': '#FFC72C',         
    'rdp_downsample': '#A0522D',       
    'minmaxlttb_downsample': '#d95f02', 
    'uniform_subsample': '#F08080', 
    'fpcs_downsample': '#722F37',     
    'tda_downsample': '#B22222',        

    # Aggregators (2 algorithms) - Reuse from palette
    'asap_aggregator': '#800080',       
    'bin_average_aggregator': '#e7298a', 
}


def get_algorithm_color(algorithm_name: str) -> str:
    """
    Get the color for a given algorithm name.
    Returns a default gray color if the algorithm is not found.
    
    Args:
        algorithm_name: The name of the algorithm
        
    Returns:
        Hex color string
    """
    return ALGORITHM_COLORS.get(algorithm_name, '#9E9E9E')  # Default to Gray if not found


def get_all_colors() -> dict:
    """
    Get the complete algorithm color mapping.
    
    Returns:
        Dictionary mapping algorithm names to hex colors
    """
    return ALGORITHM_COLORS.copy()
