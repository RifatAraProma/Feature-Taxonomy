import pandas as pd
import numpy as np

# Load the CSV
df = pd.read_csv('supplemental_material/csv_data/algorithm_metric_mode_grades.csv')

# Calculate average deviation per algorithm
algo_avg_deviation = df.groupby('algorithm')['deviation'].mean().sort_values()

print("="*80)
print("AVERAGE DEVIATION BY ALGORITHM (sorted from most to least consistent)")
print("="*80)
for algo, dev in algo_avg_deviation.items():
    if dev < 25:
        category = "CONSISTENT"
    elif dev < 50:
        category = "MODERATE"
    else:
        category = "HIGH DATA-DEPENDENT"
    print(f"{algo:30s}: {dev:5.2f}% ({category})")

print("\n" + "="*80)
print("ALGORITHMS BY CONSISTENCY CATEGORY")
print("="*80)

consistent = algo_avg_deviation[algo_avg_deviation < 25]
moderate = algo_avg_deviation[(algo_avg_deviation >= 25) & (algo_avg_deviation < 50)]
high_dep = algo_avg_deviation[algo_avg_deviation >= 50]

print(f"\nCONSISTENT (< 25% avg deviation): {len(consistent)} algorithms")
for algo in consistent.index:
    print(f"  - {algo}")

print(f"\nMODERATELY DATA-DEPENDENT (25-50% avg deviation): {len(moderate)} algorithms")
for algo in moderate.index:
    print(f"  - {algo}")

print(f"\nHIGHLY DATA-DEPENDENT (> 50% avg deviation): {len(high_dep)} algorithms")
for algo in high_dep.index:
    print(f"  - {algo}")

# Find specific examples mentioned in the text
print("\n" + "="*80)
print("VERIFYING SPECIFIC CLAIMS IN THE TEXT")
print("="*80)

# Check Douglas-Peucker (RDP) consistency
rdp_data = df[df['algorithm'] == 'rdp_downsample']
rdp_zero_dev = rdp_data[rdp_data['deviation'] == 0]
print(f"\nDouglas-Peucker (RDP):")
print(f"  Average deviation: {rdp_data['deviation'].mean():.2f}%")
print(f"  Metrics with 0% deviation: {len(rdp_zero_dev)}")
if len(rdp_zero_dev) > 0:
    print(f"  Those metrics: {', '.join(rdp_zero_dev['metric'].tolist())}")
print(f"  Lowest deviation: {rdp_data['deviation'].min():.2f}% on {rdp_data.loc[rdp_data['deviation'].idxmin(), 'metric']}")

# Check Gaussian filter
gaussian_data = df[df['algorithm'] == 'gaussian_filter']
gaussian_zero_dev = gaussian_data[gaussian_data['deviation'] == 0]
print(f"\nGaussian Filter:")
print(f"  Average deviation: {gaussian_data['deviation'].mean():.2f}%")
print(f"  Metrics with 0% deviation: {len(gaussian_zero_dev)}")
if len(gaussian_zero_dev) > 0:
    print(f"  Those metrics: {', '.join(gaussian_zero_dev['metric'].tolist())}")

# Check Min/Max/Median filters for high deviation
print(f"\nMin Filter (extreme value):")
min_data = df[df['algorithm'] == 'min_filter']
print(f"  Average deviation: {min_data['deviation'].mean():.2f}%")
print(f"  Max deviation: {min_data['deviation'].max():.2f}% on {min_data.loc[min_data['deviation'].idxmax(), 'metric']}")

print(f"\nMax Filter (extreme value):")
max_data = df[df['algorithm'] == 'max_filter']
print(f"  Average deviation: {max_data['deviation'].mean():.2f}%")
print(f"  Max deviation: {max_data['deviation'].max():.2f}% on {max_data.loc[max_data['deviation'].idxmax(), 'metric']}")

print(f"\nMedian Filter:")
median_data = df[df['algorithm'] == 'median_filter']
print(f"  Average deviation: {median_data['deviation'].mean():.2f}%")
print(f"  Max deviation: {median_data['deviation'].max():.2f}% on {median_data.loc[median_data['deviation'].idxmax(), 'metric']}")

# Check FPCS
print(f"\nFPCS (mentioned as highly data-dependent):")
fpcs_data = df[df['algorithm'] == 'fpcs_downsample']
print(f"  Average deviation: {fpcs_data['deviation'].mean():.2f}%")
print(f"  Metrics with >50% deviation: {len(fpcs_data[fpcs_data['deviation'] > 50])}")

# Find overall min and max deviations
print("\n" + "="*80)
print("OVERALL DEVIATION STATISTICS")
print("="*80)
print(f"Minimum deviation across all: {df['deviation'].min():.2f}%")
min_row = df.loc[df['deviation'].idxmin()]
print(f"  Algorithm: {min_row['algorithm']}, Metric: {min_row['metric']}")

print(f"\nMaximum deviation across all: {df['deviation'].max():.2f}%")
max_row = df.loc[df['deviation'].idxmax()]
print(f"  Algorithm: {max_row['algorithm']}, Metric: {max_row['metric']}")

# Count how many algorithm-metric pairs fall in each category
total_pairs = len(df)
consistent_pairs = len(df[df['deviation'] < 25])
moderate_pairs = len(df[(df['deviation'] >= 25) & (df['deviation'] < 50)])
high_pairs = len(df[df['deviation'] > 50])

print(f"\nDistribution of {total_pairs} algorithm-metric pairs:")
print(f"  Consistent (< 25%): {consistent_pairs} ({consistent_pairs/total_pairs*100:.1f}%)")
print(f"  Moderate (25-50%): {moderate_pairs} ({moderate_pairs/total_pairs*100:.1f}%)")
print(f"  High (> 50%): {high_pairs} ({high_pairs/total_pairs*100:.1f}%)")

# Check specific examples for extrema metrics
print("\n" + "="*80)
print("EXTREMA METRIC DEVIATIONS (mentioned in text)")
print("="*80)
for algo in ['min_filter', 'max_filter', 'median_filter']:
    algo_df = df[df['algorithm'] == algo]
    extrema_w1 = algo_df[algo_df['metric'] == 'extrema_wasserstein']
    extrema_winf = algo_df[algo_df['metric'] == 'extrema_bottleneck']
    if not extrema_w1.empty:
        print(f"{algo} extrema_wasserstein (W1): {extrema_w1['deviation'].values[0]:.2f}%")
    if not extrema_winf.empty:
        print(f"{algo} extrema_bottleneck (W∞): {extrema_winf['deviation'].values[0]:.2f}%")
