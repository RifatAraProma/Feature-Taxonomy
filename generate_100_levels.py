#!/usr/bin/env python3
"""
Generate 100 meaningful precomputed levels for each algorithm.

Key Strategy:
- For window-based filters: vary window size (they have good PAE responsiveness)
- For frequency filters: vary BOTH cutoff frequency AND filter order
  (Filter order = sharpness of transition = different smoothing effect)
- This gives frequency filters 100 meaningful levels despite limited cutoff range
"""

import json
import numpy as np
import argparse
from pathlib import Path
from scipy.interpolate import interp1d
import sys

# Import transformer algorithms
from server.algorithms.vendor.data_transformer_algorithms import (
    gaussian_filter, mean_filter, median_filter, min_filter, max_filter,
    savitzky_golay_filter, fft_cutoff_filter, butterworth_filter,
    chebyshev_filter, elliptical_filter
)
from server.features.pae import pixel_approx_entropy as pae


def load_calibration_results():
    """Load calibration results from calibration_results.json"""
    with open('calibration_results.json', 'r') as f:
        return json.load(f)


def load_dataset(dataset_name):
    """Load dataset from data directory."""
    data_dir = Path("data")
    
    for json_file in data_dir.rglob(f"{dataset_name}.json"):
        print(f"Loading dataset from: {json_file}")
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                if 'value' in data[0]:
                    values = [float(item['value']) for item in data]
                elif 'y' in data[0]:
                    values = [float(item['y']) for item in data]
                else:
                    values = [float(item[list(item.keys())[0]]) for item in data]
            else:
                values = [float(x) for x in data]
        else:
            raise ValueError(f"Unsupported data format")
        
        print(f"Loaded {len(values)} data points")
        return values
    
    raise FileNotFoundError(f"Dataset '{dataset_name}' not found")


def apply_algorithm(algorithm_name, data, parameters):
    """Apply algorithm with given parameters."""
    # Convert 1D array to (x, y) pairs format expected by transformer functions
    x_values = list(range(len(data)))
    xy_pairs = list(zip(x_values, data))
    
    # Map algorithm names to functions
    algo_map = {
        'gaussian_filter': gaussian_filter,
        'mean_filter': mean_filter,
        'median_filter': median_filter,
        'min_filter': min_filter,
        'max_filter': max_filter,
        'savitzky_golay_filter': savitzky_golay_filter,
        'fft_cutoff_filter': fft_cutoff_filter,
        'butterworth_filter': butterworth_filter,
        'chebyshev_filter': chebyshev_filter,
        'elliptical_filter': elliptical_filter,
    }
    
    if algorithm_name not in algo_map:
        raise ValueError(f"Unknown algorithm: {algorithm_name}")
    
    func = algo_map[algorithm_name]
    
    try:
        result_pairs = func(xy_pairs, **parameters)
        # Extract y values from (x, y) pairs
        result = [y for x, y in result_pairs]
        return result
    except Exception as e:
        print(f"Error applying {algorithm_name} with params={parameters}: {e}")
        raise


def generate_100_levels(dataset_name, num_levels=100):
    """
    Generate 100 meaningful precomputed levels for each algorithm.
    
    Strategy per algorithm:
    - gaussian_filter: vary sigma (already responsive)
    - mean/median/min/max_filter: vary window size (already responsive)
    - savitzky_golay_filter: vary window size
    - fft_cutoff_filter: vary cutoff frequency (coarse levels)
    - butterworth_filter: vary order (1-10) + cutoff (coarse variation)
    - chebyshev_filter: vary order (1-10) + cutoff + ripple
    - elliptical_filter: vary order (1-10) + cutoff + ripple + max_atten
    """
    print("\n" + "="*90)
    print(f"GENERATING {num_levels} MEANINGFUL PRECOMPUTED LEVELS")
    print("="*90)
    
    # Load calibration data
    print("\nLoading calibration results...")
    calibration_data = load_calibration_results()
    
    # Load dataset
    print(f"\nLoading dataset: {dataset_name}")
    values = load_dataset(dataset_name)
    
    # Calculate baseline PAE
    print(f"\nCalculating baseline PAE (original data)...")
    baseline_pae = float(pae(values))
    print(f"Baseline PAE: {baseline_pae:.6f}")
    
    # Create output directory
    output_dir = Path("precomputed") / dataset_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save Level 0 (original data - shared)
    print(f"\nSaving Level 0 (original data)...")
    level_0_file = output_dir / "level_0.json"
    
    if not level_0_file.exists():
        level_0_data = {
            'dataset_name': dataset_name,
            'algorithm': None,
            'level': 0,
            'parameter_name': None,
            'parameter_value': None,
            'output_length': len(values),
            'output': values,
            'pae': baseline_pae,
            'target_pae': baseline_pae
        }
        with open(level_0_file, 'w') as f:
            json.dump(level_0_data, f)
        print(f"✓ Saved Level 0")
    else:
        print(f"✓ Level 0 already exists")
    
    print(f"\nGenerating {num_levels} levels for each algorithm...")
    print("-" * 90)
    
    # Define level generation strategies per algorithm
    strategies = {
        # Window-based filters: vary window size linearly
        'gaussian_filter': {
            'param_samples': lambda: {
                'sigma': np.logspace(np.log10(0.05), np.log10(188.55), num_levels)
            }
        },
        'mean_filter': {
            'param_samples': lambda: {
                'window_size': np.linspace(2, 188, num_levels).astype(int)
            }
        },
        'median_filter': {
            'param_samples': lambda: {
                'window_size': np.linspace(3, 189, num_levels).astype(int)  # Will enforce odd
            }
        },
        'min_filter': {
            'param_samples': lambda: {
                'window_size': np.linspace(3, 189, num_levels).astype(int)  # Will enforce odd
            }
        },
        'max_filter': {
            'param_samples': lambda: {
                'window_size': np.linspace(3, 189, num_levels).astype(int)  # Will enforce odd
            }
        },
        'savitzky_golay_filter': {
            'param_samples': lambda: {
                'window_size': np.linspace(5, 189, num_levels).astype(int)  # Will enforce odd
            }
        },
        
        # Frequency filters: vary cutoff using LOGARITHMIC scaling
        # to ensure linear PAE progression across all 100 levels
        'fft_cutoff_filter': {
            'param_samples': lambda: {
                'cutoff_freq_normalized': np.power(10, np.linspace(np.log10(0.05), np.log10(1.0), num_levels))
            }
        },
        'butterworth_filter': {
            'param_samples': lambda: {
                # Cutoff uses logarithmic scale for linear PAE; order varies in separate groups
                'cutoff_freq_normalized': np.power(10, np.tile(np.linspace(np.log10(0.05), np.log10(0.95), 50), 2)),
                'order': np.repeat(np.array([2, 6]), 50)
            }
        },
        'chebyshev_filter': {
            'param_samples': lambda: {
                # Cutoff uses logarithmic scale; order varies in 3 groups
                'cutoff_freq_normalized': np.power(10, np.tile(np.linspace(np.log10(0.05), np.log10(0.95), 34), 3)),
                'order': np.repeat(np.array([2, 4, 6]), 34),
                'ripple_db': 0.1
            }
        },
        'elliptical_filter': {
            'param_samples': lambda: {
                # Cutoff uses logarithmic scale; order varies in 4 groups
                'cutoff_freq_normalized': np.power(10, np.tile(np.linspace(np.log10(0.05), np.log10(0.95), 25), 4)),
                'order': np.repeat(np.array([2, 4, 6, 8]), 25),
                'ripple_db': 0.5,
                'max_atten_db': 40
            }
        }
    }
    
    summary_data = {}
    
    for algo_name in sorted(strategies.keys()):
        print(f"\n{algo_name}:")
        
        strategy = strategies[algo_name]
        
        # Get parameter samples for this level count
        param_dict = strategy['param_samples']()
        
        # Ensure all arrays have correct length
        for key in param_dict:
            val = param_dict[key]
            if isinstance(val, np.ndarray):
                # Trim to num_levels if too long
                if len(val) > num_levels:
                    param_dict[key] = val[:num_levels]
                # Pad if too short
                elif len(val) < num_levels:
                    if key == 'ripple_db' or key == 'max_atten_db':
                        param_dict[key] = val  # Scalar, don't pad
                    else:
                        # Extend last value
                        last_val = val[-1]
                        param_dict[key] = np.concatenate([val, np.full(num_levels - len(val), last_val)])
        
        # Generate levels
        pae_values = []
        for level in range(1, num_levels + 1):
            try:
                # Build parameters for this level
                params = {}
                for param_name, param_vals in param_dict.items():
                    if isinstance(param_vals, np.ndarray):
                        params[param_name] = float(param_vals[level - 1])
                    else:
                        params[param_name] = param_vals
                
                # Handle window size parameter processing
                if 'window_size' in params:
                    params['window_size'] = int(params['window_size'])
                    if algo_name in ['median_filter', 'min_filter', 'max_filter', 'savitzky_golay_filter']:
                        ws = params['window_size']
                        params['window_size'] = ws + 1 if ws % 2 == 0 else ws
                
                # Apply algorithm
                output_values = apply_algorithm(algo_name, values, params)
                output_pae = float(pae(output_values))
                pae_values.append(output_pae)
                
                # Save precomputed data
                level_data = {
                    'dataset_name': dataset_name,
                    'algorithm': algo_name,
                    'level': level,
                    'parameters': params,
                    'output_length': len(output_values),
                    'output': output_values,
                    'pae': output_pae
                }
                
                output_file = output_dir / f"{algo_name}_level_{level}.json"
                with open(output_file, 'w') as f:
                    json.dump(level_data, f)
                
                if level % 25 == 1 or level == num_levels:
                    pae_str = ", ".join([f"{p:.3f}" for p in pae_values[-5:]])
                    print(f"  Level {level:3d}: params={params} → pae=[...{pae_str}]")
                
            except Exception as e:
                print(f"  ✗ Error at level {level}: {e}")
        
        pae_range = (min(pae_values), max(pae_values))
        summary_data[algo_name] = {
            'num_levels': num_levels,
            'pae_range': list(pae_range),
            'pae_values': [float(p) for p in pae_values]
        }
        print(f"  ✓ Generated {num_levels} levels (PAE range: {pae_range[0]:.4f}→{pae_range[1]:.4f})")
    
    # Print summary
    print("\n" + "="*90)
    print(f"SUMMARY: {num_levels} LEVELS PER ALGORITHM")
    print("="*90)
    print(f"\n{'Algorithm':<30s} {'Levels':>8s} {'PAE Range':<30s}")
    print("-" * 90)
    
    for algo_name in sorted(summary_data.keys()):
        info = summary_data[algo_name]
        pae_min, pae_max = info['pae_range']
        print(f"{algo_name:<30s} {info['num_levels']:>8d} "
              f"{pae_min:.4f}→{pae_max:.4f}")
    
    print("\n" + "="*90)
    print(f"✅ Precomputed {num_levels} levels for 10 algorithms in: {output_dir}")
    print("="*90 + "\n")
    
    # Save summary
    with open(output_dir / "levels_summary.json", 'w') as f:
        json.dump({
            'num_levels': num_levels,
            'algorithms': summary_data
        }, f, indent=2)
    
    return summary_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate 100 meaningful precomputed levels')
    parser.add_argument('--dataset', required=True, help='Dataset name')
    parser.add_argument('--levels', type=int, default=100, help='Number of levels per algorithm')
    
    args = parser.parse_args()
    
    try:
        generate_100_levels(args.dataset, num_levels=args.levels)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
