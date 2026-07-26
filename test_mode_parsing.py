import pandas as pd

df = pd.read_csv('plots/fc_visualizations/algorithm_metric_mode_grades.csv')
tied = df[df['mode'].str.contains(',', na=False)]

print(f"Found {len(tied)} rows with ties\n")

for idx, row in tied.head(3).iterrows():
    print(f"Row {idx}:")
    print(f"  Algorithm: {row['algorithm']}")
    print(f"  Metric: {row['metric']}")
    print(f"  Mode: '{row['mode']}'")
    print(f"  Split: {[g.strip() for g in row['mode'].split(',')]}")
    print(f"  Counts: A={row['A']}, B={row['B']}, C={row['C']}, D={row['D']}, F={row['F']}")
    print()
