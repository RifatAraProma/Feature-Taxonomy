"""
PAE-based parameter calibration for perceptually equivalent simplification levels.
This module finds algorithm parameters that produce equivalent PAE values across different methods.
"""
import numpy as np
from .features.pae import pixel_approx_entropy as pae
from .util import load_series
from .app import run_method

def compute_pae_with_scaling(y, width=800, height=450):
    """
    Compute PAE with pixel-based scaling similar to the user's implementation.
    Uses the standard PAE calculation with width/height context.
    """
    if not isinstance(y, (list, tuple, np.ndarray)) or len(y) == 0:
        raise ValueError("Invalid input: Expected non-empty array.")
    
    y_arr = np.asarray(y, dtype=float)
    
    # For pixel-based PAE, we use the standard calculation
    # The width/height would typically be used for scaling in a visualization context
    # Here we use the standard PAE which considers the data's standard deviation
    return pae(y_arr)


def get_pae_range_for_level(level):
    """
    Map slider level (0-100) to target PAE value.
    Level 0 = maximum PAE (no simplification)
    Level 100 = minimum PAE (maximum simplification)
    
    Returns: (min_pae, max_pae) tuple defining acceptable range
    """
    # Original series typically has PAE around 0.5-2.0
    # Heavy simplification can reduce it to near 0
    # We'll use a logarithmic scale for better perceptual spacing
    
    # Define PAE endpoints (these may need tuning based on your data)
    max_pae = 2.0  # Typical maximum for unsimplified series
    min_pae = 0.01  # Near-zero for heavily simplified
    
    # Exponential mapping: more granularity at lower simplification levels
    target_pae = max_pae * np.exp(-level / 100 * np.log(max_pae / min_pae))
    
    # Allow 2 decimal places tolerance (0.01 range)
    tolerance = 0.01
    return (target_pae - tolerance, target_pae + tolerance)


def calibrate_parameter_for_pae(y, method, target_level, width=800, height=450, max_iterations=15):
    """
    Find the parameter value that produces PAE matching the target level.
    
    Args:
        y: Input time series data
        method: Algorithm method name
        target_level: Slider level (0-100)
        width: Visualization width for PAE calculation
        height: Visualization height for PAE calculation
        max_iterations: Maximum binary search iterations
    
    Returns:
        dict: Parameter dictionary for the algorithm
    """
    # Get target PAE range
    min_target_pae, max_target_pae = get_pae_range_for_level(target_level)
    target_pae = (min_target_pae + max_target_pae) / 2
    
    # Compute original PAE
    orig_pae = compute_pae_with_scaling(y, width, height)
    
    # If target level is 0 (no simplification), return minimal parameters
    if target_level == 0:
        return get_minimal_params(method, len(y))
    
    # If target level is 100 (maximum simplification), return maximal parameters
    if target_level == 100:
        return get_maximal_params(method, len(y))
    
    # Define parameter search bounds based on method type
    param_min, param_max = get_param_bounds(method, len(y))
    
    # Binary search to find parameter that achieves target PAE
    best_param = param_min
    best_diff = float('inf')
    
    for iteration in range(max_iterations):
        # Try middle parameter value
        mid_param = (param_min + param_max) / 2
        
        # Create parameter dict for this method
        params = create_params_from_value(method, len(y), mid_param)
        
        # Run algorithm and compute PAE
        try:
            yhat = run_method(method, params, y)
            current_pae = compute_pae_with_scaling(yhat, width, height)
            
            # Check if within target range
            diff = abs(current_pae - target_pae)
            if diff < best_diff:
                best_diff = diff
                best_param = mid_param
            
            # If within tolerance, we're done
            if min_target_pae <= current_pae <= max_target_pae:
                return create_params_from_value(method, len(y), mid_param)
            
            # Adjust search range
            # Lower PAE means more simplification, so if PAE is too low, reduce parameter
            # Higher PAE means less simplification, so if PAE is too high, increase parameter
            if current_pae < target_pae:
                # Too much simplification, reduce parameter
                param_max = mid_param
            else:
                # Too little simplification, increase parameter
                param_min = mid_param
                
        except Exception as e:
            # If algorithm fails, try different parameter
            param_max = mid_param
            continue
    
    # Return best found parameter
    return create_params_from_value(method, len(y), best_param)


def get_param_bounds(method, data_length):
    """
    Get min/max parameter values for binary search based on method type.
    Returns normalized bounds (0-100 scale).
    """
    if 'filter' in method and not any(x in method for x in ['fft', 'butterworth', 'chebyshev']):
        return (0, 100)  # Window size based filters
    elif any(x in method for x in ['butterworth', 'fft', 'chebyshev']):
        return (0, 100)  # Frequency cutoff based
    elif 'downsample' in method:
        return (0, 100)  # Output length based
    elif 'aggregator' in method:
        return (0, 100)  # Window/bin based
    return (0, 100)


def get_minimal_params(method, data_length):
    """Return parameters that produce minimal simplification (level 0)."""
    if 'filter' in method and not any(x in method for x in ['fft', 'butterworth', 'chebyshev']):
        return {'w': 1}
    elif any(x in method for x in ['butterworth', 'fft', 'chebyshev']):
        return {'cutoff_freq_normalized': 0.5}
    elif 'downsample' in method:
        return {'output_length': data_length}
    elif method == 'asap_aggregator':
        return {'max_window': 1}
    elif method == 'bin_average_aggregator':
        return {'bins': data_length}
    return {'w': 1}


def get_maximal_params(method, data_length):
    """Return parameters that produce maximal simplification (level 100)."""
    min_points = max(50, int(data_length * 0.05))
    
    if 'filter' in method and not any(x in method for x in ['fft', 'butterworth', 'chebyshev']):
        return {'w': 51}
    elif any(x in method for x in ['butterworth', 'fft', 'chebyshev']):
        return {'cutoff_freq_normalized': 0.01}
    elif 'downsample' in method:
        return {'output_length': min_points}
    elif method == 'asap_aggregator':
        return {'max_window': 100}
    elif method == 'bin_average_aggregator':
        return {'bins': 10}
    return {'w': 51}


def create_params_from_value(method, data_length, param_value):
    """
    Convert normalized parameter value (0-100) to actual algorithm parameters.
    This mirrors the logic in App.tsx but in Python.
    """
    param_value = max(0, min(100, param_value))  # Clamp to 0-100
    
    if 'filter' in method and not any(x in method for x in ['fft', 'butterworth', 'chebyshev']):
        # Window-based filters
        w = max(1, int(1 + (param_value / 100) * 50))
        return {'w': w}
    
    elif any(x in method for x in ['butterworth', 'fft', 'chebyshev']):
        # Frequency-based filters
        cutoff = 0.5 - (param_value / 100) * 0.49
        return {'cutoff_freq_normalized': cutoff}
    
    elif 'downsample' in method:
        # Downsamplers
        min_points = max(50, int(data_length * 0.05))
        output_length = max(min_points, int(data_length - (param_value / 100) * (data_length - min_points)))
        return {'output_length': output_length}
    
    elif method == 'asap_aggregator':
        max_window = max(1, int(1 + (param_value / 100) * 99))
        return {'max_window': max_window}
    
    elif method == 'bin_average_aggregator':
        min_bins = 10
        bins = max(min_bins, int(data_length - (param_value / 100) * (data_length - min_bins)))
        return {'bins': bins}
    
    # Fallback
    w = max(1, int(1 + (param_value / 100) * 50))
    return {'w': w}
