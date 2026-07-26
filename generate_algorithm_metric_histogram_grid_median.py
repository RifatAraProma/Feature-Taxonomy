"""
Generate histogram grid showing grade distribution for each algorithm-metric combination
with MEDIAN grade aggregation and variance indicator
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, 'server')
from algorithm_names import get_algorithm_name

# Metric display names (same as original histogram)
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

# Define metric ordering (same as weighted average histogram)
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

# Grade to numeric mapping
GRADE_TO_NUM = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'F': 0}
NUM_TO_GRADE = {4: 'A', 3: 'B', 2: 'C', 1: 'D', 0: 'F'}

# Grade colors - Purple gradient (lightest to darkest)
GRADE_COLORS = {
    'F': '#e6d5f5',  # Very light purple
    'D': '#c9a8e8',  # Light purple
    'C': '#9b6fd9',  # Medium purple
    'B': '#7340b8',  # Dark purple
    'A': '#4a1a7a'   # Darkest purple
}

def calculate_median_and_variance(grades_df):
    """
    Calculate median grade and variance (% deviation from mode) for each algorithm-metric combination
    """
    results = []
    
    for (algo, metric), group in grades_df.groupby(['algorithm', 'metric']):
        # Count each grade
        grade_counts = group['grade'].value_counts()
        count_A = grade_counts.get('A', 0)
        count_B = grade_counts.get('B', 0)
        count_C = grade_counts.get('C', 0)
        count_D = grade_counts.get('D', 0)
        count_F = grade_counts.get('F', 0)
        total = len(group)
        
        # Calculate median grade
        numeric_grades = group['grade'].map(GRADE_TO_NUM).sort_values()
        median_idx = len(numeric_grades) // 2
        if len(numeric_grades) % 2 == 0:
            # Average of two middle values
            median_value = (numeric_grades.iloc[median_idx-1] + numeric_grades.iloc[median_idx]) / 2
        else:
            median_value = numeric_grades.iloc[median_idx]
        
        # Round to nearest grade
        median_grade = NUM_TO_GRADE[round(median_value)]
        
        # Calculate variance as % deviation from mode
        mode_count = grade_counts.max()
        variance_pct = ((total - mode_count) / total) * 100
        
        results.append({
            'algorithm': algo,
            'metric': metric,
            'count_A': count_A,
            'count_B': count_B,
            'count_C': count_C,
            'count_D': count_D,
            'count_F': count_F,
            'total': total,
            'median_grade': median_grade,
            'variance_pct': variance_pct
        })
    
    return pd.DataFrame(results)

def get_variance_alpha(variance_pct):
    """Get steelblue alpha based on variance percentage"""
    if variance_pct < 25:
        return 0.3  # Light steelblue (30% opacity)
    elif variance_pct < 50:
        return 0.5  # Medium steelblue (50% opacity)
    else:
        return 0.7  # Dark steelblue (70% opacity)

def get_variance_color(variance_pct):
    """Return orange color based on variance percentage"""
    if variance_pct < 25:
        return (1.0, 0.8, 0.4)  # Light orange
    elif variance_pct < 50:
        return (1.0, 0.6, 0.0)  # Medium orange
    else:
        return (0.9, 0.4, 0.0)  # Dark orange

def plot_histogram_grid(summary_df, output_path):
    """Generate grid of histograms with median grade and variance line"""
    
    # Get unique algorithms and sort by display name
    algo_internal_names = summary_df['algorithm'].unique()
    algorithms = sorted(algo_internal_names, key=lambda x: get_algorithm_name(x))
    
    # Get metrics in the defined order (only include metrics that exist)
    all_metrics = summary_df['metric'].unique()
    metrics = [m for m in metric_order if m in all_metrics]
    
    n_algos = len(algorithms)
    n_metrics = len(metrics)
    
    # Create figure
    fig_width = max(40, n_metrics * 2.0)
    fig_height = max(24, n_algos * 1.5)  # Increased from 1.2 to 1.5 for more vertical space
    fig, axes = plt.subplots(n_algos, n_metrics, figsize=(fig_width, fig_height),
                            gridspec_kw={'hspace': 0.08, 'wspace': 0.02})  # Increased hspace from 0.02 to 0.08
    
    # Text colors: white for dark backgrounds (A, B, C), black for light backgrounds (D, F)
    text_colors = {
        'A': 'white',
        'B': 'white', 
        'C': 'white',
        'D': 'black',
        'F': 'black'
    }
    
    for i, algo in enumerate(algorithms):
        for j, metric in enumerate(metrics):
            ax = axes[i, j]
            
            # Get data for this combination
            row = summary_df[(summary_df['algorithm'] == algo) & (summary_df['metric'] == metric)]
            
            if len(row) == 0:
                ax.axis('off')
                continue
            
            row = row.iloc[0]
            
            # Plot histogram
            grades = ['A', 'B', 'C', 'D', 'F']
            counts = [row['count_A'], row['count_B'], row['count_C'], row['count_D'], row['count_F']]
            max_count = max(counts) if max(counts) > 0 else 1
            x_positions = np.arange(len(grades))
            
            median_grade = row['median_grade']
            
            # Draw bars
            for x, count, grade in zip(x_positions, counts, grades):
                if count > 0:
                    color = GRADE_COLORS[grade]
                    # Highlight median grade bar with thick border
                    if grade == median_grade:
                        ax.bar(x, count, color=color, edgecolor='black', linewidth=3, width=0.8)
                        
                        # Add median grade annotation
                        text_color = text_colors[grade]
                        
                        # If bar is too short, place text above; otherwise place in center
                        if count < max_count * 0.15:
                            ax.text(x, count, grade, 
                                   ha='center', va='bottom', 
                                   fontsize=16, fontweight='bold', 
                                   color='black')
                        else:
                            ax.text(x, count / 2, grade, 
                                   ha='center', va='center', 
                                   fontsize=16, fontweight='bold', 
                                   color=text_color)
                    else:
                        ax.bar(x, count, color=color, edgecolor='gray', linewidth=0.5, width=0.8)
            
            # Configure axes first
            ax.set_xlim(-0.5, len(grades) - 0.5)
            ax.set_ylim(-max_count * 0.25, max_count * 1.1)  # Extended further below for variance line
            ax.set_xticks([])  # No x-axis ticks
            ax.set_yticks([])
            
            # Remove spines
            for spine in ax.spines.values():
                spine.set_visible(False)
            
            # Add variance line below the chart
            variance_pct = row['variance_pct']
            var_color = get_variance_color(variance_pct)
            
            # Draw thick orange line well below the chart (below where x-axis ticks would be)
            line_y = -max_count * 0.18  # Position below x-axis area
            ax.plot([-0.5, len(grades) - 0.5], [line_y, line_y],
                   color=var_color, linewidth=12, solid_capstyle='butt', clip_on=False)
            
            # Add labels only on edges
            if j == 0:
                ax.set_ylabel(get_algorithm_name(algo), fontsize=18, fontweight='bold',
                            rotation=0, ha='right', va='center', labelpad=10)
            
            if i == 0:
                metric_display = metric_display_names.get(metric, metric.replace('_', ' ').title())
                ax.set_title(metric_display, fontsize=18, fontweight='bold', pad=10, rotation=90, ha='center')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.savefig(str(output_path).replace('.svg', '.pdf'), bbox_inches='tight')
    print(f"✅ Saved: {output_path}")
    print(f"✅ Saved: {str(output_path).replace('.svg', '.pdf')}")
    plt.close()

def main():
    # Load data
    grades_file = Path('plots/fc_visualizations/dataset_algorithm_metric_grades.csv')
    if not grades_file.exists():
        print(f"❌ Error: {grades_file} not found")
        return
    
    print(f"📂 Loading data from {grades_file}")
    grades_df = pd.read_csv(grades_file)
    
    # Calculate median and variance
    print("📊 Calculating median grades and variance...")
    summary_df = calculate_median_and_variance(grades_df)
    
    # Save summary
    output_csv = Path('plots/fc_visualizations/algorithm_metric_median_summary.csv')
    summary_df.to_csv(output_csv, index=False)
    print(f"💾 Saved summary: {output_csv}")
    
    # Generate plot
    output_plot = Path('plots/fc_visualizations/algorithm_metric_histogram_grid_median.svg')
    print("🎨 Generating histogram grid...")
    plot_histogram_grid(summary_df, output_plot)
    
    print("\n✅ Complete!")

if __name__ == '__main__':
    main()
