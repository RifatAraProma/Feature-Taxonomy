"""
Generate static smoothed visualization for Evaluation Pipeline tab.
Creates a plot of Gaussian filter at level 50 on Apple stock for demonstration.
Matches the original plot style: no titles, no labels, no ticks - just the lines.
"""

import json
import os
import altair as alt
import pandas as pd

# Load Gaussian filter level 50 data
with open('precomputed/stock_aapl_price/gaussian_filter_level_50.json', 'r') as f:
    level_data = json.load(f)

# Extract smoothed data
smoothed_y = level_data['output']

# Also load original data for comparison
with open('data/stock_price/stock_aapl_price.json', 'r') as f:
    original_y = json.load(f)  # It's a list, not a dict

# Create DataFrame with both series
df = pd.DataFrame({
    't': list(range(1, len(original_y) + 1)),
    'original': original_y,
    'smoothed': smoothed_y
})

# Chart dimensions matching original plots
WIDTH = 1000
HEIGHT = 375

# Create base for original (transparent stroke)
original_line = alt.Chart(df).mark_line(
    color='#707475',
    strokeWidth=2,
    opacity=0  # Fully transparent - keeps the scale but invisible
).encode(
    x=alt.X('t:Q', 
            title=None,
            axis=alt.Axis(labels=False, ticks=False, title=None)),
    y=alt.Y('original:Q', 
            title=None,
            axis=alt.Axis(labels=False, ticks=False, title=None))
)

# Create smoothed line (purple, visible)
smoothed_line = alt.Chart(df).mark_line(
    color='#9c27b0',
    strokeWidth=2
).encode(
    x=alt.X('t:Q', 
            title=None,
            axis=alt.Axis(labels=False, ticks=False, title=None)),
    y=alt.Y('smoothed:Q', 
            title=None,
            axis=alt.Axis(labels=False, ticks=False, title=None))
)

# Layer both charts
chart = alt.layer(original_line, smoothed_line).properties(
    width=WIDTH,
    height=HEIGHT
).configure_view(
    strokeWidth=0
).configure_axis(
    grid=True,
    gridOpacity=0.2
)

# Create output directory
os.makedirs('plots/pipeline', exist_ok=True)

# Save the chart
chart.save('plots/pipeline/gaussian_smoothed_overlay.svg')
print("✓ Generated plots/pipeline/gaussian_smoothed_overlay.svg")
