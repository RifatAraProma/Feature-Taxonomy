#!/usr/bin/env python3
"""
Unified Precomputation Script - Combines Output Generation + Feature Preservation

This script efficiently combines precompute_100_levels.py and precompute_feature_preservation.py
into a single pass to avoid redundant file I/O.

For each algorithm:
1. Generate smoothed outputs for levels 0-100
2. Compute features for original data (once)
3. For each level, compute features + preservation metrics immediately
4. Save complete level files with output, features, and metrics

Features:
- Resume capability: Skip already completed levels
- Parallel processing: Process multiple algorithms simultaneously
- Progress tracking: Real-time progress bars with ETA

Usage:
    python precompute_all_unified.py <dataset_name> [options]
    
Options:
    --resume            Resume from existing files (default: enabled)
    --no-resume         Force re-computation of all levels
    --parallel N        Process N algorithms in parallel (default: 1)
    --algorithm NAME    Process only specific algorithm
    
Examples:
    python precompute_all_unified.py stock_aapl_price
    python precompute_all_unified.py stock_aapl_price --parallel 4
    python precompute_all_unified.py stock_aapl_price --algorithm gaussian_filter
    python precompute_all_unified.py stock_aapl_price --no-resume --parallel 2
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

# Import algorithm routers
from server.algorithms.transformers import CALLS as TRANSFORMER_CALLS
from server.algorithms.reducers import CALLS as REDUCER_CALLS
from server.algorithms.aggregators import CALLS as AGGREGATOR_CALLS

# Import feature computation
from server.features.compute_features import (
    compute_all_features,
    compute_feature_preservation_metrics,
    FeatureConfig
)

# Import PAE computation
from server.features.pae import get_pae


# =======================================================================================
# CONFIGURATION - Same as precompute_100_levels.py
# =======================================================================================

NUM_LEVELS = 101  # Level 0 (original) + 100 smoothing levels
TEST_DATASET = "stock_aapl_price"  # Default dataset

# Algorithm configurations - matches precompute_100_levels.py
ALGORITHMS_CONFIG = {
    # TRANSFORMER ALGORITHMS - Modify values without changing length
    'gaussian_filter': {
        'param_name': 'sigma',
        'param_bounds': (1.0, None),  # Will be set dynamically based on data length
        'param_type': 'float',
        'param_direction': 'direct',  # Higher sigma = More smoothing = Lower PAE
        'algorithm_type': 'transformer',
        'use_logscale': True,
    },
    'mean_filter': {
        'param_name': 'window_size',
        'param_bounds': (2, None),  # Will be set dynamically: (2, data_length // 4)
        'param_type': 'int',
        'param_direction': 'direct',  # Higher window = More smoothing = Lower PAE
        'algorithm_type': 'transformer',
        'use_logscale': True,
    },
    'median_filter': {
        'param_name': 'window_size',
        'param_bounds': (2, None),
        'param_type': 'int',
        'param_direction': 'direct',
        'algorithm_type': 'transformer',
        'use_logscale': True,
    },
    'max_filter': {
        'param_name': 'window_size',
        'param_bounds': (2, None),
        'param_type': 'int',
        'param_direction': 'direct',
        'algorithm_type': 'transformer',
        'use_logscale': True,
    },
    'min_filter': {
        'param_name': 'window_size',
        'param_bounds': (2, None),
        'param_type': 'int',
        'param_direction': 'direct',
        'algorithm_type': 'transformer',
        'use_logscale': True,
    },
    'savitzky_golay_filter': {
        'param_name': 'window_size',
        'param_bounds': (3, None),
        'param_type': 'int',
        'param_direction': 'direct',
        'algorithm_type': 'transformer',
        'use_logscale': True,
    },
    'butterworth_filter': {
        'param_name': 'cutoff_freq_normalized',
        'param_bounds': (0.99, 0.01),  # Inverse: high freq (0.99) = less smoothing
        'param_type': 'float',
        'param_direction': 'inverse',  # INVERSE: Lower cutoff = More smoothing = Lower PAE
        'algorithm_type': 'transformer',
        'use_logscale': True,
    },
    'chebyshev_filter': {
        'param_name': 'cutoff_freq_normalized',
        'param_bounds': (0.99, 0.01),
        'param_type': 'float',
        'param_direction': 'inverse',
        'algorithm_type': 'transformer',
        'use_logscale': True,
    },
    'elliptical_filter': {
        'param_name': 'cutoff_freq_normalized',
        'param_bounds': (0.99, 0.01),
        'param_type': 'float',
        'param_direction': 'inverse',
        'algorithm_type': 'transformer',
        'use_logscale': True,
    },
    'fft_cutoff_filter': {
        'param_name': 'cutoff_freq',
        'param_bounds': (None, 2),  # Will be set to (data_length, 2)
        'param_type': 'int',
        'param_direction': 'inverse',  # INVERSE: Lower cutoff = More smoothing
        'algorithm_type': 'transformer',
        'use_logscale': True,
    },
    
    # REDUCER ALGORITHMS - Downsample to fewer points
    'lttb_downsample': {
        'param_name': 'output_length',
        'param_bounds': (None, None),  # Will be set to (data_length, data_length * 0.05)
        'param_type': 'int',
        'param_direction': 'inverse',  # INVERSE: Fewer points = More reduction = Lower PAE
        'algorithm_type': 'reducer',
        'use_logscale': True,
    },
    'minmaxlttb_downsample': {
        'param_name': 'output_length',
        'param_bounds': (None, None),
        'param_type': 'int',
        'param_direction': 'inverse',
        'algorithm_type': 'reducer',
        'use_logscale': True,
    },
    'm4_downsample': {
        'param_name': 'output_length',
        'param_bounds': (None, 8),  # Will be (data_length, 8) - M4 requires >= 8 points
        'param_type': 'int',
        'param_direction': 'inverse',
        'algorithm_type': 'reducer',
        'use_logscale': True,
    },
    'uniform_subsample': {
        'param_name': 'output_length',
        'param_bounds': (None, None),
        'param_type': 'int',
        'param_direction': 'inverse',
        'algorithm_type': 'reducer',
        'use_logscale': True,
    },
    'rdp_downsample': {
        'param_name': 'output_length',
        'param_bounds': (None, 3),  # RDP requires >= 3 points
        'param_type': 'int',
        'param_direction': 'inverse',
        'algorithm_type': 'reducer',
        'use_logscale': True,
    },
    'fpcs_downsample': {
        'param_name': 'rate',
        'param_bounds': (1, None),  # Will be (1, data_length // 3)
        'param_type': 'int',
        'param_direction': 'direct',  # DIRECT: Higher rate = More downsampling = Lower PAE
        'algorithm_type': 'reducer',
        'use_logscale': True,
    },
    'tda_downsample': {
        'param_name': 'filter_level',
        'param_bounds': (0.0, 1.0),
        'param_type': 'float',
        'param_direction': 'direct',
        'algorithm_type': 'reducer',
        'use_logscale': True,
    },
    
    # AGGREGATOR ALGORITHMS
    'bin_average_aggregator': {
        'param_name': 'bins',
        'param_bounds': (2, None),  # Will be (2, data_length)
        'param_type': 'int',
        'param_direction': 'inverse',
        'algorithm_type': 'aggregator',
        'use_logscale': True,
    },
    'asap_aggregator': {
        'param_name': 'resolution',
        'param_bounds': (10, None),  # Will be (10, data_length // 2)
        'param_type': 'int',
        'param_direction': 'inverse',
        'algorithm_type': 'aggregator',
        'use_logscale': True,
    },
}


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

def load_dataset(dataset_id: str) -> np.ndarray:
    """Load dataset from data/ directory structure."""
    # Search for dataset in all subdirectories
    for root, dirs, files in os.walk("data"):
        for file in files:
            if file.endswith(".json"):
                name_without_ext = file.replace(".json", "")
                if name_without_ext == dataset_id:
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'y' in data:
                            return np.array(data['y'])
                        else:
                            return np.array(data)
    
    raise FileNotFoundError(f"Dataset {dataset_id} not found in data/ directory")


def ensure_odd_window(window_size: int) -> int:
    """Ensure window size is odd (required for some filters)."""
    if window_size % 2 == 0:
        return window_size + 1
    return window_size


def call_algorithm(algo_name: str, data: np.ndarray, param_name: str, param_value) -> List:
    """Call the appropriate algorithm with given parameters."""
    # Convert to (x, y) pairs
    pairs = [(i, float(y)) for i, y in enumerate(data)]
    
    # Try transformer first
    if algo_name in TRANSFORMER_CALLS:
        result = TRANSFORMER_CALLS[algo_name](pairs, **{param_name: param_value})
        # Transformers return pairs, extract y values
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], tuple):
            return [y for x, y in result]
        return result
    
    # Try reducer
    elif algo_name in REDUCER_CALLS:
        result = REDUCER_CALLS[algo_name](pairs, **{param_name: param_value})
        # Reducers return pairs
        return result
    
    # Try aggregator
    elif algo_name in AGGREGATOR_CALLS:
        result = AGGREGATOR_CALLS[algo_name](pairs, **{param_name: param_value})
        # Aggregators return pairs
        return result
    
    else:
        raise ValueError(f"Unknown algorithm: {algo_name}")


def generate_parameter_values(config: Dict, data_length: int) -> List:
    """Generate 100 parameter values using log-scale sampling (levels 1-100)."""
    param_name = config['param_name']
    param_bounds = config['param_bounds']
    param_type = config['param_type']
    param_direction = config.get('param_direction', 'inverse')
    use_logscale = config.get('use_logscale', False)
    algo_type = config.get('algorithm_type', 'transformer')
    
    # Determine actual bounds based on data length
    param_min, param_max = param_bounds
    
    # Dynamic bounds for data-length-dependent algorithms
    if param_min is None or param_max is None:
        if 'window_size' in param_name:
            param_min = param_bounds[0] if param_bounds[0] is not None else 2
            param_max = data_length // 4
        elif 'sigma' in param_name:
            param_min = 1.0
            param_max = data_length / 10.0
        elif param_name == 'cutoff_freq':
            param_min = data_length
            param_max = 2
        elif param_name == 'output_length':
            param_min = data_length
            param_max = max(3, int(data_length * 0.05))
            if 'm4' in str(config):
                param_max = max(8, param_max)
        elif param_name == 'rate':
            param_min = 1
            param_max = data_length // 3
        elif param_name == 'bins':
            param_min = 2
            param_max = data_length
        elif param_name == 'resolution':
            param_min = 10
            param_max = data_length // 2
    
    num_transform_levels = NUM_LEVELS - 1  # 100 levels (excluding level 0)
    
    if use_logscale:
        param_values = []
        for i in range(num_transform_levels):
            filter_level = i / (num_transform_levels - 1)
            scaled_level = math.log(1.0 * (1 - filter_level) + math.e * filter_level)
            
            if param_direction == 'direct':
                param_val = param_min + scaled_level * (param_max - param_min)
            else:  # 'inverse'
                param_val = param_max - scaled_level * (param_max - param_min)
            
            if param_type == 'int':
                param_val = int(param_val)
                param_val = max(param_min, min(param_val, param_max))
            else:
                param_val = max(param_min, min(param_val, param_max))
            
            param_values.append(param_val)
    else:
        # Linear spacing
        if param_direction == 'direct':
            param_values = np.linspace(param_min, param_max, num_transform_levels)
        else:
            param_values = np.linspace(param_max, param_min, num_transform_levels)
        
        if param_type == 'int':
            param_values = [int(v) for v in param_values]
    
    return param_values


# =======================================================================================
# MAIN UNIFIED COMPUTATION
# =======================================================================================

def compute_algorithm_unified(algo_name: str, dataset_id: str, y_data: np.ndarray, 
                              output_dir: str, resume: bool = True) -> bool:
    """
    Unified computation: Generate outputs + features + metrics in one pass.
    
    Args:
        algo_name: Algorithm name
        dataset_id: Dataset identifier
        y_data: Original time series data
        output_dir: Directory to save output files
        resume: If True, skip already completed levels
        
    Returns:
        bool: Success status
    """
    print(f"\n{'='*70}")
    print(f"Processing: {algo_name}")
    print(f"{'='*70}")
    print(f"Original data: {len(y_data)} points")
    
    config = ALGORITHMS_CONFIG[algo_name]
    
    # ============================================================
    # STEP 0: Check existing files if resume is enabled
    # ============================================================
    levels_to_process = list(range(NUM_LEVELS))
    
    if resume:
        existing_complete = []
        for level_idx in range(NUM_LEVELS):
            level_file = os.path.join(output_dir, f"{algo_name}_level_{level_idx}.json")
            if os.path.exists(level_file):
                try:
                    with open(level_file, 'r') as f:
                        data = json.load(f)
                    # Check if file has all required fields
                    if ('output' in data and 
                        'features' in data and 
                        'featurePreservation' in data):
                        existing_complete.append(level_idx)
                except:
                    pass  # File corrupt or incomplete, will re-compute
        
        if existing_complete:
            print(f"✓ Resume mode: Found {len(existing_complete)} complete levels, will skip them")
            levels_to_process = [i for i in levels_to_process if i not in existing_complete]
        
        if not levels_to_process:
            print(f"✓ All levels already complete for {algo_name}, skipping")
            return True
    
    # ============================================================
    # STEP 1: Compute features for ORIGINAL data (once)
    # ============================================================
    print("Computing features for original series...")
    cfg = FeatureConfig()
    original_features = compute_all_features(y_data, cfg)
    
    # ============================================================
    # STEP 2: Generate parameter values for levels 1-100
    # ============================================================
    param_values = generate_parameter_values(config, len(y_data))
    param_name = config['param_name']
    
    # ============================================================
    # STEP 3: Process each level with progress bar
    # ============================================================
    progress = ProgressBar(len(levels_to_process), desc=f"{algo_name:25}")
    
    for level_idx in levels_to_process:
        if level_idx == 0:
            # Create Level 0 (original data)
            pae_original = get_pae(y_data.tolist())
            
            level_0_data = {
                "dataset_name": dataset_id,
                "algorithm": algo_name,
                "level": 0,
                "parameter_name": "none",
                "parameter_value": None,
                "pae": float(pae_original),
                "output": y_data.tolist(),
                "features": original_features,
                "featurePreservation": {}  # Perfect preservation
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
            
            try:
                # Generate smoothed output
                output = call_algorithm(algo_name, y_data, param_name, param_val)
                
                # Extract y-values if output is pairs
                if isinstance(output, list) and len(output) > 0 and isinstance(output[0], (tuple, list)):
                    y_simplified = [y for x, y in output]
                else:
                    y_simplified = output
                
                # Compute PAE
                pae_val = get_pae(y_simplified)
                
                # Compute features for simplified series
                simplified_features = compute_all_features(np.array(y_simplified), cfg)
                
                # Compute preservation metrics
                preservation_metrics = compute_feature_preservation_metrics(
                    original_features=original_features,
                    simplified_features=simplified_features
                )
                
                # Save level data
                level_data = {
                    "dataset_name": dataset_id,
                    "algorithm": algo_name,
                    "level": level_idx,
                    "parameter_name": param_name,
                    "parameter_value": param_val,
                    "pae": float(pae_val),
                    "output": output,  # Keep original format (pairs or values)
                    "features": simplified_features,
                    "featurePreservation": preservation_metrics
                }
                
                level_file = os.path.join(output_dir, f"{algo_name}_level_{level_idx}.json")
                with open(level_file, 'w') as f:
                    json.dump(level_data, f, indent=2)
            
            except Exception as e:
                print(f"\n  ⚠ Error at level {level_idx} (param={param_val}): {e}")
                continue
        
        progress.update(1)
    
    print(f"✓ Completed {algo_name}")
    return True


def compute_feature_scales(dataset_id: str, output_dir: str):
    """
    Compute global feature scales from all algorithms and levels.
    Same as precompute_feature_preservation.py
    """
    print(f"\n{'='*70}")
    print("Calculating Feature Preservation Scales...")
    print(f"{'='*70}")
    
    # Collect all metrics from all algorithm level files
    metric_values = {}
    
    for filename in os.listdir(output_dir):
        if not filename.endswith('.json') or filename.startswith('_'):
            continue
        
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        if 'featurePreservation' not in data:
            continue
        
        preservation = data['featurePreservation']
        
        for feature_name, metrics in preservation.items():
            if not isinstance(metrics, dict):
                continue
            
            for metric_name, value in metrics.items():
                if not isinstance(value, (int, float)):
                    continue
                
                full_key = f"{feature_name}_{metric_name}"
                
                if full_key not in metric_values:
                    metric_values[full_key] = []
                
                metric_values[full_key].append(float(value))
    
    # Compute scales (25th, 50th, 75th percentiles)
    scales = {}
    
    for metric_key, values in metric_values.items():
        if len(values) == 0:
            continue
        
        values_sorted = sorted(values)
        n = len(values_sorted)
        
        # Determine metric type
        if any(x in metric_key for x in ['bottleneck', 'wasserstein', 'l1', 'linf', 'delta', 'mae']):
            metric_type = 'error'
        elif 'retention' in metric_key or 'correlation' in metric_key:
            metric_type = 'correlation'
        elif 'ratio' in metric_key:
            metric_type = 'ratio'
        else:
            metric_type = 'error'
        
        p25_idx = int(n * 0.25)
        p50_idx = int(n * 0.50)
        p75_idx = int(n * 0.75)
        
        if metric_type == 'error':
            scales[metric_key] = {
                'type': 'error',
                'excellent': values_sorted[p25_idx],
                'good': values_sorted[p50_idx],
                'fair': values_sorted[p75_idx],
                'poor': values_sorted[-1],
                'samples': len(values)
            }
        elif metric_type == 'correlation':
            scales[metric_key] = {
                'type': 'correlation',
                'poor': values_sorted[0],
                'fair': values_sorted[p25_idx],
                'good': values_sorted[p50_idx],
                'excellent': values_sorted[p75_idx],
                'samples': len(values)
            }
        else:  # ratio
            deviations = [abs(v - 1.0) for v in values]
            dev_sorted = sorted(deviations)
            scales[metric_key] = {
                'type': 'ratio',
                'excellent': dev_sorted[p25_idx],
                'good': dev_sorted[p50_idx],
                'fair': dev_sorted[p75_idx],
                'poor': dev_sorted[-1],
                'samples': len(values)
            }
        
        print(f"  {metric_key:30} {metric_type:12} {len(values):8}")
    
    # Save scales
    scales_file = os.path.join(output_dir, '_feature_scales.json')
    with open(scales_file, 'w') as f:
        json.dump(scales, f, indent=2)
    
    print(f"\n✓ Saved feature scales to {scales_file}")
    print(f"✓ Computed scales for {len(scales)} metrics")
    print(f"✓ Based on {sum(s['samples'] for s in scales.values())} total samples")


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
        return (algo_name, success, None)
    except Exception as e:
        return (algo_name, False, str(e))


# =======================================================================================
# MAIN ENTRY POINT
# =======================================================================================

def main():
    """Main execution function."""
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python precompute_all_unified.py <dataset_name> [options]")
        print("\nOptions:")
        print("  --resume            Resume from existing files (default)")
        print("  --no-resume         Force re-computation of all levels")
        print("  --parallel N        Process N algorithms in parallel (default: 1)")
        print("  --algorithm NAME    Process only specific algorithm")
        print("\nExamples:")
        print("  python precompute_all_unified.py stock_aapl_price")
        print("  python precompute_all_unified.py stock_aapl_price --parallel 4")
        print("  python precompute_all_unified.py stock_aapl_price --algorithm gaussian_filter")
        print("  python precompute_all_unified.py stock_aapl_price --no-resume --parallel 2")
        return
    
    dataset_id = sys.argv[1]
    specific_algo = None
    resume = True
    num_parallel = 1
    
    # Parse options
    i = 2
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
            return
    
    print(f"\n{'UNIFIED PRECOMPUTATION: OUTPUTS + FEATURES + METRICS':^70}")
    print(f"{'='*70}")
    print(f"Dataset: {dataset_id}")
    if specific_algo:
        print(f"Algorithm: {specific_algo}")
    else:
        print(f"Algorithms: All ({len(ALGORITHMS_CONFIG)} total)")
    print(f"Resume mode: {'Enabled' if resume else 'Disabled'}")
    print(f"Parallel workers: {num_parallel}")
    print(f"{'='*70}")
    
    # Load dataset
    try:
        y_data = load_dataset(dataset_id)
        print(f"\n✓ Loaded dataset: {len(y_data)} points")
    except Exception as e:
        print(f"\n❌ Error loading dataset: {e}")
        return
    
    # Create output directory
    output_dir = f"precomputed/{dataset_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine which algorithms to process
    if specific_algo:
        if specific_algo not in ALGORITHMS_CONFIG:
            print(f"\n❌ Unknown algorithm: {specific_algo}")
            print(f"Available: {', '.join(ALGORITHMS_CONFIG.keys())}")
            return
        algorithms = [specific_algo]
    else:
        algorithms = list(ALGORITHMS_CONFIG.keys())
    
    print(f"\nProcessing {len(algorithms)} algorithm(s)...")
    
    # Process algorithms
    success_count = 0
    failed = []
    start_time = time.time()
    
    if num_parallel > 1 and len(algorithms) > 1:
        # PARALLEL PROCESSING
        print(f"\n🚀 Using {num_parallel} parallel workers\n")
        
        # Prepare arguments for parallel execution
        tasks = [(algo, dataset_id, output_dir, resume) for algo in algorithms]
        
        with ProcessPoolExecutor(max_workers=num_parallel) as executor:
            # Submit all tasks
            futures = {executor.submit(compute_algorithm_parallel_wrapper, task): task[0] 
                      for task in tasks}
            
            # Process completed tasks
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
                else:
                    failed.append((algo_name, "Returned False"))
            except Exception as e:
                print(f"\n❌ Error processing {algo_name}: {e}")
                import traceback
                traceback.print_exc()
                failed.append((algo_name, str(e)))
                continue
    
    # Compute global feature scales
    print(f"\n{'='*70}")
    compute_feature_scales(dataset_id, output_dir)
    
    # Final summary
    elapsed_time = time.time() - start_time
    print(f"\n{'='*70}")
    print(f"{'✅ UNIFIED PRECOMPUTATION COMPLETE!':^70}")
    print(f"{'='*70}")
    print(f"Successfully processed: {success_count}/{len(algorithms)} algorithms")
    if failed:
        print(f"\n❌ Failed algorithms ({len(failed)}):")
        for algo, error in failed:
            print(f"  - {algo}: {error[:80]}")
    print(f"\nOutput directory: {output_dir}")
    print(f"Total files: {len(os.listdir(output_dir))}")
    print(f"Time elapsed: {str(timedelta(seconds=int(elapsed_time)))}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
