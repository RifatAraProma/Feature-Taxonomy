import numpy as np
import pandas as pd
from pae import PAEMeasure, Scaler


def pixel_approx_entropy(data, width=128, height=128, r=None):
    """
    Calculate Pixel Approximate Entropy (PAE) for a time series.
    
    This implementation is based on the paper "Approximate entropy as a measure of system complexity"
    and uses a proper 2D pixel-based embedding approach.
    
    Args:
        data: Time series as list, tuple, or array
        width: Width of the 2D pixel grid (default: 128)
        height: Height of the 2D pixel grid (default: 128)
        r: Tolerance for pattern matching. If None, defaults to 0.2 * std(data_scaled)
           Range 0.1-0.2 * SD is recommended by the paper; we use 0.2 for higher tolerance.
    
    Returns:
        float: PAE value rounded to 3 decimal places
        
    Reference:
        "Approximate entropy as a measure of system complexity" 
        Uses Chebyshev distance with tolerance-based pattern matching
    """
    if not isinstance(data, (list, tuple, np.ndarray)) or len(data) == 0:
        raise ValueError("Invalid input: Expected non-empty list, tuple, or array.")
    
    # Scale the data to fit the pixel grid
    scaler = Scaler(int(width), int(height))
    data_scaled = scaler.scale(data)
    
    # Set tolerance r based on input or default behavior
    if r is None:
        # Default: 0.2 * std as recommended by the paper
        # Range 0.1-0.2 SD is good choice; we chose 0.2 for higher tolerance
        r = 0.2 * np.std(data_scaled)
    else:
        r = float(r)  # Ensure r is a float
    
    # Calculate PAE using the proper pixel-based measure
    pae_measure = PAEMeasure(w=int(width), h=int(height), r=r)
    pae_value = pae_measure.pae(data)
    
    return round(float(pae_value), 3)
