import pandas as pd

# Grade mapping
grade_map = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}

# Load the letter grades CSV
df = pd.read_csv('plots/fc_visualizations/algorithm_metric_average_grades.csv', index_col=0)

print(f"Loaded {df.shape[0]} algorithms x {df.shape[1]} metrics")

# Convert all letter grades to numeric
df_numeric = df.map(lambda x: grade_map.get(x, 0) if isinstance(x, str) else x)

# Calculate metric averages (column averages)
metric_avgs = df_numeric.mean(axis=0)

# Add average row at the bottom
metric_avgs.name = 'METRIC_AVERAGE'
df_with_avg = pd.concat([df_numeric, metric_avgs.to_frame().T])

# Save
output_path = 'plots/fc_visualizations/algorithm_metric_numeric_grades.csv'
df_with_avg.to_csv(output_path)

print(f'\n✓ Created: {output_path}')
print(f'  Shape: 20 rows x 21 metrics (19 algorithms + 1 average row)')
print(f'\nMetric averages:')
for metric, avg in metric_avgs.items():
    print(f'  {metric}: {avg:.3f}')
