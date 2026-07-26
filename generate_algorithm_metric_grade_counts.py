"""
Generate a CSV with grade counts for each algorithm-metric combination
"""
import pandas as pd

# Load the per-dataset grades
df = pd.read_csv('plots/fc_visualizations/dataset_algorithm_metric_grades.csv')

# Count grades for each algorithm-metric combination
results = []

for (algo, metric), group in df.groupby(['algorithm', 'metric']):
    counts = group['grade'].value_counts()
    
    result = {
        'algorithm': algo,
        'metric': metric,
        'count_A': counts.get('A', 0),
        'count_B': counts.get('B', 0),
        'count_C': counts.get('C', 0),
        'count_D': counts.get('D', 0),
        'count_F': counts.get('F', 0),
        'total': len(group)
    }
    
    # Calculate current mean-based grade
    avg_score = (result['count_A']*4 + result['count_B']*3 + result['count_C']*2 + 
                 result['count_D']*1 + result['count_F']*0) / result['total']
    
    if avg_score >= 3.5:
        mean_grade = 'A'
    elif avg_score >= 2.5:
        mean_grade = 'B'
    elif avg_score >= 1.5:
        mean_grade = 'C'
    elif avg_score >= 0.5:
        mean_grade = 'D'
    else:
        mean_grade = 'F'
    
    result['mean_score'] = round(avg_score, 4)
    result['mean_grade'] = mean_grade
    
    # Mode (most common grade)
    mode_grade = counts.idxmax()
    result['mode_grade'] = mode_grade
    result['mode_count'] = counts.max()
    
    results.append(result)

# Create DataFrame
results_df = pd.DataFrame(results)

# Sort by algorithm and metric
results_df = results_df.sort_values(['algorithm', 'metric'])

# Save
output_path = 'plots/fc_visualizations/algorithm_metric_grade_counts.csv'
results_df.to_csv(output_path, index=False)

print(f"✓ Generated: {output_path}")
print(f"✓ {len(results_df)} algorithm-metric combinations")
print(f"\nSample (median_filter + regimes_delta):")
sample = results_df[(results_df['algorithm'] == 'median_filter') & 
                    (results_df['metric'] == 'regimes_delta')]
if not sample.empty:
    print(sample.to_string(index=False))
