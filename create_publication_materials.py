"""
Generate Publication-Ready Materials
Comprehensive algorithm × feature preservation analysis with all nuances
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import glob

# Set publication-quality style
sns.set_style('whitegrid')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10

print("=" * 80)
print("GENERATING PUBLICATION MATERIALS")
print("=" * 80)

# Load data
char_path = Path('plots/insights/dataset_characteristics.csv')
df_datasets = pd.read_csv(char_path)

rank_files = glob.glob('plots/*/ranking/rankings_ranked.csv')
all_rankings = []
for f in rank_files:
    df_rank = pd.read_csv(f)
    dataset_id = Path(f).parent.parent.name
    df_rank['dataset_id'] = dataset_id
    all_rankings.append(df_rank)

df_rankings = pd.concat(all_rankings, ignore_index=True)
df_combined = df_rankings.merge(df_datasets, on='dataset_id', how='left')

# Get metric columns
metric_cols = [col for col in df_combined.columns 
               if col not in ['algorithm', 'dataset_id', 'folder', 'n_points', 
                             'spikiness', 'r_value', 'p_value', 'has_trend', 
                             'trend_direction', 'has_periodicity', 'period',
                             'volatility', 'noise_ratio', 'cv', 'upward_trend',
                             'downward_trend', 'periodic']
               and df_combined[col].dtype in ['float64', 'int64']]

print(f"✓ Loaded {len(df_datasets)} datasets")
print(f"✓ Loaded {len(df_rankings)} ranking rows")
print(f"✓ Analyzing {len(metric_cols)} metrics")
print(f"✓ Analyzing {df_combined['algorithm'].nunique()} algorithms")

# ============================================================================
# 1. COMPREHENSIVE ALGORITHM × FEATURE TABLE
# ============================================================================
print("\n" + "=" * 80)
print("TABLE 1: Algorithm × Feature Category Performance")
print("=" * 80)

# Define feature categories
feature_categories = {
    'Level': ['level_l1', 'level_linf', 'mean_delta'],
    'Shape': ['extrema_bottleneck', 'extrema_wasserstein', 'spikes_dips_bottleneck', 
              'spikes_dips_wasserstein', 'change_points_delta', 'regimes_delta'],
    'Derivative': ['slope_l1', 'slope_linf', 'curvature_l1', 'curvature_linf', 'roughness_delta'],
    'Frequency': ['trend_l1', 'trend_linf', 'noise_l1', 'noise_linf', 'noise_auc_delta',
                  'periodicity_amplitude_delta', 'periodicity_num_periods_delta'],
    'Statistical': ['regression_l1', 'regression_linf']
}

# Compute average rank for each algorithm in each category
algo_category_ranks = {}
for algo in df_combined['algorithm'].unique():
    algo_data = df_combined[df_combined['algorithm'] == algo]
    algo_category_ranks[algo] = {}
    
    for cat_name, cat_metrics in feature_categories.items():
        # Filter to metrics that exist
        existing_metrics = [m for m in cat_metrics if m in metric_cols]
        if existing_metrics:
            avg_rank = algo_data[existing_metrics].mean().mean()
            algo_category_ranks[algo][cat_name] = avg_rank
        else:
            algo_category_ranks[algo][cat_name] = np.nan

# Create DataFrame
df_table1 = pd.DataFrame(algo_category_ranks).T
df_table1['Overall'] = df_combined.groupby('algorithm')[metric_cols].mean().mean(axis=1)

# Sort by overall performance
df_table1 = df_table1.sort_values('Overall')

# Add algorithm type column
algo_types = {
    'gaussian_filter': 'Transformer',
    'mean_filter': 'Transformer',
    'savitzky_golay_filter': 'Transformer',
    'median_filter': 'Transformer',
    'min_filter': 'Transformer',
    'max_filter': 'Transformer',
    'butterworth_filter': 'Transformer',
    'chebyshev_filter': 'Transformer',
    'elliptical_filter': 'Transformer',
    'fft_cutoff_filter': 'Transformer',
    'asap_aggregator': 'Aggregator',
    'bin_average_aggregator': 'Aggregator',
    'lttb_downsample': 'Reducer',
    'minmaxlttb_downsample': 'Reducer',
    'm4_downsample': 'Reducer',
    'uniform_subsample': 'Reducer',
    'rdp_downsample': 'Reducer',
    'fpcs_downsample': 'Reducer',
    'tda_downsample': 'Reducer'
}
df_table1.insert(0, 'Type', [algo_types.get(a, 'Unknown') for a in df_table1.index])

# Save CSV
out_csv = Path('plots/insights/TABLE1_algorithm_feature_performance.csv')
df_table1.to_csv(out_csv)
print(f"✓ Saved: {out_csv}")

# Create heatmap visualization
fig, ax = plt.subplots(figsize=(10, 12))

# Prepare data for heatmap (excluding Type and Overall columns)
heatmap_data = df_table1[['Level', 'Shape', 'Derivative', 'Frequency', 'Statistical']]

# Create heatmap
sns.heatmap(heatmap_data, annot=True, fmt='.2f', cmap='RdYlGn_r',
            center=10, vmin=1, vmax=19, cbar_kws={'label': 'Average Rank (lower=better)'},
            ax=ax, linewidths=0.5, cbar=True)

ax.set_title('Algorithm Performance by Feature Category\n(Rank: 1=Best, 19=Worst)', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_xlabel('Feature Category', fontsize=12, fontweight='bold')
ax.set_ylabel('Algorithm (sorted by overall performance)', fontsize=12, fontweight='bold')

# Color-code by algorithm type
for i, (idx, row) in enumerate(df_table1.iterrows()):
    if row['Type'] == 'Transformer':
        ax.get_yticklabels()[i].set_color('blue')
    elif row['Type'] == 'Aggregator':
        ax.get_yticklabels()[i].set_color('green')
    elif row['Type'] == 'Reducer':
        ax.get_yticklabels()[i].set_color('red')

plt.tight_layout()
out_path = Path('plots/insights/FIGURE1_algorithm_feature_heatmap.png')
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {out_path}")
plt.close()

# ============================================================================
# 2. PATTERN-SPECIFIC PERFORMANCE TABLE
# ============================================================================
print("\n" + "=" * 80)
print("TABLE 2: Algorithm Performance by Data Pattern")
print("=" * 80)

patterns = {
    'Large\n(>2000)': df_datasets[df_datasets['n_points'] > 2000]['dataset_id'].tolist(),
    'Spiky\n(>5%)': df_datasets[df_datasets['spikiness'] > 5]['dataset_id'].tolist(),
    'Trending\n(|r|>0.5)': df_datasets[abs(df_datasets['r_value']) > 0.5]['dataset_id'].tolist(),
    'Periodic': df_datasets[df_datasets['has_periodicity'] == True]['dataset_id'].tolist(),
    'Volatile\n(top 25%)': df_datasets.nlargest(20, 'volatility')['dataset_id'].tolist(),
    'Noisy\n(top 25%)': df_datasets.nlargest(20, 'noise_ratio')['dataset_id'].tolist(),
}

pattern_ranks = {}
for pattern_name, dataset_list in patterns.items():
    cat_data = df_combined[df_combined['dataset_id'].isin(dataset_list)]
    if len(cat_data) > 0:
        algo_ranks = cat_data.groupby('algorithm')[metric_cols].mean().mean(axis=1)
        pattern_ranks[pattern_name] = algo_ranks

df_table2 = pd.DataFrame(pattern_ranks)
df_table2['Overall'] = df_combined.groupby('algorithm')[metric_cols].mean().mean(axis=1)
df_table2 = df_table2.sort_values('Overall')
df_table2.insert(0, 'Type', [algo_types.get(a, 'Unknown') for a in df_table2.index])

# Save CSV
out_csv = Path('plots/insights/TABLE2_pattern_performance.csv')
df_table2.to_csv(out_csv)
print(f"✓ Saved: {out_csv}")

# Create visualization
fig, ax = plt.subplots(figsize=(12, 12))

# Prepare data (exclude Type and Overall)
heatmap_cols = [c for c in df_table2.columns if c not in ['Type', 'Overall']]
heatmap_data2 = df_table2[heatmap_cols]

sns.heatmap(heatmap_data2, annot=True, fmt='.2f', cmap='RdYlGn_r',
            center=10, vmin=1, vmax=19, cbar_kws={'label': 'Average Rank (lower=better)'},
            ax=ax, linewidths=0.5)

ax.set_title('Algorithm Performance by Dataset Pattern\n(Rank: 1=Best, 19=Worst)', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_xlabel('Dataset Pattern', fontsize=12, fontweight='bold')
ax.set_ylabel('Algorithm (sorted by overall performance)', fontsize=12, fontweight='bold')

# Color-code by type
for i, (idx, row) in enumerate(df_table2.iterrows()):
    if row['Type'] == 'Transformer':
        ax.get_yticklabels()[i].set_color('blue')
    elif row['Type'] == 'Aggregator':
        ax.get_yticklabels()[i].set_color('green')
    elif row['Type'] == 'Reducer':
        ax.get_yticklabels()[i].set_color('red')

plt.tight_layout()
out_path = Path('plots/insights/FIGURE2_pattern_performance_heatmap.png')
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {out_path}")
plt.close()

# ============================================================================
# 3. COMBINED VISUALIZATION: FEATURE × PATTERN INTERACTION
# ============================================================================
print("\n" + "=" * 80)
print("FIGURE 3: Top Algorithm Performance Across Dimensions")
print("=" * 80)

# For top 5 algorithms, show their performance across features and patterns
top5_algos = df_table1.nsmallest(5, 'Overall').index.tolist()

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Left: Feature categories
feature_data = df_table1.loc[top5_algos, ['Level', 'Shape', 'Derivative', 'Frequency', 'Statistical']]
feature_data.T.plot(kind='bar', ax=axes[0], width=0.8)
axes[0].set_title('Top 5 Algorithms: Performance by Feature Category', fontweight='bold', fontsize=12)
axes[0].set_xlabel('Feature Category', fontweight='bold')
axes[0].set_ylabel('Average Rank (lower=better)', fontweight='bold')
axes[0].legend(title='Algorithm', bbox_to_anchor=(1.05, 1), loc='upper left')
axes[0].grid(axis='y', alpha=0.3)
axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=45, ha='right')

# Right: Dataset patterns
pattern_data = df_table2.loc[top5_algos, heatmap_cols]
pattern_data.T.plot(kind='bar', ax=axes[1], width=0.8)
axes[1].set_title('Top 5 Algorithms: Performance by Dataset Pattern', fontweight='bold', fontsize=12)
axes[1].set_xlabel('Dataset Pattern', fontweight='bold')
axes[1].set_ylabel('Average Rank (lower=better)', fontweight='bold')
axes[1].legend(title='Algorithm', bbox_to_anchor=(1.05, 1), loc='upper left')
axes[1].grid(axis='y', alpha=0.3)
axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=45, ha='right')

plt.tight_layout()
out_path = Path('plots/insights/FIGURE3_top5_comparison.png')
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {out_path}")
plt.close()

# ============================================================================
# 4. ALGORITHM SPECIALIZATION RADAR CHART
# ============================================================================
print("\n" + "=" * 80)
print("FIGURE 4: Algorithm Specialization Profiles")
print("=" * 80)

# Select key algorithms to profile
profile_algos = ['gaussian_filter', 'mean_filter', 'savitzky_golay_filter', 
                 'median_filter', 'asap_aggregator', 'fpcs_downsample']

fig, axes = plt.subplots(2, 3, figsize=(16, 10), subplot_kw=dict(projection='polar'))
axes = axes.flatten()

categories = ['Level', 'Shape', 'Derivative', 'Frequency', 'Statistical']
num_vars = len(categories)
angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
angles += angles[:1]  # Complete the circle

for idx, algo in enumerate(profile_algos):
    ax = axes[idx]
    
    # Get values (invert so higher = better for visualization)
    values = [19 - df_table1.loc[algo, cat] for cat in categories]
    values += values[:1]  # Complete the circle
    
    # Plot
    ax.plot(angles, values, 'o-', linewidth=2, label=algo)
    ax.fill(angles, values, alpha=0.25)
    
    # Customize
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=8)
    ax.set_ylim(0, 18)
    ax.set_title(f'{algo}\n(Type: {algo_types.get(algo, "Unknown")})', 
                 fontweight='bold', size=10, pad=10)
    ax.grid(True)

plt.suptitle('Algorithm Specialization Profiles\n(Larger area = Better performance)', 
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
out_path = Path('plots/insights/FIGURE4_specialization_radar.png')
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {out_path}")
plt.close()

# ============================================================================
# 5. PERFORMANCE GAP ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("TABLE 3: Performance Gaps and Niches")
print("=" * 80)

# For each algorithm, compute relative performance vs best (Gaussian)
best_algo = df_table1.index[0]  # First row (best overall)

gap_analysis = []
for algo in df_table1.index:
    algo_gaps = {
        'Algorithm': algo,
        'Type': algo_types.get(algo, 'Unknown'),
        'Overall_Rank': df_table1.loc[algo, 'Overall'],
        'Overall_Gap': df_table1.loc[algo, 'Overall'] - df_table1.loc[best_algo, 'Overall']
    }
    
    # Find best category (smallest gap)
    category_gaps = {}
    for cat in categories:
        gap = df_table1.loc[algo, cat] - df_table1.loc[best_algo, cat]
        category_gaps[cat] = gap
    
    best_cat = min(category_gaps, key=category_gaps.get)
    worst_cat = max(category_gaps, key=category_gaps.get)
    
    algo_gaps['Best_Category'] = best_cat
    algo_gaps['Best_Gap'] = category_gaps[best_cat]
    algo_gaps['Worst_Category'] = worst_cat
    algo_gaps['Worst_Gap'] = category_gaps[worst_cat]
    algo_gaps['Specialization_Range'] = category_gaps[worst_cat] - category_gaps[best_cat]
    
    gap_analysis.append(algo_gaps)

df_table3 = pd.DataFrame(gap_analysis)
df_table3 = df_table3.sort_values('Overall_Rank')

out_csv = Path('plots/insights/TABLE3_performance_gaps.csv')
df_table3.to_csv(out_csv, index=False)
print(f"✓ Saved: {out_csv}")

# Visualize gaps
fig, ax = plt.subplots(figsize=(14, 8))

x = np.arange(len(df_table3))
width = 0.35

bars1 = ax.bar(x - width/2, df_table3['Best_Gap'], width, label='Best Category Gap', color='green', alpha=0.7)
bars2 = ax.bar(x + width/2, df_table3['Worst_Gap'], width, label='Worst Category Gap', color='red', alpha=0.7)

ax.set_xlabel('Algorithm', fontweight='bold')
ax.set_ylabel('Performance Gap vs Gaussian Filter (lower=better)', fontweight='bold')
ax.set_title('Algorithm Performance Gaps Relative to Best (Gaussian Filter)', fontweight='bold', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(df_table3['Algorithm'], rotation=45, ha='right')
ax.legend()
ax.grid(axis='y', alpha=0.3)
ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

plt.tight_layout()
out_path = Path('plots/insights/FIGURE5_performance_gaps.png')
plt.savefig(out_path, dpi=300, bbox_inches='tight')
print(f"✓ Saved: {out_path}")
plt.close()

print("\n" + "=" * 80)
print("✅ ALL PUBLICATION MATERIALS GENERATED!")
print("=" * 80)
print("\nGenerated files:")
print("  Tables:")
print("    - TABLE1_algorithm_feature_performance.csv")
print("    - TABLE2_pattern_performance.csv")
print("    - TABLE3_performance_gaps.csv")
print("  Figures:")
print("    - FIGURE1_algorithm_feature_heatmap.png")
print("    - FIGURE2_pattern_performance_heatmap.png")
print("    - FIGURE3_top5_comparison.png")
print("    - FIGURE4_specialization_radar.png")
print("    - FIGURE5_performance_gaps.png")
