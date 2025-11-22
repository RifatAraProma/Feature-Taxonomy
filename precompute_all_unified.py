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
- Directory processing: Process all JSON files in a data subdirectory

Usage:
    python precompute_all_unified.py <dataset_name_or_directory> [options]
    
Options:
    --resume            Resume from existing files (default: enabled)
    --no-resume         Force re-computation of all levels
    --parallel N        Process N algorithms in parallel (default: 1)
    --algorithm NAME    Process only specific algorithm
    --dir               Treat first argument as directory name (e.g., 'stock_price')
    
Examples:
    # Process single dataset
    python precompute_all_unified.py stock_aapl_price
    
    # Process all datasets in stock_price directory
    python precompute_all_unified.py stock_price --dir
    
    # With parallel processing
    python precompute_all_unified.py stock_price --dir --parallel 4
    
    # Specific algorithm only
    python precompute_all_unified.py stock_aapl_price --algorithm gaussian_filter
    
    # Force re-computation
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
    FeatureConfig,
    compute_selective_features,
    _interpolate_to_match_length
)

# Import PAE computation
from server.features.pae import get_pae


# =======================================================================================
# CONFIGURATION - Same as precompute_100_levels.py
# =======================================================================================

NUM_LEVELS = 101  # Level 0 (original) + 100 smoothing levels
TEST_DATASET = "stock_aapl_price"  # Default dataset

# Feature categorization for selective interpolation (from precompute_feature_preservation.py)
# Position-dependent features REQUIRE equal-length data (need interpolation)
POSITION_DEPENDENT_FEATURES = [
    'level',       # Point-by-point value comparison
    'slope',       # Derivative between consecutive points
    'curvature',   # Second derivative
    'regression',  # Fitted regression line (array comparison)
    'trend',       # Low-frequency FFT components
    'noise',       # High-frequency FFT components
    'roughness'    # Scalar roughness σ(ΔY) - requires uniform sampling
]

# Position-independent features work with different lengths (NO interpolation)
POSITION_INDEPENDENT_FEATURES = [
    'mean',             # Scalar value
    'extrema',          # Topological persistence diagrams (bottleneck/wasserstein)
    'regimes',          # Count of regimes/change points
    'change_points',    # Same as regimes
    'spikes_dips'       # Topological persistence diagrams (bottleneck/wasserstein)
]

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
        'extra_params': {'polyorder': 2},  # Fixed polynomial order (from precompute_100_levels)
    },
    'butterworth_filter': {
        'param_name': 'cutoff_freq_normalized',
        'param_bounds': (0.99, 0.01),  # Inverse: high freq (0.99) = less smoothing
        'param_type': 'float',
        'param_direction': 'inverse',  # INVERSE: Lower cutoff = More smoothing = Lower PAE
        'algorithm_type': 'transformer',
        'use_logscale': True,
        'extra_params': {'order': 2},  # Fixed order parameter (from precompute_100_levels)
    },
    'chebyshev_filter': {
        'param_name': 'cutoff_freq_normalized',
        'param_bounds': (0.99, 0.01),
        'param_type': 'float',
        'param_direction': 'inverse',
        'algorithm_type': 'transformer',
        'use_logscale': True,
        'extra_params': {'order': 2, 'ripple_db': 0.5},  # Fixed params (from precompute_100_levels)
    },
    'elliptical_filter': {
        'param_name': 'cutoff_freq_normalized',
        'param_bounds': (0.99, 0.01),
        'param_type': 'float',
        'param_direction': 'inverse',
        'algorithm_type': 'transformer',
        'use_logscale': True,
        'extra_params': {'order': 2, 'ripple_db': 0.5, 'max_atten_db': 40},  # Fixed params (from precompute_100_levels)
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

def extract_y_values(output_data):
    """
    Extract y-values from algorithm output.
    
    Handles both:
    - Transformers: list of y-values
    - Reducers/Aggregators: list of [x, y] pairs
    
    SAME AS precompute_feature_preservation.py
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


def split_features_by_dependency(feature_list):
    """
    Split feature list into position-dependent and position-independent features.
    
    Position-dependent features need equal-length data (require interpolation).
    Position-independent features work with different lengths (no interpolation).
    
    SAME AS precompute_feature_preservation.py
    
    Args:
        feature_list: List of feature names to split
        
    Returns:
        Tuple of (position_dependent_features, position_independent_features)
    """
    if not feature_list:
        return [], []
    
    position_dependent = []
    position_independent = []
    
    for feature in feature_list:
        if feature in POSITION_DEPENDENT_FEATURES:
            position_dependent.append(feature)
        elif feature in POSITION_INDEPENDENT_FEATURES:
            position_independent.append(feature)
    
    return position_dependent, position_independent


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


def find_datasets_in_directory(dir_name: str) -> List[str]:
    """
    Find all JSON datasets in a specific directory under data/.
    
    Args:
        dir_name: Directory name (e.g., 'stock_price', 'climate_awnd')
        
    Returns:
        List of dataset IDs (e.g., ['stock_aapl_price', 'stock_amzn_price', ...])
    """
    datasets = []
    search_path = os.path.join("data", dir_name)
    
    if not os.path.exists(search_path):
        raise FileNotFoundError(f"Directory not found: {search_path}")
    
    for file in os.listdir(search_path):
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
    
    Uses EXACT SAME LOGIC as precompute_feature_preservation.py for feature computation.
    
    Args:
        algo_name: Algorithm name
        dataset_id: Dataset identifier
        y_data: Original time series data
        output_dir: Directory to save output files
        resume: If True, skip already completed levels
        
    Returns:
        bool: Success status
    """
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
                        'feature_preservation' in data):  # Changed: use 'feature_preservation' not 'featurePreservation'
                        existing_complete.append(level_idx)
                except:
                    pass  # File corrupt or incomplete, will re-compute
        
        if existing_complete:
            levels_to_process = [i for i in levels_to_process if i not in existing_complete]
        
        if not levels_to_process:
            return True
    
    # ============================================================
    # STEP 1: Compute features for ORIGINAL data (once)
    # SAME AS precompute_feature_preservation.py
    # ============================================================
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
            # =====================================================
            # Create Level 0 (original data)
            # SAME AS precompute_feature_preservation.py
            # =====================================================
            pae_original = get_pae(y_data.tolist())
            
            # For level 0, feature preservation is PERFECT (all zeros)
            # SAME structure as precompute_feature_preservation.py
            # NOTE: change_points l1/linf removed due to performance concerns
            perfect_preservation = {
                'level': {'l1': 0.0, 'linf': 0.0},
                'mean': {'delta': 0.0},
                'extrema': {'bottleneck': 0.0, 'wasserstein': 0.0},
                'regimes': {'delta': 0.0},
                'change_points': {'delta': 0.0},  # Only delta, no l1/linf
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
                "pae": float(pae_original),
                "output": y_data.tolist(),
                "features": original_features,
                "feature_preservation": perfect_preservation  # Changed: use snake_case
            }
            
            level_0_file = os.path.join(output_dir, f"{algo_name}_level_0.json")
            with open(level_0_file, 'w') as f:
                json.dump(level_0_data, f, indent=2)
        
        else:
            # =====================================================
            # Process transformation levels (1-100)
            # SAME LOGIC AS precompute_feature_preservation.py
            # =====================================================
            param_val = param_values[level_idx - 1]
            
            # Special handling for window sizes (must be odd)
            if 'window_size' in param_name and config['param_type'] == 'int':
                param_val = ensure_odd_window(param_val)
            
            # Get extra_params from config if available
            extra_params = config.get('extra_params', None)
            
            try:
                # Generate smoothed output
                output = call_algorithm(algo_name, y_data, param_name, param_val, extra_params)
                
                # Extract y-values (SAME AS precompute_feature_preservation.py)
                y_simplified = extract_y_values(output)
                
                # Compute PAE
                pae_val = get_pae(y_simplified.tolist())
                
                # =====================================================
                # Compute features for simplified series
                # SAME SELECTIVE INTERPOLATION LOGIC AS precompute_feature_preservation.py
                # =====================================================
                
                # Use compute_all_features (no pre-interpolation)
                # Interpolation happens inside compute_feature_preservation_metrics()
                # This matches precompute_feature_preservation.py behavior
                simplified_features = compute_all_features(y_simplified, cfg)
                
                # =====================================================
                # Compute preservation metrics
                # EXACT SAME AS precompute_feature_preservation.py
                # =====================================================
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
                    "parameter_value": param_val,
                    "pae": float(pae_val),
                    "output": output,  # Keep original format (pairs or values)
                    "features": simplified_features,
                    "feature_preservation": preservation_metrics  # Changed: use snake_case
                }
                
                level_file = os.path.join(output_dir, f"{algo_name}_level_{level_idx}.json")
                with open(level_file, 'w') as f:
                    json.dump(level_data, f, indent=2)
            
            except Exception as e:
                # Log error but continue
                print(f"\n  ❌ Error at level {level_idx}: {e}")
                continue
        
        progress.update(1)
    
    return True


def compute_feature_scales(dataset_id: str, output_dir: str):
    """
    Compute global feature scales from all algorithms and levels.
    
    EXACT SAME LOGIC AS calculate_and_save_scales() in precompute_feature_preservation.py
    """
    # Collect all feature preservation values
    feature_values = {}
    processed_files = 0
    
    for filename in os.listdir(output_dir):
        if not filename.endswith('.json') or filename.startswith('_'):
            continue
        
        filepath = os.path.join(output_dir, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Skip level 0 (original data)
            if data.get('level', -1) == 0:
                continue
            
            feature_preservation = data.get('feature_preservation', {})
            
            # Collect values for each metric
            for feature_name, metrics in feature_preservation.items():
                if isinstance(metrics, dict):
                    # Nested metrics (e.g., level: {l1: ..., linf: ...})
                    for metric_key, metric_value in metrics.items():
                        if isinstance(metric_value, (int, float)):
                            full_key = f"{feature_name}_{metric_key}"
                            if full_key not in feature_values:
                                feature_values[full_key] = []
                            feature_values[full_key].append(float(metric_value))
                elif isinstance(metrics, (int, float)):
                    # Direct metric value
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
        
        # Calculate frequency distribution (how many samples in each quality bucket)
        total_samples = len(values_array)
        
        if metric_type == 'error':
            # For error: excellent <= p25, good <= p50, fair <= p75, poor > p75
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
            # For correlation: excellent >= p75, good >= p50, fair >= p25, poor < p25
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
        print("Usage: python precompute_all_unified.py <dataset_name_or_directory> [options]")
        print("\nOptions:")
        print("  --resume            Resume from existing files (default)")
        print("  --no-resume         Force re-computation of all levels")
        print("  --parallel N        Process N algorithms in parallel (default: 1)")
        print("  --algorithm NAME    Process only specific algorithm")
        print("  --dir               Treat first argument as directory name (e.g., 'stock_price')")
        print("\nExamples:")
        print("  # Process single dataset")
        print("  python precompute_all_unified.py stock_aapl_price")
        print("")
        print("  # Process all datasets in stock_price directory")
        print("  python precompute_all_unified.py stock_price --dir")
        print("")
        print("  # With parallel processing")
        print("  python precompute_all_unified.py stock_price --dir --parallel 4")
        print("")
        print("  # Specific algorithm only")
        print("  python precompute_all_unified.py stock_aapl_price --algorithm gaussian_filter")
        print("")
        print("  # Force re-computation")
        print("  python precompute_all_unified.py stock_aapl_price --no-resume --parallel 2")
        return
    
    dataset_or_dir = sys.argv[1]
    specific_algo = None
    resume = True
    num_parallel = 1
    is_directory = False
    
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
        elif arg == '--dir':
            is_directory = True
            i += 1
        else:
            print(f"Unknown option: {arg}")
            return
    
    # ============================================================
    # Determine which datasets to process
    # ============================================================
    if is_directory:
        # Process all datasets in directory
        try:
            datasets = find_datasets_in_directory(dataset_or_dir)
        except FileNotFoundError as e:
            print(f"\n❌ Error: {e}")
            print(f"\nAvailable directories in data/:")
            for item in os.listdir("data"):
                if os.path.isdir(os.path.join("data", item)):
                    print(f"  - {item}")
            return
        
        if not datasets:
            print(f"\n❌ No JSON files found in data/{dataset_or_dir}/")
            return
        
        print(f"\n{'UNIFIED PRECOMPUTATION: DIRECTORY MODE':^70}")
        print(f"{'='*70}")
        print(f"Directory: data/{dataset_or_dir}/")
        print(f"Datasets: {len(datasets)} found")
        print(f"  {', '.join(datasets[:5])}")
        if len(datasets) > 5:
            print(f"  ... and {len(datasets) - 5} more")
    else:
        # Single dataset mode
        datasets = [dataset_or_dir]
        print(f"\n{'UNIFIED PRECOMPUTATION: SINGLE DATASET MODE':^70}")
        print(f"{'='*70}")
        print(f"Dataset: {dataset_or_dir}")
    
    if specific_algo:
        print(f"Algorithm: {specific_algo}")
    else:
        print(f"Algorithms: All ({len(ALGORITHMS_CONFIG)} total)")
    print(f"Resume mode: {'Enabled' if resume else 'Disabled'}")
    print(f"Parallel workers: {num_parallel}")
    print(f"{'='*70}")
    
    # ============================================================
    # Process each dataset
    # ============================================================
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
                    else:
                        failed.append((algo_name, "Returned False"))
                except Exception as e:
                    print(f"\n❌ Error processing {algo_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    failed.append((algo_name, str(e)))
                    continue
        
        # Compute global feature scales for this dataset
        print(f"\n{'Computing Feature Scales...':^70}")
        compute_feature_scales(dataset_id, output_dir)
        
        # Dataset summary
        elapsed_time = time.time() - start_time
        print(f"\n{'Dataset Summary':^70}")
        print(f"{'-'*70}")
        print(f"Successfully processed: {success_count}/{len(algorithms)} algorithms")
        if failed:
            print(f"Failed algorithms: {len(failed)}")
            for algo, error in failed[:3]:  # Show first 3
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
    
    # ============================================================
    # Final Overall Summary
    # ============================================================
    overall_elapsed = time.time() - overall_start
    print(f"\n{'='*70}")
    print(f"{'✅ UNIFIED PRECOMPUTATION COMPLETE!':^70}")
    print(f"{'='*70}")
    print(f"Total datasets: {len(datasets)}")
    print(f"  ✓ Successfully processed: {datasets_processed}")
    if datasets_failed:
        print(f"  ❌ Failed: {len(datasets_failed)}")
        for ds, error in datasets_failed[:5]:
            print(f"     - {ds}: {error[:60]}")
        if len(datasets_failed) > 5:
            print(f"     ... and {len(datasets_failed) - 5} more")
    print(f"\nTotal time: {str(timedelta(seconds=int(overall_elapsed)))}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
