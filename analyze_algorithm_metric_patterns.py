"""
Analyze patterns in algorithm-metric performance from the heatmap data.
"""

import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('plots/fc_visualizations/algorithm_metric_average_grades.csv', index_col=0)

print('='*80)
print('ALGORITHM-METRIC PERFORMANCE PATTERN ANALYSIS')
print('='*80)

# Convert grades to numeric (A=4, B=3, C=2, D=1, F=0)
grade_map = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}
df_numeric = df.applymap(lambda x: grade_map.get(x, 0))

print('\n1. ALGORITHM PERFORMANCE PATTERNS:')
print('-'*80)

# Calculate average grade per algorithm across all metrics
algo_means = df_numeric.mean(axis=1).sort_values(ascending=False)
print('\nTop 5 algorithms (avg across all metrics):')
for algo, score in algo_means.head(5).items():
    grade = ['F','D','C','B','A'][int(round(score))]
    print(f'  {algo:20s} {score:.2f} (~{grade})')

print('\nBottom 5 algorithms:')
for algo, score in algo_means.tail(5).items():
    grade = ['F','D','C','B','A'][int(round(score))]
    print(f'  {algo:20s} {score:.2f} (~{grade})')

print('\n2. METRIC DIFFICULTY PATTERNS:')
print('-'*80)

# Calculate average grade per metric across all algorithms
metric_means = df_numeric.mean(axis=0).sort_values(ascending=False)
print('\nEasiest metrics (highest avg grades):')
for metric, score in metric_means.head(5).items():
    grade = ['F','D','C','B','A'][int(round(score))]
    print(f'  {metric:35s} {score:.2f} (~{grade})')

print('\nHardest metrics (lowest avg grades):')
for metric, score in metric_means.tail(5).items():
    grade = ['F','D','C','B','A'][int(round(score))]
    print(f'  {metric:35s} {score:.2f} (~{grade})')

print('\n3. FEATURE CATEGORY PATTERNS:')
print('-'*80)

# Group metrics by category
level_metrics = ['level_l1', 'level_linf', 'mean_delta']
shape_metrics = ['regimes_delta', 'extrema_wasserstein', 'extrema_bottleneck', 
                 'spikes_dips_wasserstein', 'spikes_dips_bottleneck']
derivative_metrics = ['slope_l1', 'slope_linf', 'curvature_l1', 'curvature_linf']
frequency_metrics = ['trend_l1', 'trend_linf', 'regression_l1', 'regression_linf',
                     'periodicity_amplitude_delta', 'periodicity_num_periods_delta',
                     'roughness_delta', 'noise_l1', 'noise_linf']

categories = {
    'Level': level_metrics,
    'Shape': shape_metrics,
    'Derivatives': derivative_metrics,
    'Frequency': frequency_metrics
}

for cat_name, metrics in categories.items():
    available = [m for m in metrics if m in df_numeric.columns]
    if available:
        cat_scores = df_numeric[available].mean(axis=1).sort_values(ascending=False)
        avg = cat_scores.mean()
        print(f'\n{cat_name} features (avg: {avg:.2f}):')
        print(f'  Best: {cat_scores.index[0]:20s} {cat_scores.iloc[0]:.2f}')
        print(f'  Worst: {cat_scores.index[-1]:20s} {cat_scores.iloc[-1]:.2f}')

print('\n4. ALGORITHM SPECIALIZATION PATTERNS:')
print('-'*80)

# Find algorithms that excel at specific metrics
print('\nAlgorithms with A grades by metric:')
for col in df.columns:
    a_algos = df[df[col] == 'A'].index.tolist()
    if a_algos:
        print(f'  {col:35s} {len(a_algos):2d} As: {", ".join(a_algos[:4])}{"..." if len(a_algos) > 4 else ""}')

print('\n5. WORST PERFORMERS (F grades):')
print('-'*80)
f_counts = (df == 'F').sum(axis=1).sort_values(ascending=False)
print('\nAlgorithms with most F grades:')
for algo, count in f_counts.head(5).items():
    if count > 0:
        f_metrics = df.loc[algo][df.loc[algo] == 'F'].index.tolist()
        print(f'  {algo:20s} {count:2d} Fs: {", ".join(f_metrics[:3])}')

print('\n6. CONSISTENCY PATTERNS:')
print('-'*80)
algo_variance = df_numeric.var(axis=1).sort_values(ascending=False)
print('\nMost inconsistent algorithms (high variance across metrics):')
for algo, var in algo_variance.head(5).items():
    best = df.loc[algo][df.loc[algo] == 'A'].index.tolist()
    worst = df.loc[algo][df.loc[algo] == 'F'].index.tolist()
    print(f'  {algo:20s} variance={var:.2f}  (Best: {len(best)} As, Worst: {len(worst)} Fs)')

print('\nMost consistent algorithms (low variance):')
for algo, var in algo_variance.tail(5).items():
    grades = df.loc[algo].value_counts().to_dict()
    print(f'  {algo:20s} variance={var:.2f}  {grades}')

print('\n7. TRANSFORMER vs REDUCER vs AGGREGATOR:')
print('-'*80)
transformers = ['Gaussian Filter', 'Mean Filter', 'Median Filter', 'Min Filter', 
                'Max Filter', 'Savitzky-Golay', 'Butterworth', 'Chebyshev', 
                'Elliptical', 'FFT Cutoff', 'TopoLines']
reducers = ['LTTB', 'M4', 'MinMaxLTTB', 'Douglas-Peucker', 'Uniform Subsample', 'FPCS']
aggregators = ['ASAP', 'PAA']

families = {
    'Transformers': transformers,
    'Reducers': reducers,
    'Aggregators': aggregators
}

for family, algos in families.items():
    available = [a for a in algos if a in df_numeric.index]
    if available:
        family_scores = df_numeric.loc[available].mean(axis=1)
        family_avg = family_scores.mean()
        print(f'\n{family} (n={len(available)}, avg: {family_avg:.2f}):')
        print(f'  Best: {family_scores.idxmax():20s} {family_scores.max():.2f}')
        print(f'  Worst: {family_scores.idxmin():20s} {family_scores.min():.2f}')
        
print('\n8. INTERESTING FINDINGS:')
print('-'*80)

# Find algorithms that are good at one thing but bad at others
print('\nSpecialists (high variance with some As and some Fs):')
for algo in df.index:
    a_count = (df.loc[algo] == 'A').sum()
    f_count = (df.loc[algo] == 'F').sum()
    if a_count >= 2 and f_count >= 2:
        a_metrics = df.loc[algo][df.loc[algo] == 'A'].index.tolist()
        f_metrics = df.loc[algo][df.loc[algo] == 'F'].index.tolist()
        print(f'\n  {algo}:')
        print(f'    Excels at: {", ".join(a_metrics)}')
        print(f'    Fails at: {", ".join(f_metrics)}')

print('\n' + '='*80)
