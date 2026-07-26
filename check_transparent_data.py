import pandas as pd

df = pd.read_csv('supplemental_material/csv_data/algorithm_metric_mode_grades.csv')

print("="*80)
print("TRANSPARENT ANALYSIS: Checking specific claims")
print("="*80)

# Check Gaussian Filter
gauss = df[df['algorithm'] == 'gaussian_filter'][['metric', 'deviation']].sort_values('deviation', ascending=False)
print("\nGaussian Filter - All deviations (sorted worst to best):")
for _, row in gauss.iterrows():
    print(f"  {row['metric']:40s}: {row['deviation']:5.1f}%")

# Check Mean Filter
mean = df[df['algorithm'] == 'mean_filter'][['metric', 'deviation']].sort_values('deviation', ascending=False)
print("\nMean Filter - All deviations (sorted worst to best):")
for _, row in mean.iterrows():
    print(f"  {row['metric']:40s}: {row['deviation']:5.1f}%")

# Check Savitzky-Golay
sg = df[df['algorithm'] == 'savitzky_golay_filter'][['metric', 'deviation']].sort_values('deviation', ascending=False)
print("\nSavitzky-Golay Filter - All deviations (sorted worst to best):")
for _, row in sg.iterrows():
    print(f"  {row['metric']:40s}: {row['deviation']:5.1f}%")

# Check Median Filter
median = df[df['algorithm'] == 'median_filter'][['metric', 'deviation']].sort_values('deviation', ascending=False)
print("\nMedian Filter - All deviations (sorted worst to best):")
for _, row in median.iterrows():
    print(f"  {row['metric']:40s}: {row['deviation']:5.1f}%")

# Count metrics by deviation range for each
print("\n" + "="*80)
print("DISTRIBUTION OF DEVIATION RANGES")
print("="*80)

for algo in ['gaussian_filter', 'mean_filter', 'savitzky_golay_filter', 'median_filter']:
    algo_data = df[df['algorithm'] == algo]
    low = len(algo_data[algo_data['deviation'] < 25])
    med = len(algo_data[(algo_data['deviation'] >= 25) & (algo_data['deviation'] < 50)])
    high = len(algo_data[algo_data['deviation'] >= 50])
    print(f"\n{algo}:")
    print(f"  Low deviation (<25%): {low} metrics")
    print(f"  Medium (25-50%): {med} metrics")
    print(f"  High (>50%): {high} metrics")
    if high > 0:
        high_metrics = algo_data[algo_data['deviation'] >= 50]['metric'].tolist()
        print(f"  High deviation metrics: {', '.join(high_metrics)}")
