import pandas as pd

df = pd.read_csv('supplemental_material/csv_data/algorithm_metric_mode_grades.csv')

# Exclude change_points_delta and noise_auc_delta
excluded_metrics = ['change_points_delta', 'noise_auc_delta']
df_filtered = df[~df['metric'].isin(excluded_metrics)].copy()

print("="*80)
print("DEVIATION RANGE BUCKETS (21 features, excluding change_points and noise_auc)")
print("="*80)

# Get all unique algorithms
algorithms = df_filtered['algorithm'].unique()

results = []

for algo in sorted(algorithms):
    algo_data = df_filtered[df_filtered['algorithm'] == algo]
    
    low = len(algo_data[algo_data['deviation'] < 25])
    medium = len(algo_data[(algo_data['deviation'] >= 25) & (algo_data['deviation'] < 50)])
    high = len(algo_data[algo_data['deviation'] >= 50])
    
    avg_dev = algo_data['deviation'].mean()
    
    results.append({
        'algorithm': algo,
        'low': low,
        'medium': medium,
        'high': high,
        'avg_deviation': avg_dev
    })

# Create DataFrame for easy viewing
results_df = pd.DataFrame(results)
results_df = results_df.sort_values('avg_deviation')

print("\nAlgorithm                          Low    Med    High   Avg Dev")
print("-" * 80)
for _, row in results_df.iterrows():
    print(f"{row['algorithm']:30s}  {row['low']:3d}    {row['medium']:3d}    {row['high']:3d}    {row['avg_deviation']:5.1f}%")

# Calculate some statistics
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

print(f"\nTotal algorithm-metric pairs: {len(df_filtered)} (19 algorithms × 21 metrics)")

# Algorithms by primary bucket
mostly_low = results_df[results_df['low'] >= 15]
mostly_medium = results_df[(results_df['low'] < 15) & (results_df['medium'] >= results_df[['low', 'high']].max(axis=1))]
mostly_high = results_df[results_df['high'] >= results_df[['low', 'medium']].max(axis=1)]

print(f"\nAlgorithms with majority LOW deviation (<25%):")
for _, row in mostly_low.iterrows():
    print(f"  {row['algorithm']:30s}: {row['low']}/21 metrics ({row['low']/21*100:.1f}%)")

print(f"\nAlgorithms with majority MEDIUM deviation (25-50%):")
for _, row in mostly_medium.iterrows():
    print(f"  {row['algorithm']:30s}: {row['medium']}/21 metrics ({row['medium']/21*100:.1f}%)")

print(f"\nAlgorithms with majority HIGH deviation (>50%):")
for _, row in mostly_high.iterrows():
    print(f"  {row['algorithm']:30s}: {row['high']}/21 metrics ({row['high']/21*100:.1f}%)")

# Overall distribution
total_low = results_df['low'].sum()
total_medium = results_df['medium'].sum()
total_high = results_df['high'].sum()
total_pairs = total_low + total_medium + total_high

print(f"\nOverall distribution across all {total_pairs} pairs:")
print(f"  Low deviation (<25%):     {total_low:3d} ({total_low/total_pairs*100:.1f}%)")
print(f"  Medium deviation (25-50%): {total_medium:3d} ({total_medium/total_pairs*100:.1f}%)")
print(f"  High deviation (>50%):     {total_high:3d} ({total_high/total_pairs*100:.1f}%)")
