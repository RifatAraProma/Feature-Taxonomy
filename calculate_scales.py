"""
Calculate feature preservation scales from existing precomputed data.

This script reads all precomputed feature preservation metrics and calculates
globally-informed color scale thresholds based on percentiles across all
algorithms and levels.

Usage:
    python calculate_scales.py [dataset_name]
    
    If no dataset name provided, defaults to stock_aapl_price

Examples:
    python calculate_scales.py
    python calculate_scales.py stock_aapl_price
    python calculate_scales.py climate_atl_tmax
"""

import json
import os
import sys
import numpy as np


def calculate_scales(dataset_name):
    """
    Calculate global scales for feature preservation metrics.
    
    Reads all precomputed JSON files for the dataset, collects all metric values,
    and computes percentile-based thresholds for color coding.
    
    Args:
        dataset_name: Name of the dataset (e.g., 'stock_aapl_price')
        
    Returns:
        Dictionary with scale information
    """
    precomputed_dir = f"precomputed/{dataset_name}"
    
    if not os.path.exists(precomputed_dir):
        print(f"❌ Error: Precomputed directory not found!")
        print(f"   Expected: {precomputed_dir}")
        return None
    
    print(f"\n{'='*70}")
    print(f"Calculating Feature Preservation Scales")
    print(f"{'='*70}")
    print(f"Dataset: {dataset_name}")
    print(f"Directory: {precomputed_dir}")
    print(f"{'='*70}\n")
    
    # Collect all feature preservation values across all algorithms and levels
    feature_values = {}
    total_files = 0
    processed_files = 0
    
    # Iterate through all precomputed files
    for filename in os.listdir(precomputed_dir):
        if not filename.endswith('.json') or filename.startswith('_'):
            continue
        
        total_files += 1
        filepath = os.path.join(precomputed_dir, filename)
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Skip level 0 (original data - all metrics are 0)
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
    
    print(f"📁 Processed {processed_files}/{total_files} files")
    print(f"📊 Found {len(feature_values)} unique metrics\n")
    
    if not feature_values:
        print("❌ No feature preservation data found!")
        return None
    
    # Calculate percentile-based thresholds for each metric
    feature_scales = {}
    
    print(f"{'Metric':<30} {'Type':<12} {'Samples':<10} {'Range':<20}")
    print(f"{'-'*70}")
    
    for metric_name, values in sorted(feature_values.items()):
        if len(values) == 0:
            continue
        
        values_sorted = sorted(values)
        n = len(values_sorted)
        
        # Determine metric type based on name
        metric_type = 'error'  # Default
        lower_name = metric_name.lower()
        if 'retention' in lower_name or 'correlation' in lower_name or 'similarity' in lower_name:
            metric_type = 'correlation'
        elif 'ratio' in lower_name:
            metric_type = 'ratio'
        
        # Calculate percentile thresholds
        p25 = float(np.percentile(values_sorted, 25))
        p50 = float(np.percentile(values_sorted, 50))
        p75 = float(np.percentile(values_sorted, 75))
        min_val = float(values_sorted[0])
        max_val = float(values_sorted[-1])
        
        if metric_type == 'error':
            # For errors: lower is better
            feature_scales[metric_name] = {
                'type': 'error',
                'excellent': p25,  # Bottom 25%
                'good': p50,       # Bottom 50%
                'fair': p75,       # Bottom 75%
                'min': min_val,
                'max': max_val
            }
        elif metric_type == 'ratio':
            # For ratios: calculate deviation from 1.0
            deviations = sorted([abs(v - 1.0) for v in values])
            dev_25 = float(np.percentile(deviations, 25))
            dev_50 = float(np.percentile(deviations, 50))
            dev_75 = float(np.percentile(deviations, 75))
            feature_scales[metric_name] = {
                'type': 'ratio',
                'excellent': dev_25,
                'good': dev_50,
                'fair': dev_75,
                'min': min_val,
                'max': max_val
            }
        else:
            # For correlation/retention: higher is better
            feature_scales[metric_name] = {
                'type': 'correlation',
                'poor': p25,      # Bottom 25%
                'fair': p50,      # Median
                'good': p75,      # Top 25%
                'min': min_val,
                'max': max_val
            }
        
        # Print summary
        print(f"{metric_name:<30} {metric_type:<12} {len(values):<10} [{min_val:.4f}, {max_val:.4f}]")
    
    # Save scales to JSON file
    scales_file = os.path.join(precomputed_dir, '_feature_scales.json')
    scales_data = {
        'dataset': dataset_name,
        'total_samples': sum(len(v) for v in feature_values.values()),
        'num_files': processed_files,
        'scales': feature_scales
    }
    
    with open(scales_file, 'w') as f:
        json.dump(scales_data, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✅ Saved feature scales to: {scales_file}")
    print(f"✅ Computed scales for {len(feature_scales)} metrics")
    print(f"✅ Based on {scales_data['total_samples']} total samples")
    print(f"{'='*70}\n")
    
    return feature_scales


def main():
    """Main execution."""
    # Parse command-line arguments
    dataset_name = sys.argv[1] if len(sys.argv) > 1 else "stock_aapl_price"
    
    print(f"\n{'FEATURE PRESERVATION SCALE CALCULATOR':^70}")
    print(f"{'='*70}\n")
    
    scales = calculate_scales(dataset_name)
    
    if scales:
        print("Sample scale thresholds:")
        print(f"{'-'*70}")
        for metric_name in sorted(scales.keys())[:5]:  # Show first 5 metrics
            scale = scales[metric_name]
            print(f"\n{metric_name}:")
            print(f"  Type: {scale['type']}")
            if scale['type'] == 'error':
                print(f"  Excellent: ≤ {scale['excellent']:.4f}")
                print(f"  Good:      ≤ {scale['good']:.4f}")
                print(f"  Fair:      ≤ {scale['fair']:.4f}")
            elif scale['type'] == 'correlation':
                print(f"  Excellent: ≥ {scale['good']:.4f}")
                print(f"  Good:      ≥ {scale['fair']:.4f}")
                print(f"  Fair:      ≥ {scale['poor']:.4f}")
            else:  # ratio
                print(f"  Excellent: deviation ≤ {scale['excellent']:.4f}")
                print(f"  Good:      deviation ≤ {scale['good']:.4f}")
                print(f"  Fair:      deviation ≤ {scale['fair']:.4f}")
        
        if len(scales) > 5:
            print(f"\n... and {len(scales) - 5} more metrics")
        print(f"{'-'*70}\n")
        
        print("🎯 Next step: Update frontend to fetch and use these scales!")
    else:
        print("❌ Failed to calculate scales")
        sys.exit(1)


if __name__ == "__main__":
    main()
