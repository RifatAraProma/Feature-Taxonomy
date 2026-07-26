"""
Generate histogram grid showing grade distribution for each algorithm-metric combination
with MODE grade aggregation (most common) and variance indicator
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

# Grade colors - Purple gradient (lightest to darkest)
GRADE_COLORS = {
    'F': '#e6d5f5',  # Very light purple
    'D': '#c9a8e8',  # Light purple
    'C': '#9b6fd9',  # Medium purple
    'B': '#7340b8',  # Dark purple
    'A': '#4a1a7a'   # Darkest purple
}

def load_and_prepare_data(csv_path):
    """
    Load mode grades data from algorithm_metric_mode_grades.csv
    Returns DataFrame with counts and deviation from CSV
    """
    df = pd.read_csv(csv_path)
    
    results = []
    
    for _, row in df.iterrows():
        algo = row['algorithm']
        metric = row['metric']
        
        # Get counts
        count_A = int(row['A'])
        count_B = int(row['B'])
        count_C = int(row['C'])
        count_D = int(row['D'])
        count_F = int(row['F'])
        total = count_A + count_B + count_C + count_D + count_F
        
        # Mode grades (already calculated in CSV)
        mode_str = str(row['mode'])
        
        # Debug: Check if ties are being read
        if ',' in mode_str:
            print(f"DEBUG load: {algo} + {metric} -> mode='{mode_str}' (type={type(row['mode'])})")
        
        # Read deviation directly from CSV (don't recalculate)
        variance_pct = float(row['deviation'])
        
        # Calculate mode count: for ties, sum all tied grade frequencies
        mode_grades_list = [g.strip() for g in mode_str.split(',')]
        mode_count_sum = sum([
            count_A if 'A' in mode_grades_list else 0,
            count_B if 'B' in mode_grades_list else 0,
            count_C if 'C' in mode_grades_list else 0,
            count_D if 'D' in mode_grades_list else 0,
            count_F if 'F' in mode_grades_list else 0
        ])
        
        results.append({
            'algorithm': algo,
            'metric': metric,
            'count_A': count_A,
            'count_B': count_B,
            'count_C': count_C,
            'count_D': count_D,
            'count_F': count_F,
            'total': total,
            'mode_grades': mode_str,
            'mode_count': mode_count_sum,
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
    """Generate grid of histograms with mode grade(s) and variance line"""
    
    # Algorithm categories
    transformers = [
        'gaussian_filter', 'median_filter', 'mean_filter', 'min_filter', 'max_filter',
        'savitzky_golay_filter', 'butterworth_filter', 'fft_cutoff_filter', 
        'chebyshev_filter', 'elliptical_filter'
    ]
    reducers = [
        'lttb_downsample', 'm4_downsample', 'rdp_downsample', 'minmaxlttb_downsample',
        'uniform_subsample', 'fpcs_downsample', 'tda_downsample'
    ]
    aggregators = ['asap_aggregator', 'bin_average_aggregator']
    
    # Get algorithms present in data and sort within each category
    algo_internal_names = set(summary_df['algorithm'].unique())
    
    transformers_sorted = sorted(
        [a for a in transformers if a in algo_internal_names],
        key=lambda x: get_algorithm_name(x)
    )
    reducers_sorted = sorted(
        [a for a in reducers if a in algo_internal_names],
        key=lambda x: get_algorithm_name(x)
    )
    aggregators_sorted = sorted(
        [a for a in aggregators if a in algo_internal_names],
        key=lambda x: get_algorithm_name(x)
    )
    
    # Combine all algorithms in order: transformers, reducers, aggregators
    algorithms = transformers_sorted + reducers_sorted + aggregators_sorted
    
    # Store category info for labels
    n_transformers = len(transformers_sorted)
    n_reducers = len(reducers_sorted)
    n_aggregators = len(aggregators_sorted)
    
    # Get metrics in the defined order (only include metrics that exist)
    all_metrics = summary_df['metric'].unique()
    metrics = [m for m in metric_order if m in all_metrics]
    
    n_algos = len(algorithms)
    n_metrics = len(metrics)
    
    # Create figure with adjusted spacing for gaps between categories
    fig_width = max(40, n_metrics * 2.0)
    fig_height = max(24, n_algos * 1.5)
    
    # Calculate height ratios with gaps between categories
    # Use fixed gap size for visual consistency
    height_ratios = []
    for i in range(n_algos):
        height_ratios.append(1.0)  # Normal row height
        # Add fixed gap after transformers section
        if i == n_transformers - 1 and n_reducers > 0:
            height_ratios.append(0.5)  # Fixed gap
        # Add larger gap after reducers section (before aggregators which only has 2 algorithms)
        elif i == n_transformers + n_reducers - 1 and n_aggregators > 0:
            height_ratios.append(1.5)  # Larger gap for aggregator section
    
    # Adjust total rows to include gaps
    total_rows = n_algos + (2 if n_reducers > 0 and n_aggregators > 0 else 0 if n_reducers == 0 else 1)
    
    fig = plt.figure(figsize=(fig_width, fig_height))
    gs = fig.add_gridspec(total_rows, n_metrics, hspace=0.08, wspace=0.02,
                         height_ratios=height_ratios)
    
    # Map algorithm index to grid row (accounting for gaps)
    def get_grid_row(algo_idx):
        if algo_idx < n_transformers:
            return algo_idx
        elif algo_idx < n_transformers + n_reducers:
            return algo_idx + 1  # Skip gap after transformers
        else:
            return algo_idx + 2  # Skip both gaps
    
    # Text colors: white for dark backgrounds (A, B, C), black for light backgrounds (D, F)
    text_colors = {
        'A': 'white',
        'B': 'white', 
        'C': 'white',
        'D': 'black',
        'F': 'black'
    }
    
    for i, algo in enumerate(algorithms):
        grid_row = get_grid_row(i)
        
        for j, metric in enumerate(metrics):
            ax = fig.add_subplot(gs[grid_row, j])
            
            # Get data for this combination
            row = summary_df[(summary_df['algorithm'] == algo) & (summary_df['metric'] == metric)]
            
            if len(row) == 0:
                ax.axis('off')
                continue
            
            row = row.iloc[0]
            
            # Debug: Print if this is a tied case
            if ',' in str(row['mode_grades']):
                print(f"TIE FOUND: {algo} + {metric} -> mode_grades='{row['mode_grades']}'")
            
            # Plot histogram
            grades = ['A', 'B', 'C', 'D', 'F']
            counts = [row['count_A'], row['count_B'], row['count_C'], row['count_D'], row['count_F']]
            max_count = max(counts) if max(counts) > 0 else 1
            x_positions = np.arange(len(grades))
            
            # Get mode grade(s) - can be multiple if tied
            mode_grades_list = [g.strip() for g in row['mode_grades'].split(',')]
            
            # Draw bars
            for x, count, grade in zip(x_positions, counts, grades):
                if count > 0:
                    color = GRADE_COLORS[grade]
                    # Highlight mode grade bar(s) with thick border
                    if grade in mode_grades_list:
                        ax.bar(x, count, color=color, edgecolor='black', linewidth=3, width=0.8)
                        
                        # Add mode grade annotation
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
            ax.set_ylim(-max_count * 0.25, max_count * 1.05)  # Reduced top margin since no TIE annotation
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
                ax.set_ylabel(get_algorithm_name(algo), fontsize=30, fontweight='bold',
                            rotation=0, ha='right', va='center', labelpad=10)
            
            if i == 0:
                metric_display = metric_display_names.get(metric, metric.replace('_', ' ').title())
                ax.set_title(metric_display, fontsize=30, fontweight='bold', pad=10, rotation=90, ha='center')
    
    # Add category labels on the left side
    # Calculate vertical spans for each category section
    
    def get_category_span(start_idx, count):
        """Get the start and end grid rows for a category section"""
        first_row = get_grid_row(start_idx)
        last_row = get_grid_row(start_idx + count - 1)
        return first_row, last_row
    
    def get_span_center_position(first_row, last_row):
        """Calculate center position accounting for height ratios"""
        # Sum heights from start to middle of span
        span_start_height = sum(height_ratios[:first_row])
        span_end_height = sum(height_ratios[:last_row + 1])
        center_height = (span_start_height + span_end_height) / 2
        total_height = sum(height_ratios)
        # Return figure coordinate (0 at bottom, 1 at top)
        return 1 - (center_height / total_height)
    
    if n_transformers > 0:
        # Add "Transformer" label
        first_row, last_row = get_category_span(0, n_transformers)
        y_pos = get_span_center_position(first_row, last_row)
        fig.text(0.001, y_pos, 'Transformer',
                rotation=90, va='center', ha='left', fontsize=42, fontweight='bold')
    
    if n_reducers > 0:
        # Add "Reducer" label
        first_row, last_row = get_category_span(n_transformers, n_reducers)
        y_pos = get_span_center_position(first_row, last_row)
        fig.text(0.001, y_pos, 'Reducer',
                rotation=90, va='center', ha='left', fontsize=42, fontweight='bold')
    
    if n_aggregators > 0:
        # Add "Aggregator" label - manually adjust up since only 2 algorithms
        first_row, last_row = get_category_span(n_transformers + n_reducers, n_aggregators)
        y_pos = get_span_center_position(first_row, last_row)
        # Adjust position upward by 2% of total figure height for better visual balance
        y_pos += 0.09
        fig.text(0.001, y_pos, 'Aggregator',
                rotation=90, va='center', ha='left', fontsize=42, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.savefig(str(output_path).replace('.svg', '.pdf'), bbox_inches='tight')
    print(f"✅ Saved: {output_path}")
    print(f"✅ Saved: {str(output_path).replace('.svg', '.pdf')}")
    plt.close()

def main():
    # Load data from algorithm_metric_mode_grades.csv
    grades_file = Path('plots/fc_visualizations/algorithm_metric_mode_grades.csv')
    if not grades_file.exists():
        print(f"❌ Error: {grades_file} not found")
        return
    
    print(f"📂 Loading data from {grades_file}")
    summary_df = load_and_prepare_data(grades_file)
    
    # Save summary (optional - for verification)
    output_csv = Path('plots/fc_visualizations/algorithm_metric_mode_summary.csv')
    summary_df.to_csv(output_csv, index=False)
    print(f"💾 Saved summary: {output_csv}")
    
    # Generate plot
    output_plot = Path('plots/fc_visualizations/algorithm_metric_histogram_grid_mode.svg')
    print("🎨 Generating histogram grid...")
    plot_histogram_grid(summary_df, output_plot)
    
    print("\n✅ Complete!")

if __name__ == '__main__':
    main()
