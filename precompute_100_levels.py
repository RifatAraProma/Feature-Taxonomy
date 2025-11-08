import json
import os
import numpy as np
import matplotlib.pyplot as plt
from server.algorithms import transformers
from server.features.pae import get_pae


# Configuration
NUM_LEVELS = 101  # 0-100 inclusive
PRECOMPUTED_DIR = "precomputed/stock_aapl_price"
TEST_DATASET_CATEGORY = "stock_price"
TEST_DATASET = "stock_aapl_price"

ALGORITHMS_CONFIG = {
    # 'fft_cutoff_filter': {
    #     'param_name': 'cutoff_freq',
    #     'param_bounds': None,  # Will be set dynamically: (2, data_length)
    #     'param_type': 'int',
    #     'use_logscale': True,  # Use logarithmic scaling for linear PAE
    #     'param_direction': 'inverse',  # Higher cutoff_freq = Less smoothing = Higher PAE
    # },
    # 'gaussian_filter': {
    #     'param_name': 'sigma',
    #     'param_bounds': None,  # Will be set dynamically based on data length
    #     'param_type': 'float',
    #     'param_direction': 'direct',  # Higher sigma = More smoothing = Lower PAE
    # },
    # 'butterworth_filter': {
    #     'param_name': 'cutoff_freq_normalized',
    #     'param_bounds': (0.01, 0.99),  # Normalized frequency (0 to 1)
    #     'param_type': 'float',
    #     'use_logscale': True,  # Use logarithmic scaling for linear PAE
    #     'param_direction': 'inverse',  # Lower cutoff = More smoothing = Lower PAE
    #     'extra_params': {'order': 2},  # Fixed order parameter
    # },
    # 'chebyshev_filter': {
    #     'param_name': 'cutoff_freq_normalized',
    #     'param_bounds': (0.01, 0.99),  # Normalized frequency (0 to 1)
    #     'param_type': 'float',
    #     'use_logscale': True,  # Use logarithmic scaling for linear PAE
    #     'param_direction': 'inverse',  # Lower cutoff = More smoothing = Lower PAE
    #     'extra_params': {'order': 2, 'ripple_db': 0.5},  # Fixed order and ripple
    # },
    # 'elliptical_filter': {
    #     'param_name': 'cutoff_freq_normalized',
    #     'param_bounds': (0.01, 0.99),  # Normalized frequency (0 to 1)
    #     'param_type': 'float',
    #     'use_logscale': True,  # Use logarithmic scaling for linear PAE
    #     'param_direction': 'inverse',  # Lower cutoff = More smoothing = Lower PAE
    #     'extra_params': {'order': 2, 'ripple_db': 0.5, 'max_atten_db': 40},  # Fixed params
    # },
    'mean_filter': {
        'param_name': 'window_size',
        'param_bounds': None,  # Will be set dynamically: (2, data_length // 4)
        'param_type': 'int',
        'param_direction': 'direct',  # Higher window_size = More smoothing = Lower PAE
    },
    'median_filter': {
        'param_name': 'window_size',
        'param_bounds': None,  # Will be set dynamically: (2, data_length // 4)
        'param_type': 'int',
        'param_direction': 'direct',  # Higher window_size = More smoothing = Lower PAE
    },
    'min_filter': {
        'param_name': 'window_size',
        'param_bounds': None,  # Will be set dynamically: (2, data_length // 4)
        'param_type': 'int',
        'param_direction': 'direct',  # Higher window_size = More smoothing = Lower PAE
    },
    'max_filter': {
        'param_name': 'window_size',
        'param_bounds': None,  # Will be set dynamically: (2, data_length // 4)
        'param_type': 'int',
        'param_direction': 'direct',  # Higher window_size = More smoothing = Lower PAE
    },
    'savitzky_golay_filter': {
        'param_name': 'window_size',
        'param_bounds': None,  # Will be set dynamically: (3, data_length // 4)
        'param_type': 'int',
        'param_direction': 'direct',  # Higher window_size = More smoothing = Lower PAE
        'extra_params': {'polyorder': 2},  # Fixed polynomial order
    },
}


def load_dataset(category, name):
    """Load time series data from JSON file."""
    with open(f"data/{category}/{name}.json", 'r') as f:
        return np.array(json.load(f))


def create_level_0(y_data):
    """Create level 0 file with original unfiltered data.
    This is the same for all algorithms.
    
    Args:
        y_data: Original time series data (numpy array)
    
    Returns:
        dict: Level 0 data info
    """
    pae_value = get_pae(y_data.tolist())
    
    output_data = {
        "dataset_name": TEST_DATASET,
        "algorithm": "original",  # Not algorithm-specific
        "level": 0,
        "parameter_name": "none",
        "parameter_value": None,
        "pae": float(pae_value),
        "output": y_data.tolist()
    }
    
    return output_data


def generate_levels(algo_name, y_data):
    """Generate 101 precomputed levels (0-100) by sampling parameter space.
    Level 0 is the original data (same for all algorithms).
    Levels 1-100 apply the transformation with varying parameters.
    
    Args:
        algo_name: Name of the algorithm
        y_data: Time series data
    """
    config = ALGORITHMS_CONFIG[algo_name]
    os.makedirs(PRECOMPUTED_DIR, exist_ok=True)
    
    # Set parameter bounds
    param_name = config['param_name']
    param_bounds = config.get('param_bounds')
    
    if param_bounds is None:
        # Dynamic bounds based on algorithm
        if algo_name == 'gaussian_filter':
            param_min = 1.0
            param_max = len(y_data) / 10.0
            print(f"Gaussian filter: sigma range = [{param_min:.2f}, {param_max:.2f}]")
        elif algo_name == 'fft_cutoff_filter':
            param_min = 2
            param_max = len(y_data)
            print(f"FFT cutoff filter: cutoff_freq range = [{param_min}, {param_max}]")
        elif algo_name in ['mean_filter', 'median_filter', 'min_filter', 'max_filter']:
            # Window-based filters: window_size from 2 to data_length/4
            param_min = 2
            param_max = max(5, len(y_data) // 4)
            print(f"{algo_name}: window_size range = [{param_min}, {param_max}]")
        elif algo_name == 'savitzky_golay_filter':
            # Savitzky-Golay: window_size must be odd and > polyorder
            # Start from 3 (minimum for polyorder=2) to data_length/4
            param_min = 3
            param_max = max(7, len(y_data) // 4)
            print(f"{algo_name}: window_size range = [{param_min}, {param_max}]")
    else:
        param_min, param_max = param_bounds
        print(f"{algo_name}: {param_name} range = [{param_min}, {param_max}]")
    
    # Generate parameter values for levels 1-100 (100 levels)
    num_transform_levels = NUM_LEVELS - 1  # Exclude level 0
    
    if config.get('use_logscale', False):
        # LineSmooth approach: logarithmic scaling for linear PAE relationship
        import math
        param_values = []
        param_direction = config.get('param_direction')
        
        for i in range(num_transform_levels):
            # Normalize to [0, 1] for levels 1-100
            filter_level = i / (num_transform_levels - 1)
            # Apply logarithmic scaling: log(1.0 * (1 - x) + e * x)
            scaled_level = math.log(1.0 * (1 - filter_level) + math.e * filter_level)
            
            # Map to parameter range based on direction
            # Goal: Higher level → More smoothing → Lower PAE
            if param_direction == 'direct':
                # Direct relationship: Higher param = More smoothing
                # Level 1: param_min (least smoothing)
                # Level 100: param_max (most smoothing)
                param_val = param_min + scaled_level * (param_max - param_min)
            else:  # 'inverse'
                # Inverse relationship: Lower param = More smoothing
                # Level 1: param_max (least smoothing)
                # Level 100: param_min (most smoothing)
                param_val = param_max - scaled_level * (param_max - param_min)
            
            if config['param_type'] == 'int':
                param_val = int(param_val)
                if algo_name == 'fft_cutoff_filter':
                    param_val = max(2, min(param_val, len(y_data)))
            else:
                param_val = max(param_min, min(param_val, param_max))
            
            param_values.append(param_val)
        param_values = np.array(param_values)
    else:
        # Linear mapping (for algorithms without LineSmooth)
        param_direction = config.get('param_direction', 'inverse')
        
        if param_direction == 'direct':
            # Direct: Higher level → Higher param → More smoothing → Lower PAE
            if config['param_type'] == 'float':
                param_values = np.linspace(param_min, param_max, num_transform_levels)
            else:
                param_values = np.linspace(param_min, param_max, num_transform_levels, dtype=int)
        else:  # 'inverse'
            # Inverse: Higher level → Lower param → More smoothing → Lower PAE
            if config['param_type'] == 'float':
                param_values = np.linspace(param_max, param_min, num_transform_levels)
            else:
                param_values = np.linspace(param_max, param_min, num_transform_levels, dtype=int)
    
    # Special handling for savitzky_golay_filter: ensure window_size is odd
    if algo_name == 'savitzky_golay_filter':
        polyorder = config.get('extra_params', {}).get('polyorder', 2)
        # Ensure all window sizes are odd and > polyorder
        param_values_fixed = []
        for p in param_values:
            p_int = int(p)
            # Make odd if even
            if p_int % 2 == 0:
                p_int += 1
            # Ensure > polyorder
            if p_int <= polyorder:
                p_int = polyorder + 1
                # Make odd if needed
                if p_int % 2 == 0:
                    p_int += 1
            param_values_fixed.append(p_int)
        param_values = np.array(param_values_fixed)
        print(f"  Adjusted window_size values to be odd and > polyorder={polyorder}")
        print(f"  First few values: {param_values[:5]}, Last few: {param_values[-5:]}")
    
    # Generate precomputed files and collect data for plotting
    levels_data = []
    successful_levels = 0
    
    print(f"\nGenerating {NUM_LEVELS} levels for {algo_name}...")
    
    # LEVEL 0: Original unfiltered data
    print(f"  Level 0: Original data (no transformation)")
    level_0_data = create_level_0(y_data)
    filename = f"{PRECOMPUTED_DIR}/{algo_name}_level_0.json"
    with open(filename, 'w') as f:
        json.dump(level_0_data, f)
    
    levels_data.append({
        'level': 0,
        'param_value': None,
        'pae': level_0_data['pae']
    })
    successful_levels += 1
    
    # LEVELS 1-100: Apply transformations
    extra_params = config.get('extra_params', {})
    
    for i, param_value in enumerate(param_values):
        level_idx = i + 1  # Levels 1-100
        try:
            # Build full parameter dict: main param + extra params
            all_params = {param_name: param_value}
            all_params.update(extra_params)
            
            # Apply algorithm
            y_smooth = transformers.apply(algo_name, y_data, **all_params)
            pae_value = get_pae(y_smooth)
            
            # Save to file
            filename = f"{PRECOMPUTED_DIR}/{algo_name}_level_{level_idx}.json"
            
            # Ensure y_smooth is a list for JSON serialization
            if isinstance(y_smooth, np.ndarray):
                y_smooth_list = y_smooth.tolist()
            else:
                y_smooth_list = y_smooth
            
            output_data = {
                "dataset_name": TEST_DATASET,
                "algorithm": algo_name,
                "level": level_idx,
                "parameter_name": param_name,
                "parameter_value": float(param_value) if config['param_type'] == 'float' else int(param_value),
                "pae": float(pae_value),
                "output": y_smooth_list
            }
            
            with open(filename, 'w') as f:
                json.dump(output_data, f)
            
            levels_data.append({
                'level': level_idx,
                'param_value': output_data['parameter_value'],
                'pae': output_data['pae']
            })
            successful_levels += 1
            
            if level_idx % 20 == 0:
                print(f"  Completed {level_idx}/{NUM_LEVELS - 1} transformation levels")
                
        except Exception as e:
            print(f"  Error at level {level_idx}: {e}")
    
    print(f"✓ Generated {successful_levels}/{NUM_LEVELS} levels for {algo_name}")
    
    return levels_data


def plot_levels(algo_name, levels_data):
    """Generate plot of PAE vs parameter value for an algorithm.
    
    Args:
        algo_name: Algorithm name
        levels_data: List of dicts with 'level', 'param_value', 'pae'
    """
    if not levels_data:
        print(f"No data to plot for {algo_name}")
        return
    
    param_name = ALGORITHMS_CONFIG[algo_name]['param_name']
    
    # Filter out level 0 (which has None param_value) for plotting
    transform_levels = [d for d in levels_data if d['param_value'] is not None]
    
    if not transform_levels:
        print(f"No transformation levels to plot for {algo_name}")
        return
    
    param_values = [d['param_value'] for d in transform_levels]
    pae_values = [d['pae'] for d in transform_levels]
    
    # Create single plot: PAE vs Parameter Value
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    ax.plot(param_values, pae_values, 'o-', linewidth=2, markersize=5, color='#2196F3')
    ax.set_xlabel(param_name, fontsize=13, fontweight='bold')
    ax.set_ylabel('PAE', fontsize=13, fontweight='bold')
    ax.set_title(f'{algo_name}: PAE vs {param_name} (Levels 1-100)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Save plot
    dataset_plot_dir = os.path.join('plots', TEST_DATASET)
    os.makedirs(dataset_plot_dir, exist_ok=True)
    
    plot_filename = os.path.join(dataset_plot_dir, f"{algo_name}_100levels.png")
    plt.tight_layout()
    plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved plot to {plot_filename}")
    
    # Save CSV (include level 0)
    csv_filename = os.path.join(dataset_plot_dir, f"{algo_name}_100levels.csv")
    with open(csv_filename, 'w') as f:
        f.write("level,param_value,pae\n")
        for d in levels_data:
            param_str = f"{d['param_value']:.6f}" if d['param_value'] is not None else "None"
            f.write(f"{d['level']},{param_str},{d['pae']:.6f}\n")
    
    print(f"✓ Saved data to {csv_filename}")


if __name__ == "__main__":
    # Load data
    y_data = load_dataset(TEST_DATASET_CATEGORY, TEST_DATASET)
    print(f"Loaded dataset: {TEST_DATASET} with {len(y_data)} points")
    
    # Generate 101 levels for each algorithm using parameter sampling
    for algo_name in ALGORITHMS_CONFIG.keys():
        print(f"\n{'=' * 60}")
        print(f"Processing {algo_name}")
        print(f"{'=' * 60}")
        
        # Generate all 101 levels (0-100)
        levels_data = generate_levels(algo_name, y_data)
        
        # Plot param vs PAE for these 101 levels
        plot_levels(algo_name, levels_data)
        
        print(f"\n✅ Completed {algo_name}: {len(levels_data)} levels generated and plotted")
    
    print(f"\n{'=' * 60}")
    print("✅ All algorithms complete!")
    print(f"{'=' * 60}")

