"""
Analyze algorithm rankings across all datasets to identify performance patterns.
"""

import pandas as pd
import numpy as np
import os
import glob
from collections import defaultdict

# Load all ranking files
rank_files = glob.glob('plots/*/ranking/rankings_ranked.csv')
print(f"Found {len(rank_files)} datasets with ranking data\n")

all_ranks = []
for f in rank_files:
    # Extract dataset name from path: plots/DATASET/ranking/rankings_ranked.csv
    dataset = os.path.basename(os.path.dirname(os.path.dirname(f)))
    df = pd.read_csv(f)
    df['dataset'] = dataset
    all_ranks.append(df)

combined = pd.concat(all_ranks, ignore_index=True)

# Extract dataset categories
def categorize_dataset(name):
    if name.startswith('stock_'):
        if 'price' in name:
            return 'stock_price'
        else:
            return 'stock_volume'
    elif name.startswith('climate_'):
        parts = name.split('_')
        return f'climate_{parts[-1]}'  # awnd, prcp, tmax
    elif name.startswith('unemployment_'):
        return 'unemployment'
    elif name.startswith('eeg_'):
        return 'eeg'
    elif name.startswith('astro_'):
        return 'astro'
    elif name.startswith('chi_'):
        return 'chicago_crime'
    elif name.startswith('flights_'):
        return 'flights'
    elif name.startswith('nz_'):
        return 'nz_tourism'
    return 'other'

combined['category'] = combined['dataset'].apply(categorize_dataset)

# Get all metric columns (exclude algorithm, dataset, category)
metric_cols = [col for col in combined.columns if col not in ['algorithm', 'dataset', 'category']]

print("="*80)
print("1. OVERALL ALGORITHM PERFORMANCE")
print("="*80)
avg_ranks = combined.groupby('algorithm')[metric_cols].mean().mean(axis=1).sort_values()
print("\nAverage Rank Across ALL Metrics and ALL Datasets:")
print("-" * 50)
for i, (algo, rank) in enumerate(avg_ranks.items(), 1):
    print(f"{i:2d}. {algo:30s} {rank:5.2f}")

print("\n" + "="*80)
print("2. BEST ALGORITHMS BY FEATURE CATEGORY")
print("="*80)

# Group metrics by feature type
feature_groups = {
    'Level Features': ['level_l1', 'level_linf', 'mean_delta'],
    'Shape Features (Extrema)': ['extrema_bottleneck', 'extrema_wasserstein'],
    'Shape Features (Spikes/Dips)': ['spikes_dips_bottleneck', 'spikes_dips_wasserstein'],
    'Shape Features (Regimes)': ['regimes_delta', 'change_points_delta'],
    'Derivative Features (Slope)': ['slope_l1', 'slope_linf'],
    'Derivative Features (Curvature)': ['curvature_l1', 'curvature_linf'],
    'Derivative Features (Roughness)': ['roughness_delta'],
    'Frequency Features (Trend)': ['trend_l1', 'trend_linf'],
    'Frequency Features (Noise)': ['noise_l1', 'noise_linf', 'noise_auc_delta'],
    'Frequency Features (Periodicity)': ['periodicity_amplitude_delta', 'periodicity_num_periods_delta'],
    'Statistical Features': ['regression_l1', 'regression_linf']
}

for group_name, metrics in feature_groups.items():
    available_metrics = [m for m in metrics if m in metric_cols]
    if available_metrics:
        group_ranks = combined.groupby('algorithm')[available_metrics].mean().mean(axis=1).sort_values()
        print(f"\n{group_name}:")
        print(f"  Best: {group_ranks.index[0]} (rank {group_ranks.iloc[0]:.2f})")
        print(f"  Top 3: {', '.join([f'{algo} ({rank:.2f})' for algo, rank in group_ranks.head(3).items()])}")

print("\n" + "="*80)
print("3. ALGORITHM PERFORMANCE BY DATASET TYPE")
print("="*80)

for category in sorted(combined['category'].unique()):
    cat_data = combined[combined['category'] == category]
    cat_ranks = cat_data.groupby('algorithm')[metric_cols].mean().mean(axis=1).sort_values()
    print(f"\n{category.upper()} datasets:")
    print(f"  Best: {cat_ranks.index[0]} (rank {cat_ranks.iloc[0]:.2f})")
    top3 = ', '.join([f'{algo} ({rank:.2f})' for algo, rank in cat_ranks.head(3).items()])
    print(f"  Top 3: {top3}")

print("\n" + "="*80)
print("4. ALGORITHM SPECIALIZATIONS (Where Each Algorithm Excels)")
print("="*80)

for algo in avg_ranks.index[:10]:  # Top 10 algorithms only
    algo_data = combined[combined['algorithm'] == algo][metric_cols].mean().sort_values()
    best_metrics = algo_data.head(5)
    print(f"\n{algo}:")
    print(f"  Overall rank: {avg_ranks[algo]:.2f}")
    best_at = ', '.join([f"{m.replace('_', ' ')} ({r:.1f})" for m, r in best_metrics.items()])
    print(f"  Best at: {best_at}")

print("\n" + "="*80)
print("5. KEY INSIGHTS")
print("="*80)

# Identify algorithm types
transformers = ['gaussian_filter', 'mean_filter', 'median_filter', 'savitzky_golay_filter',
                'butterworth_filter', 'chebyshev_filter', 'elliptical_filter', 'fft_cutoff_filter',
                'max_filter', 'min_filter']
reducers = ['lttb_downsample', 'm4_downsample', 'minmaxlttb_downsample', 'uniform_subsample',
            'rdp_downsample', 'fpcs_downsample', 'tda_downsample']
aggregators = ['asap_aggregator', 'bin_average_aggregator']

transformer_ranks = avg_ranks[avg_ranks.index.isin(transformers)]
reducer_ranks = avg_ranks[avg_ranks.index.isin(reducers)]
aggregator_ranks = avg_ranks[avg_ranks.index.isin(aggregators)]

print(f"\nBest Transformer: {transformer_ranks.index[0]} (rank {transformer_ranks.iloc[0]:.2f})")
print(f"Best Reducer: {reducer_ranks.index[0]} (rank {reducer_ranks.iloc[0]:.2f})")
print(f"Best Aggregator: {aggregator_ranks.index[0]} (rank {aggregator_ranks.iloc[0]:.2f})")

print(f"\nAverage transformer rank: {transformer_ranks.mean():.2f}")
print(f"Average reducer rank: {reducer_ranks.mean():.2f}")
print(f"Average aggregator rank: {aggregator_ranks.mean():.2f}")

# Find metrics with high variance in rankings
print("\n" + "="*80)
print("6. MOST CHALLENGING METRICS (High Variance in Algorithm Performance)")
print("="*80)

metric_variances = combined.groupby('algorithm')[metric_cols].mean().std().sort_values(ascending=False)
print("\nMetrics where algorithms differ most:")
for metric, variance in metric_variances.head(10).items():
    print(f"  {metric.replace('_', ' '):40s} (std: {variance:.2f})")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
