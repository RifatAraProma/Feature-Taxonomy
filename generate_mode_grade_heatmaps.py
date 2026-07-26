"""
Generate Mode-Based Grade Heatmaps with Purple Color Scheme
Creates two heatmaps:
1. Algorithm × Metric: Shows mode grade for each algorithm-metric combination
2. Algorithm × Dataset: Shows mode grade for each algorithm-dataset combination

Supports split diagonal cells for ties (multiple mode grades)
Matches format of existing grade heatmaps (no legends, same sizing)
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
from pathlib import Path
from matplotlib.colors import ListedColormap
import sys
sys.path.insert(0, 'server')
from algorithm_names import get_algorithm_name
from algorithm_colors import ALGORITHM_COLORS

# Purple color scheme matching histogram
GRADE_COLORS = {
    'A': '#4a1a7a',  # Darkest purple
    'B': '#7340b8',  # Dark purple
    'C': '#9b6fd9',  # Medium purple
    'D': '#c9a8e8',  # Light purple
    'F': '#e6d5f5'   # Very light purple
}

# Text colors for readability
GRADE_TEXT_COLORS = {
    'A': 'white',
    'B': 'white',
    'C': 'white',
    'D': 'black',
    'F': 'black'
}

# Metric order matching grade_algorithms.py
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
    # Noise (exclude AUC, change_points)
    'noise_l1', 'noise_linf'
]

# Feature display names with LaTeX notation
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


def generate_algorithm_metric_heatmap():
    """Generate Algorithm × Metric mode grade heatmap matching grade_algorithms.py format"""
    print("\n📊 Generating Algorithm × Metric Mode Grade Heatmap...")
    
    # Load mode summary data
    df = pd.read_csv('plots/fc_visualizations/algorithm_metric_mode_grades.csv')
    print(f"   Loaded {len(df)} rows")
    
    # Apply display names to algorithms
    df['algorithm'] = df['algorithm'].apply(get_algorithm_name)
    
    # Pivot to Algorithm × Metric
    pivot = df.pivot(index='algorithm', columns='metric', values='mode')
    
    # Reorder columns by defined metric order (only include metrics that exist)
    existing_metrics = [m for m in metric_order if m in pivot.columns]
    pivot = pivot.reindex(existing_metrics, axis=1)
    
    # Rename columns for display with LaTeX notation
    display_columns = [metric_display_names.get(m, m) for m in pivot.columns]
    pivot_display = pivot.copy()
    pivot_display.columns = display_columns
    
    # Sort algorithms alphabetically by display name
    pivot_display = pivot_display.sort_index()
    
    # Check for ties and create annotation matrix
    has_ties = False
    for idx in pivot_display.index:
        for col in pivot_display.columns:
            val = pivot_display.loc[idx, col]
            if isinstance(val, str) and ',' in val:
                has_ties = True
                break
        if has_ties:
            break
    
    if not has_ties:
        # No ties - use simple seaborn heatmap
        grade_map = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
        pivot_numeric = pivot_display.applymap(lambda x: grade_map.get(x, 0) if isinstance(x, str) and ',' not in x else grade_map.get(str(x).strip(), 0))
        
        fig, ax = plt.subplots(figsize=(28, 10))
        
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
            annot=pivot_display,
            fmt='',
            annot_kws={'fontsize': 16, 'fontweight': 'bold'}
        )
        
        # Manually adjust text colors for better contrast
        for text in ax.texts:
            grade = text.get_text()
            if grade in ['A', 'B', 'C']:
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
    else:
        # Has ties - use manual drawing with diagonal splits
        n_algos = len(pivot_display)
        n_metrics = len(pivot_display.columns)
        fig, ax = plt.subplots(figsize=(28, 10))
        
        # Draw cells manually
        for i, algo in enumerate(pivot_display.index):
            for j, metric in enumerate(pivot_display.columns):
                val = pivot_display.loc[algo, metric]
                x, y = j, n_algos - i - 1
                
                if isinstance(val, str) and ',' in val:
                    # Tie - split diagonally
                    grades = [g.strip() for g in val.split(',')][:2]
                    grade1, grade2 = sorted(grades)
                    
                    # Lower-left triangle
                    triangle1 = mpatches.Polygon(
                        [(x, y), (x + 1, y), (x, y + 1)],
                        facecolor=GRADE_COLORS[grade1],
                        edgecolor='white',
                        linewidth=0.5
                    )
                    ax.add_patch(triangle1)
                    
                    # Upper-right triangle
                    triangle2 = mpatches.Polygon(
                        [(x + 1, y), (x + 1, y + 1), (x, y + 1)],
                        facecolor=GRADE_COLORS[grade2],
                        edgecolor='white',
                        linewidth=0.5
                    )
                    ax.add_patch(triangle2)
                    
                    # Add both grade labels
                    ax.text(x + 0.3, y + 0.3, grade1,
                           ha='center', va='center',
                           fontsize=14, fontweight='bold',
                           color=GRADE_TEXT_COLORS[grade1])
                    ax.text(x + 0.7, y + 0.7, grade2,
                           ha='center', va='center',
                           fontsize=14, fontweight='bold',
                           color=GRADE_TEXT_COLORS[grade2])
                else:
                    # Single grade
                    grade = str(val).strip() if pd.notna(val) else 'F'
                    rect = mpatches.Rectangle((x, y), 1, 1,
                                              facecolor=GRADE_COLORS.get(grade, GRADE_COLORS['F']),
                                              edgecolor='white',
                                              linewidth=0.5)
                    ax.add_patch(rect)
                    
                    ax.text(x + 0.5, y + 0.5, grade,
                           ha='center', va='center',
                           fontsize=16, fontweight='bold',
                           color=GRADE_TEXT_COLORS.get(grade, GRADE_TEXT_COLORS['F']))
        
        # Set axis properties
        ax.set_xlim(0, n_metrics)
        ax.set_ylim(0, n_algos)
        ax.set_aspect('equal')
        
        # Set ticks and labels
        ax.set_xticks(np.arange(n_metrics) + 0.5)
        ax.set_xticklabels(pivot_display.columns, rotation=90, ha='center', fontsize=22)
        
        ax.set_yticks(np.arange(n_algos) + 0.5)
        ax.set_yticklabels(reversed(pivot_display.index), rotation=0, fontsize=22)
        
        # No titles or axis labels
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_title('')
        
        # Metric names at top
        ax.xaxis.tick_top()
        
        # Remove spines
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Remove tick marks
        ax.tick_params(length=0)
        
        plt.tight_layout()
    
    # Save
    output_dir = Path('plots/fc_visualizations')
    svg_path = output_dir / 'algorithm_metric_mode_grades.svg'
    pdf_path = output_dir / 'algorithm_metric_mode_grades.pdf'
    
    print(f"   Saving to {svg_path}...")
    plt.savefig(svg_path, format='svg', bbox_inches='tight', dpi=300)
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', dpi=300)
    
    print(f"✅ Saved: {svg_path}")
    print(f"✅ Saved: {pdf_path}")
    print(f"   SVG size: {svg_path.stat().st_size} bytes")
    print(f"   PDF size: {pdf_path.stat().st_size} bytes")
    
    plt.close()


def generate_algorithm_dataset_heatmap():
    """Generate Algorithm × Dataset mode grade heatmap"""
    print("\n📊 Generating Algorithm × Dataset Mode Grade Heatmap...")
    
    # Load mode summary data
    df = pd.read_csv('plots/fc_visualizations/algorithm_dataset_mode_grades.csv')
    print(f"   Loaded {len(df)} rows")
    
    # Apply display names to algorithms
    df['algorithm_display'] = df['algorithm'].apply(get_algorithm_name)
    
    # Parse mode column (may contain comma-separated values for ties)
    df['mode_grades'] = df['mode'].apply(lambda x: [g.strip() for g in str(x).split(',')])
    
    # Sort algorithms alphabetically by display name
    unique_algos = df[['algorithm', 'algorithm_display']].drop_duplicates()
    unique_algos = unique_algos.sort_values('algorithm_display')
    algorithms = unique_algos['algorithm'].tolist()
    print(f"   Algorithms: {len(algorithms)}")
    
    datasets = sorted(df['dataset'].unique())
    print(f"   Datasets: {len(datasets)}")
    
    # Create figure
    n_algos = len(algorithms)
    n_datasets = len(datasets)
    fig, ax = plt.subplots(figsize=(40, 10))
    print(f"   Drawing {n_algos} × {n_datasets} = {n_algos * n_datasets} cells...")
    
    # Create pivot for easy lookup
    pivot_data = {}
    for _, row in df.iterrows():
        key = (row['algorithm'], row['dataset'])
        pivot_data[key] = row['mode_grades']
    
    # Draw cells manually
    cells_drawn = 0
    for i, algo in enumerate(algorithms):
        for j, dataset in enumerate(datasets):
            grades = pivot_data.get((algo, dataset), ['F'])
            x, y = j, n_algos - i - 1
            
            if len(grades) == 1:
                # Single grade
                grade = grades[0]
                rect = mpatches.Rectangle((x, y), 1, 1,
                                          facecolor=GRADE_COLORS[grade],
                                          edgecolor='white',
                                          linewidth=0.5)
                ax.add_patch(rect)
                
                ax.text(x + 0.5, y + 0.5, grade,
                       ha='center', va='center',
                       fontsize=16, fontweight='bold',
                       color=GRADE_TEXT_COLORS[grade])
            else:
                # Tie - split diagonally
                grade1, grade2 = sorted(grades[:2])
                
                # Lower-left triangle
                triangle1 = mpatches.Polygon(
                    [(x, y), (x + 1, y), (x, y + 1)],
                    facecolor=GRADE_COLORS[grade1],
                    edgecolor='white',
                    linewidth=0.5
                )
                ax.add_patch(triangle1)
                
                # Upper-right triangle
                triangle2 = mpatches.Polygon(
                    [(x + 1, y), (x + 1, y + 1), (x, y + 1)],
                    facecolor=GRADE_COLORS[grade2],
                    edgecolor='white',
                    linewidth=0.5
                )
                ax.add_patch(triangle2)
                
                # Add both grade labels
                ax.text(x + 0.3, y + 0.3, grade1,
                       ha='center', va='center',
                       fontsize=14, fontweight='bold',
                       color=GRADE_TEXT_COLORS[grade1])
                ax.text(x + 0.7, y + 0.7, grade2,
                       ha='center', va='center',
                       fontsize=14, fontweight='bold',
                       color=GRADE_TEXT_COLORS[grade2])
            cells_drawn += 1
    
    print(f"   Drew {cells_drawn} cells")
    
    # Set axis properties
    ax.set_xlim(0, n_datasets)
    ax.set_ylim(0, n_algos)
    ax.set_aspect('equal')
    
    # Set ticks and labels
    ax.set_xticks(np.arange(n_datasets) + 0.5)
    ax.set_xticklabels(datasets, rotation=90, ha='center', fontsize=16)
    
    ax.set_yticks(np.arange(n_algos) + 0.5)
    algo_labels = [get_algorithm_name(a) for a in reversed(algorithms)]
    ax.set_yticklabels(algo_labels, rotation=0, fontsize=16)
    
    # No titles or axis labels
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_title('')
    
    # Dataset names at top
    ax.xaxis.tick_top()
    
    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Remove tick marks
    ax.tick_params(length=0)
    
    plt.tight_layout()
    
    # Save
    output_dir = Path('plots/fc_visualizations')
    svg_path = output_dir / 'algorithm_dataset_mode_grades.svg'
    pdf_path = output_dir / 'algorithm_dataset_mode_grades.pdf'
    
    print(f"   Saving to {svg_path}...")
    plt.savefig(svg_path, format='svg', bbox_inches='tight', dpi=300)
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"✅ Saved: {svg_path}")
    print(f"✅ Saved: {pdf_path}")
    print(f"   SVG size: {svg_path.stat().st_size} bytes")
    print(f"   PDF size: {pdf_path.stat().st_size} bytes")


def main():
    print("="*80)
    print("MODE-BASED GRADE HEATMAP GENERATOR")
    print("="*80)
    
    # Generate both heatmaps
    generate_algorithm_metric_heatmap()
    # generate_algorithm_dataset_heatmap()
    
    print("\n" + "="*80)
    print("✅ Complete! Generated:")
    print("   1. algorithm_metric_mode_grades.svg/pdf - Algorithm × Metric mode grades")
    print("   2. algorithm_dataset_mode_grades.svg/pdf - Algorithm × Dataset mode grades")
    print("="*80)


if __name__ == '__main__':
    main()
