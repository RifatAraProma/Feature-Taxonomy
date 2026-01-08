import pandas as pd

# Read the variance data
df = pd.read_csv('plots/fc_visualizations/algorithm_metric_variance_table.csv')

# Metric order and display names - EXACTLY as in variance_table.tex
metrics = [
    'level_l1',
    'level_linf',
    'mean_delta',
    'regimes_delta',
    'extrema_wasserstein',
    'extrema_bottleneck',
    'spikes_dips_wasserstein',
    'spikes_dips_bottleneck',
    'slope_l1',
    'slope_linf',
    'curvature_l1',
    'curvature_linf',
    'trend_l1',
    'trend_linf',
    'regression_l1',
    'regression_linf',
    'periodicity_amplitude_delta',
    'periodicity_num_periods_delta',
    'roughness_delta',
    'noise_l1',
    'noise_linf'
]

# Metric names mapping for display - EXACTLY as in variance_table.tex
metric_display_names = {
    'level_l1': 'Level ℓ₁',
    'level_linf': 'Level ℓ∞',
    'mean_delta': 'Mean Δ',
    'regimes_delta': 'Regimes Δ',
    'extrema_wasserstein': 'Extrema W₁',
    'extrema_bottleneck': 'Extrema W∞',
    'spikes_dips_wasserstein': 'Spikes/Dips W₁',
    'spikes_dips_bottleneck': 'Spikes/Dips W∞',
    'slope_l1': 'Slope ℓ₁',
    'slope_linf': 'Slope ℓ∞',
    'curvature_l1': 'Curvature ℓ₁',
    'curvature_linf': 'Curvature ℓ∞',
    'trend_l1': 'Trend ℓ₁',
    'trend_linf': 'Trend ℓ∞',
    'regression_l1': 'Regression ℓ₁',
    'regression_linf': 'Regression ℓ∞',
    'periodicity_amplitude_delta': 'Periodicity Amplitude Δ',
    'periodicity_num_periods_delta': 'Periodicity Periods Δ',
    'roughness_delta': 'Roughness Δ',
    'noise_l1': 'Noise ℓ₁',
    'noise_linf': 'Noise ℓ∞'
}

# Algorithm name mapping - EXACTLY as in variance_table.tex
algo_display_names = {
    'asap_aggregator': 'ASAP',
    'bin_average_aggregator': 'PAA',
    'butterworth_filter': 'Butterworth',
    'chebyshev_filter': 'Chebyshev',
    'elliptical_filter': 'Elliptical',
    'fft_cutoff_filter': 'FFT Cutoff',
    'fpcs_downsample': 'FPCS',
    'gaussian_filter': 'Gaussian Filter',
    'lttb_downsample': 'LTTB',
    'm4_downsample': 'M4',
    'max_filter': 'Max Filter',
    'mean_filter': 'Mean Filter',
    'median_filter': 'Median Filter',
    'min_filter': 'Min Filter',
    'minmaxlttb_downsample': 'MinMaxLTTB',
    'rdp_simplify': 'Douglas-Peucker',
    'savitzky_golay_filter': 'Savitzky-Golay',
    'topology_lines': 'TopoLines',
    'uniform_subsample': 'Uniform Subsample'
}

# Algorithm order - EXACTLY as in variance_table.tex
algo_order = [
    'asap_aggregator',
    'bin_average_aggregator',
    'butterworth_filter',
    'chebyshev_filter',
    'elliptical_filter',
    'fft_cutoff_filter',
    'fpcs_downsample',
    'gaussian_filter',
    'lttb_downsample',
    'm4_downsample',
    'max_filter',
    'mean_filter',
    'median_filter',
    'min_filter',
    'minmaxlttb_downsample',
    'rdp_simplify',
    'savitzky_golay_filter',
    'topology_lines',
    'uniform_subsample'
]

# Reorder dataframe to match tex table order
df['algorithm'] = pd.Categorical(df['algorithm'], categories=algo_order, ordered=True)
df = df.sort_values('algorithm').reset_index(drop=True)

# Function to get color based on variance value - EXACTLY as in variance_table.tex
def get_color(value):
    # steelblue RGB(70,130,180) with opacity
    if value < 0.5:
        return '#ffffff'  # No color
    elif value <= 1.5:  # 0.5 to 1.5 inclusive
        return 'rgba(70,130,180,0.30)'  # steelblue!30
    else:  # > 1.5
        return 'rgba(70,130,180,0.70)'  # steelblue!70

def get_text_color(value):
    if value >= 1.0:
        return '#000000'  # Black text even for dark background for better contrast
    else:
        return '#000000'  # Black text

# SVG parameters
cell_width = 65
cell_height = 30
header_height = 140
row_height = 28
first_col_width = 140
legend_height = 60  # Space for legend

width = first_col_width + cell_width * len(metrics) + 20
height = header_height + row_height * len(df) + legend_height + 50  # 50 for top/bottom padding

# Start SVG
svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .header-text {{ font-family: Arial, sans-serif; font-size: 11px; font-weight: bold; }}
      .algo-text {{ font-family: Arial, sans-serif; font-size: 11px; font-weight: bold; }}
      .cell-text {{ font-family: Arial, sans-serif; font-size: 10px; }}
      .title {{ font-family: Arial, sans-serif; font-size: 14px; font-weight: bold; }}
    </style>
  </defs>
  
  <!-- Title -->
  <text x="{width/2}" y="20" text-anchor="middle" class="title">Algorithm × Metric Variance Table</text>
  <text x="{width/2}" y="38" text-anchor="middle" style="font-family: Arial; font-size: 10px; fill: #666;">(Darker = Higher Variance, White = Low Variance &lt; 0.5)</text>
  
  <!-- Header row -->
'''

# Algorithm column header
svg += f'''  <rect x="10" y="50" width="{cell_width + 50}" height="{header_height}" fill="#e0e0e0" stroke="#999" stroke-width="1"/>
  <text x="{10 + (cell_width + 50)/2}" y="115" text-anchor="middle" class="header-text">Algorithm</text>
'''

# Metric headers (rotated)
for i, metric in enumerate(metrics):
    x = 10 + cell_width + 50 + i * cell_width
    y = 50
    display_name = metric_display_names.get(metric, metric)
    
    svg += f'''  <rect x="{x}" y="{y}" width="{cell_width}" height="{header_height}" fill="#e0e0e0" stroke="#999" stroke-width="1"/>
  <g transform="translate({x + cell_width/2}, {y + header_height - 10}) rotate(-90)">
    <text text-anchor="start" class="header-text">{display_name}</text>
  </g>
'''

# Data rows
y_data_start = 50 + header_height
for row_idx, (_, row) in enumerate(df.iterrows()):
    y = y_data_start + row_idx * row_height
    algo = row['algorithm']
    display_algo = algo_display_names.get(algo, algo)
    
    # Algorithm name cell
    svg += f'''  <rect x="10" y="{y}" width="{cell_width + 50}" height="{row_height}" fill="#f5f5f5" stroke="#999" stroke-width="1"/>
  <text x="15" y="{y + row_height/2 + 4}" class="algo-text">{display_algo}</text>
'''
    
    # Variance values
    for col_idx, metric in enumerate(metrics):
        x = 10 + cell_width + 50 + col_idx * cell_width
        value = row[metric]
        bg_color = get_color(value)
        text_color = get_text_color(value)
        
        svg += f'''  <rect x="{x}" y="{y}" width="{cell_width}" height="{row_height}" fill="{bg_color}" stroke="#999" stroke-width="1"/>
  <text x="{x + cell_width/2}" y="{y + row_height/2 + 4}" text-anchor="middle" class="cell-text" fill="{text_color}">{value:.2f}</text>
'''

# Legend - positioned at bottom with proper spacing
table_bottom = y_data_start + len(df) * row_height
legend_y = table_bottom + 35  # 35px gap from table bottom
svg += f'''
  <!-- Legend -->
  <text x="10" y="{legend_y}" style="font-family: Arial; font-size: 11px; font-weight: bold;">Legend:</text>
  
  <rect x="80" y="{legend_y - 12}" width="30" height="15" fill="#ffffff" stroke="#999" stroke-width="1"/>
  <text x="115" y="{legend_y}" style="font-family: Arial; font-size: 10px;">&lt; 0.5 (Low)</text>
  
  <rect x="210" y="{legend_y - 12}" width="30" height="15" fill="rgba(70,130,180,0.30)" stroke="#999" stroke-width="1"/>
  <text x="245" y="{legend_y}" style="font-family: Arial; font-size: 10px;">0.5 - 1.5 (Moderate)</text>
  
  <rect x="370" y="{legend_y - 12}" width="30" height="15" fill="rgba(70,130,180,0.70)" stroke="#999" stroke-width="1"/>
  <text x="405" y="{legend_y}" style="font-family: Arial; font-size: 10px; fill: #000;">&gt; 1.5 (High)</text>
'''

svg += '\n</svg>'

# Save the SVG
with open('plots/pipeline/variance_table.svg', 'w', encoding='utf-8') as f:
    f.write(svg)

print("SVG variance table created successfully at plots/pipeline/variance_table.svg")
