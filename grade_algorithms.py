"""
Create Graded Performance Visualization
Assign letter grades (A/B/C/D/F) based on rating percentages
Simplifies Dataset × Algorithm × Feature complexity into readable heatmaps
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np
import sys
sys.path.insert(0, 'server')
from algorithm_names import get_algorithm_name

def load_detailed_fc_scores():
    """Load FC scores from all datasets"""
    from server.util import list_datasets
    
    datasets = list_datasets()
    all_data = []
    
    print(f"\n📊 Loading detailed FC scores from {len(datasets)} datasets...")
    
    for i, dataset_info in enumerate(datasets, 1):
        # list_datasets returns dicts, extract the 'id' field
        dataset = dataset_info['id'] if isinstance(dataset_info, dict) else dataset_info
        fc_file = Path('plots') / dataset / 'ranking' / 'fc_scores_all.csv'
        if not fc_file.exists():
            continue
            
        df = pd.read_csv(fc_file)
        df['dataset'] = dataset
        all_data.append(df)
        
        if i % 10 == 0:
            print(f"   Loaded {i}/{len(datasets)} datasets...")
    
    print(f"   ✅ Loaded {len(all_data)} datasets successfully")
    
    return pd.concat(all_data, ignore_index=True)


def categorize_fc_scores(combined_df):
    """Add rating categories based on dataset-metric-specific quartiles"""
    print("\nCategorizing FC scores into ratings using per-metric quartiles...")
    
    # Cache quartiles per dataset to avoid repeated file reads
    quartiles_cache = {}
    
    def get_rating(row):
        dataset = row['dataset']
        metric = row['metric']
        fc_score = row['fc_score']
        
        # Load quartiles for this dataset if not cached
        if dataset not in quartiles_cache:
            quartiles_file = Path('plots') / dataset / 'ranking' / 'fc_scores_quartiles.csv'
            if not quartiles_file.exists():
                return 'unknown'
            quartiles_df = pd.read_csv(quartiles_file)
            # Create lookup: {metric: {q25, q50, q75}}
            quartiles_cache[dataset] = quartiles_df.set_index('metric')[['q25', 'q50', 'q75']].to_dict('index')
        
        # Get metric-specific quartiles
        if metric not in quartiles_cache[dataset]:
            return 'unknown'
        
        q = quartiles_cache[dataset][metric]
        if fc_score > q['q75']:
            return 'excellent'
        elif fc_score > q['q50']:
            return 'good'
        elif fc_score > q['q25']:
            return 'fair'
        else:
            return 'poor'
    
    combined_df['rating'] = combined_df.apply(get_rating, axis=1)
    
    return combined_df


def compute_grade_per_dataset_algorithm_metric(df):
    """
    Compute letter grade for each Dataset × Algorithm × Metric combination
    Based on performance for that specific metric only
    
    GPA-Style Grading with Equal Ranges (Rating Points: excellent=4, good=3, fair=2, poor=1):
    Range: 4.0 - 1.0 = 3.0 points, divided equally into 5 grades = 0.6 per grade
    - A: 3.4 - 4.0 (85-100%)
    - B: 2.8 - 3.4 (70-85%)
    - C: 2.2 - 2.8 (55-70%)
    - D: 1.6 - 2.2 (40-55%)
    - F: 1.0 - 1.6 (25-40%)
    """
    print("\n📊 Computing grades for Dataset × Algorithm × Metric combinations...")
    
    # Group by dataset, algorithm, metric and count ratings
    grouped = df.groupby(['dataset', 'algorithm', 'metric', 'rating']).size().unstack(fill_value=0)
    
    # Ensure all rating columns exist
    for rating in ['excellent', 'good', 'fair', 'poor']:
        if rating not in grouped.columns:
            grouped[rating] = 0
    
    # Calculate GPA-style score
    rating_points = {'excellent': 4, 'good': 3, 'fair': 2, 'poor': 1}
    total = grouped.sum(axis=1)
    
    # Weighted average: (excellent*4 + good*3 + fair*2 + poor*1) / total
    scores = (grouped['excellent'] * 4 + grouped['good'] * 3 + 
              grouped['fair'] * 2 + grouped['poor'] * 1) / total
    
    # Assign letter grades based on equal-range GPA scale
    def assign_grade(score):
        if score >= 3.4:
            return 'A'
        elif score >= 2.8:
            return 'B'
        elif score >= 2.2:
            return 'C'
        elif score >= 1.6:
            return 'D'
        else:
            return 'F'
    
    grades_df = grouped.copy()
    grades_df['score'] = scores
    grades_df['grade'] = scores.apply(assign_grade)
    grades_df = grades_df.reset_index()
    
    print(f"   ✅ Computed {len(grades_df)} grades")
    
    return grades_df


def compute_grade_per_dataset_algorithm(df):
    """
    Compute letter grade for each Dataset × Algorithm combination
    Based on average performance across all metrics
    
    GPA-Style Grading with Equal Ranges (Rating Points: excellent=4, good=3, fair=2, poor=1):
    Range: 4.0 - 1.0 = 3.0 points, divided equally into 5 grades = 0.6 per grade
    - A: 3.4 - 4.0 (85-100%)
    - B: 2.8 - 3.4 (70-85%)
    - C: 2.2 - 2.8 (55-70%)
    - D: 1.6 - 2.2 (40-55%)
    - F: 1.0 - 1.6 (25-40%)
    """
    print("\n📊 Computing grades for Dataset × Algorithm combinations...")
    
    # Group by dataset, algorithm and count ratings across ALL metrics
    grouped = df.groupby(['dataset', 'algorithm', 'rating']).size().unstack(fill_value=0)
    
    # Ensure all rating columns exist
    for rating in ['excellent', 'good', 'fair', 'poor']:
        if rating not in grouped.columns:
            grouped[rating] = 0
    
    # Calculate GPA-style score
    total = grouped.sum(axis=1)
    scores = (grouped['excellent'] * 4 + grouped['good'] * 3 + 
              grouped['fair'] * 2 + grouped['poor'] * 1) / total
    
    # Assign letter grades based on equal-range GPA scale
    def assign_grade(score):
        if score >= 3.4:
            return 'A'
        elif score >= 2.8:
            return 'B'
        elif score >= 2.2:
            return 'C'
        elif score >= 1.6:
            return 'D'
        else:
            return 'F'
    
    grades_df = grouped.copy()
    grades_df['score'] = scores
    grades_df['grade'] = scores.apply(assign_grade)
    grades_df = grades_df.reset_index()
    
    print(f"   ✅ Computed {len(grades_df)} grades")
    
    return grades_df


def create_grade_heatmap(grades_df, output_dir='plots/fc_visualizations'):
    """
    Create a single heatmap: Algorithm × Dataset with letter grades (GREYSCALE)
    """
    print("\n📊 Creating greyscale grade heatmap...")
    
    # Apply display names to algorithms
    grades_df = grades_df.copy()
    grades_df['algorithm'] = grades_df['algorithm'].apply(get_algorithm_name)
    
    # Pivot for heatmap (swapped: algorithms on rows, datasets on columns)
    pivot = grades_df.pivot(index='algorithm', columns='dataset', values='grade')
    
    # Convert grades to numeric for color mapping
    grade_map = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
    pivot_numeric = pivot.applymap(lambda x: grade_map.get(x, 0))
    
    # Create figure
    fig, ax = plt.subplots(figsize=(40, 10))
    
    # Create heatmap with grey colormap (matching FC score distributions)
    cmap = sns.color_palette(['#2d2d2d', '#525252', '#7a7a7a', '#a8a8a8', '#d6d6d6'], as_cmap=True)
    
    sns.heatmap(
        pivot_numeric,
        ax=ax,
        cmap=cmap,
        vmin=1,
        vmax=5,
        cbar=False,  # No legend
        linewidths=0.5,
        linecolor='white',
        annot=pivot,  # Show letter grades
        fmt='',
        annot_kws={'fontsize': 16, 'fontweight': 'bold'}
    )
    
    # No titles or axis labels
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_title('')
    ax.tick_params(labelsize=22)
    
    # Dataset names at top
    ax.xaxis.tick_top()
    
    # Rotate labels
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='center')
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    
    plt.tight_layout()
    
    # Save
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    svg_path = output_path / 'algorithm_grades_by_dataset.svg'
    png_path = output_path / 'algorithm_grades_by_dataset.pdf'
    
    plt.savefig(svg_path, dpi=300, bbox_inches='tight')
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    
    print(f"   ✅ Saved: {svg_path.name}")
    
    plt.close()


def create_grade_heatmap_colored(grades_df, output_dir='plots/fc_visualizations'):
    """
    Create colored version using frontend color scheme:
    Excellent: #2E7D32 (dark green)
    Good: #66BB6A (light green)
    Fair: #FFA726 (orange)
    Poor: #E53935 (red)
    F: #9E9E9E (grey)
    """
    print("\n📊 Creating colored grade heatmap...")
    
    # Apply display names to algorithms
    grades_df = grades_df.copy()
    grades_df['algorithm'] = grades_df['algorithm'].apply(get_algorithm_name)
    
    # Pivot for heatmap (algorithms on rows, datasets on columns)
    pivot = grades_df.pivot(index='algorithm', columns='dataset', values='grade')
    
    # Convert grades to numeric for color mapping
    grade_map = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
    pivot_numeric = pivot.applymap(lambda x: grade_map.get(x, 0))
    
    # Create figure
    fig, ax = plt.subplots(figsize=(40, 10))
    
    # Use frontend color scheme
    # A (excellent) = dark green, B (good) = light green, C (fair) = orange, D = dark orange, F = red
    from matplotlib.colors import ListedColormap
    colors = ["#ebfada", '#c2e699','#78c679', '#31a354', '#006837']  # F, D, C, B, A
    cmap = ListedColormap(colors)
    
    sns.heatmap(
        pivot_numeric,
        ax=ax,
        cmap=cmap,
        vmin=1,
        vmax=5,
        cbar=False,  # No legend
        linewidths=0.5,
        linecolor='white',
        annot=pivot,  # Show letter grades
        fmt='',
        annot_kws={'fontsize': 16, 'fontweight': 'bold'}
    )
    
    # Manually adjust text colors for better contrast
    for text in ax.texts:
        grade = text.get_text()
        # Use white text for A and B (dark green), black for C, D, F (lighter greens)
        if grade in ['A', 'B']:
            text.set_color('white')
        else:
            text.set_color('black')
    
    # No titles or axis labels
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_title('')
    ax.tick_params(labelsize=16)
    
    # Dataset names at top
    ax.xaxis.tick_top()
    
    # Rotate labels
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='center')
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    
    plt.tight_layout()
    
    # Save
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    svg_path = output_path / 'algorithm_grades_by_dataset_green.svg'
    png_path = output_path / 'algorithm_grades_by_dataset_green.pdf'
    
    plt.savefig(svg_path, dpi=300, bbox_inches='tight')
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    
    print(f"   ✅ Saved: {svg_path.name}")
    
    plt.close()


def create_grade_distribution_bar(grades_df, output_dir='plots/fc_visualizations'):
    """
    Bar chart showing grade distribution for each algorithm
    """
    print("\n📊 Creating grade distribution bar chart...")
    
    # Apply display names to algorithms
    grades_df = grades_df.copy()
    grades_df['algorithm'] = grades_df['algorithm'].apply(get_algorithm_name)
    
    # Count grades per algorithm
    grade_counts = grades_df.groupby(['algorithm', 'grade']).size().unstack(fill_value=0)
    
    # Ensure all grades exist
    for grade in ['A', 'B', 'C', 'D', 'F']:
        if grade not in grade_counts.columns:
            grade_counts[grade] = 0
    
    # Reorder columns
    grade_counts = grade_counts[['A', 'B', 'C', 'D', 'F']]
    
    # Sort algorithms by number of A's + B's
    grade_counts['total_good'] = grade_counts['A'] + grade_counts['B']
    grade_counts = grade_counts.sort_values('total_good', ascending=False)
    grade_counts = grade_counts.drop('total_good', axis=1)
    
    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(14, 8))
    
    grade_counts.plot(
        kind='bar',
        stacked=True,
        ax=ax,
        color=['#006837', '#31a354', '#78c679', '#c2e699', "#ebfada"],
        width=0.8
    )
    
    ax.set_title('Algorithm Grade Distribution Across All Datasets', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Algorithm', fontsize=11, fontweight='bold')
    ax.set_ylabel('Number of Datasets', fontsize=11, fontweight='bold')
    ax.legend(title='Grade', loc='upper right', frameon=True)
    ax.tick_params(labelsize=9)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Save
    output_path = Path(output_dir)
    svg_path = output_path / 'algorithm_grade_distribution.svg'
    png_path = output_path / 'algorithm_grade_distribution.pdf'
    
    plt.savefig(svg_path, dpi=300, bbox_inches='tight')
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    
    print(f"   ✅ Saved: {svg_path.name}")
    
    plt.close()


def create_summary_table(grades_df, output_dir='plots/fc_visualizations'):
    """
    Create summary CSV with grade statistics
    """
    print("\n📊 Creating summary statistics...")
    
    # Apply display names to algorithms
    grades_df = grades_df.copy()
    grades_df['algorithm'] = grades_df['algorithm'].apply(get_algorithm_name)
    
    # Overall grade distribution
    overall = grades_df['grade'].value_counts().sort_index()
    
    # Grade distribution by algorithm
    by_algo = grades_df.groupby('algorithm')['grade'].value_counts().unstack(fill_value=0)
    for grade in ['A', 'B', 'C', 'D', 'F']:
        if grade not in by_algo.columns:
            by_algo[grade] = 0
    by_algo = by_algo[['A', 'B', 'C', 'D', 'F']]
    
    # Add GPA-style metric (A=4.0, B=3.0, C=2.0, D=1.0, F=0.0)
    grade_values = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}
    grades_df['grade_value'] = grades_df['grade'].map(grade_values)
    
    gpa = grades_df.groupby('algorithm')['grade_value'].mean().sort_values(ascending=False)
    by_algo['GPA'] = gpa
    
    # Sort by GPA
    by_algo = by_algo.sort_values('GPA', ascending=False)
    
    # Save
    output_path = Path(output_dir)
    csv_path = output_path / 'algorithm_grade_summary.csv'
    by_algo.to_csv(csv_path)
    
    print(f"   ✅ Saved: {csv_path.name}")
    
    # Print top performers
    print("\n📊 Top 5 Algorithms by GPA:")
    for i, (algo, row) in enumerate(by_algo.head(5).iterrows(), 1):
        print(f"   {i}. {algo}: GPA={row['GPA']:.2f} (A:{int(row['A'])}, B:{int(row['B'])}, C:{int(row['C'])}, D:{int(row['D'])}, F:{int(row['F'])})")
    
    return by_algo


def compute_average_grade_per_algorithm_metric(grades_df):
    """
    Compute average grade for each Algorithm × Metric combination across all datasets
    Returns a pivot table with algorithms as rows and metrics as columns
    """
    print("\n📊 Computing average grades per Algorithm × Metric...")
    
    # Apply display names to algorithms
    grades_df = grades_df.copy()
    grades_df['algorithm'] = grades_df['algorithm'].apply(get_algorithm_name)
    
    # Exclude noise_auc
    grades_df = grades_df[grades_df['metric'] != 'noise_auc']
    
    # Convert grades to numeric
    grade_map = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}
    grades_df['grade_value'] = grades_df['grade'].map(grade_map)
    
    # Average grade value per algorithm-metric pair across datasets
    avg_grades = grades_df.groupby(['algorithm', 'metric'])['grade_value'].mean()
    
    # Convert back to letter grades
    def value_to_grade(val):
        if val >= 3.5:
            return 'A'
        elif val >= 2.5:
            return 'B'
        elif val >= 1.5:
            return 'C'
        elif val >= 0.5:
            return 'D'
        else:
            return 'F'
    
    avg_grades_letters = avg_grades.apply(value_to_grade)
    
    # Pivot to Algorithm × Metric
    pivot = avg_grades_letters.unstack()
    
    print(f"   ✅ Computed {len(pivot)} algorithms × {len(pivot.columns)} metrics")
    
    return pivot, avg_grades.unstack()


def create_algorithm_metric_heatmap(grades_df, output_dir='plots/fc_visualizations'):
    """
    Create heatmap showing average grade for each Algorithm × Metric combination
    Similar to variance table layout: algorithms as rows, metrics as columns
    """
    print("\n📊 Creating Algorithm × Metric average grade heatmap...")
    
    pivot_letters, pivot_values = compute_average_grade_per_algorithm_metric(grades_df)
    
    # Define metric ordering by feature groups
    metric_order = [
        # Level
        'level_l1', 'level_linf',
        # Mean
        'mean_delta',
        # Regimes
        'regimes_delta',
        # Extrema
        'extrema_wasserstein', 'extrema_bottleneck',
        # Spikes & Dips
        'spikes_dips_wasserstein', 'spikes_dips_bottleneck',
        # Slope
        'slope_l1', 'slope_linf',
        # Curvature
        'curvature_l1', 'curvature_linf',
        # Trend
        'trend_l1', 'trend_linf',
        # Regression
        'regression_l1', 'regression_linf',
        # Periodicity
        'periodicity_amplitude_delta', 'periodicity_num_periods_delta',
        # Roughness
        'roughness_delta',
        # Noise (exclude AUC)
        'noise_l1', 'noise_linf'
    ]
    
    # Reorder columns by defined order (only include metrics that exist)
    existing_metrics = [m for m in metric_order if m in pivot_letters.columns]
    pivot_letters = pivot_letters.reindex(existing_metrics, axis=1)
    pivot_values = pivot_values.reindex(existing_metrics, axis=1)
    
    # Create display names with proper mathematical notation
    metric_display_names = {
        # Level
        'level_l1': r'Level $\ell_1$',
        'level_linf': r'Level $\ell_\infty$',
        # Mean
        'mean_delta': r'Mean $\delta$',
        # Regimes
        'regimes_delta': r'Regimes $\delta$',
        # Extrema
        'extrema_wasserstein': r'Extrema $W_1$',
        'extrema_bottleneck': r'Extrema $W_\infty$',
        # Spikes & Dips
        'spikes_dips_wasserstein': r'Spikes & Dips $W_1$',
        'spikes_dips_bottleneck': r'Spikes & Dips $W_\infty$',
        # Slope
        'slope_l1': r'Slope $\ell_1$',
        'slope_linf': r'Slope $\ell_\infty$',
        # Curvature
        'curvature_l1': r'Curvature $\ell_1$',
        'curvature_linf': r'Curvature $\ell_\infty$',
        # Trend
        'trend_l1': r'Trend $\ell_1$',
        'trend_linf': r'Trend $\ell_\infty$',
        # Regression
        'regression_l1': r'Regression $\ell_1$',
        'regression_linf': r'Regression $\ell_\infty$',
        # Periodicity
        'periodicity_amplitude_delta': r'Periodicity Amplitude $\delta$',
        'periodicity_num_periods_delta': r'Periodicity Periods $\delta$',
        # Roughness
        'roughness_delta': r'Roughness $\delta$',
        # Noise
        'noise_l1': r'Noise $\ell_1$',
        'noise_linf': r'Noise $\ell_\infty$'
    }
    
    # Rename columns for display
    display_columns = [metric_display_names.get(m, m) for m in pivot_letters.columns]
    pivot_letters_display = pivot_letters.copy()
    pivot_letters_display.columns = display_columns
    
    # Convert grades to numeric for color mapping
    grade_map = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
    pivot_numeric = pivot_letters_display.applymap(lambda x: grade_map.get(x, 0))
    
    # Create both greyscale and colored versions
    for version in ['greyscale', 'colored']:
        fig, ax = plt.subplots(figsize=(28, 10))
        
        if version == 'greyscale':
            cmap = sns.color_palette(['#2d2d2d', '#525252', '#7a7a7a', '#a8a8a8', '#d6d6d6'], as_cmap=True)
        else:  # colored
            from matplotlib.colors import ListedColormap
            colors = ["#ebfada", '#c2e699','#78c679', '#31a354', '#006837']  # F, D, C, B, A
            cmap = ListedColormap(colors)
        
        sns.heatmap(
            pivot_numeric,
            ax=ax,
            cmap=cmap,
            vmin=1,
            vmax=5,
            cbar=False,
            linewidths=0.5,
            linecolor='white',
            annot=pivot_letters_display,
            fmt='',
            annot_kws={'fontsize': 16, 'fontweight': 'bold'}
        )
        
        # Manually adjust text colors for better contrast in colored version
        if version == 'colored':
            for text in ax.texts:
                grade = text.get_text()
                if grade in ['A', 'B']:
                    text.set_color('white')
                else:
                    text.set_color('black')
        
        # No titles
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_title('')
        ax.tick_params(labelsize=22)
        
        # Metric names at top
        ax.xaxis.tick_top()
        
        # Rotate labels
        ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='center')
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
        
        plt.tight_layout()
        
        # Save
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)
        
        if version == 'greyscale':
            svg_path = output_path / 'algorithm_metric_average_grades.svg'
            png_path = output_path / 'algorithm_metric_average_grades.pdf'
        else:
            svg_path = output_path / 'algorithm_metric_average_grades_colored.svg'
            png_path = output_path / 'algorithm_metric_average_grades_colored.pdf'
        
        plt.savefig(svg_path, dpi=300, bbox_inches='tight')
        plt.savefig(png_path, dpi=300, bbox_inches='tight')
        
        print(f"   ✅ Saved: {svg_path.name}")
        
        plt.close()
    
    # Save CSV
    csv_path = Path(output_dir) / 'algorithm_metric_average_grades.csv'
    pivot_letters.to_csv(csv_path)
    print(f"   ✅ Saved: {csv_path.name}")


def create_metric_heatmaps(grades_df, output_dir='plots/fc_visualizations/by_metric'):
    """
    Create separate heatmaps for each of the 23 metrics
    Both greyscale and colored versions
    """
    print("\n📊 Creating per-metric heatmaps...")
    
    # Apply display names to algorithms
    grades_df = grades_df.copy()
    grades_df['algorithm'] = grades_df['algorithm'].apply(get_algorithm_name)
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Get list of all metrics
    metrics = sorted(grades_df['metric'].unique())
    print(f"   Found {len(metrics)} metrics")
    
    grade_map = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
    
    for i, metric in enumerate(metrics, 1):
        # Filter data for this metric
        metric_df = grades_df[grades_df['metric'] == metric]
        
        # Pivot: algorithms on rows, datasets on columns
        pivot = metric_df.pivot(index='algorithm', columns='dataset', values='grade')
        pivot_numeric = pivot.applymap(lambda x: grade_map.get(x, 0))
        
        # Create both versions
        for version in ['greyscale', 'colored']:
            fig, ax = plt.subplots(figsize=(40, 10))
            
            if version == 'greyscale':
                cmap = sns.color_palette(['#2d2d2d', '#525252', '#7a7a7a', '#a8a8a8', '#d6d6d6'], as_cmap=True)
            else:  # colored
                from matplotlib.colors import ListedColormap
                colors = ["#e6d5f5", '#c9a8e8','#9b6fd9', '#7340b8', '#4a1a7a']  # F, D, C, B, A (purple)
                cmap = ListedColormap(colors)
            
            sns.heatmap(
                pivot_numeric,
                ax=ax,
                cmap=cmap,
                vmin=1,
                vmax=5,
                cbar=False,
                linewidths=0.5,
                linecolor='white',
                annot=pivot,
                fmt='',
                annot_kws={'fontsize': 16, 'fontweight': 'bold'}
            )
            
            # Manually adjust text colors for better contrast in colored version
            if version == 'colored':
                for text in ax.texts:
                    grade = text.get_text()
                    # Use white text for A, B, C (dark/medium purple), black for D, F (light purple)
                    if grade in ['A', 'B', 'C']:
                        text.set_color('white')
                    else:
                        text.set_color('black')
            
            # No titles or axis labels
            ax.set_xlabel('')
            ax.set_ylabel('')
            ax.set_title('')
            ax.tick_params(labelsize=16)
            
            # Dataset names at top
            ax.xaxis.tick_top()
            
            # Rotate labels
            ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='center')
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            
            plt.tight_layout()
            
            # Save with metric name
            safe_metric_name = metric.replace('/', '_').replace(' ', '_')
            svg_path = output_path / f'{safe_metric_name}_{version}.svg'
            png_path = output_path / f'{safe_metric_name}_{version}.pdf'
            
            plt.savefig(svg_path, dpi=300, bbox_inches='tight')
            plt.savefig(png_path, dpi=300, bbox_inches='tight')
            
            plt.close()
        
        if i % 5 == 0 or i == len(metrics):
            print(f"   Processed {i}/{len(metrics)} metrics...")
    
    print(f"   ✅ Created {len(metrics) * 2} heatmaps ({len(metrics)} greyscale + {len(metrics)} colored)")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Grade algorithm performance')
    parser.add_argument('--algorithm-metric-avg', action='store_true',
                       help='Create Algorithm × Metric average grade heatmap')
    args = parser.parse_args()
    
    print("=" * 80)
    print("ALGORITHM GRADING SYSTEM")
    print("=" * 80)
    
    # Load data
    combined = load_detailed_fc_scores()
    
    # Categorize scores
    combined = categorize_fc_scores(combined)
    
    # Compute grades averaged across all metrics
    grades_df = compute_grade_per_dataset_algorithm(combined)
    
    # Save grades CSV
    output_path = Path('plots/fc_visualizations')
    output_path.mkdir(exist_ok=True, parents=True)
    grades_csv = output_path / 'dataset_algorithm_grades.csv'
    grades_df.to_csv(grades_csv, index=False)
    print(f"\n💾 Saved grades: {grades_csv}")
    
    # Create overall visualizations
    create_grade_heatmap(grades_df)
    create_grade_heatmap_colored(grades_df)
    create_grade_distribution_bar(grades_df)
    summary = create_summary_table(grades_df)
    
    # Compute grades per metric
    metric_grades_df = compute_grade_per_dataset_algorithm_metric(combined)
    
    # Save metric-specific grades CSV
    metric_grades_csv = output_path / 'dataset_algorithm_metric_grades.csv'
    metric_grades_df.to_csv(metric_grades_csv, index=False)
    print(f"\n💾 Saved metric-specific grades: {metric_grades_csv}")
    
    # Create per-metric heatmaps (23 metrics × 2 versions = 46 heatmaps)
    create_metric_heatmaps(metric_grades_df)
    
    # Create Algorithm × Metric average grade heatmap if flag is set
    if args.algorithm_metric_avg:
        create_algorithm_metric_heatmap(metric_grades_df)
    
    print("\n" + "=" * 80)
    print("✅ GRADING COMPLETE!")
    print("=" * 80)
    print(f"\nFiles created in {output_path}:")
    print("  1. dataset_algorithm_grades.csv - Full grade table (averaged across metrics)")
    print("  2. algorithm_grades_by_dataset.svg/png - Heatmap with letter grades (greyscale)")
    print("  3. algorithm_grades_by_dataset_colored.svg/png - Heatmap with letter grades (colored)")
    print("  4. algorithm_grade_distribution.svg/png - Stacked bar chart")
    print("  5. algorithm_grade_summary.csv - Summary statistics with GPA")
    print("  6. dataset_algorithm_metric_grades.csv - Grades for each metric separately")
    print(f"  7. by_metric/ - 46 heatmaps (23 metrics × 2 versions each)")
    if args.algorithm_metric_avg:
        print("  8. algorithm_metric_average_grades.csv - Average grades per Algorithm × Metric")
        print("  9. algorithm_metric_average_grades.svg/pdf - Algorithm × Metric heatmap (greyscale)")
        print("  10. algorithm_metric_average_grades_colored.svg/pdf - Algorithm × Metric heatmap (colored)")
    print("=" * 80)


if __name__ == '__main__':
    main()
