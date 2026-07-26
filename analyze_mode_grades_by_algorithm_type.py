import pandas as pd

# Read the data
df = pd.read_csv('supplemental_material/csv_data/algorithm_metric_mode_grades.csv')

# Exclude change_points_delta and noise_auc_delta
excluded_metrics = ['change_points_delta', 'noise_auc_delta']
df_filtered = df[~df['metric'].isin(excluded_metrics)].copy()

# Define algorithm categories based on your taxonomy
transformers = ['gaussian_filter', 'mean_filter', 'median_filter', 'savitzky_golay_filter',
                'butterworth_filter', 'chebyshev_filter', 'elliptical_filter', 'fft_cutoff_filter',
                'min_filter', 'max_filter']

reducers = ['lttb_downsample', 'm4_downsample', 'minmaxlttb_downsample', 'uniform_subsample',
            'rdp_downsample', 'fpcs_downsample']

aggregators = ['asap_aggregator', 'bin_average_aggregator', 'tda_downsample']

print("=" * 80)
print("MODE GRADE DISTRIBUTION BY ALGORITHM TYPE (21 features)")
print("=" * 80)

def analyze_group(algorithms, group_name):
    print(f"\n{group_name.upper()}")
    print("-" * 80)
    
    group_data = df_filtered[df_filtered['algorithm'].isin(algorithms)]
    
    # Count mode grades (handle tied modes)
    mode_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    
    for _, row in group_data.iterrows():
        mode = row['mode']
        if ',' in mode:  # Tied modes
            # Count each tied mode
            modes = [m.strip() for m in mode.split(',')]
            for m in modes:
                mode_counts[m] += 1
        else:
            mode_counts[mode] += 1
    
    total = sum(mode_counts.values())
    
    print(f"Total algorithm-metric pairs: {len(group_data)} ({len(algorithms)} algorithms × 21 metrics)")
    print(f"\nMode grade distribution:")
    for grade in ['A', 'B', 'C', 'D', 'F']:
        count = mode_counts[grade]
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {grade}: {count:3d} ({pct:5.1f}%)")
    
    print(f"\nPer-algorithm breakdown:")
    for algo in sorted(algorithms):
        algo_data = df_filtered[df_filtered['algorithm'] == algo]
        algo_modes = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        
        for _, row in algo_data.iterrows():
            mode = row['mode']
            if ',' in mode:
                modes = [m.strip() for m in mode.split(',')]
                for m in modes:
                    algo_modes[m] += 1
            else:
                algo_modes[mode] += 1
        
        total_algo = sum(algo_modes.values())
        mode_str = ', '.join([f"{g}:{algo_modes[g]}" for g in ['A', 'B', 'C', 'D', 'F'] if algo_modes[g] > 0])
        print(f"  {algo:30s}: {mode_str}")

analyze_group(transformers, "Transformers")
analyze_group(reducers, "Reducers")
analyze_group(aggregators, "Aggregators")

print("\n" + "=" * 80)
print("COMPARISON: Do transformers really receive higher grades?")
print("=" * 80)

# Calculate average grade (A=4, B=3, C=2, D=1, F=0)
grade_values = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}

def calculate_avg_grade(algorithms):
    group_data = df_filtered[df_filtered['algorithm'].isin(algorithms)]
    total_score = 0
    count = 0
    
    for _, row in group_data.iterrows():
        mode = row['mode']
        if ',' in mode:
            # For tied modes, take average
            modes = [m.strip() for m in mode.split(',')]
            score = sum(grade_values[m] for m in modes) / len(modes)
        else:
            score = grade_values[mode]
        total_score += score
        count += 1
    
    return total_score / count if count > 0 else 0

trans_avg = calculate_avg_grade(transformers)
red_avg = calculate_avg_grade(reducers)
agg_avg = calculate_avg_grade(aggregators)

print(f"\nAverage mode grade (A=4, B=3, C=2, D=1, F=0):")
print(f"  Transformers: {trans_avg:.2f}")
print(f"  Reducers:     {red_avg:.2f}")
print(f"  Aggregators:  {agg_avg:.2f}")

print("\n" + "=" * 80)
print("KEY ALGORITHMS MENTIONED IN ORIGINAL DISCUSSION")
print("=" * 80)

key_algos = {
    'gaussian_filter': 'Gaussian (transformer)',
    'mean_filter': 'Mean (transformer)',
    'savitzky_golay_filter': 'Savitzky-Golay (transformer)',
    'rdp_downsample': 'RDP (reducer)',
    'lttb_downsample': 'LTTB (reducer)',
    'asap_aggregator': 'ASAP (aggregator)',
    'bin_average_aggregator': 'PAA (aggregator)',
    'chebyshev_filter': 'Chebyshev (transformer)',
    'elliptical_filter': 'Elliptical (transformer)',
    'min_filter': 'Min (transformer)',
    'max_filter': 'Max (transformer)',
    'fpcs_downsample': 'FPCS (reducer)'
}

for algo, name in key_algos.items():
    algo_data = df_filtered[df_filtered['algorithm'] == algo]
    algo_modes = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
    
    for _, row in algo_data.iterrows():
        mode = row['mode']
        if ',' in mode:
            modes = [m.strip() for m in mode.split(',')]
            for m in modes:
                algo_modes[m] += 1
        else:
            algo_modes[mode] += 1
    
    mode_str = ', '.join([f"{g}:{algo_modes[g]}" for g in ['A', 'B', 'C', 'D', 'F'] if algo_modes[g] > 0])
    avg_grade = sum(algo_modes[g] * grade_values[g] for g in algo_modes) / sum(algo_modes.values())
    
    # Get deviation stats
    algo_dev = df_filtered[df_filtered['algorithm'] == algo]
    low = len(algo_dev[algo_dev['deviation'] < 25])
    medium = len(algo_dev[(algo_dev['deviation'] >= 25) & (algo_dev['deviation'] < 50)])
    high = len(algo_dev[algo_dev['deviation'] >= 50])
    
    print(f"\n{name:30s}")
    print(f"  Mode grades: {mode_str}")
    print(f"  Avg grade:   {avg_grade:.2f}")
    print(f"  Deviation:   {low} low, {medium} med, {high} high")
