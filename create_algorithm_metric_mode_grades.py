import pandas as pd
from pathlib import Path
from collections import Counter

# Use the original dataset_algorithm_metric_grades.csv which has the authoritative grades
print('Reading dataset_algorithm_metric_grades.csv...')
df_original = pd.read_csv('supplemental_material/csv_data/dataset_algorithm_metric_grades.csv')

print(f'Loaded {len(df_original)} rows')
print(f'Columns: {df_original.columns.tolist()}\n')

# Collect all grades for each algorithm-metric pair
all_grades = {}

for _, row in df_original.iterrows():
    algorithm = row['algorithm']
    metric = row['metric']
    grade = row['grade']
    
    key = (algorithm, metric)
    if key not in all_grades:
        all_grades[key] = []
    all_grades[key].append(grade)

print(f'Processed {len(df_original)} grade records')

print(f'\nCollected grades for {len(all_grades)} algorithm-metric pairs')
print('\nCalculating mode grades and statistics...')

# Calculate statistics for each algorithm-metric pair
results = []

for (algorithm, metric), grades in all_grades.items():
    # Count each grade
    counter = Counter(grades)
    count_A = counter.get('A', 0)
    count_B = counter.get('B', 0)
    count_C = counter.get('C', 0)
    count_D = counter.get('D', 0)
    count_F = counter.get('F', 0)
    total = len(grades)
    
    # Find mode grade(s) - can be multiple
    max_count = max(counter.values())
    mode_grades = [grade for grade, count in counter.items() if count == max_count]
    mode_grades_str = ','.join(sorted(mode_grades))
    
    # Calculate deviation percentage
    deviation = ((total - max_count) / total) * 100
    
    results.append({
        'algorithm': algorithm,
        'metric': metric,
        'count_A': count_A,
        'count_B': count_B,
        'count_C': count_C,
        'count_D': count_D,
        'count_F': count_F,
        'total': total,
        'mode_grades': mode_grades_str,
        'mode_count': max_count,
        'deviation': round(deviation, 2)
    })

# Create dataframe and save
df_results = pd.DataFrame(results)
df_results = df_results.sort_values(['algorithm', 'metric'])

output_file = 'supplemental_material/csv_data/algorithm_metric_mode_grades_verified.csv'
df_results.to_csv(output_file, index=False)

print(f'\nSaved to {output_file}')
print(f'Total rows: {len(df_results)}')
print(f'\nSample rows:')
print(df_results.head(10).to_string())
