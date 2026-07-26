import pandas as pd

df = pd.read_csv('plots/fc_visualizations/algorithm_metric_mode_grades.csv')
row = df[(df['algorithm'] == 'gaussian_filter') & (df['metric'] == 'level_l1')].iloc[0]

print(f"Gaussian Filter + Level L1:")
print(f"  A: {row['A']}")
print(f"  B: {row['B']}")
print(f"  C: {row['C']}")
print(f"  D: {row['D']}")
print(f"  F: {row['F']}")
print(f"  Mode: {row['mode']}")
