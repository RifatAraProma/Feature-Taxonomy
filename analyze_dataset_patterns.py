"""
Analyze dataset patterns and algorithm performance by data characteristics.

This script:
1. Loads all dataset files and computes characteristics
2. Categorizes datasets by patterns (spiky, trending, periodic, large, etc.)
3. Analyzes which algorithms perform best for each pattern
4. Generates visualizations showing algorithm recommendations by data type
"""

import json
import glob
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats, signal
from collections import defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")
plt.rcParams['figure.facecolor'] = 'white'

# =====================================================================
# STEP 1: Load all datasets and compute characteristics
# =====================================================================

print("=" * 70)
print("DATASET PATTERN ANALYSIS")
print("=" * 70)

data_dir = Path('data')
dataset_files = list(data_dir.glob('*/*.json'))

print(f"\n📊 Found {len(dataset_files)} dataset files")

dataset_info = []

for filepath in dataset_files:
    with open(filepath) as f:
        data = json.load(f)
    
    # Extract dataset_id from filename
    dataset_id = filepath.stem  # e.g., "stock_aapl_price"
    
    # Handle both formats: direct array or {id, y} object
    if isinstance(data, list):
        y = np.array(data)
    else:
        y = np.array(data.get('y', data))
    n = len(y)
    
    # Compute characteristics
    
    # 1. Size
    size_category = 'large' if n > 2000 else 'medium' if n > 500 else 'small'
    
    # 2. Spikiness (using coefficient of variation and peak prominence)
    cv = np.std(y) / (np.abs(np.mean(y)) + 1e-10)
    peaks, properties = signal.find_peaks(y, prominence=np.std(y) * 0.5)
    spikiness = len(peaks) / n * 100  # percentage of points that are peaks
    
    # 3. Trend (linear regression slope significance)
    x = np.arange(n)
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    has_trend = abs(r_value) > 0.3 and p_value < 0.05
    trend_direction = 'upward' if slope > 0 else 'downward' if slope < 0 else 'flat'
    
    # 4. Periodicity (using autocorrelation)
    if n > 50:
        autocorr = np.correlate(y - np.mean(y), y - np.mean(y), mode='full')
        autocorr = autocorr[n-1:] / autocorr[n-1]
        
        # Find peaks in autocorrelation (excluding lag 0)
        ac_peaks, _ = signal.find_peaks(autocorr[1:min(n//2, 200)], height=0.3)
        has_periodicity = len(ac_peaks) > 0
        
        if len(ac_peaks) > 0:
            dominant_period = ac_peaks[0] + 1  # +1 because we excluded lag 0
        else:
            dominant_period = None
    else:
        has_periodicity = False
        dominant_period = None
    
    # 5. Volatility (using standard deviation of differences)
    volatility = np.std(np.diff(y))
    
    # 6. Noise level (high-frequency content)
    if n > 10:
        fft = np.fft.fft(y)
        freqs = np.fft.fftfreq(n)
        high_freq_power = np.sum(np.abs(fft[np.abs(freqs) > 0.3])**2)
        total_power = np.sum(np.abs(fft)**2)
        noise_ratio = high_freq_power / (total_power + 1e-10)
    else:
        noise_ratio = 0
    
    dataset_info.append({
        'dataset_id': dataset_id,
        'folder': filepath.parent.name,
        'n_points': n,
        'size_category': size_category,
        'mean': np.mean(y),
        'std': np.std(y),
        'cv': cv,
        'spikiness': spikiness,
        'has_trend': has_trend,
        'trend_direction': trend_direction,
        'r_value': r_value,
        'slope': slope,
        'has_periodicity': has_periodicity,
        'dominant_period': dominant_period,
        'volatility': volatility,
        'noise_ratio': noise_ratio
    })

df_datasets = pd.DataFrame(dataset_info)

print(f"\n✓ Analyzed {len(df_datasets)} datasets")

# =====================================================================
# STEP 2: Categorize datasets by interesting patterns
# =====================================================================

print("\n" + "=" * 70)
print("DATASET CATEGORIZATION")
print("=" * 70)

categories = {
    'Very Large (>2000 points)': df_datasets[df_datasets['n_points'] > 2000]['dataset_id'].tolist(),
    'High Spikiness (>5% peaks)': df_datasets[df_datasets['spikiness'] > 5]['dataset_id'].tolist(),
    'Clear Upward Trend (r>0.5)': df_datasets[(df_datasets['r_value'] > 0.5) & (df_datasets['has_trend'])]['dataset_id'].tolist(),
    'Clear Downward Trend (r<-0.5)': df_datasets[(df_datasets['r_value'] < -0.5) & (df_datasets['has_trend'])]['dataset_id'].tolist(),
    'Strong Periodicity': df_datasets[df_datasets['has_periodicity']]['dataset_id'].tolist(),
    'High Volatility (top 25%)': df_datasets[df_datasets['volatility'] > df_datasets['volatility'].quantile(0.75)]['dataset_id'].tolist(),
    'High Noise (top 25%)': df_datasets[df_datasets['noise_ratio'] > df_datasets['noise_ratio'].quantile(0.75)]['dataset_id'].tolist(),
}

for category, datasets in categories.items():
    print(f"\n{category}: {len(datasets)} datasets")
    if datasets:
        print(f"  Examples: {', '.join(datasets[:5])}")

# =====================================================================
# STEP 3: Load ranking data
# =====================================================================

print("\n" + "=" * 70)
print("LOADING ALGORITHM PERFORMANCE DATA")
print("=" * 70)

rank_files = glob.glob('plots/*/ranking/rankings_ranked.csv')
print(f"\nFound {len(rank_files)} ranking files")

all_rankings = []
for filepath in rank_files:
    dataset_id = Path(filepath).parent.parent.name
    df = pd.read_csv(filepath)
    df['dataset_id'] = dataset_id
    all_rankings.append(df)

if all_rankings:
    df_rankings = pd.concat(all_rankings, ignore_index=True)
    print(f"Loaded rankings: {len(df_rankings)} rows")
    
    # Merge with dataset characteristics
    df_combined = df_rankings.merge(df_datasets, on='dataset_id', how='left')
else:
    print("⚠ No ranking data found")
    df_combined = None

# =====================================================================
# STEP 4: Analyze algorithm performance by pattern
# =====================================================================

if df_combined is not None:
    print("\n" + "=" * 70)
    print("ALGORITHM PERFORMANCE BY DATASET PATTERN")
    print("=" * 70)
    
    # For each category, compute average rank per algorithm
    category_performance = {}
    
    # Get metric column names (exclude algorithm, dataset_id, and characteristics)
    metric_cols = [col for col in df_combined.columns 
                   if col not in ['algorithm', 'dataset_id', 'folder', 'n_points', 'size_category',
                                  'mean', 'std', 'cv', 'spikiness', 'has_trend', 'trend_direction',
                                  'r_value', 'slope', 'has_periodicity', 'dominant_period', 
                                  'volatility', 'noise_ratio']]
    
    for category_name, dataset_list in categories.items():
        if not dataset_list:
            continue
        
        # Filter to datasets in this category
        cat_data = df_combined[df_combined['dataset_id'].isin(dataset_list)]
        
        if len(cat_data) == 0:
            continue
        
        # Average rank across all metrics for each algorithm
        algo_ranks = cat_data.groupby('algorithm')[metric_cols].mean().mean(axis=1).sort_values()
        
        category_performance[category_name] = algo_ranks
        
        print(f"\n{category_name}:")
        print(f"  Datasets: {len(dataset_list)}")
        print(f"  Top 3 algorithms:")
        for i, (algo, rank) in enumerate(algo_ranks.head(3).items(), 1):
            print(f"    {i}. {algo}: {rank:.2f}")
    
    # =====================================================================
    # STEP 5: Create visualizations
    # =====================================================================
    
    print("\n" + "=" * 70)
    print("GENERATING VISUALIZATIONS")
    print("=" * 70)
    
    output_dir = Path('plots/insights')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Plot 1: Heatmap of algorithm performance by pattern
    if category_performance:
        # Create matrix: categories × algorithms (top 10 algorithms)
        all_algos = set()
        for ranks in category_performance.values():
            all_algos.update(ranks.index)
        
        # Get top 10 algorithms overall
        overall_ranks = df_combined.groupby('algorithm')[metric_cols].mean().mean(axis=1).sort_values()
        top_algos = overall_ranks.head(10).index.tolist()
        
        # Build matrix
        matrix_data = []
        categories_with_data = []
        for cat_name, algo_ranks in category_performance.items():
            if len(algo_ranks) > 0:
                row = [algo_ranks.get(algo, np.nan) for algo in top_algos]
                matrix_data.append(row)
                categories_with_data.append(cat_name)
        
        if matrix_data:
            heatmap_df = pd.DataFrame(matrix_data, 
                                     index=categories_with_data,
                                     columns=top_algos)
            
            fig, ax = plt.subplots(figsize=(14, 8))
            sns.heatmap(heatmap_df, annot=True, fmt='.1f', cmap='RdYlGn_r',
                       vmin=1, vmax=15, ax=ax, cbar_kws={'label': 'Average Rank'})
            ax.set_title('Algorithm Performance by Dataset Pattern\n(Lower rank = Better)', 
                        fontsize=14, fontweight='bold', pad=20)
            ax.set_xlabel('Algorithm', fontsize=12, fontweight='bold')
            ax.set_ylabel('Dataset Pattern', fontsize=12, fontweight='bold')
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)
            plt.tight_layout()
            plt.savefig(output_dir / '8_algorithm_by_pattern.png', dpi=300, bbox_inches='tight')
            print("\n✓ Saved: plots/insights/8_algorithm_by_pattern.png")
            plt.close()
    
    # Plot 2: Dataset characteristics distribution
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    # Plot distributions
    characteristics = [
        ('n_points', 'Number of Data Points', 'skyblue'),
        ('spikiness', 'Spikiness (%)', 'coral'),
        ('r_value', 'Trend Correlation (r)', 'lightgreen'),
        ('volatility', 'Volatility (σ of diffs)', 'plum'),
        ('noise_ratio', 'Noise Ratio', 'khaki'),
        ('cv', 'Coefficient of Variation', 'lightcoral')
    ]
    
    for idx, (col, title, color) in enumerate(characteristics):
        ax = axes[idx]
        ax.hist(df_datasets[col].dropna(), bins=30, color=color, alpha=0.7, edgecolor='black')
        ax.set_title(title, fontweight='bold')
        ax.set_xlabel('Value')
        ax.set_ylabel('Frequency')
        ax.grid(axis='y', alpha=0.3)
    
    plt.suptitle('Dataset Characteristics Distribution', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / '9_dataset_characteristics.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: plots/insights/9_dataset_characteristics.png")
    plt.close()
    
    # Plot 3: Recommended algorithm by pattern (winner only)
    if category_performance:
        fig, ax = plt.subplots(figsize=(12, 8))
        
        winners = []
        categories_list = []
        for cat_name, algo_ranks in category_performance.items():
            if len(algo_ranks) > 0:
                winner = algo_ranks.index[0]
                rank = algo_ranks.iloc[0]
                winners.append(f"{winner} ({rank:.2f})")
                categories_list.append(cat_name)
        
        y_pos = np.arange(len(categories_list))
        colors = plt.cm.Set3(np.linspace(0, 1, len(categories_list)))
        
        ax.barh(y_pos, [1] * len(categories_list), color=colors, alpha=0.8)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories_list)
        ax.set_xlim(0, 1.5)
        ax.set_xticks([])
        
        # Add algorithm names as annotations
        for i, winner in enumerate(winners):
            ax.text(0.5, i, winner, ha='center', va='center', 
                   fontweight='bold', fontsize=11)
        
        ax.set_title('Best Algorithm for Each Dataset Pattern\n(Algorithm name with average rank)',
                    fontsize=14, fontweight='bold', pad=20)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(output_dir / '10_best_algorithm_by_pattern.png', dpi=300, bbox_inches='tight')
        print("✓ Saved: plots/insights/10_best_algorithm_by_pattern.png")
        plt.close()
    
    # =====================================================================
    # STEP 6: Generate detailed report
    # =====================================================================
    
    print("\n" + "=" * 70)
    print("DETAILED FINDINGS REPORT")
    print("=" * 70)
    
    report_lines = []
    report_lines.append("# Dataset Pattern Analysis Report\n")
    report_lines.append("## Dataset Categorization\n")
    
    for category_name, dataset_list in categories.items():
        report_lines.append(f"\n### {category_name}\n")
        report_lines.append(f"**Count:** {len(dataset_list)} datasets\n")
        
        if dataset_list:
            report_lines.append(f"\n**Examples:**\n")
            for ds in dataset_list[:10]:
                ds_info = df_datasets[df_datasets['dataset_id'] == ds].iloc[0]
                report_lines.append(f"- `{ds}`: {ds_info['n_points']} points")
                if ds_info['has_trend']:
                    report_lines.append(f", {ds_info['trend_direction']} trend (r={ds_info['r_value']:.2f})")
                if ds_info['has_periodicity']:
                    report_lines.append(f", periodic (period≈{ds_info['dominant_period']})")
                report_lines.append(f"\n")
            
            if category_name in category_performance:
                algo_ranks = category_performance[category_name]
                report_lines.append(f"\n**Best Algorithms:**\n")
                for i, (algo, rank) in enumerate(algo_ranks.head(5).items(), 1):
                    report_lines.append(f"{i}. `{algo}`: rank {rank:.2f}\n")
    
    report_lines.append("\n## Key Insights\n\n")
    
    # Insight 1: Size-based performance
    large_datasets = df_datasets[df_datasets['size_category'] == 'large']['dataset_id'].tolist()
    if large_datasets and category_performance:
        large_data = df_combined[df_combined['dataset_id'].isin(large_datasets)]
        if len(large_data) > 0:
            large_ranks = large_data.groupby('algorithm')[metric_cols].mean().mean(axis=1).sort_values()
            report_lines.append(f"### For Large Datasets (>2000 points)\n")
            report_lines.append(f"The top 3 algorithms are:\n")
            for i, (algo, rank) in enumerate(large_ranks.head(3).items(), 1):
                report_lines.append(f"{i}. `{algo}` (rank: {rank:.2f})\n")
            report_lines.append("\n")
    
    # Insight 2: Periodic data
    periodic_datasets = df_datasets[df_datasets['has_periodicity']]['dataset_id'].tolist()
    if periodic_datasets and category_performance:
        periodic_data = df_combined[df_combined['dataset_id'].isin(periodic_datasets)]
        if len(periodic_data) > 0:
            periodic_ranks = periodic_data.groupby('algorithm')[metric_cols].mean().mean(axis=1).sort_values()
            report_lines.append(f"### For Periodic Data\n")
            report_lines.append(f"The top 3 algorithms are:\n")
            for i, (algo, rank) in enumerate(periodic_ranks.head(3).items(), 1):
                report_lines.append(f"{i}. `{algo}` (rank: {rank:.2f})\n")
            report_lines.append("\n")
    
    # Save report
    report_path = output_dir / 'DATASET_PATTERN_ANALYSIS.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.writelines(report_lines)
    print(f"\n✓ Saved detailed report: {report_path}")
    
    # Also save dataset characteristics CSV
    df_datasets.to_csv(output_dir / 'dataset_characteristics.csv', index=False)
    print(f"✓ Saved dataset characteristics: plots/insights/dataset_characteristics.csv")

print("\n" + "=" * 70)
print("✅ ANALYSIS COMPLETE!")
print("=" * 70)
print("\nGenerated outputs:")
print("  - plots/insights/8_algorithm_by_pattern.png")
print("  - plots/insights/9_dataset_characteristics.png")
print("  - plots/insights/10_best_algorithm_by_pattern.png")
print("  - plots/insights/DATASET_PATTERN_ANALYSIS.md")
print("  - plots/insights/dataset_characteristics.csv")
print("=" * 70)
