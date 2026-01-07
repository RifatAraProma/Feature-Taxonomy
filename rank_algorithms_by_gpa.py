import pandas as pd

# Load numeric grades CSV
csv_path = r"plots\fc_visualizations\algorithm_metric_numeric_grades.csv"
df = pd.read_csv(csv_path, index_col=0)

# Remove the METRIC_AVERAGE row if it exists
if 'METRIC_AVERAGE' in df.index:
    df = df.drop('METRIC_AVERAGE')

# Calculate GPA for each algorithm (average across all 21 metrics)
algorithm_gpas = df.mean(axis=1).sort_values(ascending=False)

# Create ranking dataframe
ranking_df = pd.DataFrame({
    'Rank': range(1, len(algorithm_gpas) + 1),
    'Algorithm': algorithm_gpas.index,
    'GPA': algorithm_gpas.values
})

# Save to CSV
output_path = r"plots\fc_visualizations\algorithm_ranking_by_gpa.csv"
ranking_df.to_csv(output_path, index=False)

print("=" * 60)
print("ALGORITHM RANKING BY AVERAGE GPA ACROSS 21 FEATURES")
print("=" * 60)
print(f"\nTotal algorithms: {len(algorithm_gpas)}")
print(f"GPA range: {algorithm_gpas.min():.3f} to {algorithm_gpas.max():.3f}")
print(f"GPA spread: {algorithm_gpas.max() - algorithm_gpas.min():.3f} grade points\n")

print("Ranking:")
print("-" * 60)
for idx, row in ranking_df.iterrows():
    print(f"{row['Rank']:2d}. {row['Algorithm']:30s} {row['GPA']:.3f}")

print("\n" + "=" * 60)
print(f"✓ Saved to: {output_path}")
print("=" * 60)
