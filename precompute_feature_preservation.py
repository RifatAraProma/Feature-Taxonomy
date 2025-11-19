"""
Precompute FEATURE PRESERVATION metrics for all algorithms.

This script computes visual feature preservation metrics by comparing
original and simplified time series across all precomputed algorithm outputs.

Features computed:
1. Level - Point values (L1 and L∞ distance)
2. Mean - Overall average (TODO)
3. Extrema - Local min/max retention (TODO)
4. Regimes - Plateau detection (TODO)
5. Spikes/Dips - Outlier detection (TODO)
6. Slope - First derivative (TODO)
7. Curvature - Second derivative (TODO)
8. Trend - Low-frequency component (TODO)
9. Regression - Linear fit (TODO)
10. Periodicity - Dominant frequency (TODO)
11. Roughness - High-frequency variation (TODO)
12. Noise - High-frequency residual (TODO)

Usage:
    python precompute_feature_preservation.py [dataset_name] [algorithm_name] [--features feature1,feature2,...]
    
    If no arguments provided, processes stock_aapl_price with all algorithms and all features
    
Valid feature names for --features flag:
    level, mean, extrema_retention, regimes, change_points, spike_retention,
    slope_correlation, curvature_correlation, trend_correlation, noise_ratio,
    regression_error, periodicity_preservation, roughness_ratio
    
Examples:
    # Process all features for all algorithms (default dataset)
    python precompute_feature_preservation.py
    
    # Process all features for specific algorithm
    python precompute_feature_preservation.py stock_aapl_price gaussian_filter
    
    # Process specific features for specific algorithm
    python precompute_feature_preservation.py stock_aapl_price gaussian_filter --features level,mean
    
    # Process specific features for all algorithms
    python precompute_feature_preservation.py stock_aapl_price --features level,mean,extrema_retention
"""

import json
import os
import sys
import numpy as np
from pathlib import Path
from server.features.compute_features import (
    compute_all_features,
    compute_feature_preservation_metrics,
    FeatureConfig
)


# Configuration
DEFAULT_DATASET = "stock_aapl_price"
NUM_LEVELS = 101  # 0-100

# Valid feature names that can be specified with --features
VALID_FEATURES = [
    'level',
    'mean', 
    'extrema_retention',
    'regimes',
    'change_points',
    'spike_retention',
    'slope_correlation',
    'curvature_correlation',
    'trend_correlation',
    'noise_ratio',
    'regression_error',
    'periodicity_preservation',
    'roughness_ratio'
]


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


def filter_preservation_metrics(all_metrics, feature_list):
    """
    Filter preservation metrics to only include specified features.
    
    Args:
        all_metrics: Complete dictionary of preservation metrics
        feature_list: List of feature names to keep (None = keep all)
        
    Returns:
        Filtered metrics dictionary
    """
    if feature_list is None:
        return all_metrics
    
    filtered = {}
    for feature_name in feature_list:
        if feature_name in all_metrics:
            filtered[feature_name] = all_metrics[feature_name]
    
    return filtered


def compute_features_for_algorithm(algo_name, dataset_name=DEFAULT_DATASET, feature_list=None):
    """
    Compute features and preservation metrics for all levels of an algorithm.
    
    Args:
        algo_name: Algorithm name (e.g., 'm4_downsample')
        dataset_name: Dataset name (e.g., 'stock_aapl_price')
        feature_list: Optional list of feature names to compute. If None, computes all features.
                     Valid values: 'level', 'mean', 'extrema_retention', 'regime_retention', 
                                  'spike_retention', 'slope_correlation', 'curvature_correlation',
                                  'trend_correlation', 'regression_error', 'periodicity_preservation',
                                  'roughness_ratio', 'noise_ratio'
    """
    precomputed_dir = f"precomputed/{dataset_name}"
    
    if not os.path.exists(precomputed_dir):
        print(f"❌ Precomputed directory not found: {precomputed_dir}")
        print(f"   Run precompute_100_levels.py first!")
        return False
    
    print(f"\n{'='*70}")
    print(f"Processing: {algo_name}")
    print(f"{'='*70}")
    
    # Load Level 0 (original data)
    level_0_file = f"{precomputed_dir}/{algo_name}_level_0.json"
    if not os.path.exists(level_0_file):
        print(f"⚠️  Level 0 file not found: {level_0_file}")
        print(f"   Skipping {algo_name}")
        return False
    
    with open(level_0_file, 'r') as f:
        level_0_data = json.load(f)
    
    # Extract original y-values
    y_original = extract_y_values(level_0_data['output'])
    
    # Compute original features (all 12 features)
    cfg = FeatureConfig()
    original_features = compute_all_features(y_original, cfg)
    
    print(f"Original data: {len(y_original)} points")
    if feature_list:
        print(f"Computing specified features: {', '.join(feature_list)}")
    else:
        print(f"Computing all features for original series...")
    
    # Update Level 0 file with features and perfect preservation metrics
    level_0_data['features'] = original_features
    
    # For level 0 (no smoothing), feature preservation is perfect
    # Original == Simplified, so all errors are 0
    perfect_preservation = {
        'level': {'l1': 0.0, 'linf': 0.0},
        'mean': {'delta': 0.0},
        'extrema_retention': 0.0,
        'regimes': {'delta': 0.0},
        'change_points': {'delta': 0.0},
        'spike_retention': 0.0,
        'slope_correlation': 0.0,
        'curvature_correlation': 0.0,
        'trend_correlation': 0.0,
        'noise_ratio': 0.0,
        'regression_error': 0.0,
        'periodicity_preservation': 0.0,
        'roughness_ratio': 0.0
    }
    
    # Filter to only requested features if specified
    level_0_data['feature_preservation'] = filter_preservation_metrics(
        perfect_preservation, 
        feature_list
    )
    
    with open(level_0_file, 'w') as f:
        json.dump(level_0_data, f, indent=2)
    print(f"✓ Updated level 0 with features and perfect preservation metrics")
    
    # Process levels 1-100
    successful = 0
    failed = 0
    
    for level_idx in range(1, NUM_LEVELS):
        level_file = f"{precomputed_dir}/{algo_name}_level_{level_idx}.json"
        
        if not os.path.exists(level_file):
            # Skip missing levels (happens with commented-out algorithms)
            continue
        
        try:
            # Load simplified data
            with open(level_file, 'r') as f:
                level_data = json.load(f)
            
            # Extract simplified y-values
            y_simplified = extract_y_values(level_data['output'])
            
            # Compute simplified features (all 12 features)
            simplified_features = compute_all_features(y_simplified, cfg)
            
            # Compute preservation metrics (compares all features)
            all_preservation_metrics = compute_feature_preservation_metrics(
                original_features,
                simplified_features
            )
            
            # Filter to only requested features if specified
            preservation_metrics = filter_preservation_metrics(
                all_preservation_metrics,
                feature_list
            )
            
            # Update level data
            level_data['features'] = simplified_features
            level_data['feature_preservation'] = preservation_metrics
            
            # Save updated file
            with open(level_file, 'w') as f:
                json.dump(level_data, f, indent=2)
            
            successful += 1
            
            # Progress indicator
            if level_idx % 20 == 0:
                print(f"  Processed {level_idx}/{NUM_LEVELS-1} levels...")
            
        except Exception as e:
            print(f"  ❌ Error processing level {level_idx}: {e}")
            failed += 1
            continue
    
    print(f"\n{'Results':^70}")
    print(f"{'-'*70}")
    print(f"  ✓ Successfully processed: {successful} levels")
    if failed > 0:
        print(f"  ❌ Failed: {failed} levels")
    print(f"{'-'*70}")
    
    return True


def show_sample_metrics(algo_name, dataset_name=DEFAULT_DATASET, levels=[1, 50, 100]):
    """
    Display sample feature preservation metrics for verification.
    
    Args:
        algo_name: Algorithm name
        dataset_name: Dataset name
        levels: List of level indices to show
    """
    precomputed_dir = f"precomputed/{dataset_name}"
    
    print(f"\n{'='*70}")
    print(f"Sample Feature Preservation Metrics: {algo_name}")
    print(f"{'='*70}")
    
    for level_idx in levels:
        level_file = f"{precomputed_dir}/{algo_name}_level_{level_idx}.json"
        
        if not os.path.exists(level_file):
            continue
        
        with open(level_file, 'r') as f:
            data = json.load(f)
        
        metrics = data.get('feature_preservation', {})
        level_metrics = metrics.get('level', {})
        
        param_name = data.get('parameter_name', 'param')
        param_value = data.get('parameter_value', 'N/A')
        pae = data.get('pae', 0.0)
        
        print(f"\nLevel {level_idx}:")
        print(f"  {param_name} = {param_value}")
        print(f"  PAE = {pae:.4f}")
        print(f"  LEVEL:")
        print(f"    • L1 (avg error) = {level_metrics.get('l1', 0.0):.4f}")
        print(f"    • L∞ (max error) = {level_metrics.get('linf', 0.0):.4f}")
        
        # Show mean preservation if available
        mean_metrics = metrics.get('mean', {})
        if isinstance(mean_metrics, dict) and mean_metrics.get('delta', 0) != 0:
            print(f"  MEAN:")
            print(f"    • Delta = {mean_metrics.get('delta', 0.0):.4f}")


def calculate_and_save_scales(dataset_name, precomputed_dir):
    """
    Calculate global scales for feature preservation metrics.
    
    Reads all precomputed JSON files, collects all metric values,
    and computes percentile-based thresholds for color coding.
    
    Args:
        dataset_name: Name of the dataset
        precomputed_dir: Directory containing precomputed files
    """
    # Collect all feature preservation values
    feature_values = {}
    processed_files = 0
    
    for filename in os.listdir(precomputed_dir):
        if not filename.endswith('.json') or filename.startswith('_'):
            continue
        
        filepath = os.path.join(precomputed_dir, filename)
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
    
    print(f"{'Metric':<30} {'Type':<12} {'Samples':<10}")
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
    scales_file = os.path.join(precomputed_dir, '_feature_scales.json')
    scales_data = {
        'dataset': dataset_name,
        'total_samples': sum(len(v) for v in feature_values.values()),
        'num_files': processed_files,
        'scales': feature_scales
    }
    
    with open(scales_file, 'w') as f:
        json.dump(scales_data, f, indent=2)
    
    print(f"\n✓ Saved feature scales to {scales_file}")
    print(f"✓ Computed scales for {len(feature_scales)} metrics")
    print(f"✓ Based on {scales_data['total_samples']} total samples")


def main():
    """
    Main execution.
    
    Usage:
        python precompute_feature_preservation.py [dataset] [algorithm] [--features feature1,feature2,...]
        
    Examples:
        # Compute all features for all algorithms in stock_aapl_price
        python precompute_feature_preservation.py stock_aapl_price
        
        # Compute all features for gaussian_filter only
        python precompute_feature_preservation.py stock_aapl_price gaussian_filter
        
        # Compute only level and mean preservation for gaussian_filter
        python precompute_feature_preservation.py stock_aapl_price gaussian_filter --features level,mean
        
        # Compute specific features for all algorithms
        python precompute_feature_preservation.py stock_aapl_price --features level,mean,extrema_retention
    """
    # Parse command-line arguments
    dataset_name = DEFAULT_DATASET
    algo_name = None
    feature_list = None
    
    # Simple argument parsing
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == '--features':
            # Next argument should be comma-separated feature list
            if i + 1 < len(sys.argv):
                feature_str = sys.argv[i + 1]
                feature_list = [f.strip() for f in feature_str.split(',')]
                
                # Backward compatibility: expand 'regime_retention' to both 'regimes' and 'change_points'
                expanded_list = []
                for feat in feature_list:
                    if feat == 'regime_retention':
                        expanded_list.extend(['regimes', 'change_points'])
                    else:
                        expanded_list.append(feat)
                feature_list = expanded_list
                
                # Validate feature names
                invalid_features = [f for f in feature_list if f not in VALID_FEATURES]
                if invalid_features:
                    print(f"❌ Error: Invalid feature name(s): {', '.join(invalid_features)}")
                    print(f"\nValid features: {', '.join(VALID_FEATURES)}")
                    print(f"Note: 'regime_retention' is now split into 'regimes' and 'change_points'")
                    return
                
                i += 2
            else:
                print("❌ Error: --features requires a comma-separated list of feature names")
                print(f"Valid features: {', '.join(VALID_FEATURES)}")
                return
        elif i == 1:
            # First positional arg is dataset
            dataset_name = arg
            i += 1
        elif i == 2 and not arg.startswith('--'):
            # Second positional arg is algorithm (if not a flag)
            algo_name = arg
            i += 1
        else:
            i += 1
    
    print(f"\n{'FEATURE PRESERVATION PRECOMPUTATION':^70}")
    print(f"{'='*70}")
    print(f"Dataset: {dataset_name}")
    if feature_list:
        print(f"Features: {', '.join(feature_list)}")
    else:
        print(f"Features: All")
    print(f"{'='*70}")
    
    # Find all algorithm files in precomputed directory
    precomputed_dir = f"precomputed/{dataset_name}"
    
    if not os.path.exists(precomputed_dir):
        print(f"\n❌ Error: Precomputed directory not found!")
        print(f"   Expected: {precomputed_dir}")
        print(f"\n   Please run: python precompute_100_levels.py")
        return
    
    # Get list of algorithms from level_0 files
    level_0_files = [f for f in os.listdir(precomputed_dir) if f.endswith('_level_0.json')]
    algorithms = [f.replace('_level_0.json', '') for f in level_0_files]
    
    if not algorithms:
        print(f"\n❌ No precomputed algorithms found in {precomputed_dir}")
        return
    
    print(f"\nFound {len(algorithms)} algorithm(s): {', '.join(algorithms)}")
    
    # Process specific algorithm or all
    if algo_name:
        if algo_name in algorithms:
            success = compute_features_for_algorithm(algo_name, dataset_name, feature_list)
            if success:
                show_sample_metrics(algo_name, dataset_name)
        else:
            print(f"\n❌ Algorithm '{algo_name}' not found!")
            print(f"   Available: {', '.join(algorithms)}")
    else:
        # Process all algorithms
        for algo in algorithms:
            success = compute_features_for_algorithm(algo, dataset_name, feature_list)
            if success:
                show_sample_metrics(algo, dataset_name, levels=[1, 50, 100])
    
    # Calculate and save feature scales
    print(f"\n{'='*70}")
    print(f"Calculating Feature Preservation Scales...")
    print(f"{'='*70}\n")
    
    calculate_and_save_scales(dataset_name, precomputed_dir)
    
    print(f"\n{'='*70}")
    print(f"{'✅ FEATURE PRESERVATION COMPUTATION COMPLETE!':^70}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
