"""
Generate feature-specific performance visualization
Shows which algorithms excel at each feature category
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import glob
import os

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 10)
plt.rcParams['font.size'] = 10

# Load all ranking data
print("Loading ranking data from all datasets...")
rank_files = glob.glob('plots/*/ranking/rankings_ranked.csv')
print(f"Found {len(rank_files)} ranking files")

all_data = []
for f in rank_files:
    dataset = os.path.basename(os.path.dirname(os.path.dirname(f)))
    df = pd.read_csv(f)
    df['dataset'] = dataset
    all_data.append(df)

combined = pd.concat(all_data, ignore_index=True)
metric_cols = [col for col in combined.columns if col not in ['algorithm', 'dataset']]

print(f"Loaded data: {len(combined)} rows across {combined['dataset'].nunique()} datasets")
print(f"Metrics: {len(metric_cols)}")

# Define feature groups
feature_groups = {
    'Level Features': ['level_l1', 'level_linf', 'mean_delta'],
    'Extrema': ['extrema_bottleneck', 'extrema_wasserstein'],
    'Spikes/Dips': ['spikes_dips_bottleneck', 'spikes_dips_wasserstein'],
    'Regimes': ['regimes_delta', 'change_points_delta'],
    'Slope': ['slope_l1', 'slope_linf'],
    'Curvature': ['curvature_l1', 'curvature_linf'],
    'Roughness': ['roughness_delta'],
    'Trend': ['trend_l1', 'trend_linf'],
    'Noise': ['noise_l1', 'noise_linf', 'noise_auc_delta'],
    'Periodicity': ['periodicity_amplitude_delta', 'periodicity_num_periods_delta'],
    'Regression': ['regression_l1', 'regression_linf']
}

# Create output directory
os.makedirs('plots/insights', exist_ok=True)

print("\n[1/1] Creating feature-specific performance visualization...")

# Calculate top 3 algorithms for each feature category
feature_winners = []
for cat_name, metrics in feature_groups.items():
    available_metrics = [m for m in metrics if m in metric_cols]
    if available_metrics:
        # Average rank across all metrics in this category
        cat_ranks = combined.groupby('algorithm')[available_metrics].mean().mean(axis=1).sort_values()
        
        # Get top 3
        top_3 = cat_ranks.head(3)
        for rank_pos, (algo, avg_rank) in enumerate(top_3.items(), 1):
            feature_winners.append({
                'Feature Category': cat_name,
                'Algorithm': algo.replace('_', ' ').title(),
                'Average Rank': avg_rank,
                'Position': rank_pos
            })

winners_df = pd.DataFrame(feature_winners)

# Create visualization
fig, axes = plt.subplots(2, 1, figsize=(16, 12), gridspec_kw={'height_ratios': [2, 1]})

# ============================================================================
# SUBPLOT 1: Horizontal bar chart showing top 3 per feature
# ============================================================================
ax1 = axes[0]

categories = list(feature_groups.keys())
y_positions = np.arange(len(categories))
bar_height = 0.25

# Color scheme for 1st, 2nd, 3rd
colors = ['#2ecc71', '#3498db', '#e67e22']  # Green, Blue, Orange

for pos in [1, 2, 3]:
    pos_data = winners_df[winners_df['Position'] == pos]
    
    ranks = []
    labels = []
    for cat in categories:
        cat_data = pos_data[pos_data['Feature Category'] == cat]
        if len(cat_data) > 0:
            ranks.append(cat_data['Average Rank'].values[0])
            labels.append(cat_data['Algorithm'].values[0])
        else:
            ranks.append(0)
            labels.append('')
    
    bars = ax1.barh(y_positions + (pos-2)*bar_height, ranks, bar_height, 
                     label=f'{["1st", "2nd", "3rd"][pos-1]} Best',
                     color=colors[pos-1], alpha=0.85, edgecolor='black', linewidth=0.5)
    
    # Add algorithm names inside or next to bars
    for bar, label, rank in zip(bars, labels, ranks):
        if rank > 0:
            # Place text inside bar if it's wide enough, otherwise outside
            text_x = rank / 2 if rank > 3 else rank + 0.3
            text_color = 'white' if rank > 3 else 'black'
            ax1.text(text_x, bar.get_y() + bar.get_height()/2, 
                    label.split()[0][:10],  # First word, max 10 chars
                    ha='left' if rank <= 3 else 'center', 
                    va='center', fontsize=8, fontweight='bold',
                    color=text_color)

ax1.set_yticks(y_positions)
ax1.set_yticklabels(categories, fontsize=11, fontweight='bold')
ax1.set_xlabel('Average Rank (Lower = Better)', fontsize=12, fontweight='bold')
ax1.set_title('Top 3 Algorithms by Feature Category\n(Lower rank indicates better feature preservation)', 
              fontsize=14, fontweight='bold', pad=20)
ax1.legend(loc='upper right', fontsize=11, framealpha=0.9)
ax1.set_xlim(0, max([winners_df[winners_df['Position'] == 1]['Average Rank'].max() * 1.2, 10]))
ax1.grid(axis='x', alpha=0.3)
ax1.invert_yaxis()

# ============================================================================
# SUBPLOT 2: Summary table showing winners
# ============================================================================
ax2 = axes[1]
ax2.axis('tight')
ax2.axis('off')

# Create table data
table_data = []
for cat in categories:
    row = [cat]
    for pos in [1, 2, 3]:
        pos_data = winners_df[(winners_df['Feature Category'] == cat) & 
                              (winners_df['Position'] == pos)]
        if len(pos_data) > 0:
            algo = pos_data['Algorithm'].values[0]
            rank = pos_data['Average Rank'].values[0]
            row.append(f"{algo}\n({rank:.2f})")
        else:
            row.append('')
    table_data.append(row)

# Create table
table = ax2.table(cellText=table_data,
                  colLabels=['Feature Category', '🥇 1st Place', '🥈 2nd Place', '🥉 3rd Place'],
                  cellLoc='left',
                  loc='center',
                  colWidths=[0.25, 0.25, 0.25, 0.25])

table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 2.5)

# Style header
for i in range(4):
    cell = table[(0, i)]
    cell.set_facecolor('#34495e')
    cell.set_text_props(weight='bold', color='white', fontsize=10)

# Color code rows
row_colors = ['#ecf0f1', '#ffffff']
for i, row in enumerate(table_data, 1):
    for j in range(4):
        cell = table[(i, j)]
        cell.set_facecolor(row_colors[i % 2])
        if j > 0:  # Algorithm cells
            cell.set_text_props(fontsize=8)

ax2.set_title('Algorithm Rankings by Feature Category\n(Algorithm name with average rank)', 
              fontsize=12, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('plots/insights/6_feature_category_winners.png', dpi=300, bbox_inches='tight')
print("  ✓ Saved: plots/insights/6_feature_category_winners.png")
plt.close()

# ============================================================================
# Create a second visualization: Feature category difficulty
# ============================================================================
print("[2/2] Creating feature category difficulty analysis...")

fig, ax = plt.subplots(figsize=(14, 8))

# Calculate statistics for each feature category
category_stats = []
for cat_name, metrics in feature_groups.items():
    available_metrics = [m for m in metrics if m in metric_cols]
    if available_metrics:
        # Get all ranks for this category
        cat_ranks = combined[available_metrics].values.flatten()
        
        category_stats.append({
            'Category': cat_name,
            'Mean Rank': np.mean(cat_ranks),
            'Std Dev': np.std(cat_ranks),
            'Best (Min)': np.min(cat_ranks),
            'Worst (Max)': np.max(cat_ranks),
            'Median': np.median(cat_ranks)
        })

stats_df = pd.DataFrame(category_stats).sort_values('Mean Rank')

# Create grouped bar chart
x = np.arange(len(stats_df))
width = 0.35

bars1 = ax.bar(x - width/2, stats_df['Mean Rank'], width, 
               label='Mean Rank', color='#3498db', alpha=0.8, edgecolor='black')
bars2 = ax.bar(x + width/2, stats_df['Std Dev'], width, 
               label='Std Dev (Algorithm Variability)', color='#e74c3c', alpha=0.8, edgecolor='black')

# Add value labels on bars
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=8, fontweight='bold')

ax.set_xlabel('Feature Category', fontsize=12, fontweight='bold')
ax.set_ylabel('Rank Value', fontsize=12, fontweight='bold')
ax.set_title('Feature Category Difficulty & Algorithm Variability\n' + 
             '(Mean rank = overall difficulty, Std Dev = how much algorithms differ)',
             fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(stats_df['Category'], rotation=45, ha='right', fontsize=10)
ax.legend(fontsize=11)
ax.grid(axis='y', alpha=0.3)

# Add interpretation text
textstr = ('Higher Mean Rank = Harder to preserve (all algorithms struggle)\n' +
           'Higher Std Dev = Algorithm choice matters more')
ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=9,
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('plots/insights/7_feature_difficulty.png', dpi=300, bbox_inches='tight')
print("  ✓ Saved: plots/insights/7_feature_difficulty.png")
plt.close()

# ============================================================================
# Print summary statistics
# ============================================================================
print("\n" + "="*70)
print("FEATURE CATEGORY WINNERS SUMMARY")
print("="*70)

for cat in categories:
    print(f"\n{cat}:")
    cat_data = winners_df[winners_df['Feature Category'] == cat].sort_values('Position')
    for _, row in cat_data.iterrows():
        medal = ['🥇', '🥈', '🥉'][row['Position']-1]
        print(f"  {medal} {row['Algorithm']}: {row['Average Rank']:.2f}")

print("\n" + "="*70)
print("FEATURE DIFFICULTY RANKING")
print("="*70)
print(f"{'Category':<20} {'Mean Rank':<12} {'Std Dev':<12} {'Interpretation'}")
print("-"*70)

for _, row in stats_df.iterrows():
    difficulty = "Easy" if row['Mean Rank'] < 8 else "Medium" if row['Mean Rank'] < 12 else "Hard"
    variability = "Low" if row['Std Dev'] < 4 else "Medium" if row['Std Dev'] < 5 else "High"
    print(f"{row['Category']:<20} {row['Mean Rank']:<12.2f} {row['Std Dev']:<12.2f} {difficulty}, {variability} variance")

print("\n" + "="*70)
print("✅ FEATURE PERFORMANCE VISUALIZATIONS COMPLETE!")
print("="*70)
print(f"\nGenerated 2 additional plots in: plots/insights/")
print("  6. Feature Category Winners (Top 3 per category + summary table)")
print("  7. Feature Difficulty Analysis (Mean rank + algorithm variability)")
print("\n" + "="*70)
