"""
Generate deviation table showing % of datasets that deviated from mode grade
for each algorithm-metric combination
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, 'server')
from algorithm_names import get_algorithm_name

# Metric display names
metric_display_names = {
    'level_l1': r'Level $\ell_1$',
    'level_linf': r'Level $\ell_\infty$',
    'mean_delta': r'Mean $\delta$',
    'regimes_delta': r'Regimes $\delta$',
    'extrema_wasserstein': r'Extrema $W_1$',
    'extrema_bottleneck': r'Extrema $W_\infty$',
    'spikes_dips_wasserstein': r'Spikes & Dips $W_1$',
    'spikes_dips_bottleneck': r'Spikes & Dips $W_\infty$',
    'slope_l1': r'Slope $\ell_1$',
    'slope_linf': r'Slope $\ell_\infty$',
    'curvature_l1': r'Curvature $\ell_1$',
    'curvature_linf': r'Curvature $\ell_\infty$',
    'trend_l1': r'Trend $\ell_1$',
    'trend_linf': r'Trend $\ell_\infty$',
    'regression_l1': r'Regression $\ell_1$',
    'regression_linf': r'Regression $\ell_\infty$',
    'periodicity_amplitude_delta': r'Periodicity Amplitude $\delta$',
    'periodicity_num_periods_delta': r'Periodicity Periods $\delta$',
    'roughness_delta': r'Roughness $\delta$',
    'noise_l1': r'Noise $\ell_1$',
    'noise_linf': r'Noise $\ell_\infty$'
}

# Metric order
metric_order = [
    'level_l1', 'level_linf', 'mean_delta', 'regimes_delta',
    'extrema_wasserstein', 'extrema_bottleneck',
    'spikes_dips_wasserstein', 'spikes_dips_bottleneck',
    'slope_l1', 'slope_linf', 'curvature_l1', 'curvature_linf',
    'trend_l1', 'trend_linf', 'regression_l1', 'regression_linf',
    'periodicity_amplitude_delta', 'periodicity_num_periods_delta',
    'roughness_delta', 'noise_l1', 'noise_linf'
]

def load_deviation_data(csv_path):
    """Load deviation data directly from algorithm_metric_mode_grades.csv"""
    df = pd.read_csv(csv_path)
    
    # Select only needed columns
    return df[['algorithm', 'metric', 'deviation']].copy()

def create_deviation_table(deviation_df, output_path):
    """Create deviation table heatmap"""
    
    # Get algorithms and sort by display name
    algo_internal = deviation_df['algorithm'].unique()
    algorithms = sorted(algo_internal, key=lambda x: get_algorithm_name(x))
    
    # Get metrics in defined order
    all_metrics = deviation_df['metric'].unique()
    metrics = [m for m in metric_order if m in all_metrics]
    
    # Create pivot table - algorithms as rows (y-axis), metrics as columns (x-axis)
    pivot = deviation_df.pivot(index='algorithm', columns='metric', values='deviation')
    pivot = pivot.reindex(index=algorithms, columns=metrics)
    
    # Create figure
    n_algos = len(algorithms)
    n_metrics = len(metrics)
    
    fig_width = max(40, n_metrics * 2.5)
    fig_height = max(12, n_algos * 0.5)
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    
    # Create color mapping: 3 colors matching histogram - <25%, 25-50%, >50%
    def get_color(deviation):
        if pd.isna(deviation):
            return (0.95, 0.95, 0.95)  # Light gray for missing
        elif deviation < 25:
            return (1.0, 0.8, 0.4)  # Light orange
        elif deviation < 50:
            return (1.0, 0.6, 0.0)  # Medium orange
        else:
            return (0.9, 0.4, 0.0)  # Dark orange
    
    # Draw cells - make them wider (1.5 width instead of 1)
    cell_width = 1.5
    cell_height = 1
    
    for i, algo in enumerate(algorithms):
        for j, metric in enumerate(metrics):
            deviation = pivot.loc[algo, metric]
            color = get_color(deviation)
            
            # Draw cell
            rect = mpatches.Rectangle((j * cell_width, n_algos - i - 1), cell_width, cell_height,
                                      facecolor=color,
                                      edgecolor='white',
                                      linewidth=2)
            ax.add_patch(rect)
            
            # Add text if not missing
            if not pd.isna(deviation):
                text_color = 'black' if deviation < 50 else 'white'
                ax.text(j * cell_width + cell_width/2, n_algos - i - 0.5, f'{deviation:.2f}%',
                       ha='center', va='center',
                       fontsize=18, fontweight='bold',
                       color=text_color)
    
    # Set axis properties
    ax.set_xlim(0, n_metrics * cell_width)
    ax.set_ylim(0, n_algos)
    
    # Set ticks and labels
    ax.set_xticks(np.arange(n_metrics) * cell_width + cell_width/2)
    ax.set_xticklabels([metric_display_names.get(m, m) for m in metrics],
                       rotation=90, ha='center', fontsize=18)
    
    ax.set_yticks(np.arange(n_algos) + 0.5)
    ax.set_yticklabels([get_algorithm_name(a) for a in reversed(algorithms)],
                       fontsize=18)
    
    # Move x-axis labels to top
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')
    
    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Add legend - only 3 colors
    legend_elements = [
        mpatches.Patch(facecolor=(1.0, 0.8, 0.4), edgecolor='black', label='<25% (Consistent)'),
        mpatches.Patch(facecolor=(1.0, 0.6, 0.0), edgecolor='black', label='25-50% (Moderate)'),
        mpatches.Patch(facecolor=(0.9, 0.4, 0.0), edgecolor='black', label='>50% (Variable)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1),
             frameon=True, fontsize=18, title='Deviation Range', title_fontsize=18)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.savefig(str(output_path).replace('.svg', '.pdf'), bbox_inches='tight')
    print(f"✅ Saved: {output_path}")
    print(f"✅ Saved: {str(output_path).replace('.svg', '.pdf')}")
    plt.close()

def main():
    # Load deviation data from algorithm_metric_mode_grades.csv
    grades_file = Path('plots/fc_visualizations/algorithm_metric_mode_grades.csv')
    if not grades_file.exists():
        print(f"❌ Error: {grades_file} not found")
        print(f"   Run aggregate_mode_grades.py first to generate the CSV with deviation column")
        return
    
    print(f"📂 Loading deviation data from {grades_file}")
    deviation_df = load_deviation_data(grades_file)
    
    # Generate table
    output_path = Path('plots/pipeline/deviation_table.svg')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print("🎨 Generating deviation table...")
    create_deviation_table(deviation_df, output_path)
    
    # Print summary statistics
    print("\n" + "="*80)
    print("DEVIATION STATISTICS")
    print("="*80)
    print(f"Min deviation: {deviation_df['deviation'].min():.1f}%")
    print(f"Max deviation: {deviation_df['deviation'].max():.1f}%")
    print(f"Mean deviation: {deviation_df['deviation'].mean():.1f}%")
    print(f"Median deviation: {deviation_df['deviation'].median():.1f}%")
    print(f"\nDeviation distribution:")
    print(f"  <25% (very consistent): {(deviation_df['deviation'] < 25).sum()} combinations")
    print(f"  25-50% (consistent): {((deviation_df['deviation'] >= 25) & (deviation_df['deviation'] < 50)).sum()} combinations")
    print(f"  50-75% (moderate): {((deviation_df['deviation'] >= 50) & (deviation_df['deviation'] < 75)).sum()} combinations")
    print(f"  >75% (variable): {(deviation_df['deviation'] >= 75).sum()} combinations")
    
    print("\n✅ Complete!")

if __name__ == '__main__':
    main()
