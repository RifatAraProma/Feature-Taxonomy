import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the detailed grade data (dataset × algorithm × metric)
grades_df = pd.read_csv('plots/fc_visualizations/dataset_algorithm_metric_grades.csv')

# Exclude noise_auc_delta and change_points_delta (use only 21 metrics)
excluded_metrics = ['noise_auc_delta', 'change_points_delta']
grades_df = grades_df[~grades_df['metric'].isin(excluded_metrics)]

# Classify algorithms into families (using actual names from dataset)
transformers = ['gaussian_filter', 'mean_filter', 'savitzky_golay_filter', 'median_filter', 
                'max_filter', 'min_filter', 'butterworth_filter', 'chebyshev_filter', 
                'elliptical_filter', 'fft_cutoff_filter', 'tda_downsample']
reducers = ['lttb_downsample', 'm4_downsample', 'minmaxlttb_downsample', 
            'rdp_downsample', 'uniform_subsample', 'fpcs_downsample']
aggregators = ['asap_aggregator', 'bin_average_aggregator']

# Map algorithm names to families
def classify_algorithm(algo):
    if algo in transformers:
        return 'Transformers'
    elif algo in reducers:
        return 'Reducers'
    elif algo in aggregators:
        return 'Aggregators'
    else:
        return 'Unknown'

grades_df['family'] = grades_df['algorithm'].apply(classify_algorithm)

# Count grades for each family
family_grade_counts = grades_df.groupby(['family', 'grade']).size().unstack(fill_value=0)

# Ensure all grade columns exist
for grade in ['A', 'B', 'C', 'D', 'F']:
    if grade not in family_grade_counts.columns:
        family_grade_counts[grade] = 0

# Reorder columns and calculate percentages
family_grade_counts = family_grade_counts[['A', 'B', 'C', 'D', 'F']]
family_grade_pct = family_grade_counts.div(family_grade_counts.sum(axis=1), axis=0) * 100

# Sort families by overall performance (Transformers first)
family_order = ['Transformers', 'Aggregators', 'Reducers']
family_grade_pct = family_grade_pct.reindex(family_order)

# Set up the plot
fig, ax = plt.subplots(figsize=(10, 6))

# Define colors for each grade (same as heatmap: shades of green from dark to light)
colors = {
    'A': '#006837',  # Dark green (excellent)
    'B': '#31a354',  # Medium green (good)
    'C': '#78c679',  # Light green (fair)
    'D': '#c2e699',  # Very light green (poor)
    'F': '#ebfada'   # Pale green (fail)
}

# Prepare data for stacked bar chart
families = family_grade_pct.index.values
grades = ['A', 'B', 'C', 'D', 'F']
x = np.arange(len(families))
width = 0.6

# Create stacked bars
bottom = np.zeros(len(families))
for grade in grades:
    values = family_grade_pct[grade].values
    ax.bar(x, values, width, label=grade, bottom=bottom, color=colors[grade], edgecolor='white', linewidth=1)
    
    # Add percentage labels inside bars
    for i, (fam, val) in enumerate(zip(families, values)):
        if val > 3:  # Only show label if segment is large enough
            ax.text(i, bottom[i] + val/2, f'{val:.1f}%', 
                   ha='center', va='center', fontsize=10, fontweight='bold',
                   color='white' if grade in ['A', 'B'] else 'black')
    
    bottom += values

# Customize the plot
ax.set_xlabel('Algorithm Family', fontsize=13, fontweight='bold')
ax.set_ylabel('Percentage of Grades (%)', fontsize=13, fontweight='bold')
ax.set_title('Grade Distribution by Algorithm Family\n(80 datasets × 21 metrics, aggregated across all algorithms in family)', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(families, fontsize=12, fontweight='bold')
ax.legend(title='Grade', loc='upper right', frameon=True, fontsize=11)
ax.set_ylim(0, 100)
ax.grid(axis='y', alpha=0.3, linestyle='--')

# Tight layout
plt.tight_layout()

# Save the figure
output_path = 'plots/fc_visualizations/family_metric_grade_comparison.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f'✅ Saved: {output_path}')

output_path_svg = 'plots/fc_visualizations/family_metric_grade_comparison.svg'
plt.savefig(output_path_svg, bbox_inches='tight')
print(f'✅ Saved: {output_path_svg}')

output_path_pdf = 'plots/fc_visualizations/family_metric_grade_comparison.pdf'
plt.savefig(output_path_pdf, bbox_inches='tight')
print(f'✅ Saved: {output_path_pdf}')

plt.show()

# Print summary statistics
print("\n" + "="*80)
print("GRADE DISTRIBUTION BY ALGORITHM FAMILY (21 metrics)")
print("="*80)

for family in family_order:
    if family in family_grade_counts.index:
        counts = family_grade_counts.loc[family]
        pcts = family_grade_pct.loc[family]
        total = counts.sum()
        
        print(f"\n{family}:")
        print(f"  Total grades: {int(total)}")
        print(f"  Grade breakdown:")
        for grade in ['A', 'B', 'C', 'D', 'F']:
            print(f"    {grade}: {int(counts[grade]):5d} ({pcts[grade]:5.1f}%)")
        
        # Calculate GPA
        gpa = (counts['A']*4 + counts['B']*3 + counts['C']*2 + counts['D']*1) / total
        print(f"  Average GPA: {gpa:.3f}")

print("\n" + "="*80)
print("SUMMARY:")
print("="*80)
for family in family_order:
    if family in family_grade_counts.index:
        counts = family_grade_counts.loc[family]
        total = counts.sum()
        gpa = (counts['A']*4 + counts['B']*3 + counts['C']*2 + counts['D']*1) / total
        excellent_good = (counts['A'] + counts['B']) / total * 100
        print(f"{family:15s}: GPA={gpa:.3f}, A+B={excellent_good:5.1f}%, Total={int(total)}")
