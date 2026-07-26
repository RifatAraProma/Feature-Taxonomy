#!/usr/bin/env python3
"""
Pedometer Data Precomputation Script

This script processes all JSON files in the data/pedometer/ directory using
the exact same logic as precompute_all_unified.py to generate precomputed outputs
with features and preservation metrics.

Usage:
    python precompute_pedometer.py [options]
    
Options:
    --resume            Resume from existing files (default: enabled)
    --no-resume         Force re-computation of all levels
    --parallel N        Process N algorithms in parallel (default: 1)
    --algorithm NAME    Process only specific algorithm
    
Examples:
    # Process all pedometer datasets
    python precompute_pedometer.py
    
    # With parallel processing
    python precompute_pedometer.py --parallel 4
    
    # Specific algorithm only
    python precompute_pedometer.py --algorithm gaussian_filter
    
    # Force re-computation
    python precompute_pedometer.py --no-resume --parallel 2
"""

import os
import sys
import json
import numpy as np
import math
import time
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server environments
import matplotlib.pyplot as plt


def convert_to_serializable(obj):
    """Convert NumPy types to native Python types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_to_serializable(item) for item in obj)
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    else:
        return obj

# Import algorithm routers
from server.algorithms.transformers import CALLS as TRANSFORMER_CALLS
from server.algorithms.reducers import CALLS as REDUCER_CALLS
from server.algorithms.aggregators import CALLS as AGGREGATOR_CALLS

# Import feature computation
from server.features.compute_features import (
    compute_all_features,
    compute_feature_preservation_metrics,
    FeatureConfig,
    compute_selective_features,
    _interpolate_to_match_length
)

# Import PAE computation
from server.features.pae import get_pae

# Import ONLY configuration from precompute_100_levels.py to ensure consistency
from precompute_100_levels import ALGORITHMS_CONFIG, NUM_LEVELS


# =======================================================================================
# CONFIGURATION
# =======================================================================================

# Pedometer data directory
PEDOMETER_DIR = "data/pedometer"

# Feature categorization for selective interpolation
POSITION_DEPENDENT_FEATURES = [
    'level', 'slope', 'curvature', 'regression', 'trend', 'noise', 'roughness'
]

POSITION_INDEPENDENT_FEATURES = [
    'mean', 'extrema', 'regimes', 'change_points', 'spikes_dips'
]


# =======================================================================================
# PROGRESS BAR UTILITIES
# =======================================================================================

class ProgressBar:
    """Simple terminal progress bar with ETA."""
    
    def __init__(self, total: int, desc: str = "", width: int = 40):
        self.total = total
        self.current = 0
        self.desc = desc
        self.width = width
        self.start_time = time.time()
    
    def update(self, n: int = 1):
        """Update progress by n steps."""
        self.current = min(self.current + n, self.total)
        # Only display every 10th update or at completion to reduce spam
        if self.current % 10 == 0 or self.current >= self.total:
            self._display()
    
    def _display(self):
        """Display current progress."""
        if self.total == 0:
            return
        
        percent = self.current / self.total
        filled = int(self.width * percent)
        bar = '█' * filled + '░' * (self.width - filled)
        
        # Calculate ETA
        elapsed = time.time() - self.start_time
        if self.current > 0:
            eta_seconds = (elapsed / self.current) * (self.total - self.current)
            eta = str(timedelta(seconds=int(eta_seconds)))
        else:
            eta = "calculating..."
        
        # Format output
        print(f"\r  {self.desc} |{bar}| {self.current}/{self.total} ({percent*100:.1f}%) ETA: {eta}", 
              end='', flush=True)
        
        if self.current >= self.total:
            print()  # New line when complete


# =======================================================================================
# HELPER FUNCTIONS
# =======================================================================================

def extract_y_values(output_data):
    """
    Extract y-values from algorithm output.
    
    Handles both:
    - Transformers: list of y-values
    - Reducers/Aggregators: list of [x, y] pairs
    """
    if not output_data:
        return np.array([])
    
    # Check if it's a list of pairs (reducers/aggregators)
    if isinstance(output_data, list) and len(output_data) > 0:
        if isinstance(output_data[0], (list, tuple)) and len(output_data[0]) == 2:
            # Extract y-values from [x, y] pairs
            return np.array([y for x, y in output_data])
        else:
            # Already y-values
            return np.array(output_data)
    
    return np.array(output_data)


def load_dataset(dataset_id: str) -> np.ndarray:
    """Load dataset from pedometer directory."""
    filepath = os.path.join(PEDOMETER_DIR, f"{dataset_id}.json")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset {dataset_id} not found in {PEDOMETER_DIR}/")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
        if isinstance(data, dict) and 'y' in data:
            return np.array(data['y'])
        else:
            return np.array(data)


def find_pedometer_datasets() -> List[str]:
    """Find all JSON datasets in the pedometer directory."""
    datasets = []
    
    if not os.path.exists(PEDOMETER_DIR):
        raise FileNotFoundError(f"Directory not found: {PEDOMETER_DIR}")
    
    for file in os.listdir(PEDOMETER_DIR):
        if file.endswith(".json"):
            dataset_id = file.replace(".json", "")
            datasets.append(dataset_id)
    
    return sorted(datasets)


def ensure_odd_window(window_size: int) -> int:
    """Ensure window size is odd (required for some filters)."""
    if window_size % 2 == 0:
        return window_size + 1
    return window_size


def call_algorithm(algo_name: str, data: np.ndarray, param_name: str, param_value, extra_params: dict = None) -> List:
    """Call the appropriate algorithm with given parameters."""
    # Convert to (x, y) pairs
    pairs = [(i, float(y)) for i, y in enumerate(data)]
    
    # Build parameter dict
    params = {param_name: param_value}
    if extra_params:
        params.update(extra_params)
    
    # Try transformer first
    if algo_name in TRANSFORMER_CALLS:
        result = TRANSFORMER_CALLS[algo_name](pairs, **params)
        # Transformers return pairs, extract y values
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], tuple):
            return [y for x, y in result]
        return result
    
    # Try reducer
    elif algo_name in REDUCER_CALLS:
        result = REDUCER_CALLS[algo_name](pairs, **params)
        # Reducers return pairs
        return result
    
    # Try aggregator
    elif algo_name in AGGREGATOR_CALLS:
        result = AGGREGATOR_CALLS[algo_name](pairs, **params)
        # Aggregators return pairs
        return result
    
    else:
        raise ValueError(f"Unknown algorithm: {algo_name}")


def generate_parameter_values(algo_name: str, data_length: int, config: Dict) -> List:
    """
    Generate 100 parameter values using log-scale sampling (levels 1-100).
    
    FOLLOWS EXACT SAME LOGIC AS precompute_all_unified.py
    """
    param_name = config['param_name']
    param_bounds = config.get('param_bounds')
    
    # Check if we need to set dynamic bounds
    if param_bounds is None or (isinstance(param_bounds, tuple) and param_bounds[1] is None):
        # Dynamic bounds based on algorithm
        if param_bounds is not None and isinstance(param_bounds, tuple):
            param_min = param_bounds[0]
        else:
            param_min = None
            
        if algo_name == 'gaussian_filter':
            param_min = 1.0
            param_max = data_length / 10.0
        elif algo_name == 'fft_cutoff_filter':
            param_min = 2
            param_max = data_length
        elif algo_name in ['mean_filter', 'median_filter', 'min_filter', 'max_filter']:
            param_min = 2
            param_max = max(5, data_length // 4)
        elif algo_name == 'savitzky_golay_filter':
            param_min = 3
            param_max = max(7, data_length // 4)
        elif algo_name in ['lttb_downsample', 'minmaxlttb_downsample', 'uniform_subsample', 'rdp_downsample']:
            param_min = 3
            param_max = data_length - 1
        elif algo_name == 'fpcs_downsample':
            param_min = 1
            param_max = max(3, data_length // 3)
        elif algo_name == 'm4_downsample':
            param_min = config.get('minimum_value', 8)
            param_max = data_length - 1
        elif algo_name == 'bin_average_aggregator':
            param_min = 2
            param_max = data_length
        elif algo_name == 'asap_aggregator':
            if param_min is None:
                param_min = 10
            param_max = data_length // 2
    else:
        param_min, param_max = param_bounds
    
    # Generate parameter values for levels 1-100 (100 levels)
    num_transform_levels = NUM_LEVELS - 1  # Exclude level 0
    
    if config.get('use_logscale', False):
        # Logarithmic scaling
        import math
        param_values = []
        param_direction = config.get('param_direction')
        
        for i in range(num_transform_levels):
            filter_level = i / (num_transform_levels - 1)
            scaled_level = math.log(1.0 * (1 - filter_level) + math.e * filter_level)
            
            if param_direction == 'direct':
                param_val = param_min + scaled_level * (param_max - param_min)
            else:  # 'inverse'
                param_val = param_max - scaled_level * (param_max - param_min)
            
            if config['param_type'] == 'int':
                param_val = int(param_val)
                if algo_name == 'fft_cutoff_filter':
                    param_val = max(2, min(param_val, data_length))
            else:
                param_val = max(param_min, min(param_val, param_max))
            
            param_values.append(param_val)
        param_values = np.array(param_values)
    else:
        # Linear mapping
        param_direction = config.get('param_direction', 'inverse')
        
        if param_direction == 'direct':
            if config['param_type'] == 'float':
                param_values = np.linspace(param_min, param_max, num_transform_levels)
            else:
                param_values = np.linspace(param_min, param_max, num_transform_levels, dtype=int)
        else:  # 'inverse'
            if config['param_type'] == 'float':
                param_values = np.linspace(param_max, param_min, num_transform_levels)
            else:
                param_values = np.linspace(param_max, param_min, num_transform_levels, dtype=int)
    
    # Special handling for savitzky_golay_filter
    if algo_name == 'savitzky_golay_filter':
        polyorder = config.get('extra_params', {}).get('polyorder', 2)
        param_values_fixed = []
        for p in param_values:
            p_int = int(p)
            if p_int % 2 == 0:
                p_int += 1
            if p_int <= polyorder:
                p_int = polyorder + 1
                if p_int % 2 == 0:
                    p_int += 1
            param_values_fixed.append(p_int)
        param_values = np.array(param_values_fixed)
    
    # Special handling for m4_downsample
    if algo_name == 'm4_downsample':
        multiple_of = config.get('requires_multiple_of', 4)
        minimum_val = config.get('minimum_value', 8)
        param_values_fixed = []
        for p in param_values:
            p_int = int(p)
            if p_int < minimum_val:
                p_int = minimum_val
            p_int = (p_int // multiple_of) * multiple_of
            if p_int < minimum_val:
                p_int = minimum_val
            param_values_fixed.append(p_int)
        param_values = np.array(param_values_fixed)
    
    return param_values.tolist()


# =======================================================================================
# MAIN UNIFIED COMPUTATION
# =======================================================================================

def compute_algorithm_unified(algo_name: str, dataset_id: str, y_data: np.ndarray, 
                              output_dir: str, resume: bool = True) -> bool:
    """
    Unified computation: Generate outputs + features + metrics in one pass.
    
    EXACT SAME LOGIC as precompute_all_unified.py
    """
    config = ALGORITHMS_CONFIG[algo_name]
    
    # Check existing files if resume is enabled
    levels_to_process = list(range(NUM_LEVELS))
    
    if resume:
        existing_complete = []
        for level_idx in range(NUM_LEVELS):
            level_file = os.path.join(output_dir, f"{algo_name}_level_{level_idx}.json")
            if os.path.exists(level_file):
                try:
                    with open(level_file, 'r') as f:
                        data = json.load(f)
                    if ('output' in data and 
                        'features' in data and 
                        'feature_preservation' in data):
                        existing_complete.append(level_idx)
                except:
                    pass
        
        if existing_complete:
            levels_to_process = [i for i in levels_to_process if i not in existing_complete]
        
        if not levels_to_process:
            return True
    
    # Compute features for ORIGINAL data (once)
    cfg = FeatureConfig()
    original_features = compute_all_features(y_data, cfg)
    
    # Generate parameter values for levels 1-100
    param_values = generate_parameter_values(algo_name, len(y_data), config)
    param_name = config['param_name']
    
    # Process each level with progress bar
    progress = ProgressBar(len(levels_to_process), desc=f"{algo_name:25}")
    
    for level_idx in levels_to_process:
        if level_idx == 0:
            # Create Level 0 (original data)
            pae_original = get_pae(y_data.tolist())
            
            # For level 0, feature preservation is PERFECT (all zeros)
            perfect_preservation = {
                'level': {'l1': 0.0, 'linf': 0.0},
                'mean': {'delta': 0.0},
                'extrema': {'bottleneck': 0.0, 'wasserstein': 0.0},
                'regimes': {'delta': 0.0},
                'change_points': {'delta': 0.0},
                'spikes_dips': {'bottleneck': 0.0, 'wasserstein': 0.0},
                'slope': {'l1': 0.0, 'linf': 0.0},
                'curvature': {'l1': 0.0, 'linf': 0.0},
                'regression': {'l1': 0.0, 'linf': 0.0},
                'trend': {'l1': 0.0, 'linf': 0.0},
                'noise': {'l1': 0.0, 'linf': 0.0, 'auc_delta': 0.0},
                'periodicity': {'amplitude_delta': 0.0, 'num_periods_delta': 0.0},
                'roughness': {'delta': 0.0}
            }
            
            level_0_data = {
                "dataset_name": dataset_id,
                "algorithm": algo_name,
                "level": 0,
                "parameter_name": "none",
                "parameter_value": None,
                "pae": convert_to_serializable(pae_original),
                "output": convert_to_serializable(y_data.tolist()),
                "features": convert_to_serializable(original_features),
                "feature_preservation": convert_to_serializable(perfect_preservation)
            }
            
            level_0_file = os.path.join(output_dir, f"{algo_name}_level_0.json")
            with open(level_0_file, 'w') as f:
                json.dump(level_0_data, f, indent=2)
        
        else:
            # Process transformation levels (1-100)
            param_val = param_values[level_idx - 1]
            
            # Special handling for window sizes (must be odd)
            if 'window_size' in param_name and config['param_type'] == 'int':
                param_val = ensure_odd_window(param_val)
            
            # Get extra_params from config if available
            extra_params = config.get('extra_params', None)
            
            try:
                # Generate smoothed output
                output = call_algorithm(algo_name, y_data, param_name, param_val, extra_params)
                
                # Extract y-values
                y_simplified = extract_y_values(output)
                
                # Compute PAE
                if isinstance(output, list) and len(output) > 0 and isinstance(output[0], (list, tuple)) and len(output[0]) == 2:
                    # Reducer/Aggregator output: interpolate to original length
                    if len(output) < len(y_data):
                        x_smooth = np.array([x for x, y in output])
                        y_smooth_vals = np.array([y for x, y in output])
                        x_original = np.arange(len(y_data))
                        y_for_pae = np.interp(x_original, x_smooth, y_smooth_vals).tolist()
                    else:
                        y_for_pae = y_simplified.tolist()
                else:
                    # Transformer output: already y-values at original length
                    y_for_pae = y_simplified.tolist()
                
                pae_val = get_pae(y_for_pae)
                
                # Compute features for simplified series
                simplified_features = compute_all_features(y_simplified, cfg)
                
                # Compute preservation metrics
                preservation_metrics = compute_feature_preservation_metrics(
                    original_features,
                    simplified_features
                )
                
                # Save level data
                level_data = {
                    "dataset_name": dataset_id,
                    "algorithm": algo_name,
                    "level": level_idx,
                    "parameter_name": param_name,
                    "parameter_value": convert_to_serializable(param_val),
                    "pae": convert_to_serializable(pae_val),
                    "output": convert_to_serializable(output),
                    "features": convert_to_serializable(simplified_features),
                    "feature_preservation": convert_to_serializable(preservation_metrics)
                }
                
                level_file = os.path.join(output_dir, f"{algo_name}_level_{level_idx}.json")
                with open(level_file, 'w') as f:
                    json.dump(level_data, f, indent=2)
            
            except Exception as e:
                print(f"\n  ❌ Error at level {level_idx}: {e}")
                continue
        
        progress.update(1)
    
    return True


def create_pae_plot(algo_name: str, dataset_id: str, output_dir: str):
    """Create a plot showing Level vs PAE for sanity checking."""
    levels = []
    pae_values = []
    param_values = []
    
    for level_idx in range(NUM_LEVELS):
        level_file = os.path.join(output_dir, f"{algo_name}_level_{level_idx}.json")
        if not os.path.exists(level_file):
            continue
        
        try:
            with open(level_file, 'r') as f:
                data = json.load(f)
            
            levels.append(level_idx)
            pae_values.append(data.get('pae', 0.0))
            param_values.append(data.get('parameter_value', None))
        except Exception as e:
            print(f"⚠️  Warning: Could not read {level_file}: {e}")
            continue
    
    if len(levels) < 2:
        print(f"⚠️  Not enough data to plot for {algo_name}")
        return
    
    # Create plots directory
    plots_dir = os.path.join(output_dir, 'plots')
    os.makedirs(plots_dir, exist_ok=True)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(levels, pae_values, marker='o', linewidth=2, markersize=4, alpha=0.7)
    ax.set_xlabel('Level', fontsize=12, fontweight='bold')
    ax.set_ylabel('PAE (Pixel Approximate Entropy)', fontsize=12, fontweight='bold')
    ax.set_title(f'{algo_name} - Level vs PAE\n{dataset_id}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Add parameter range as subtitle
    if param_values[0] is not None and param_values[-1] is not None:
        param_name = ALGORITHMS_CONFIG[algo_name]['param_name']
        ax.text(0.5, 0.98, f'{param_name}: {param_values[0]:.3f} → {param_values[-1]:.3f}',
                transform=ax.transAxes, ha='center', va='top', fontsize=10, style='italic')
    
    plt.tight_layout()
    
    # Save plot
    plot_filename = f"{algo_name}_level_vs_pae.png"
    plot_path = os.path.join(plots_dir, plot_filename)
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    print(f"  ✓ Saved plot: {plot_path}")


def compute_feature_scales(dataset_id: str, output_dir: str):
    """Compute global feature scales from all algorithms and levels."""
    feature_values = {}
    processed_files = 0
    
    for filename in os.listdir(output_dir):
        if not filename.endswith('.json') or filename.startswith('_'):
            continue
        
        filepath = os.path.join(output_dir, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Skip level 0
            if data.get('level', -1) == 0:
                continue
            
            feature_preservation = data.get('feature_preservation', {})
            
            # Collect values for each metric
            for feature_name, metrics in feature_preservation.items():
                if isinstance(metrics, dict):
                    for metric_key, metric_value in metrics.items():
                        if isinstance(metric_value, (int, float)):
                            full_key = f"{feature_name}_{metric_key}"
                            if full_key not in feature_values:
                                feature_values[full_key] = []
                            feature_values[full_key].append(float(metric_value))
                elif isinstance(metrics, (int, float)):
                    if feature_name not in feature_values:
                        feature_values[feature_name] = []
                    feature_values[feature_name].append(float(metrics))
            
            processed_files += 1
            
        except Exception as e:
            print(f"⚠️  Warning: Could not process {filename}: {e}")
    
    if not feature_values:
        print("❌ No feature preservation data found!")
        return
    
    # Calculate percentile-based thresholds
    feature_scales = {}
    
    print(f"\n{'Metric':<30} {'Type':<12} {'Samples':<10}")
    print(f"{'-'*70}")
    
    for metric_name, values in sorted(feature_values.items()):
        if len(values) == 0:
            continue
        
        values_array = np.array(values)
        
        # Determine metric type
        metric_type = 'error'
        lower_name = metric_name.lower()
        if 'retention' in lower_name or 'correlation' in lower_name:
            metric_type = 'correlation'
        elif 'ratio' in lower_name:
            metric_type = 'ratio'
        
        # Calculate percentiles
        p25 = float(np.percentile(values_array, 25))
        p50 = float(np.percentile(values_array, 50))
        p75 = float(np.percentile(values_array, 75))
        min_val = float(np.min(values_array))
        max_val = float(np.max(values_array))
        
        # Calculate frequency distribution
        total_samples = len(values_array)
        
        if metric_type == 'error':
            excellent_count = int(np.sum(values_array <= p25))
            good_count = int(np.sum((values_array > p25) & (values_array <= p50)))
            fair_count = int(np.sum((values_array > p50) & (values_array <= p75)))
            poor_count = int(np.sum(values_array > p75))
            
            feature_scales[metric_name] = {
                'type': 'error',
                'excellent': p25,
                'good': p50,
                'fair': p75,
                'min': min_val,
                'max': max_val,
                'distribution': {
                    'excellent': excellent_count,
                    'good': good_count,
                    'fair': fair_count,
                    'poor': poor_count,
                    'total': total_samples
                }
            }
        elif metric_type == 'ratio':
            deviations = np.abs(values_array - 1.0)
            dev_p25 = float(np.percentile(deviations, 25))
            dev_p50 = float(np.percentile(deviations, 50))
            dev_p75 = float(np.percentile(deviations, 75))
            
            excellent_count = int(np.sum(deviations <= dev_p25))
            good_count = int(np.sum((deviations > dev_p25) & (deviations <= dev_p50)))
            fair_count = int(np.sum((deviations > dev_p50) & (deviations <= dev_p75)))
            poor_count = int(np.sum(deviations > dev_p75))
            
            feature_scales[metric_name] = {
                'type': 'ratio',
                'excellent': dev_p25,
                'good': dev_p50,
                'fair': dev_p75,
                'min': min_val,
                'max': max_val,
                'distribution': {
                    'excellent': excellent_count,
                    'good': good_count,
                    'fair': fair_count,
                    'poor': poor_count,
                    'total': total_samples
                }
            }
        else:  # correlation
            excellent_count = int(np.sum(values_array >= p75))
            good_count = int(np.sum((values_array >= p50) & (values_array < p75)))
            fair_count = int(np.sum((values_array >= p25) & (values_array < p50)))
            poor_count = int(np.sum(values_array < p25))
            
            feature_scales[metric_name] = {
                'type': 'correlation',
                'poor': p25,
                'fair': p50,
                'good': p75,
                'min': min_val,
                'max': max_val,
                'distribution': {
                    'excellent': excellent_count,
                    'good': good_count,
                    'fair': fair_count,
                    'poor': poor_count,
                    'total': total_samples
                }
            }
        
        print(f"{metric_name:<30} {metric_type:<12} {len(values):<10}")
    
    # Save scales to JSON
    scales_file = os.path.join(output_dir, '_feature_scales.json')
    scales_data = {
        'dataset': dataset_id,
        'total_samples': sum(len(v) for v in feature_values.values()),
        'num_files': processed_files,
        'scales': feature_scales
    }
    
    with open(scales_file, 'w') as f:
        json.dump(scales_data, f, indent=2)
    
    print(f"\n✓ Saved feature scales to {scales_file}")
    print(f"✓ Computed scales for {len(feature_scales)} metrics")
    print(f"✓ Based on {scales_data['total_samples']} total samples")


# =======================================================================================
# PARALLEL PROCESSING WRAPPER
# =======================================================================================

def compute_algorithm_parallel_wrapper(args):
    """Wrapper function for parallel processing (needs to be picklable)."""
    algo_name, dataset_id, output_dir, resume = args
    
    # Load dataset (each process loads its own copy)
    y_data = load_dataset(dataset_id)
    
    # Compute
    try:
        success = compute_algorithm_unified(algo_name, dataset_id, y_data, output_dir, resume)
        
        # Create PAE plot after algorithm completes
        if success:
            try:
                create_pae_plot(algo_name, dataset_id, output_dir)
            except Exception as plot_error:
                print(f"  ⚠️  Warning: Could not create plot for {algo_name}: {plot_error}")
        
        return (algo_name, success, None)
    except Exception as e:
        return (algo_name, False, str(e))


# =======================================================================================
# MAIN ENTRY POINT
# =======================================================================================

def main():
    """Main execution function."""
    # Parse arguments
    specific_algo = None
    resume = True
    num_parallel = 1
    
    # Parse options
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--no-resume':
            resume = False
            i += 1
        elif arg == '--resume':
            resume = True
            i += 1
        elif arg == '--parallel':
            if i + 1 < len(sys.argv):
                num_parallel = int(sys.argv[i + 1])
                i += 2
            else:
                print("Error: --parallel requires a number")
                return
        elif arg == '--algorithm':
            if i + 1 < len(sys.argv):
                specific_algo = sys.argv[i + 1]
                i += 2
            else:
                print("Error: --algorithm requires a name")
                return
        else:
            print(f"Unknown option: {arg}")
            print(__doc__)
            return
    
    # Find pedometer datasets
    try:
        datasets = find_pedometer_datasets()
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        return
    
    if not datasets:
        print(f"\n❌ No JSON files found in {PEDOMETER_DIR}/")
        return
    
    print(f"\n{'PEDOMETER DATA PRECOMPUTATION':^70}")
    print(f"{'='*70}")
    print(f"Directory: {PEDOMETER_DIR}/")
    print(f"Datasets: {len(datasets)} found")
    print(f"  {', '.join(datasets)}")
    
    if specific_algo:
        print(f"Algorithm: {specific_algo}")
    else:
        print(f"Algorithms: All ({len(ALGORITHMS_CONFIG)} total)")
    print(f"Resume mode: {'Enabled' if resume else 'Disabled'}")
    print(f"Parallel workers: {num_parallel}")
    print(f"{'='*70}")
    
    # Process each dataset
    overall_start = time.time()
    datasets_processed = 0
    datasets_failed = []
    
    for dataset_idx, dataset_id in enumerate(datasets, 1):
        print(f"\n{'='*70}")
        print(f"Dataset {dataset_idx}/{len(datasets)}: {dataset_id}")
        print(f"{'='*70}")
        
        # Load dataset
        try:
            y_data = load_dataset(dataset_id)
            print(f"✓ Loaded: {len(y_data)} data points")
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            datasets_failed.append((dataset_id, str(e)))
            continue
        
        # Create output directory
        output_dir = f"precomputed/{dataset_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Determine which algorithms to process
        if specific_algo:
            if specific_algo not in ALGORITHMS_CONFIG:
                print(f"\n❌ Unknown algorithm: {specific_algo}")
                print(f"Available: {', '.join(ALGORITHMS_CONFIG.keys())}")
                datasets_failed.append((dataset_id, f"Unknown algorithm: {specific_algo}"))
                continue
            algorithms = [specific_algo]
        else:
            algorithms = list(ALGORITHMS_CONFIG.keys())
        
        # Process algorithms
        success_count = 0
        failed = []
        start_time = time.time()
        
        if num_parallel > 1 and len(algorithms) > 1:
            # PARALLEL PROCESSING
            tasks = [(algo, dataset_id, output_dir, resume) for algo in algorithms]
            
            with ProcessPoolExecutor(max_workers=num_parallel) as executor:
                futures = {executor.submit(compute_algorithm_parallel_wrapper, task): task[0] 
                          for task in tasks}
                
                for future in as_completed(futures):
                    algo_name = futures[future]
                    try:
                        result_algo, success, error = future.result()
                        if success:
                            success_count += 1
                        else:
                            failed.append((result_algo, error))
                            print(f"\n❌ {result_algo} failed: {error}")
                    except Exception as e:
                        failed.append((algo_name, str(e)))
                        print(f"\n❌ {algo_name} failed with exception: {e}")
        else:
            # SEQUENTIAL PROCESSING
            for algo_name in algorithms:
                try:
                    success = compute_algorithm_unified(algo_name, dataset_id, y_data, output_dir, resume)
                    if success:
                        success_count += 1
                        # Create PAE plot
                        try:
                            create_pae_plot(algo_name, dataset_id, output_dir)
                        except Exception as plot_error:
                            print(f"  ⚠️  Warning: Could not create plot for {algo_name}: {plot_error}")
                    else:
                        failed.append((algo_name, "Returned False"))
                except Exception as e:
                    print(f"\n❌ Error processing {algo_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    failed.append((algo_name, str(e)))
                    continue
        
        # Compute global feature scales
        print(f"\n{'Computing Feature Scales...':^70}")
        compute_feature_scales(dataset_id, output_dir)
        
        # Dataset summary
        elapsed_time = time.time() - start_time
        print(f"\n{'Dataset Summary':^70}")
        print(f"{'-'*70}")
        print(f"Successfully processed: {success_count}/{len(algorithms)} algorithms")
        if failed:
            print(f"Failed algorithms: {len(failed)}")
            for algo, error in failed[:3]:
                print(f"  - {algo}: {error[:60]}")
            if len(failed) > 3:
                print(f"  ... and {len(failed) - 3} more")
        print(f"Output directory: {output_dir}")
        print(f"Total files: {len(os.listdir(output_dir))}")
        print(f"Time: {str(timedelta(seconds=int(elapsed_time)))}")
        print(f"{'-'*70}")
        
        if success_count > 0:
            datasets_processed += 1
        else:
            datasets_failed.append((dataset_id, f"{len(failed)} algorithms failed"))
    
    # Final summary
    overall_elapsed = time.time() - overall_start
    print(f"\n{'='*70}")
    print(f"{'✅ PEDOMETER PRECOMPUTATION COMPLETE!':^70}")
    print(f"{'='*70}")
    print(f"Total datasets: {len(datasets)}")
    print(f"  ✓ Successfully processed: {datasets_processed}")
    if datasets_failed:
        print(f"  ❌ Failed: {len(datasets_failed)}")
        for ds, error in datasets_failed:
            print(f"     - {ds}: {error[:60]}")
    print(f"\nTotal time: {str(timedelta(seconds=int(overall_elapsed)))}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
