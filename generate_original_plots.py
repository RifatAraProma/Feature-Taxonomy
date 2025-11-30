"""
Generate SVG line charts for all original datasets using Vega-Lite.

Creates simple line visualizations matching the frontend ChartPanel dimensions:
- Width: 1000px
- Height: 375px
- Color: #707475

Output: SVG files in plots/original/ directory
"""

import json
import glob
from pathlib import Path
import altair as alt
import pandas as pd

# Chart dimensions matching ChartPanel.tsx
WIDTH = 1000
HEIGHT = 375
LINE_COLOR = '#707475'

def load_all_datasets():
    """Load all datasets from data/ directory."""
    datasets = {}
    data_folders = glob.glob("data/*/")
    
    for folder in data_folders:
        category = Path(folder).name
        json_files = glob.glob(f"{folder}*.json")
        
        for json_file in json_files:
            dataset_name = Path(json_file).stem
            with open(json_file, 'r') as f:
                data = json.load(f)
                # Data format: {"id": "...", "y": [...]} or just [...]
                if isinstance(data, dict):
                    y_values = data.get('y', data.get('values', []))
                else:
                    y_values = data
                
                datasets[dataset_name] = y_values
    
    return datasets

def create_line_chart(dataset_name, y_values):
    """Create a Vega-Lite line chart for the dataset."""
    # Create DataFrame with time index
    df = pd.DataFrame({
        't': list(range(1, len(y_values) + 1)),
        'y': y_values
    })
    
    # Create Vega-Lite chart
    chart = alt.Chart(df).mark_line(
        color=LINE_COLOR,
        strokeWidth=2
    ).encode(
        x=alt.X('t:Q', 
                title=None,
                axis=alt.Axis(labels=False, ticks=False, title=None)),
        y=alt.Y('y:Q', 
                title=None,
                axis=alt.Axis(labels=False, ticks=False, title=None))
    ).properties(
        width=WIDTH,
        height=HEIGHT
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=True,
        gridOpacity=0.2
    )
    
    return chart

def main():
    """Generate SVG plots for all datasets."""
    print("Loading datasets...")
    datasets = load_all_datasets()
    print(f"Found {len(datasets)} datasets")
    
    output_dir = Path("plots/original")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nGenerating SVG plots...")
    for dataset_name, y_values in sorted(datasets.items()):
        # Create chart
        chart = create_line_chart(dataset_name, y_values)
        
        # Save as SVG
        output_path = output_dir / f"{dataset_name}.svg"
        chart.save(str(output_path))
        
        print(f"  ✓ {dataset_name}.svg ({len(y_values)} points)")
    
    print(f"\n✅ Generated {len(datasets)} SVG files in {output_dir}/")

if __name__ == "__main__":
    main()
