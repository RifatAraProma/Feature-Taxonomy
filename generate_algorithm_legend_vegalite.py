"""
Generate algorithm legend using Vega-Lite (matching generate_vegalite_plots.py style)
Creates both SVG and PDF versions
"""

import sys
sys.path.insert(0, 'server')

import pandas as pd
import altair as alt
from pathlib import Path
from algorithm_colors import ALGORITHM_COLORS
from algorithm_names import get_algorithm_name

def create_algorithm_legend():
    """
    Create a standalone algorithm color legend with horizontal layout.
    Uses the same style as generate_vegalite_plots.py
    """
    
    # Get all algorithms and sort alphabetically by display name
    all_algorithms = list(ALGORITHM_COLORS.keys())
    
    # Create legend data sorted alphabetically by algorithm display name
    legend_rows = []
    for algo in all_algorithms:
        legend_rows.append({
            'algorithm': algo,
            'algorithm_name': get_algorithm_name(algo),
            'color': ALGORITHM_COLORS.get(algo, '#999999')
        })
    
    legend_data = pd.DataFrame(legend_rows)
    # Sort alphabetically by algorithm_name
    #legend_data = legend_data.sort_values('algorithm_name').reset_index(drop=True)
    legend_data['order'] = range(len(legend_data))
    
    # Create horizontal legend with rectangles and text labels on top
    chart = alt.Chart(legend_data).mark_rect(
        stroke='black',
        strokeWidth=0.5,
        size=1440  # Increased by 20% (1200 * 1.2)
    ).encode(
        x=alt.X('order:O', 
                title='',
                axis=None,
                scale=alt.Scale(paddingInner=0.5, paddingOuter=0.1)),  # Increase padding between boxes
        color=alt.Color('algorithm:N',
                       scale=alt.Scale(domain=legend_data['algorithm'].tolist(),
                                     range=legend_data['color'].tolist()),
                       legend=None),
        tooltip=['algorithm_name:N']
    ).properties(
        width=3000,  # Increased to accommodate wider boxes
        height=50  # Increased height for taller boxes
    )
    
    # Add text labels on top with larger font and proper spacing
    text = alt.Chart(legend_data).mark_text(
        dy=-35,  # Increased gap between text and boxes
        fontSize=16,
        fontWeight='normal',
        angle=0,
        align='center'
    ).encode(
        x=alt.X('order:O', axis=None),
        text='algorithm_name:N',
        color=alt.value('black')
    )
    
    # Combine rectangles and text
    final_chart = (chart + text).configure_view(
        strokeWidth=0
    )
    
    return final_chart


def main():
    print("\n" + "=" * 80)
    print("ALGORITHM LEGEND GENERATOR (Vega-Lite)")
    print("=" * 80)
    
    # Create output directory
    output_dir = Path('plots/fc_visualizations')
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate legend
    print("\n📊 Generating algorithm legend...")
    chart = create_algorithm_legend()
    
    # Save as SVG
    svg_path = output_dir / 'algorithm_legend.svg'
    chart.save(str(svg_path))
    print(f"  ✅ SVG saved: {svg_path}")
    
    # Save as PDF
    pdf_path = output_dir / 'algorithm_legend.pdf'
    chart.save(str(pdf_path))
    print(f"  ✅ PDF saved: {pdf_path}")
    
    print("\n" + "=" * 80)
    print("✅ LEGEND GENERATION COMPLETE!")
    print("=" * 80)


if __name__ == '__main__':
    main()
