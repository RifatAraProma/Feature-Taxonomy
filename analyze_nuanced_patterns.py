import pandas as pd

df = pd.read_csv('supplemental_material/csv_data/algorithm_metric_mode_grades.csv')

print("="*80)
print("NUANCED PATTERNS: Feature-Specific Consistency")
print("="*80)

# Define feature categories
level_features = ['level_l1', 'level_linf', 'mean_delta']
shape_features = ['extrema_bottleneck', 'extrema_wasserstein', 'spikes_dips_bottleneck', 'spikes_dips_wasserstein']
structure_features = ['regimes_delta', 'change_points_delta']
derivative_features = ['slope_l1', 'slope_linf', 'curvature_l1', 'curvature_linf', 'roughness_delta']
frequency_features = ['trend_l1', 'trend_linf', 'noise_l1', 'noise_linf', 'periodicity_amplitude_delta', 'periodicity_num_periods_delta']

def analyze_algorithm(algo_name, display_name):
    algo_data = df[df['algorithm'] == algo_name].copy()
    
    print(f"\n{display_name}:")
    print(f"  Overall avg deviation: {algo_data['deviation'].mean():.1f}%")
    
    # Analyze by feature category
    categories = {
        'Level': level_features,
        'Shape': shape_features,
        'Structure': structure_features,
        'Derivative': derivative_features,
        'Frequency': frequency_features
    }
    
    for cat_name, features in categories.items():
        cat_data = algo_data[algo_data['metric'].isin(features)]
        if len(cat_data) > 0:
            avg_dev = cat_data['deviation'].mean()
            min_dev = cat_data['deviation'].min()
            max_dev = cat_data['deviation'].max()
            print(f"  {cat_name:12s}: avg={avg_dev:5.1f}% (range: {min_dev:5.1f}%-{max_dev:5.1f}%)")
            
            # Show extremes if there's large variation
            if max_dev - min_dev > 30:
                low_metrics = cat_data[cat_data['deviation'] < 20]['metric'].tolist()
                high_metrics = cat_data[cat_data['deviation'] > 50]['metric'].tolist()
                if low_metrics:
                    print(f"                 Low deviation: {', '.join([m.replace('_', ' ') for m in low_metrics])}")
                if high_metrics:
                    print(f"                 High deviation: {', '.join([m.replace('_', ' ') for m in high_metrics])}")

# Analyze key algorithms
analyze_algorithm('rdp_downsample', 'Douglas-Peucker (RDP)')
analyze_algorithm('gaussian_filter', 'Gaussian Filter')
analyze_algorithm('mean_filter', 'Mean Filter')
analyze_algorithm('savitzky_golay_filter', 'Savitzky-Golay')
analyze_algorithm('median_filter', 'Median Filter')
analyze_algorithm('min_filter', 'Min Filter')
analyze_algorithm('max_filter', 'Max Filter')
analyze_algorithm('lttb_downsample', 'LTTB')
analyze_algorithm('fpcs_downsample', 'FPCS')
analyze_algorithm('asap_aggregator', 'ASAP')
analyze_algorithm('butterworth_filter', 'Butterworth')
analyze_algorithm('chebyshev_filter', 'Chebyshev')

print("\n" + "="*80)
print("INTERESTING CONTRASTS")
print("="*80)

# Compare Gaussian vs Median on extrema
gauss_extrema = df[(df['algorithm'] == 'gaussian_filter') & (df['metric'].isin(['extrema_bottleneck', 'extrema_wasserstein']))]['deviation'].mean()
median_extrema = df[(df['algorithm'] == 'median_filter') & (df['metric'].isin(['extrema_bottleneck', 'extrema_wasserstein']))]['deviation'].mean()
print(f"\nExtrema preservation consistency:")
print(f"  Gaussian: {gauss_extrema:.1f}% avg deviation")
print(f"  Median:   {median_extrema:.1f}% avg deviation")

# Compare RDP on different feature types
rdp = df[df['algorithm'] == 'rdp_downsample']
rdp_level = rdp[rdp['metric'].isin(level_features)]['deviation'].mean()
rdp_shape = rdp[rdp['metric'].isin(shape_features)]['deviation'].mean()
print(f"\nRDP feature selectivity:")
print(f"  Level features: {rdp_level:.1f}% avg deviation")
print(f"  Shape features: {rdp_shape:.1f}% avg deviation")

# Min/Max filter on noise
min_noise = df[(df['algorithm'] == 'min_filter') & (df['metric'].isin(['noise_l1', 'noise_linf']))]['deviation'].mean()
max_noise = df[(df['algorithm'] == 'max_filter') & (df['metric'].isin(['noise_l1', 'noise_linf']))]['deviation'].mean()
gauss_noise = df[(df['algorithm'] == 'gaussian_filter') & (df['metric'].isin(['noise_l1', 'noise_linf']))]['deviation'].mean()
print(f"\nNoise reduction consistency:")
print(f"  Gaussian: {gauss_noise:.1f}% avg deviation")
print(f"  Min:      {min_noise:.1f}% avg deviation")
print(f"  Max:      {max_noise:.1f}% avg deviation")
