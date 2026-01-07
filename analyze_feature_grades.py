import pandas as pd

# Load the letter grades
df = pd.read_csv('plots/fc_visualizations/algorithm_metric_average_grades.csv', index_col=0)

print(f"Analyzing {df.shape[1]} metrics across {df.shape[0]} algorithms")
print("=" * 80)

# Count grade distribution for each metric
grade_counts = {}
for metric in df.columns:
    counts = df[metric].value_counts().to_dict()
    grade_counts[metric] = {
        'A': counts.get('A', 0),
        'B': counts.get('B', 0),
        'C': counts.get('C', 0),
        'D': counts.get('D', 0),
        'F': counts.get('F', 0)
    }

# Create summary DataFrame
summary = pd.DataFrame(grade_counts).T
summary = summary[['A', 'B', 'C', 'D', 'F']]
summary['Total'] = summary.sum(axis=1)

# Sort by number of As (descending), then by number of Fs (ascending)
summary['GoodGrades'] = summary['A'] + summary['B']
summary['BadGrades'] = summary['D'] + summary['F']
summary = summary.sort_values(['A', 'F'], ascending=[False, True])

print("\nGrade Distribution by Metric (sorted by A count, then F count):")
print(summary.to_string())

# Summary stats
print("\n" + "=" * 80)
print("\nSUMMARY STATISTICS:")
print(f"Metric with most As: {summary['A'].idxmax()} ({summary['A'].max()} As)")
print(f"Metric with most Fs: {summary['F'].idxmax()} ({summary['F'].max()} Fs)")
print(f"Metric with fewest As: {summary['A'].idxmin()} ({summary['A'].min()} As)")
print(f"Metric with fewest Fs: {summary['F'].idxmin()} ({summary['F'].min()} Fs)")

print(f"\nRange of A grades: {summary['A'].min()} to {summary['A'].max()} (span: {summary['A'].max() - summary['A'].min()})")
print(f"Range of F grades: {summary['F'].min()} to {summary['F'].max()} (span: {summary['F'].max() - summary['F'].min()})")

# Check if there are meaningful patterns
a_variance = summary['A'].std()
f_variance = summary['F'].std()
print(f"\nVariance in A grades across metrics: {a_variance:.2f}")
print(f"Variance in F grades across metrics: {f_variance:.2f}")

# Top and bottom metrics
print("\n" + "=" * 80)
print("\nTOP 5 METRICS (most As):")
for idx, (metric, row) in enumerate(summary.head(5).iterrows(), 1):
    print(f"{idx}. {metric}: {int(row['A'])} As, {int(row['B'])} Bs, {int(row['C'])} Cs, {int(row['D'])} Ds, {int(row['F'])} Fs")

print("\nBOTTOM 5 METRICS (fewest As):")
for idx, (metric, row) in enumerate(summary.tail(5).iterrows(), 1):
    print(f"{idx}. {metric}: {int(row['A'])} As, {int(row['B'])} Bs, {int(row['C'])} Cs, {int(row['D'])} Ds, {int(row['F'])} Fs")

# Save detailed summary
output_path = 'plots/fc_visualizations/metric_grade_distribution.csv'
summary.to_csv(output_path)
print(f"\n✓ Saved detailed summary to: {output_path}")
