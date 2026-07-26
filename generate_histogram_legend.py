"""
Generate horizontal legend for histogram grids showing grade colors and variance colors
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# Grade colors - Purple gradient
GRADE_COLORS = {
    'F': '#e6d5f5',
    'D': '#c9a8e8',
    'C': '#9b6fd9',
    'B': '#7340b8',
    'A': '#4a1a7a'
}

# Variance colors - Orange gradient
VARIANCE_COLORS = {
    '<25%': (1.0, 0.8, 0.4),    # Light orange
    '25-50%': (1.0, 0.6, 0.0),  # Medium orange
    '>50%': (0.9, 0.4, 0.0)     # Dark orange
}

# Text colors for grades
GRADE_TEXT_COLORS = {
    'A': 'white',
    'B': 'white',
    'C': 'white',
    'D': 'black',
    'F': 'black'
}

def create_legend():
    """Create horizontal legend with grade boxes and variance boxes"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 1.5), 
                                     gridspec_kw={'wspace': 0.5})
    
    # Grade legend
    grades = ['A', 'B', 'C', 'D', 'F']
    for i, grade in enumerate(grades):
        color = GRADE_COLORS[grade]
        text_color = GRADE_TEXT_COLORS[grade]
        
        # Draw colored box
        rect = mpatches.Rectangle((i * 1.2, 0), 1, 1, 
                                   facecolor=color, 
                                   edgecolor='black', 
                                   linewidth=1.5)
        ax1.add_patch(rect)
        
        # Add grade letter in center of box
        ax1.text(i * 1.2 + 0.5, 0.5, grade, 
                ha='center', va='center', 
                fontsize=20, fontweight='bold',
                color=text_color)
    
    ax1.set_xlim(-0.2, len(grades) * 1.2)
    ax1.set_ylim(-0.2, 1.2)
    ax1.axis('off')
    ax1.set_aspect('equal')
    
    # Variance legend
    variance_labels = ['<25%', '25-50%', '>50%']
    for i, label in enumerate(variance_labels):
        color = VARIANCE_COLORS[label]
        
        # Draw colored box - same height as grade boxes (1 unit), but wider (2.0 instead of 1.5)
        rect = mpatches.Rectangle((i * 2.2, 0), 2.0, 1, 
                                   facecolor=color, 
                                   edgecolor='black', 
                                   linewidth=1.5)
        ax2.add_patch(rect)
        
        # Add label below box
        ax2.text(i * 2.2 + 1.0, -0.35, label, 
                ha='center', va='top', 
                fontsize=14, fontweight='bold')
    
    ax2.set_xlim(-0.2, len(variance_labels) * 2.2)
    ax2.set_ylim(-0.7, 1.2)
    ax2.axis('off')
    ax2.set_aspect('equal')
    
    # Save
    output_svg = Path('plots/fc_visualizations/histogram_legend.svg')
    output_pdf = Path('plots/fc_visualizations/histogram_legend.pdf')
    
    plt.tight_layout()
    plt.savefig(output_svg, bbox_inches='tight', dpi=150)
    plt.savefig(output_pdf, bbox_inches='tight')
    
    print(f"✅ Saved: {output_svg}")
    print(f"✅ Saved: {output_pdf}")
    plt.close()

if __name__ == '__main__':
    create_legend()
