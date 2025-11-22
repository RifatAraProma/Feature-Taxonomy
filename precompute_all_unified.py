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

# Import ONLY configuration from precompute_100_levels.py to ensure consistency
# The parameter generation logic is copied here to follow the exact same implementation
from precompute_100_levels import ALGORITHMS_CONFIG, NUM_LEVELS


# =======================================================================================
# CONFIGURATION - Imported from precompute_100_levels.py
# =======================================================================================

# NUM_LEVELS and ALGORITHMS_CONFIG are imported directly from precompute_100_levels.py
# This ensures both scripts use EXACTLY the same algorithm configuration
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

# NOTE: ALGORITHMS_CONFIG and NUM_LEVELS are now imported from precompute_100_levels.py
# This eliminates duplication and ensures both scripts use EXACTLY the same configuration


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


def generate_parameter_values(algo_name: str, data_length: int, config: Dict) -> List:
    """
    Generate 100 parameter values using log-scale sampling (levels 1-100).
    
    FOLLOWS EXACT SAME LOGIC AS precompute_100_levels.py generate_levels() function.
    """
    param_name = config['param_name']
    param_bounds = config.get('param_bounds')
    
    # Check if we need to set dynamic bounds
    # param_bounds could be None, or a tuple with None as max (e.g., (10, None))
    if param_bounds is None or (isinstance(param_bounds, tuple) and param_bounds[1] is None):
        # Dynamic bounds based on algorithm
        if param_bounds is not None and isinstance(param_bounds, tuple):
            # Use the specified min from config
            param_min = param_bounds[0]
        else:
            param_min = None  # Will be set below
            
        if algo_name == 'gaussian_filter':
            param_min = 1.0
            param_max = data_length / 10.0
        elif algo_name == 'fft_cutoff_filter':
            param_min = 2
            param_max = data_length
        elif algo_name in ['mean_filter', 'median_filter', 'min_filter', 'max_filter']:
            # Window-based filters: window_size from 2 to data_length/4
            param_min = 2
            param_max = max(5, data_length // 4)
        elif algo_name == 'savitzky_golay_filter':
            # Savitzky-Golay: window_size must be odd and > polyorder
            # Start from 3 (minimum for polyorder=2) to data_length/4
            param_min = 3
            param_max = max(7, data_length // 4)
        elif algo_name in ['lttb_downsample', 'minmaxlttb_downsample', 'uniform_subsample', 'rdp_downsample']:
            # Fixed-count downsamplers: output_length from 3 to data_length - 1
            param_min = 3
            param_max = data_length - 1
        elif algo_name == 'fpcs_downsample':
            # FPCS: rate from 1 (most points) to a value that ensures complete coverage
            param_min = 1
            param_max = max(3, data_length // 3)  # Ensure at least 3 windows
        elif algo_name == 'm4_downsample':
            # M4: minimum 8, must be multiple of 4
            param_min = config.get('minimum_value', 8)
            param_max = data_length - 1
        elif algo_name == 'bin_average_aggregator':
            # Bin average: bins from 2 to data_length
            param_min = 2
            param_max = data_length
        elif algo_name == 'asap_aggregator':
            # ASAP: resolution from 10 to data_length // 2
            if param_min is None:
                param_min = 10  # Fallback if not set in config
            param_max = data_length // 2  # Max that triggers aggregation
    else:
        param_min, param_max = param_bounds
    
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
                param_val = int(param_val)  # EXACT SAME: use int() like precompute_100_levels.py
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
    
    # Special handling for m4_downsample: ensure output_length is multiple of 4
    if algo_name == 'm4_downsample':
        multiple_of = config.get('requires_multiple_of', 4)
        minimum_val = config.get('minimum_value', 8)
        # Ensure all values are multiples of 4 and >= minimum
        param_values_fixed = []
        for p in param_values:
            p_int = int(p)
            # Ensure >= minimum
            if p_int < minimum_val:
                p_int = minimum_val
            # Round to nearest multiple of 4
            p_int = (p_int // multiple_of) * multiple_of
            # Ensure still >= minimum after rounding
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
    # EXACT SAME LOGIC AS precompute_100_levels.py
    # ============================================================
    param_values = generate_parameter_values(algo_name, len(y_data), config)
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
