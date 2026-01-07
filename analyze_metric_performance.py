"""
Analyze which algorithms preserve specific features well
and identify feature-specific strengths across algorithms
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

# Feature categories based on actual metric names in the data
FEATURE_CATEGORIES = {
    'Level': ['level_l1', 'level_linf'],
    'Shape - Extrema': ['extrema_bottleneck', 'extrema_wasserstein'],
    'Shape - Regimes': ['regimes_delta'],
    'Shape - Change Points': ['change_points_delta'],
    'Shape - Spikes/Dips': ['spikes_dips_bottleneck', 'spikes_dips_wasserstein'],
    'Derivative - Slope': ['slope_l1', 'slope_linf'],
    'Derivative - Curvature': ['curvature_l1', 'curvature_linf'],
    'Derivative - Roughness': ['roughness_delta'],
    'Frequency - Trend': ['trend_l1', 'trend_linf'],
    'Frequency - Noise': ['noise_auc_delta', 'noise_l1', 'noise_linf'],
    'Frequency - Periodicity': ['periodicity_amplitude_delta', 'periodicity_num_periods_delta'],
    'Statistics - Mean': ['mean_delta'],
    'Statistics - Regression': ['regression_l1', 'regression_linf']
}

# Flatten for lookup
METRIC_TO_CATEGORY = {}
for category, metrics in FEATURE_CATEGORIES.items():
    for metric in metrics:
        METRIC_TO_CATEGORY[metric] = category


def load_metric_grades():
    """Load per-metric grades"""
    print("📊 Loading metric-specific grades...")
    df = pd.read_csv('plots/fc_visualizations/dataset_algorithm_metric_grades.csv')
    print(f"   Loaded {len(df)} grade records")
    return df


def analyze_algorithm_by_feature_category(df):
    """
    For each algorithm, compute average grade by feature category
    Shows which algorithms excel at preserving specific feature types
    """
    print("\n📊 Analyzing algorithm performance by feature category...")
    
    # Add feature category
    df['category'] = df['metric'].map(METRIC_TO_CATEGORY)
    
    # Convert grades to numeric
    grade_map = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}
    df['grade_value'] = df['grade'].map(grade_map)
    
    # Group by algorithm and category
    avg_by_category = df.groupby(['algorithm', 'category'])['grade_value'].mean().unstack()
    
    # Sort by overall average
    avg_by_category['Overall'] = avg_by_category.mean(axis=1)
    avg_by_category = avg_by_category.sort_values('Overall', ascending=False)
    
    # Save
    output_path = Path('plots/fc_visualizations')
    csv_path = output_path / 'algorithm_performance_by_category.csv'
    avg_by_category.to_csv(csv_path)
    print(f"   ✅ Saved: {csv_path.name}")
    
    # Print top performers per category
    print("\n🏆 Top 3 Algorithms by Feature Category:")
    available_categories = [col for col in avg_by_category.columns if col != 'Overall']
    for category in available_categories:
        print(f"\n   {category}:")
        top3 = avg_by_category[category].sort_values(ascending=False).head(3)
        for i, (algo, gpa) in enumerate(top3.items(), 1):
            print(f"      {i}. {algo}: {gpa:.2f}")
    
    return avg_by_category


def analyze_metric_difficulty(df):
    """
    For each metric, compute average grade across all algorithms
    Shows which metrics are hardest/easiest to preserve
    """
    print("\n📊 Analyzing metric preservation difficulty...")
    
    # Convert grades to numeric
    grade_map = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}
    df['grade_value'] = df['grade'].map(grade_map)
    
    # Average grade per metric across all algorithms and datasets
    metric_avg = df.groupby('metric')['grade_value'].mean().sort_values(ascending=False)
    
    # Count grade distribution per metric
    metric_grades = df.groupby(['metric', 'grade']).size().unstack(fill_value=0)
    for grade in ['A', 'B', 'C', 'D', 'F']:
        if grade not in metric_grades.columns:
            metric_grades[grade] = 0
    metric_grades = metric_grades[['A', 'B', 'C', 'D', 'F']]
    metric_grades['avg_gpa'] = metric_avg
    metric_grades = metric_grades.sort_values('avg_gpa', ascending=False)
    
    # Save
    output_path = Path('plots/fc_visualizations')
    csv_path = output_path / 'metric_difficulty.csv'
    metric_grades.to_csv(csv_path)
    print(f"   ✅ Saved: {csv_path.name}")
    
    # Print easiest and hardest
    print("\n✅ Top 5 Easiest Metrics to Preserve:")
    for i, (metric, gpa) in enumerate(metric_avg.head(5).items(), 1):
        print(f"   {i}. {metric}: {gpa:.2f}")
    
    print("\n❌ Top 5 Hardest Metrics to Preserve:")
    for i, (metric, gpa) in enumerate(metric_avg.tail(5).items(), 1):
        print(f"   {i}. {metric}: {gpa:.2f}")
    
    return metric_grades


def create_algorithm_category_heatmap(avg_by_category, output_dir='plots/fc_visualizations'):
    """
    Heatmap showing algorithm performance across feature categories
    """
    print("\n📊 Creating algorithm × feature category heatmap...")
    
    # Drop 'Overall' column for visualization
    data = avg_by_category.drop('Overall', axis=1)
    
    # Create both versions
    for version in ['greyscale', 'colored']:
        fig, ax = plt.subplots(figsize=(12, 10))
        
        if version == 'greyscale':
            cmap = sns.color_palette(['#2d2d2d', '#525252', '#7a7a7a', '#a8a8a8', '#d6d6d6'], as_cmap=True)
        else:
            from matplotlib.colors import ListedColormap
            # Use gradient from red (0.0) to green (4.0)
            colors = ['#E53935', '#FF6F00', '#FFA726', '#66BB6A', '#2E7D32']
            cmap = ListedColormap(colors)
        
        sns.heatmap(
            data,
            ax=ax,
            cmap=cmap,
            vmin=0,
            vmax=4,
            cbar=False,
            linewidths=0.5,
            linecolor='white',
            annot=True,
            fmt='.2f',
            annot_kws={'fontsize': 14, 'fontweight': 'bold'}
        )
        
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_title('')
        ax.tick_params(labelsize=14)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
        
        plt.tight_layout()
        
        output_path = Path(output_dir)
        svg_path = output_path / f'algorithm_by_category_{version}.svg'
        png_path = output_path / f'algorithm_by_category_{version}.png'
        
        plt.savefig(svg_path, dpi=300, bbox_inches='tight')
        plt.savefig(png_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    print(f"   ✅ Created algorithm × category heatmaps")


def find_algorithm_specializations(df):
    """
    Find metrics where specific algorithms significantly outperform others
    """
    print("\n📊 Finding algorithm specializations...")
    
    # Convert grades to numeric
    grade_map = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}
    df['grade_value'] = df['grade'].map(grade_map)
    
    # For each metric, find average grade per algorithm
    metric_algo_avg = df.groupby(['metric', 'algorithm'])['grade_value'].mean().unstack()
    
    # Find metrics where an algorithm is >0.5 GPA points above average
    specializations = []
    
    for metric in metric_algo_avg.index:
        metric_avg = metric_algo_avg.loc[metric].mean()
        metric_std = metric_algo_avg.loc[metric].std()
        
        # Find algorithms significantly above average
        strong_algos = metric_algo_avg.loc[metric][metric_algo_avg.loc[metric] > metric_avg + 0.5]
        
        if len(strong_algos) > 0 and len(strong_algos) < len(metric_algo_avg.columns):  # Not if everyone is good
            for algo, gpa in strong_algos.items():
                specializations.append({
                    'metric': metric,
                    'algorithm': algo,
                    'gpa': gpa,
                    'metric_avg': metric_avg,
                    'advantage': gpa - metric_avg
                })
    
    spec_df = pd.DataFrame(specializations).sort_values('advantage', ascending=False)
    
    # Save
    output_path = Path('plots/fc_visualizations')
    csv_path = output_path / 'algorithm_specializations.csv'
    spec_df.to_csv(csv_path, index=False)
    print(f"   ✅ Saved: {csv_path.name}")
    
    # Print top specializations
    print("\n🎯 Top 10 Algorithm-Metric Specializations:")
    print("   (Where an algorithm significantly outperforms others on a specific metric)")
    for i, row in spec_df.head(10).iterrows():
        print(f"   {row['algorithm']} on {row['metric']}: {row['gpa']:.2f} (avg: {row['metric_avg']:.2f}, +{row['advantage']:.2f})")
    
    return spec_df


def compare_algorithm_types(df):
    """
    Compare transformers vs reducers vs aggregators
    """
    print("\n📊 Comparing algorithm types...")
    
    # Categorize algorithms
    transformers = ['gaussian_filter', 'mean_filter', 'median_filter', 'savitzky_golay_filter',
                   'butterworth_filter', 'chebyshev_filter', 'elliptical_filter', 'fft_cutoff_filter']
    reducers = ['lttb_downsample', 'm4_downsample', 'minmaxlttb_downsample', 'uniform_subsample']
    aggregators = ['asap_aggregator', 'bin_average_aggregator']
    
    def get_algo_type(algo):
        if algo in transformers:
            return 'Transformer'
        elif algo in reducers:
            return 'Reducer'
        elif algo in aggregators:
            return 'Aggregator'
        else:
            return 'Other'
    
    df['algo_type'] = df['algorithm'].apply(get_algo_type)
    
    # Convert grades to numeric
    grade_map = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}
    df['grade_value'] = df['grade'].map(grade_map)
    
    # Average by type and category
    df['category'] = df['metric'].map(METRIC_TO_CATEGORY)
    type_category_avg = df.groupby(['algo_type', 'category'])['grade_value'].mean().unstack()
    
    print("\n📊 Algorithm Type Performance by Feature Category:")
    print(type_category_avg.to_string())
    
    # Save
    output_path = Path('plots/fc_visualizations')
    csv_path = output_path / 'algorithm_type_comparison.csv'
    type_category_avg.to_csv(csv_path)
    print(f"\n   ✅ Saved: {csv_path.name}")
    
    return type_category_avg


def main():
    print("=" * 80)
    print("METRIC-SPECIFIC PERFORMANCE ANALYSIS")
    print("=" * 80)
    
    # Load data
    df = load_metric_grades()
    
    # Analysis 1: Algorithm performance by feature category
    avg_by_category = analyze_algorithm_by_feature_category(df)
    create_algorithm_category_heatmap(avg_by_category)
    
    # Analysis 2: Metric difficulty
    metric_difficulty = analyze_metric_difficulty(df)
    
    # Analysis 3: Algorithm specializations
    specializations = find_algorithm_specializations(df)
    
    # Analysis 4: Compare algorithm types
    type_comparison = compare_algorithm_types(df)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print("\nFiles created in plots/fc_visualizations:")
    print("  1. algorithm_performance_by_category.csv - GPA by feature category")
    print("  2. algorithm_by_category_greyscale.svg/png - Heatmap visualization")
    print("  3. algorithm_by_category_colored.svg/png - Heatmap visualization")
    print("  4. metric_difficulty.csv - Which metrics are hardest to preserve")
    print("  5. algorithm_specializations.csv - Algorithm-metric strengths")
    print("  6. algorithm_type_comparison.csv - Transformers vs Reducers vs Aggregators")
    print("=" * 80)


if __name__ == '__main__':
    main()
