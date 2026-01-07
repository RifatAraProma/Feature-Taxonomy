import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the detailed grade data (dataset × algorithm × metric)
grades_df = pd.read_csv('plots/fc_visualizations/dataset_algorithm_metric_grades.csv')

# Exclude noise_auc_delta and change_points_delta (use only 21 metrics)
excluded_metrics = ['noise_auc_delta', 'change_points_delta']
grades_df = grades_df[~grades_df['metric'].isin(excluded_metrics)]

# Count grades for each metric
grade_counts = grades_df.groupby(['metric', 'grade']).size().unstack(fill_value=0)

# Ensure all grade columns exist
for grade in ['A', 'B', 'C', 'D', 'F']:
    if grade not in grade_counts.columns:
        grade_counts[grade] = 0

# Reorder columns
grade_counts = grade_counts[['A', 'B', 'C', 'D', 'F']]

# Calculate GPA for sorting (A=4, B=3, C=2, D=1, F=0)
grade_counts['total'] = grade_counts.sum(axis=1)
grade_counts['GPA'] = (
    grade_counts['A'] * 4 + 
    grade_counts['B'] * 3 + 
    grade_counts['C'] * 2 + 
    grade_counts['D'] * 1 + 
    grade_counts['F'] * 0
) / grade_counts['total']

# Sort by GPA (descending) and reset index
df = grade_counts.sort_values('GPA', ascending=False).reset_index()

# Set up the plot
fig, ax = plt.subplots(figsize=(16, 8))

# Define colors for each grade (same as heatmap: shades of green from dark to light)
colors = {
    'A': '#006837',  # Dark green (excellent)
    'B': '#31a354',  # Medium green (good)
    'C': '#78c679',  # Light green (fair)
    'D': '#c2e699',  # Very light green (poor)
    'F': '#ebfada'   # Pale green (fail)
}

# Prepare data for stacked bar chart
metrics = df['metric'].values
grades = ['A', 'B', 'C', 'D', 'F']
x = np.arange(len(metrics))

# Create stacked bars
bottom = np.zeros(len(metrics))
for grade in grades:
    values = df[grade].values
    ax.bar(x, values, label=grade, bottom=bottom, color=colors[grade], edgecolor='white', linewidth=0.5)
    bottom += values

# Customize the plot
ax.set_xlabel('Feature Metric', fontsize=12, fontweight='bold')
ax.set_ylabel('Number of Grades', fontsize=12, fontweight='bold')
ax.set_title('Grade Distribution by Feature Metric (80 datasets × 19 algorithms = 1,520 total grades per metric)', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(metrics, rotation=45, ha='right')
ax.legend(title='Grade', loc='upper right', frameon=True)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Add GPA values on top of bars
for i, (metric, gpa) in enumerate(zip(metrics, df['GPA'].values)):
    total_height = bottom[i]
    ax.text(i, total_height + 20, f'{gpa:.2f}', 
            ha='center', va='bottom', fontsize=8, fontweight='bold')

# Tight layout
plt.tight_layout()

# Save the figure
output_path = 'plots/fc_visualizations/metric_grade_distribution_barchart.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f'✅ Saved: {output_path}')

output_path_svg = 'plots/fc_visualizations/metric_grade_distribution_barchart.svg'
plt.savefig(output_path_svg, bbox_inches='tight')
print(f'✅ Saved: {output_path_svg}')

output_path_pdf = 'plots/fc_visualizations/metric_grade_distribution_barchart.pdf'
plt.savefig(output_path_pdf, bbox_inches='tight')
print(f'✅ Saved: {output_path_pdf}')

plt.show()

# Print summary statistics
print("\n" + "="*80)
print("METRIC DIFFICULTY SUMMARY (21 metrics: excluding noise_auc_delta, change_points_delta)")
print("="*80)
total_per_metric = df['total'].iloc[0]
print(f"\nTotal grades per metric: {int(total_per_metric)} (80 datasets × 19 algorithms)")
print(f"\nTop 5 EASIEST metrics (highest GPA):")
for i, row in df.head(5).iterrows():
    print(f"  {row['metric']:30s} GPA: {row['GPA']:.2f}  | A:{int(row['A']):3d} B:{int(row['B']):3d} C:{int(row['C']):3d} D:{int(row['D']):3d} F:{int(row['F']):3d}")

print(f"\nTop 5 HARDEST metrics (lowest GPA):")
for i, row in df.tail(5).iloc[::-1].iterrows():
    print(f"  {row['metric']:30s} GPA: {row['GPA']:.2f}  | A:{int(row['A']):3d} B:{int(row['B']):3d} C:{int(row['C']):3d} D:{int(row['D']):3d} F:{int(row['F']):3d}")
