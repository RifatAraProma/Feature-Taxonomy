"""
Generate Mode-Based Grade Heatmaps with Purple Color Scheme
Exact copy of mean-based aggregation but using mode instead
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path
from matplotlib.colors import ListedColormap
import sys
sys.path.insert(0, 'server')
from algorithm_names import get_algorithm_name

# Purple color scheme
GRADE_COLORS = ["#e6d5f5", '#c9a8e8','#9b6fd9', '#7340b8', '#4a1a7a']  # F, D, C, B, A

# Grade to color mapping
GRADE_COLOR_MAP = {
    'A': '#4a1a7a',
    'B': '#7340b8',
    'C': '#9b6fd9',
    'D': '#c9a8e8',
    'F': '#e6d5f5'
}

# Text colors
GRADE_TEXT_COLORS = {
    'A': 'white',
    'B': 'white',
    'C': 'white',
    'D': 'black',
    'F': 'black'
}


def split_cell_with_two_colors(ax, row, col, grades, cell_width=1, cell_height=1):
    """
    Redraw a cell with diagonal split for two grades
    row, col are the cell positions in the heatmap
    """
    grade1, grade2 = grades.split(',')
    
    # Calculate cell boundaries
    x = col
    y = row
    
    # Draw lower-left triangle (grade1)
    triangle1 = mpatches.Polygon(
        [(x, y), (x + cell_width, y), (x, y + cell_height)],
        facecolor=GRADE_COLOR_MAP[grade1],
        edgecolor='white',
        linewidth=0.5,
        zorder=3
    )
    ax.add_patch(triangle1)
    
    # Draw upper-right triangle (grade2)
    triangle2 = mpatches.Polygon(
        [(x + cell_width, y), (x + cell_width, y + cell_height), (x, y + cell_height)],
        facecolor=GRADE_COLOR_MAP[grade2],
        edgecolor='white',
        linewidth=0.5,
        zorder=3
    )
    ax.add_patch(triangle2)


def compute_mode_grade_per_algorithm_metric(grades_df):
    """
    Compute mode grade for each Algorithm × Metric combination across all datasets
    Returns a pivot table with algorithms as rows and metrics as columns
    """
    print("\n📊 Computing mode grades per Algorithm × Metric...")
    
    # Apply display names to algorithms
    grades_df = grades_df.copy()
    grades_df['algorithm'] = grades_df['algorithm'].apply(get_algorithm_name)
    
    # Exclude noise_auc
    grades_df = grades_df[grades_df['metric'] != 'noise_auc']
    
    # Calculate mode for each algorithm-metric pair
    mode_grades = []
    for (algo, metric), group in grades_df.groupby(['algorithm', 'metric']):
        grade_counts = group['grade'].value_counts()
        max_count = grade_counts.max()
        modes = grade_counts[grade_counts == max_count].index.tolist()
        # Join multiple modes with comma
        mode_grade = ','.join(sorted(modes))
        mode_grades.append({'algorithm': algo, 'metric': metric, 'mode_grade': mode_grade})
    
    mode_df = pd.DataFrame(mode_grades)
    
    # Pivot to Algorithm × Metric
    pivot = mode_df.pivot(index='algorithm', columns='metric', values='mode_grade')
    
    print(f"   ✅ Computed {len(pivot)} algorithms × {len(pivot.columns)} metrics")
    
    return pivot


def create_algorithm_metric_mode_heatmap(grades_df, output_dir='plots/fc_visualizations'):
    """
    Create heatmap showing mode grade for each Algorithm × Metric combination
    """
    print("\n📊 Creating Algorithm × Metric mode grade heatmap...")
    
    pivot_letters = compute_mode_grade_per_algorithm_metric(grades_df)
    
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
    
    # Convert grades to numeric for color mapping (use first grade if tied)
    grade_map = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
    pivot_numeric = pivot_letters_display.applymap(lambda x: grade_map.get(str(x).split(',')[0], 0))
    
    # Create purple version
    fig, ax = plt.subplots(figsize=(28, 10))
    
    cmap = ListedColormap(GRADE_COLORS)
    
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
    
    # Post-process: redraw cells with ties using diagonal split
    for i, row_label in enumerate(pivot_letters_display.index):
        for j, col_label in enumerate(pivot_letters_display.columns):
            grade_str = str(pivot_letters_display.iloc[i, j])
            if ',' in grade_str and len(grade_str.split(',')) == 2:
                # This cell has a tie - redraw with diagonal split
                split_cell_with_two_colors(ax, i, j, grade_str)
    
    # Manually adjust text colors for better contrast
    for text in ax.texts:
        grade = text.get_text().split(',')[0]  # Get first grade if tied
        if grade in ['A', 'B', 'C']:
            text.set_color('white')
        else:
            text.set_color('black')
        # Bring text to front
        text.set_zorder(4)
    
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
    
    svg_path = output_path / 'algorithm_metric_mode_grades.svg'
    pdf_path = output_path / 'algorithm_metric_mode_grades.pdf'
    
    plt.savefig(svg_path, dpi=300, bbox_inches='tight')
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
    
    print(f"   ✅ Saved: {svg_path.name}")
    
    plt.close()
    
    # Save CSV
    csv_path = Path(output_dir) / 'algorithm_metric_mode_grades.csv'
    pivot_letters.to_csv(csv_path)
    print(f"   ✅ Saved: {csv_path.name}")


def compute_mode_grade_per_algorithm_dataset(grades_df):
    """
    Compute mode grade for each Algorithm × Dataset combination across all metrics
    """
    print("\n📊 Computing mode grades per Algorithm × Dataset...")
    
    # Apply display names to algorithms
    grades_df = grades_df.copy()
    grades_df['algorithm'] = grades_df['algorithm'].apply(get_algorithm_name)
    
    # Calculate mode for each algorithm-dataset pair across all metrics
    mode_grades = []
    for (algo, dataset), group in grades_df.groupby(['algorithm', 'dataset']):
        grade_counts = group['grade'].value_counts()
        max_count = grade_counts.max()
        modes = grade_counts[grade_counts == max_count].index.tolist()
        # Join multiple modes with comma
        mode_grade = ','.join(sorted(modes))
        mode_grades.append({'algorithm': algo, 'dataset': dataset, 'mode_grade': mode_grade})
    
    mode_df = pd.DataFrame(mode_grades)
    
    # Pivot to Algorithm × Dataset
    pivot = mode_df.pivot(index='algorithm', columns='dataset', values='mode_grade')
    
    print(f"   ✅ Computed {len(pivot)} algorithms × {len(pivot.columns)} datasets")
    
    return pivot


def create_algorithm_dataset_mode_heatmap(grades_df, output_dir='plots/fc_visualizations'):
    """
    Create heatmap showing mode grade for each Algorithm × Dataset combination
    """
    print("\n📊 Creating Algorithm × Dataset mode grade heatmap...")
    
    pivot_letters = compute_mode_grade_per_algorithm_dataset(grades_df)
    
    # Convert grades to numeric for color mapping (use first grade if tied)
    grade_map = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
    pivot_numeric = pivot_letters.applymap(lambda x: grade_map.get(str(x).split(',')[0], 0))
    
    # Create figure
    fig, ax = plt.subplots(figsize=(40, 10))
    
    cmap = ListedColormap(GRADE_COLORS)
    
    sns.heatmap(
        pivot_numeric,
        ax=ax,
        cmap=cmap,
        vmin=1,
        vmax=5,
        cbar=False,  # No legend
        linewidths=0.5,
        linecolor='white',
        annot=pivot_letters,  # Show letter grades
        fmt='',
        annot_kws={'fontsize': 16, 'fontweight': 'bold'}
    )
    
    # Post-process: redraw cells with ties using diagonal split
    for i, row_label in enumerate(pivot_letters.index):
        for j, col_label in enumerate(pivot_letters.columns):
            grade_str = str(pivot_letters.iloc[i, j])
            if ',' in grade_str and len(grade_str.split(',')) == 2:
                # This cell has a tie - redraw with diagonal split
                split_cell_with_two_colors(ax, i, j, grade_str)
    
    # Manually adjust text colors for better contrast
    for text in ax.texts:
        grade = text.get_text().split(',')[0]  # Get first grade if tied
        if grade in ['A', 'B', 'C']:
            text.set_color('white')
        else:
            text.set_color('black')
        # Bring text to front
        text.set_zorder(4)
    
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
    
    svg_path = output_path / 'algorithm_dataset_mode_grades.svg'
    pdf_path = output_path / 'algorithm_dataset_mode_grades.pdf'
    
    plt.savefig(svg_path, dpi=300, bbox_inches='tight')
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
    
    print(f"   ✅ Saved: {svg_path.name}")
    
    plt.close()
    
    # Save CSV
    csv_path = Path(output_dir) / 'algorithm_dataset_mode_grades.csv'
    pivot_letters.to_csv(csv_path)
    print(f"   ✅ Saved: {csv_path.name}")


def main():
    print("="*80)
    print("MODE-BASED GRADE HEATMAP GENERATOR")
    print("="*80)
    
    # Load dataset-algorithm-metric grades
    grades_df = pd.read_csv('plots/fc_visualizations/dataset_algorithm_metric_grades.csv')
    
    # Generate both heatmaps
    create_algorithm_metric_mode_heatmap(grades_df)
    create_algorithm_dataset_mode_heatmap(grades_df)
    
    print("\n" + "="*80)
    print("✅ Complete! Generated:")
    print("   1. algorithm_metric_mode_grades.svg/pdf - Algorithm × Metric mode grades")
    print("   2. algorithm_dataset_mode_grades.svg/pdf - Algorithm × Dataset mode grades")
    print("="*80)


if __name__ == '__main__':
    main()
