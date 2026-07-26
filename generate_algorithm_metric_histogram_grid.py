"""
Generate a comprehensive grid showing algorithm×metric performance with histograms.

Each cell contains:
- Mini histogram of grade distribution (E, G, F, P bar counts)
- Average grade bar is highlighted with a border
- Background color intensity represents variance (lighter = more consistent, darker = more variable)
- Large readable fonts (16pt+)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import sys
sys.path.insert(0, 'server')
from algorithm_names import get_algorithm_name

# Grade colors (same palette as algorithm_metric_average_grades_colored.svg)
GRADE_COLORS = {
    'F': '#ebfada',  # Light green
    'D': '#c2e699',  # Medium light green
    'C': '#78c679',  # Medium green
    'B': '#31a354',  # Dark green
    'A': '#006837'   # Darkest green
}

GRADE_TO_VALUE = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}
VALUE_TO_GRADE = {4: 'A', 3: 'B', 2: 'C', 1: 'D', 0: 'F'}

def load_data():
    """Load grades and variance data"""
    # Load detailed grades (dataset×algorithm×metric)
    grades_df = pd.read_csv('plots/fc_visualizations/dataset_algorithm_metric_grades.csv')
    
    # Load variance data
    variance_df = pd.read_csv('plots/fc_visualizations/algorithm_metric_variance_table.csv', index_col=0)
    
    return grades_df, variance_df

def calculate_average_grades(grades_df):
    """Calculate average grade for each algorithm×metric combination"""
    # Group by algorithm and metric, count actual grades
    avg_grades = []
    
    for (algo, metric), group in grades_df.groupby(['algorithm', 'metric']):
        # Count actual letter grades across all datasets
        grade_counts = group['grade'].value_counts()
        
        count_A = grade_counts.get('A', 0)
        count_B = grade_counts.get('B', 0)
        count_C = grade_counts.get('C', 0)
        count_D = grade_counts.get('D', 0)
        count_F = grade_counts.get('F', 0)
        
        total_count = count_A + count_B + count_C + count_D + count_F
        
        # Calculate weighted average (A=4, B=3, C=2, D=1, F=0)
        avg_score = (count_A * 4 + count_B * 3 + count_C * 2 + count_D * 1 + count_F * 0) / total_count
        
        # Convert to letter grade
        if avg_score >= 3.5:
            avg_grade = 'A'
        elif avg_score >= 2.5:
            avg_grade = 'B'
        elif avg_score >= 1.5:
            avg_grade = 'C'
        elif avg_score >= 0.5:
            avg_grade = 'D'
        else:
            avg_grade = 'F'
        
        avg_grades.append({
            'algorithm': algo,
            'metric': metric,
            'count_A': count_A,
            'count_B': count_B,
            'count_C': count_C,
            'count_D': count_D,
            'count_F': count_F,
            'avg_score': avg_score,
            'avg_grade': avg_grade
        })
    
    return pd.DataFrame(avg_grades)

def create_histogram_grid(grades_df, variance_df, output_path='plots/fc_visualizations/algorithm_metric_histogram_grid.pdf'):
    """
    Create the grid visualization with mini histograms in each cell
    """
    # Metric display names (same as heatmap)
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
    
    # Define metric ordering (same as heatmap)
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
        # Noise
        'noise_l1', 'noise_linf'
    ]
    
    # Calculate average grades
    avg_df = calculate_average_grades(grades_df)
    
    # Get unique algorithms (alphabetically sorted, same as heatmap)
    algorithms = sorted(avg_df['algorithm'].unique())
    
    # Get metrics in the defined order (only include metrics that exist)
    all_metrics = avg_df['metric'].unique()
    metrics = [m for m in metric_order if m in all_metrics]
    
    n_algorithms = len(algorithms)
    n_metrics = len(metrics)
    
    print(f"Creating {n_algorithms} algorithms × {n_metrics} metrics grid...")
    
    # Create figure with appropriate sizing
    # Larger cell sizes for better readability
    fig_width = max(40, n_metrics * 2.0)  # Increased from 1.6 to 2.0
    fig_height = max(24, n_algorithms * 1.2)
    
    fig, axes = plt.subplots(n_algorithms, n_metrics, 
                            figsize=(fig_width, fig_height),
                            gridspec_kw={'hspace': 0.02, 'wspace': 0.02})
    
    # Ensure axes is 2D
    if n_algorithms == 1:
        axes = axes.reshape(1, -1)
    if n_metrics == 1:
        axes = axes.reshape(-1, 1)
    
    # Process each cell
    for i, algo in enumerate(algorithms):
        for j, metric in enumerate(metrics):
            ax = axes[i, j]
            
            # Get data for this cell
            cell_data = avg_df[(avg_df['algorithm'] == algo) & (avg_df['metric'] == metric)]
            
            if cell_data.empty:
                ax.axis('off')
                continue
            
            row = cell_data.iloc[0]
            
            # Get grade counts (now correctly from the counted grades)
            count_A = row['count_A']
            count_B = row['count_B']
            count_C = row['count_C']
            count_D = row['count_D']
            count_F = row['count_F']
            avg_grade = row['avg_grade']
            
            # Get variance for background color (same thresholds as variance_table.tex)
            try:
                variance = variance_df.loc[algo, metric]
                # Apply same thresholding as LaTeX table:
                # No color: < 0.5, 30%: 0.5-1.5, 70%: >= 1.5
                if variance < 0.5:
                    bg_alpha = 0.0  # No background
                elif variance < 1.5:
                    bg_alpha = 0.3  # Light steelblue
                else:
                    bg_alpha = 0.7  # Dark steelblue
            except:
                bg_alpha = 0.0
            
            # Set background color (steelblue with thresholded intensity)
            ax.set_facecolor((0.27, 0.51, 0.71, bg_alpha))  # Steelblue RGB normalized
            
            # Create mini histogram
            grades = ['A', 'B', 'C', 'D', 'F']
            counts = [count_A, count_B, count_C, count_D, count_F]
            colors_list = [GRADE_COLORS[g] for g in grades]
            
            # Text colors: white for dark backgrounds (A, B), black for light backgrounds (C, D, F)
            text_colors = {
                'A': 'white',
                'B': 'white', 
                'C': 'black',
                'D': 'black',
                'F': 'black'
            }
            
            # Draw bars
            max_count = max(counts) if max(counts) > 0 else 1
            x_positions = np.arange(len(grades))
            
            for x, count, color, grade in zip(x_positions, counts, colors_list, grades):
                if count > 0:
                    # Highlight average grade bar with thick border
                    if grade == avg_grade:
                        ax.bar(x, count, color=color, edgecolor='black', linewidth=3, width=0.8)
                        # Add grade letter annotation ONLY on the mean grade bar
                        text_color = text_colors[grade]
                        
                        # If bar is too short, place text above; otherwise place in center
                        # Threshold: if count is less than 10% of max, place on top
                        if count < max_count * 0.15:
                            # Place on top of bar
                            ax.text(x, count, grade, 
                                   ha='center', va='bottom', 
                                   fontsize=16, fontweight='bold', 
                                   color='black')
                        else:
                            # Place in center of bar
                            ax.text(x, count / 2, grade, 
                                   ha='center', va='center', 
                                   fontsize=16, fontweight='bold', 
                                   color=text_color)
                    else:
                        ax.bar(x, count, color=color, edgecolor='gray', linewidth=0.5, width=0.8)
            
            # Configure axes
            ax.set_xlim(-0.5, len(grades) - 0.5)
            ax.set_ylim(0, max_count * 1.1)
            ax.set_xticks(x_positions)
            ax.set_xticklabels([])  # No x-axis labels
            ax.set_yticks([])
            
            # Remove spines
            for spine in ax.spines.values():
                spine.set_visible(False)
            
            # Add row labels (algorithm names) on leftmost column
            if j == 0:
                ax.set_ylabel(get_algorithm_name(algo), 
                            fontsize=18, 
                            fontweight='bold',
                            rotation=0,
                            ha='right',
                            va='center',
                            labelpad=10)
            
            # Add column labels (metric names) on top row
            if i == 0:
                # Use same metric display names as heatmap
                metric_display = metric_display_names.get(metric, metric.replace('_', ' ').title())
                ax.set_title(metric_display, 
                           fontsize=18,
                           fontweight='bold',
                           pad=10,
                           rotation=90,
                           ha='center')
    
    plt.tight_layout()
    
    # Save
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.savefig(output_path.replace('.pdf', '.svg'), bbox_inches='tight')
    
    print(f"✓ Saved: {output_path}")
    print(f"✓ Saved: {output_path.replace('.pdf', '.svg')}")
    
    plt.close()

if __name__ == '__main__':
    grades_df, variance_df = load_data()
    create_histogram_grid(grades_df, variance_df)
    print("\n✅ Histogram grid visualization complete!")
