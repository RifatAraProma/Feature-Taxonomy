"""
Generate a horizontal algorithm legend showing all algorithm colors.
Creates a simple color box legend for use in papers/presentations.
"""
import sys
sys.path.insert(0, 'server')

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from algorithm_colors import ALGORITHM_COLORS
from algorithm_names import ALGORITHM_NAMES

# Group algorithms by type in the specified order
TRANSFORMERS = [
    'gaussian_filter',          # Gaussian filter
    'mean_filter',              # Mean filter
    'median_filter',            # Median filter
    'min_filter',               # Min filter
    'max_filter',               # Max filter
    'savitzky_golay_filter',    # Savitzky-Golay
    'fft_cutoff_filter',        # FFT cutoff filter
    'butterworth_filter',       # Butterworth
    'chebyshev_filter',         # Chebyshev
    'elliptical_filter'         # Elliptic
]

REDUCERS = [
    'uniform_subsample',        # Uniform subsampling
    'rdp_downsample',           # Douglas-Peucker (RDP)
    'lttb_downsample',          # LTTB
    'minmaxlttb_downsample',    # MinMax-LTTB
    'm4_downsample',            # M4
    'fpcs_downsample',          # FPCS
    'tda_downsample'            # TopoLines
]

AGGREGATORS = [
    'asap_aggregator',          # ASAP
    'bin_average_aggregator'    # PAA
]

def create_horizontal_legend():
    """Create a horizontal legend with all algorithms grouped by type in 3 rows."""
    
    fig, ax = plt.subplots(figsize=(22, 5.5))
    ax.axis('off')
    
    # Starting positions
    y_pos = 0.67  # Start higher for 3 rows
    x_start = 0.01
    x_pos = x_start
    box_width = 0.048  # Uniform width for all boxes
    box_height = 0.12
    spacing = 0.052  # Consistent spacing
    
    # Row 1: Transformers
    ax.text(x_pos - 0.005, y_pos + box_height + 0.12, 'Transformers', 
            fontsize=11, fontweight='bold', verticalalignment='bottom')
    
    for algo in TRANSFORMERS:
        color = ALGORITHM_COLORS[algo]
        name = ALGORITHM_NAMES[algo]
        
        # Draw label on TOP of box (rotated 90 degrees)
        ax.text(x_pos + box_width/2, y_pos + box_height + 0.02, name, 
                fontsize=10, horizontalalignment='left', verticalalignment='bottom',
                rotation=90)
        
        # Draw color box
        rect = mpatches.Rectangle((x_pos, y_pos), box_width, box_height, 
                                   facecolor=color, edgecolor='black', linewidth=0.8)
        ax.add_patch(rect)
        
        x_pos += spacing
    
    # Row 2: Reducers
    x_pos = x_start
    y_pos = 0.38
    
    ax.text(x_pos - 0.005, y_pos + box_height + 0.12, 'Reducers', 
            fontsize=11, fontweight='bold', verticalalignment='bottom')
    
    for algo in REDUCERS:
        color = ALGORITHM_COLORS[algo]
        name = ALGORITHM_NAMES[algo]
        
        # Draw label on TOP of box (rotated 90 degrees)
        ax.text(x_pos + box_width/2, y_pos + box_height + 0.02, name,
                fontsize=10, horizontalalignment='left', verticalalignment='bottom',
                rotation=90)
        
        # Draw color box
        rect = mpatches.Rectangle((x_pos, y_pos), box_width, box_height,
                                   facecolor=color, edgecolor='black', linewidth=0.8)
        ax.add_patch(rect)
        
        x_pos += spacing
    
    # Row 3: Aggregators (separate row)
    x_pos = x_start
    y_pos = 0.09
    
    ax.text(x_pos - 0.005, y_pos + box_height + 0.12, 'Aggregators', 
            fontsize=11, fontweight='bold', verticalalignment='bottom')
    
    for algo in AGGREGATORS:
        color = ALGORITHM_COLORS[algo]
        name = ALGORITHM_NAMES[algo]
        
        # Draw label on TOP of box (rotated 90 degrees)
        ax.text(x_pos + box_width/2, y_pos + box_height + 0.02, name,
                fontsize=10, horizontalalignment='left', verticalalignment='bottom',
                rotation=90)
        
        # Draw color box
        rect = mpatches.Rectangle((x_pos, y_pos), box_width, box_height,
                                   facecolor=color, edgecolor='black', linewidth=0.8)
        ax.add_patch(rect)
        
        x_pos += spacing
    
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    
    # Save in multiple formats (no PNG)
    output_dir = 'plots/fc_visualizations'
    plt.savefig(f'{output_dir}/algorithm_legend.svg', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.savefig(f'{output_dir}/algorithm_legend.pdf', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    
    print('✅ Saved: plots/fc_visualizations/algorithm_legend.svg')
    print('✅ Saved: plots/fc_visualizations/algorithm_legend.pdf')
    
    plt.close()


def create_compact_legend():
    """Create a compact single-row legend (all algorithms side by side)."""
    
    fig, ax = plt.subplots(figsize=(24, 2))
    ax.axis('off')
    
    # Get all algorithms in order
    all_algorithms = TRANSFORMERS + REDUCERS + AGGREGATORS
    
    y_pos = 0.2
    x_start = 0.005
    x_pos = x_start
    box_width = 0.048  # Uniform width
    box_height = 0.25
    spacing = 0.052
    
    for algo in all_algorithms:
        color = ALGORITHM_COLORS[algo]
        name = ALGORITHM_NAMES[algo]
        
        # Draw label on TOP of box (rotated 90 degrees)
        ax.text(x_pos + box_width/2, y_pos + box_height + 0.05, name,
                fontsize=10, horizontalalignment='left', verticalalignment='bottom',
                rotation=90)
        
        # Draw color box
        rect = mpatches.Rectangle((x_pos, y_pos), box_width, box_height,
                                   facecolor=color, edgecolor='black', linewidth=0.8)
        ax.add_patch(rect)
        
        x_pos += spacing
    
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    
    # Save in multiple formats (no PNG)
    output_dir = 'plots/fc_visualizations'
    plt.savefig(f'{output_dir}/algorithm_legend_compact.svg', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.savefig(f'{output_dir}/algorithm_legend_compact.pdf', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    
    print('✅ Saved: plots/fc_visualizations/algorithm_legend_compact.svg')
    print('✅ Saved: plots/fc_visualizations/algorithm_legend_compact.pdf')
    
    plt.close()


if __name__ == '__main__':
    print('='*80)
    print('ALGORITHM LEGEND GENERATOR')
    print('='*80)
    
    print('\nGenerating grouped legend (3 rows by algorithm type)...')
    create_horizontal_legend()
    
    print('\nGenerating compact legend (single row, all algorithms)...')
    create_compact_legend()
    
    print('\n' + '='*80)
    print('✅ LEGEND GENERATION COMPLETE')
    print('='*80)
