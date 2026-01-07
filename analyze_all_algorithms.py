"""
Complete Algorithm Performance Analysis
Shows ALL algorithms including ASAP, FPCS, M4, TDA to find their niches
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import glob
import json

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

print("=" * 70)
print("COMPLETE ALGORITHM PERFORMANCE ANALYSIS")
print("=" * 70)

# Load dataset characteristics
char_path = Path('plots/insights/dataset_characteristics.csv')
df_datasets = pd.read_csv(char_path)
print(f"✓ Loaded characteristics for {len(df_datasets)} datasets")

# Load ALL ranking data
rank_files = glob.glob('plots/*/ranking/rankings_ranked.csv')
print(f"✓ Found {len(rank_files)} ranking files")

all_rankings = []
for f in rank_files:
    df_rank = pd.read_csv(f)
    dataset_id = Path(f).parent.parent.name
    df_rank['dataset_id'] = dataset_id
    # Extract folder (astro, climate_awnd, etc.)
    data_dir = Path('data')
    for json_file in data_dir.glob('*/*.json'):
        if json_file.stem == dataset_id:
            df_rank['folder'] = json_file.parent.name
            break
    all_rankings.append(df_rank)

df_rankings = pd.concat(all_rankings, ignore_index=True)
print(f"✓ Loaded {len(df_rankings)} rows of ranking data")

# Merge with dataset characteristics
df_combined = df_rankings.merge(df_datasets, on='dataset_id', how='left')

# Get ALL column names to exclude (both from rankings and datasets)
exclude_cols = ['algorithm', 'dataset_id', 'folder', 'n_points', 
                'spikiness', 'r_value', 'p_value', 'has_trend', 
                'trend_direction', 'has_periodicity', 'period',
                'volatility', 'noise_ratio', 'cv', 'upward_trend',
                'downward_trend', 'periodic']

# Get metric columns (only numeric ranking columns)
metric_cols = [col for col in df_combined.columns 
               if col not in exclude_cols and df_combined[col].dtype in ['float64', 'int64']]

print(f"✓ Analyzing {len(metric_cols)} metrics")
print(f"✓ Analyzing {df_combined['algorithm'].nunique()} algorithms")

# ============================================================================
# 1. OVERALL ALGORITHM PERFORMANCE (ALL METRICS)
# ============================================================================
print("\n" + "=" * 70)
print("OVERALL ALGORITHM RANKING (Average across all metrics)")
print("=" * 70)

overall_ranks = df_combined.groupby('algorithm')[metric_cols].mean().mean(axis=1).sort_values()

for rank, (algo, score) in enumerate(overall_ranks.items(), 1):
    print(f"{rank:2d}. {algo:30s} {score:5.2f}")

# ============================================================================
# 2. FIND ALGORITHM SPECIALIZATIONS
# ============================================================================
print("\n" + "=" * 70)
print("ALGORITHM SPECIALIZATIONS (Best at specific metrics)")
print("=" * 70)

# For each algorithm, find where it ranks in top 3
specializations = {}
for metric in metric_cols:
    metric_ranks = df_combined.groupby('algorithm')[metric].mean().sort_values()
    top3 = metric_ranks.head(3)
    
    for rank, (algo, score) in enumerate(top3.items(), 1):
        if algo not in specializations:
            specializations[algo] = []
        specializations[algo].append({
            'metric': metric,
            'rank': rank,
            'score': score
        })

# Show specializations for ASAP, FPCS, M4, TDA
focus_algos = ['asap_aggregator', 'fpcs_downsample', 'm4_downsample', 'tda_downsample']

for algo in focus_algos:
    if algo in specializations:
        print(f"\n{algo.upper()}:")
        specs = specializations[algo]
        if specs:
            # Sort by rank then score
            specs.sort(key=lambda x: (x['rank'], x['score']))
            for s in specs[:5]:  # Show top 5 specializations
                print(f"  {s['rank']}{['st','nd','rd'][s['rank']-1] if s['rank'] <= 3 else 'th'} place in {s['metric']}: {s['score']:.2f}")
        else:
            print(f"  No top-3 rankings found")
    else:
        print(f"\n{algo.upper()}: Not in dataset")

# ============================================================================
# 3. PATTERN-BASED PERFORMANCE FOR ALL ALGORITHMS
# ============================================================================
print("\n" + "=" * 70)
print("ALGORITHM PERFORMANCE BY PATTERN (ALL ALGORITHMS)")
print("=" * 70)

patterns = {
    'Very Large (>2000 points)': df_datasets[df_datasets['n_points'] > 2000]['dataset_id'].tolist(),
    'High Spikiness (>5% peaks)': df_datasets[df_datasets['spikiness'] > 5]['dataset_id'].tolist(),
    'Clear Upward Trend (r>0.5)': df_datasets[df_datasets['r_value'] > 0.5]['dataset_id'].tolist(),
    'Strong Periodicity': df_datasets[df_datasets['has_periodicity'] == True]['dataset_id'].tolist(),
    'High Volatility (top 25%)': df_datasets.nlargest(20, 'volatility')['dataset_id'].tolist(),
    'High Noise (top 25%)': df_datasets.nlargest(20, 'noise_ratio')['dataset_id'].tolist(),
}

# Compute performance for each pattern
pattern_results = {}
for pattern_name, dataset_list in patterns.items():
    cat_data = df_combined[df_combined['dataset_id'].isin(dataset_list)]
    if len(cat_data) > 0:
        algo_ranks = cat_data.groupby('algorithm')[metric_cols].mean().mean(axis=1).sort_values()
        pattern_results[pattern_name] = algo_ranks

# Show full rankings for each pattern
for pattern_name, algo_ranks in pattern_results.items():
    print(f"\n{pattern_name}:")
    print(f"  Datasets: {len(patterns[pattern_name])}")
    print(f"  Top 10 algorithms:")
    for rank, (algo, score) in enumerate(algo_ranks.head(10).items(), 1):
        marker = "  ★" if algo in focus_algos else "   "
        print(f"  {marker} {rank:2d}. {algo:30s} {score:5.2f}")

# ============================================================================
# 4. METRIC CATEGORY ANALYSIS
# ============================================================================
print("\n" + "=" * 70)
print("ALGORITHM PERFORMANCE BY METRIC CATEGORY")
print("=" * 70)

metric_categories = {
    'Level Features': [c for c in metric_cols if 'level' in c or 'mean' in c],
    'Shape Features': [c for c in metric_cols if any(x in c for x in ['extrema', 'regimes', 'change_points', 'spikes'])],
    'Derivative Features': [c for c in metric_cols if any(x in c for x in ['slope', 'curvature', 'roughness'])],
    'Frequency Features': [c for c in metric_cols if any(x in c for x in ['trend', 'noise', 'periodicity'])],
    'Statistical Features': [c for c in metric_cols if 'regression' in c],
}

for cat_name, cat_metrics in metric_categories.items():
    if cat_metrics:
        cat_ranks = df_combined.groupby('algorithm')[cat_metrics].mean().mean(axis=1).sort_values()
        print(f"\n{cat_name}:")
        print(f"  Top 10 algorithms:")
        for rank, (algo, score) in enumerate(cat_ranks.head(10).items(), 1):
            marker = "  ★" if algo in focus_algos else "   "
            print(f"  {marker} {rank:2d}. {algo:30s} {score:5.2f}")

# ============================================================================
# 5. VISUALIZATION: COMPLETE HEATMAP
# ============================================================================
print("\n" + "=" * 70)
print("GENERATING VISUALIZATIONS")
print("=" * 70)

# Create heatmap of ALL algorithms by ALL patterns
fig, ax = plt.subplots(figsize=(16, 10))

# Prepare data for heatmap
heatmap_data = []
for pattern_name, algo_ranks in pattern_results.items():
    heatmap_data.append(algo_ranks)

df_heatmap = pd.DataFrame(heatmap_data, 
                          index=list(pattern_results.keys())).T

# Sort algorithms by overall performance
df_heatmap = df_heatmap.loc[overall_ranks.index]

# Create heatmap
sns.heatmap(df_heatmap, annot=True, fmt='.2f', cmap='RdYlGn_r',
            center=10, vmin=1, vmax=19, cbar_kws={'label': 'Average Rank'},
            ax=ax, linewidths=0.5)

ax.set_title('Complete Algorithm Performance by Dataset Pattern\n(Lower is better)', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_xlabel('Dataset Pattern', fontsize=12, fontweight='bold')
ax.set_ylabel('Algorithm', fontsize=12, fontweight='bold')

# Highlight focus algorithms
for i, algo in enumerate(df_heatmap.index):
    if algo in focus_algos:
        ax.get_yticklabels()[i].set_weight('bold')
        ax.get_yticklabels()[i].set_color('red')

plt.tight_layout()
out_path = Path('plots/insights/11_complete_algorithm_heatmap.png')
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {out_path}")

# ============================================================================
# 6. VISUALIZATION: METRIC CATEGORY PERFORMANCE
# ============================================================================
fig, ax = plt.subplots(figsize=(14, 10))

# Prepare data
cat_heatmap_data = []
for cat_name, cat_metrics in metric_categories.items():
    if cat_metrics:
        cat_ranks = df_combined.groupby('algorithm')[cat_metrics].mean().mean(axis=1)
        cat_heatmap_data.append(cat_ranks)

df_cat_heatmap = pd.DataFrame(cat_heatmap_data, 
                              index=list(metric_categories.keys())).T
df_cat_heatmap = df_cat_heatmap.loc[overall_ranks.index]

sns.heatmap(df_cat_heatmap, annot=True, fmt='.2f', cmap='RdYlGn_r',
            center=10, vmin=1, vmax=19, cbar_kws={'label': 'Average Rank'},
            ax=ax, linewidths=0.5)

ax.set_title('Algorithm Performance by Metric Category\n(Lower is better)', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_xlabel('Metric Category', fontsize=12, fontweight='bold')
ax.set_ylabel('Algorithm', fontsize=12, fontweight='bold')

# Highlight focus algorithms
for i, algo in enumerate(df_cat_heatmap.index):
    if algo in focus_algos:
        ax.get_yticklabels()[i].set_weight('bold')
        ax.get_yticklabels()[i].set_color('red')

plt.tight_layout()
out_path = Path('plots/insights/12_metric_category_heatmap.png')
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {out_path}")

# ============================================================================
# 7. EXPORT COMPLETE RANKINGS
# ============================================================================
print("\n" + "=" * 70)
print("EXPORTING COMPLETE ANALYSIS")
print("=" * 70)

# Export pattern rankings
pattern_df = df_heatmap.reset_index()
pattern_df.columns.name = None
pattern_df = pattern_df.rename(columns={'index': 'algorithm'})
out_csv = Path('plots/insights/complete_pattern_rankings.csv')
pattern_df.to_csv(out_csv, index=False)
print(f"✓ Saved: {out_csv}")

# Export metric category rankings
cat_df = df_cat_heatmap.reset_index()
cat_df.columns.name = None
cat_df = cat_df.rename(columns={'index': 'algorithm'})
out_csv = Path('plots/insights/metric_category_rankings.csv')
cat_df.to_csv(out_csv, index=False)
print(f"✓ Saved: {out_csv}")

# Export specializations
spec_records = []
for algo, specs in specializations.items():
    for s in specs:
        spec_records.append({
            'algorithm': algo,
            'metric': s['metric'],
            'rank': s['rank'],
            'score': s['score']
        })

spec_df = pd.DataFrame(spec_records)
spec_df = spec_df.sort_values(['algorithm', 'rank', 'score'])
out_csv = Path('plots/insights/algorithm_specializations.csv')
spec_df.to_csv(out_csv, index=False)
print(f"✓ Saved: {out_csv}")

print("\n" + "=" * 70)
print("✅ COMPLETE ANALYSIS DONE!")
print("=" * 70)
print("\nKey findings for ASAP, FPCS, M4, TDA:")
print("Check the visualizations and CSVs for detailed rankings")
