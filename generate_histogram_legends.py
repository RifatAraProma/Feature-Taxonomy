"""
Generate separate legend figures for the algorithm-metric histogram grid
- Variance legend (background colors)
- Grade legend (bar colors)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# Grade colors (same as histogram grid)
GRADE_COLORS = {
    'A': '#006837',  # Dark green
    'B': '#31a354',  # Medium-dark green
    'C': '#78c679',  # Medium green
    'D': '#c2e699',  # Light green
    'F': '#ebfada'   # Very light green
}

def create_variance_legend(output_path='plots/fc_visualizations/variance_legend.pdf'):
    """Create variance background color legend"""
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.axis('off')
    
    # Steelblue RGB normalized
    steelblue_rgb = (0.27, 0.51, 0.71)
    
    # Create three boxes for variance levels
    y_pos = [2, 1, 0]
    labels = [
        'High Variance (≥1.5): Inconsistent across datasets',
        'Moderate Variance (0.5-1.5): Some variation',
        'Low Variance (<0.5): Consistent performance'
    ]
    alphas = [0.7, 0.3, 0.0]
    
    for y, label, alpha in zip(y_pos, labels, alphas):
        # Draw colored box
        if alpha > 0:
            box = mpatches.Rectangle((0, y), 0.5, 0.8, 
                                     facecolor=(*steelblue_rgb, alpha),
                                     edgecolor='black', linewidth=1)
        else:
            box = mpatches.Rectangle((0, y), 0.5, 0.8, 
                                     facecolor='white',
                                     edgecolor='black', linewidth=1)
        ax.add_patch(box)
        
        # Add label
        ax.text(0.6, y + 0.4, label, fontsize=14, va='center')
    
    ax.set_xlim(-0.1, 5)
    ax.set_ylim(-0.5, 3)
    
    plt.title('Background Color = Variance Across Datasets', 
             fontsize=16, fontweight='bold', pad=20)
    
    # Save
    Path(output_path).parent.mkdir(exist_ok=True, parents=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(output_path.replace('.pdf', '.svg'), bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved variance legend: {output_path}")
    print(f"✓ Saved variance legend: {output_path.replace('.pdf', '.svg')}")


def create_grade_legend(output_path='plots/fc_visualizations/grade_legend.pdf'):
    """Create grade bar color legend"""
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.axis('off')
    
    # Create bars for each grade
    grades = ['A', 'B', 'C', 'D', 'F']
    y_pos = [4, 3, 2, 1, 0]
    descriptions = [
        'Excellent (≥3.5)',
        'Good (2.5-3.5)',
        'Fair (1.5-2.5)',
        'Poor (0.5-1.5)',
        'Failing (<0.5)'
    ]
    
    for grade, y, desc in zip(grades, y_pos, descriptions):
        # Draw colored box
        box = mpatches.Rectangle((0, y), 0.5, 0.8, 
                                 facecolor=GRADE_COLORS[grade],
                                 edgecolor='gray', linewidth=0.5)
        ax.add_patch(box)
        
        # Add grade letter
        ax.text(0.25, y + 0.4, grade, fontsize=18, fontweight='bold',
               ha='center', va='center',
               color='white' if grade in ['A', 'B'] else 'black')
        
        # Add description
        ax.text(0.6, y + 0.4, desc, fontsize=14, va='center')
    
    ax.set_xlim(-0.1, 4)
    ax.set_ylim(-0.5, 5)
    
    plt.title('Bar Color = Grade Distribution\n(Black border indicates average grade)', 
             fontsize=16, fontweight='bold', pad=20)
    
    # Save
    Path(output_path).parent.mkdir(exist_ok=True, parents=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.savefig(output_path.replace('.pdf', '.svg'), bbox_inches='tight')
    plt.close()
    
    print(f"✓ Saved grade legend: {output_path}")
    print(f"✓ Saved grade legend: {output_path.replace('.pdf', '.svg')}")


if __name__ == '__main__':
    print("Generating histogram grid legends...")
    print()
    
    create_variance_legend()
    print()
    create_grade_legend()
    print()
    print("✅ All legends generated!")
