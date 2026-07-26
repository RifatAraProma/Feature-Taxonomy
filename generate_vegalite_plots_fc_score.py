"""
Generate Vega-Lite SVG plots for feature preservation analysis.

Creates plots for each metric showing FC (Feature-Complexity) score analysis:
- Default mode: 2 plots (zscore_fc + ranking)
- Breakdown mode (--breakdown): 3 plots (raw + zscore_fc + ranking)

Output: SVG files organized by dataset in plots/ directory
"""

import json
import glob
import numpy as np
import pandas as pd
from pathlib import Path
import altair as alt
import sys
import argparse

# Add server directory to path to import algorithm colors and names
sys.path.insert(0, str(Path(__file__).parent / 'server'))
from algorithm_colors import ALGORITHM_COLORS, get_algorithm_color
from algorithm_names import get_algorithm_name


def format_metric_label(metric_name: str) -> str:
    """
    Convert metric names to proper mathematical notation.
    
    Examples:
        level_l1 -> L₁-Norm for Level
        level_linf -> L∞-Norm for Level
        slope_delta -> Δ for Slope
        extrema_bottleneck -> Bottleneck Distance for Extrema
    """
    # Split into feature and metric
    parts = metric_name.split('_')
    
    if len(parts) < 2:
        return metric_name.replace('_', ' ').title()
    
    # Last part is the metric type, rest is feature name
    metric_type = parts[-1]
    feature_name = '_'.join(parts[:-1])
    
    # Format feature name
    feature_label = feature_name.replace('_', ' ').title()
    
    # Format metric type with proper notation
    metric_mappings = {
        'l1': 'L₁-Norm',
        'linf': 'L∞-Norm',
        'delta': 'Δ',
        'bottleneck': 'Bottleneck Distance',
        'wasserstein': 'Wasserstein Distance',
        'auc_delta': 'AUC Δ',
        'amplitude_delta': 'Amplitude Δ',
        'num_periods_delta': 'Period Count Δ'
    }
    
    metric_label = metric_mappings.get(metric_type, metric_type.replace('_', ' ').title())
    
    return f"{metric_label} for {feature_label}"


def load_precomputed_data(dataset_name="stock_aapl_price", sample_size=None):
    """
    Load all precomputed level files for a dataset.
    
    Args:
        dataset_name: Name of dataset
        sample_size: If set, only load this many files (for testing)
    
    Returns:
        DataFrame with columns: algorithm, level, pae, metric_name, metric_value
    """
    data_rows = []
    
    # Get all JSON files in the precomputed directory
    pattern = f"precomputed/{dataset_name}/*_level_*.json"
    files = glob.glob(pattern)
    
    if sample_size:
        files = files[:sample_size]
    
    print(f"Loading {len(files)} precomputed files for {dataset_name}...")
    
    for filepath in files:
        try:
            with open(filepath, 'r') as f:
                level_data = json.load(f)
            
            # Extract algorithm name and level from filename
            filename = Path(filepath).stem  # e.g., "gaussian_filter_level_50"
            parts = filename.rsplit('_level_', 1)
            algorithm = parts[0]
            level = int(parts[1])
            
            # Extract PAE
            pae = level_data.get('pae')
            
            # Extract all feature preservation metrics
            feature_preservation = level_data.get('feature_preservation', {})
            
            # Flatten nested metrics
            for feature_group, metrics in feature_preservation.items():
                if isinstance(metrics, dict):
                    for metric_name, metric_value in metrics.items():
                        if metric_value is not None:
                            # Skip change_points l1 and linf (as requested)
                            if feature_group == 'change_points' and metric_name in ['l1', 'linf']:
                                continue
                            
                            data_rows.append({
                                'algorithm': algorithm,
                                'level': level,
                                'pae': pae,
                                'feature_group': feature_group,
                                'metric_name': metric_name,
                                'full_metric_name': f"{feature_group}_{metric_name}",
                                'metric_value': metric_value
                            })
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    
    df = pd.DataFrame(data_rows)
    print(f"Loaded {len(df)} metric samples from {df['algorithm'].nunique()} algorithms")
    print(f"Metrics: {sorted(df['full_metric_name'].unique())}")
    
    return df


def create_ranking_plot(df, metric_name, dataset_name):
    """
    Create algorithm ranking plot for a specific metric using Vega-Lite.
    
    Ranks algorithms by mean FC (Feature-Complexity) score from high to low.
    Higher FC scores indicate better feature preservation with lower complexity.
    FC Score = Preservation_z - PAE_z
    """
    # Filter for this metric
    metric_df = df[df['full_metric_name'] == metric_name].copy()
    
    if len(metric_df) == 0:
        print(f"No data for metric: {metric_name}")
        return None
    
    # Compute z-scores
    pae_mean = metric_df['pae'].mean()
    pae_std = metric_df['pae'].std()
    metric_mean = metric_df['metric_value'].mean()
    metric_std = metric_df['metric_value'].std()
    
    metric_df['pae_z'] = (metric_df['pae'] - pae_mean) / pae_std
    metric_df['metric_z'] = (metric_df['metric_value'] - metric_mean) / metric_std
    
    # Convert to preservation z-score
    # All metrics are errors (lower is better), so preservation = -error
    metric_df['preservation_z'] = -metric_df['metric_z']
    
    # FC Score = Preservation_z - PAE_z
    metric_df['fc_score'] = metric_df['preservation_z'] - metric_df['pae_z']
    
    # Aggregate by algorithm
    summary = metric_df.groupby('algorithm').agg({
        'fc_score': ['mean', 'std'],
        'pae': 'mean',
        'metric_value': 'mean'
    }).reset_index()
    
    summary.columns = ['algorithm', 'mean_fc_score', 'std_fc_score', 'mean_pae', 'mean_metric']
    summary = summary.sort_values('mean_fc_score', ascending=False).reset_index(drop=True)
    summary['rank'] = range(1, len(summary) + 1)
    
    # Add display names for algorithms
    summary['algorithm_name'] = summary['algorithm'].apply(get_algorithm_name)
    
    # Add color mapping
    summary['color'] = summary['algorithm'].map(ALGORITHM_COLORS)
    
    # Add error bar bounds for visualization
    summary['lower_bound'] = summary['mean_fc_score'] - summary['std_fc_score']
    summary['upper_bound'] = summary['mean_fc_score'] + summary['std_fc_score']
    
    # Create explicit sort order from pre-sorted data (descending by FC score)
    # Use display names for the sort order
    algorithm_name_order = summary['algorithm_name'].tolist()
    
    # Create base bar chart
    bars = alt.Chart(summary).mark_bar().encode(
        x=alt.X('mean_fc_score:Q', 
                title='Feature-Complexity Score',
                scale=alt.Scale(zero=False)),
        y=alt.Y('algorithm_name:N', 
                title='Algorithm', 
                sort=algorithm_name_order),
        color=alt.Color('algorithm:N', 
                       scale=alt.Scale(domain=list(ALGORITHM_COLORS.keys()), 
                                     range=list(ALGORITHM_COLORS.values())),
                       legend=None),
        tooltip=[
            alt.Tooltip('rank:Q', title='Rank'),
            alt.Tooltip('algorithm_name:N', title='Algorithm'),
            alt.Tooltip('mean_fc_score:Q', title='Mean FC Score', format='.4f'),
            alt.Tooltip('std_fc_score:Q', title='Std Dev', format='.4f'),
            alt.Tooltip('mean_pae:Q', title='Mean PAE', format='.6f'),
            alt.Tooltip('mean_metric:Q', title=f'Mean {metric_name}', format='.4f')
        ]
    )
    
    # Add error bars
    error_bars = alt.Chart(summary).mark_errorbar(color='black').encode(
        x=alt.X('lower_bound:Q'),
        x2=alt.X2('upper_bound:Q'),
        y=alt.Y('algorithm_name:N', 
                title='Algorithm',
                sort=algorithm_name_order)
    )
    
    # Add text labels showing mean ± std
    text = alt.Chart(summary).mark_text(
        align='left',
        baseline='middle',
        dx=5,
        fontSize=9,
        fontWeight='bold'
    ).encode(
        x='mean_fc_score:Q',
        y=alt.Y('algorithm_name:N', 
                title='Algorithm',
                sort=algorithm_name_order),
        text=alt.Text('mean_fc_score:Q', format='.3f'),
        color=alt.value('black')
    )
    
    # Combine layers
    chart = (bars + error_bars + text).properties(
        width=700,
        height=550  # Match z-score plot height
    )
    
    return chart


def create_zscore_plot(df, metric_name, dataset_name):
    """
    Create z-score breakdown plot showing PAE z-score vs Feature Preservation z-score.
    
    - X-axis: Z-normalized Pixel Approximate Entropy (PAE)
    - Y-axis: Z-normalized Feature Preservation
    - Diagonal lines: Iso-FC (Feature-Complexity) score contours
    - FC Score = Preservation_z - PAE_z
    
    All feature metrics are errors, so preservation = -error
    """
    # Filter for this metric
    metric_df = df[df['full_metric_name'] == metric_name].copy()
    
    if len(metric_df) == 0:
        return None
    
    # Compute z-scores for PAE
    pae_mean = metric_df['pae'].mean()
    pae_std = metric_df['pae'].std()
    metric_df['pae_z'] = (metric_df['pae'] - pae_mean) / pae_std
    
    # Compute z-scores for metric value
    metric_mean = metric_df['metric_value'].mean()
    metric_std = metric_df['metric_value'].std()
    metric_df['metric_z'] = (metric_df['metric_value'] - metric_mean) / metric_std
    
    # Convert to preservation z-score
    # All metrics are errors (lower is better), so preservation = -error
    metric_df['preservation_z'] = -metric_df['metric_z']
    
    # FC Score = Preservation_z - PAE_z
    metric_df['fc_score'] = metric_df['preservation_z'] - metric_df['pae_z']
    
    # Add display names for algorithms
    metric_df['algorithm_name'] = metric_df['algorithm'].apply(get_algorithm_name)
    
    # Add color mapping
    metric_df['color'] = metric_df['algorithm'].map(ALGORITHM_COLORS)
    
    # Get data range for tight axis bounds FIRST
    pae_z_range = [metric_df['pae_z'].min(), metric_df['pae_z'].max()]
    pres_z_range = [metric_df['preservation_z'].min(), metric_df['preservation_z'].max()]
    
    # Add 5% padding to data range
    pae_z_padding = (pae_z_range[1] - pae_z_range[0]) * 0.05
    pres_z_padding = (pres_z_range[1] - pres_z_range[0]) * 0.05
    
    pae_z_domain = [pae_z_range[0] - pae_z_padding, pae_z_range[1] + pae_z_padding]
    pres_z_domain = [pres_z_range[0] - pres_z_padding, pres_z_range[1] + pres_z_padding]
    
    # Create diagonal contour lines WITHIN the domain bounds
    # FC = preservation_z - pae_z, so preservation_z = pae_z + FC
    fc_contours = []
    fc_values = [-2, -1, 0, 1, 2]  # FC score contour values
    
    for fc_val in fc_values:
        # Create line data: y = x + fc_val, clipped to domain
        line_data = pd.DataFrame({
            'x': [pae_z_domain[0], pae_z_domain[1]],
            'y': [pae_z_domain[0] + fc_val, pae_z_domain[1] + fc_val],
            'fc_label': [f'FC={fc_val}', '']
        })
        fc_contours.append(line_data)
    
    # Combine all contour line data
    contour_df = pd.concat(fc_contours, keys=fc_values)
    contour_df = contour_df.reset_index(level=0).rename(columns={'level_0': 'fc_value'})
    
    # Create scatter plot: PAE z-score (x) vs Feature Preservation z-score (y)
    scatter = alt.Chart(metric_df).mark_circle(size=60, opacity=0.6).encode(
        x=alt.X('pae_z:Q', 
                title='Z-Normalized Pixel Approximate Entropy', 
                scale=alt.Scale(domain=pae_z_domain, nice=False)),
        y=alt.Y('preservation_z:Q', 
                title='Z-Normalized Feature Preservation', 
                scale=alt.Scale(domain=pres_z_domain, nice=False)),
        color=alt.Color('algorithm:N',
                       scale=alt.Scale(domain=list(ALGORITHM_COLORS.keys()),
                                     range=list(ALGORITHM_COLORS.values())),
                       legend=None),
        tooltip=[
            alt.Tooltip('algorithm_name:N', title='Algorithm'),
            alt.Tooltip('level:Q', title='Level'),
            alt.Tooltip('pae_z:Q', title='PAE Z-Score', format='.4f'),
            alt.Tooltip('preservation_z:Q', title='Preservation Z-Score', format='.4f'),
            alt.Tooltip('fc_score:Q', title='FC Score', format='.4f')
        ]
    )
    
    # Add diagonal FC score contour lines (iso-FC lines) - CLIPPED to axis domain
    fc_lines = alt.Chart(contour_df).mark_line(
        strokeDash=[3, 3],
        opacity=0.4,
        color='gray',
        clip=True  # Clip lines to axis bounds
    ).encode(
        x=alt.X('x:Q', scale=alt.Scale(domain=pae_z_domain, nice=False)),
        y=alt.Y('y:Q', scale=alt.Scale(domain=pres_z_domain, nice=False)),
        detail='fc_value:N'
    )
    
    # Add labels for FC score contours - only show labels within bounds
    label_df = pd.DataFrame([
        {'x': pae_z_domain[1] * 0.95, 'y': pae_z_domain[1] * 0.95 + fc_val, 'label': f'FC={fc_val}'}
        for fc_val in fc_values
        if pres_z_domain[0] <= (pae_z_domain[1] * 0.95 + fc_val) <= pres_z_domain[1]  # Only labels within y-bounds
    ])
    
    fc_labels = alt.Chart(label_df).mark_text(
        align='left',
        dx=5,
        fontSize=9,
        color='gray',
        opacity=0.6
    ).encode(
        x='x:Q',
        y='y:Q',
        text='label:N'
    )
    
    # Add reference lines at z=0
    hline = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='red', strokeDash=[5, 5]).encode(y='y:Q')
    vline = alt.Chart(pd.DataFrame({'x': [0]})).mark_rule(color='red', strokeDash=[5, 5]).encode(x='x:Q')
    
    # Combine all layers
    chart = (fc_lines + scatter + hline + vline + fc_labels).properties(
        width=700,
        height=550
    )
    
    return chart


def create_raw_scatter_plot(df, metric_name, dataset_name):
    """
    Create raw (pre-normalization) scatter plot showing PAE vs Metric Value.
    
    This plot shows why normalization is necessary - different scales make 
    direct comparison difficult.
    
    - X-axis: Raw PAE (Pixel Approximate Entropy)
    - Y-axis: Raw Metric Value (error metric, not negated)
    - Color: Algorithm
    """
    # Filter for this metric
    metric_df = df[df['full_metric_name'] == metric_name].copy()
    
    if len(metric_df) == 0:
        return None
    
    # Add display names and colors
    metric_df['algorithm_name'] = metric_df['algorithm'].apply(get_algorithm_name)
    metric_df['color'] = metric_df['algorithm'].map(ALGORITHM_COLORS)
    
    # Format metric label
    y_axis_label = format_metric_label(metric_name)
    
    # Get data range for tight axis bounds
    pae_range = [metric_df['pae'].min(), metric_df['pae'].max()]
    metric_range = [metric_df['metric_value'].min(), metric_df['metric_value'].max()]
    
    # Add 5% padding to data range
    pae_padding = (pae_range[1] - pae_range[0]) * 0.05
    metric_padding = (metric_range[1] - metric_range[0]) * 0.05
    
    pae_domain = [pae_range[0] - pae_padding, pae_range[1] + pae_padding]
    metric_domain = [metric_range[0] - metric_padding, metric_range[1] + metric_padding]
    
    # Create scatter plot with raw values (no normalization)
    scatter = alt.Chart(metric_df).mark_circle(size=60, opacity=0.6).encode(
        x=alt.X('pae:Q', 
                title='Pixel Approximate Entropy', 
                scale=alt.Scale(domain=pae_domain, nice=False)),
        y=alt.Y('metric_value:Q', 
                title=y_axis_label, 
                scale=alt.Scale(domain=metric_domain, nice=False)),
        color=alt.Color('algorithm:N',
                       scale=alt.Scale(domain=list(ALGORITHM_COLORS.keys()),
                                     range=list(ALGORITHM_COLORS.values())),
                       legend=None),
        tooltip=[
            alt.Tooltip('algorithm_name:N', title='Algorithm'),
            alt.Tooltip('level:Q', title='Level'),
            alt.Tooltip('pae:Q', title='PAE', format='.6f'),
            alt.Tooltip('metric_value:Q', title='Metric Value', format='.4f')
        ]
    ).properties(
        width=700,
        height=550
    )
    
    return scatter


def create_algorithm_legend(df, output_dir):
    """
    Create a standalone algorithm color legend with optimized design.
    
    - Narrower colored rectangles
    - Sorted by category: Transformers → Reducers → Aggregators
    - Side-by-side layout compatible with z-score plots
    """
    # Get unique algorithms from data
    algorithms = sorted(df['algorithm'].unique())
    
    # Categorize algorithms by type (based on ALGORITHM_COLORS order)
    transformers = [
        'gaussian_filter', 'median_filter', 'mean_filter', 'min_filter', 
        'max_filter', 'moving_average', 'savitzky_golay_filter', 
        'butterworth_filter', 'fft_cutoff_filter', 'chebyshev_filter', 
        'elliptical_filter'
    ]
    reducers = [
        'lttb_downsample', 'm4_downsample', 'rdp_downsample',
        'minmaxlttb_downsample', 'uniform_subsample', 'fpcs_downsample',
        'tda_downsample'
    ]
    aggregators = [
        'asap_aggregator', 'bin_average_aggregator'
    ]
    
    # Sort algorithms by category, keeping only those present in data
    sorted_algorithms = []
    for algo in transformers:
        if algo in algorithms:
            sorted_algorithms.append(algo)
    for algo in reducers:
        if algo in algorithms:
            sorted_algorithms.append(algo)
    for algo in aggregators:
        if algo in algorithms:
            sorted_algorithms.append(algo)
    
    # Add category labels and display names
    legend_rows = []
    for algo in sorted_algorithms:
        # Determine category
        if algo in transformers:
            category = 'Transformer'
        elif algo in reducers:
            category = 'Reducer'
        else:
            category = 'Aggregator'
        
        legend_rows.append({
            'algorithm': algo,
            'algorithm_name': get_algorithm_name(algo),
            'category': category,
            'color': ALGORITHM_COLORS.get(algo, '#999999')
        })
    
    legend_data = pd.DataFrame(legend_rows)
    
    # Create explicit sort order for display names
    algorithm_name_order = legend_data['algorithm_name'].tolist()
    
    # Create vertical legend with narrow bars
    chart = alt.Chart(legend_data).mark_bar().encode(
        x=alt.X('value:Q', 
                title='',
                axis=None,
                scale=alt.Scale(domain=[0, 1])),  # Narrow bar width
        y=alt.Y('algorithm_name:N', 
                title='',
                sort=algorithm_name_order,
                axis=alt.Axis(labelLimit=200)),
        color=alt.Color('algorithm:N',
                       scale=alt.Scale(domain=list(ALGORITHM_COLORS.keys()),
                                     range=list(ALGORITHM_COLORS.values())),
                       legend=None)
    ).transform_calculate(
        value='1'  # All bars same width
    ).properties(
        width=80,  # Narrow width for compact legend
        height=550,  # Match z-score plot height
        title={
            'text': 'Algorithms',
            'fontSize': 14,
            'fontWeight': 'bold'
        }
    )
    
    # Save
    legend_path = output_dir / "algorithm_legend.svg"
    chart.save(str(legend_path))
    print(f"  OK Legend saved: {legend_path.name}")


def save_rankings_to_csv(df, output_dir):
    """
    Save algorithm rankings for each metric to CSV files.
    
    Creates three CSV files:
    1. rankings_summary.csv - Mean FC scores with std dev for each algorithm-metric pair
    2. rankings_wide.csv - Wide format with algorithms as rows, metrics as columns
    3. rankings_ranked.csv - Rank positions (1=best) for each algorithm-metric pair
    
    Args:
        df: DataFrame with precomputed data
        output_dir: Path to save CSV files
    """
    
    # Get all unique metrics
    metrics = sorted(df['full_metric_name'].unique())
    
    # 1. SUMMARY FORMAT: All data with mean, std, and sample count
    summary_records = []
    
    for metric_name in metrics:
        metric_df = df[df['full_metric_name'] == metric_name].copy()
        
        # Compute z-scores (same logic as create_ranking_plot)
        pae_mean = metric_df['pae'].mean()
        pae_std = metric_df['pae'].std()
        metric_mean = metric_df['metric_value'].mean()
        metric_std = metric_df['metric_value'].std()
        
        metric_df['pae_z'] = (metric_df['pae'] - pae_mean) / pae_std
        metric_df['metric_z'] = (metric_df['metric_value'] - metric_mean) / metric_std
        
        # FC Score: high feature preservation - low complexity
        # Inverse for error metrics (l1, linf, delta, bottleneck, wasserstein - higher is worse)
        if any(x in metric_name for x in ['l1', 'linf', 'delta', 'bottleneck', 'wasserstein']):
            metric_df['fc_score'] = -metric_df['metric_z'] - metric_df['pae_z']
        else:
            metric_df['fc_score'] = metric_df['metric_z'] - metric_df['pae_z']
        
        # Aggregate by algorithm
        summary = metric_df.groupby('algorithm').agg({
            'fc_score': ['mean', 'std', 'count'],
            'pae': 'mean',
            'metric_value': 'mean'
        }).reset_index()
        
        # Flatten column names
        summary.columns = ['algorithm', 'mean_fc_score', 'std_fc_score', 'sample_count', 
                          'mean_pae', 'mean_metric_value']
        
        # Sort by mean FC score (descending - higher is better)
        summary = summary.sort_values('mean_fc_score', ascending=False)
        
        # Add rank (1 = best)
        summary['rank'] = range(1, len(summary) + 1)
        
        # Add metric name
        summary['metric'] = metric_name
        
        # Reorder columns
        summary = summary[['metric', 'rank', 'algorithm', 'mean_fc_score', 'std_fc_score', 
                          'sample_count', 'mean_pae', 'mean_metric_value']]
        
        summary_records.append(summary)
    
    # Combine all metrics
    rankings_summary = pd.concat(summary_records, ignore_index=True)
    
    # Save summary CSV
    summary_path = output_dir / "rankings_summary.csv"
    rankings_summary.to_csv(summary_path, index=False, float_format='%.6f')
    print(f"  OK Summary CSV: {summary_path.name}")
    print(f"     ({len(rankings_summary)} rows: {len(metrics)} metrics × algorithms)")
    
    
    # 2. WIDE FORMAT: Algorithms as rows, metrics as columns (mean FC scores)
    wide_data = []
    algorithms = sorted(df['algorithm'].unique())
    
    for algorithm in algorithms:
        row = {'algorithm': algorithm}
        for metric_name in metrics:
            metric_df = df[df['full_metric_name'] == metric_name].copy()
            
            # Compute FC score for this metric
            pae_mean = metric_df['pae'].mean()
            pae_std = metric_df['pae'].std()
            metric_mean = metric_df['metric_value'].mean()
            metric_std = metric_df['metric_value'].std()
            
            metric_df['pae_z'] = (metric_df['pae'] - pae_mean) / pae_std
            metric_df['metric_z'] = (metric_df['metric_value'] - metric_mean) / metric_std
            
            # FC Score
            if any(x in metric_name for x in ['l1', 'linf', 'delta', 'bottleneck', 'wasserstein']):
                metric_df['fc_score'] = -metric_df['metric_z'] - metric_df['pae_z']
            else:
                metric_df['fc_score'] = metric_df['metric_z'] - metric_df['pae_z']
            
            # Get this algorithm's mean FC score
            algo_df = metric_df[metric_df['algorithm'] == algorithm]
            if not algo_df.empty:
                row[metric_name] = algo_df['fc_score'].mean()
            else:
                row[metric_name] = np.nan
        wide_data.append(row)
    
    rankings_wide = pd.DataFrame(wide_data)
    
    # Save wide CSV
    wide_path = output_dir / "rankings_wide.csv"
    rankings_wide.to_csv(wide_path, index=False, float_format='%.6f')
    print(f"  OK Wide CSV: {wide_path.name}")
    print(f"     ({len(rankings_wide)} algorithms × {len(metrics)} metrics)")
    
    
    # 3. RANKED FORMAT: Rank positions (1=best) for each algorithm-metric pair
    ranked_data = []
    
    for algorithm in algorithms:
        row = {'algorithm': algorithm}
        for metric_name in metrics:
            metric_df = df[df['full_metric_name'] == metric_name].copy()
            
            # Compute FC scores for all algorithms
            pae_mean = metric_df['pae'].mean()
            pae_std = metric_df['pae'].std()
            metric_mean = metric_df['metric_value'].mean()
            metric_std = metric_df['metric_value'].std()
            
            metric_df['pae_z'] = (metric_df['pae'] - pae_mean) / pae_std
            metric_df['metric_z'] = (metric_df['metric_value'] - metric_mean) / metric_std
            
            # FC Score
            if any(x in metric_name for x in ['l1', 'linf', 'delta', 'bottleneck', 'wasserstein']):
                metric_df['fc_score'] = -metric_df['metric_z'] - metric_df['pae_z']
            else:
                metric_df['fc_score'] = metric_df['metric_z'] - metric_df['pae_z']
            
            # Get all algorithms' mean FC scores
            metric_summary = metric_df.groupby('algorithm')['fc_score'].mean().reset_index()
            metric_summary = metric_summary.sort_values('fc_score', ascending=False)
            metric_summary['rank'] = range(1, len(metric_summary) + 1)
            
            # Find this algorithm's rank
            algo_rank = metric_summary[metric_summary['algorithm'] == algorithm]['rank']
            if not algo_rank.empty:
                row[metric_name] = int(algo_rank.iloc[0])
            else:
                row[metric_name] = np.nan
        ranked_data.append(row)
    
    rankings_ranked = pd.DataFrame(ranked_data)
    
    # Save ranked CSV
    ranked_path = output_dir / "rankings_ranked.csv"
    rankings_ranked.to_csv(ranked_path, index=False)
    print(f"  OK Ranked CSV: {ranked_path.name}")
    print(f"     ({len(rankings_ranked)} algorithms × {len(metrics)} metrics, values=rank positions)")
    
    # Print statistics
    print(f"\n   Ranking Statistics:")
    avg_ranks = rankings_ranked.iloc[:, 1:].mean(axis=1)
    best_algo_idx = avg_ranks.idxmin()
    best_algo_name = rankings_ranked.iloc[best_algo_idx]['algorithm']
    best_avg_rank = avg_ranks.min()
    print(f"     Best algorithm overall (avg rank): {best_algo_name}")
    print(f"     Average rank: {best_avg_rank:.2f}")



def save_fc_scores_to_csv(df, output_dir):
    """
    Save all FC scores for each data point to CSV for future analysis.
    
    Creates fc_scores_all.csv with columns:
    - algorithm, level, metric, pae, metric_value, pae_z, preservation_z, fc_score
    
    This allows analyzing FC score distributions without regenerating plots.
    """
    print(f"\n  Computing and saving FC scores for all data points...")
    
    all_fc_data = []
    metrics = sorted(df['full_metric_name'].unique())
    
    for metric_name in metrics:
        metric_df = df[df['full_metric_name'] == metric_name].copy()
        
        # Compute z-scores for PAE
        pae_mean = metric_df['pae'].mean()
        pae_std = metric_df['pae'].std()
        metric_df['pae_z'] = (metric_df['pae'] - pae_mean) / pae_std
        
        # Compute z-scores for metric value
        metric_mean = metric_df['metric_value'].mean()
        metric_std = metric_df['metric_value'].std()
        metric_df['metric_z'] = (metric_df['metric_value'] - metric_mean) / metric_std
        
        # Preservation z-score (negate for error metrics)
        metric_df['preservation_z'] = -metric_df['metric_z']
        
        # FC Score = Preservation_z - PAE_z
        metric_df['fc_score'] = metric_df['preservation_z'] - metric_df['pae_z']
        
        # Store relevant columns
        for _, row in metric_df.iterrows():
            all_fc_data.append({
                'algorithm': row['algorithm'],
                'level': row['level'],
                'metric': metric_name,
                'pae': row['pae'],
                'metric_value': row['metric_value'],
                'pae_z': row['pae_z'],
                'preservation_z': row['preservation_z'],
                'fc_score': row['fc_score']
            })
    
    # Save to CSV
    fc_df = pd.DataFrame(all_fc_data)
    fc_path = output_dir / "fc_scores_all.csv"
    fc_df.to_csv(fc_path, index=False, float_format='%.6f')
    
    print(f"  OK FC Scores CSV: {fc_path.name}")
    print(f"     ({len(fc_df):,} data points: {df['algorithm'].nunique()} algorithms × {df['level'].nunique()} levels × {len(metrics)} metrics)")
    
    # Calculate and save quartiles PER METRIC (not pooled)
    print(f"\n  Computing quartiles per metric...")
    quartiles_data = []
    
    for metric_name in metrics:
        metric_fc = fc_df[fc_df['metric'] == metric_name]['fc_score']
        
        p25 = np.percentile(metric_fc, 25)
        p50 = np.percentile(metric_fc, 50)
        p75 = np.percentile(metric_fc, 75)
        
        quartiles_data.append({
            'metric': metric_name,
            'q25': p25,
            'q50': p50,
            'q75': p75
        })
    
    quartiles_df = pd.DataFrame(quartiles_data)
    
    quartiles_path = output_dir / "fc_scores_quartiles.csv"
    quartiles_df.to_csv(quartiles_path, index=False, float_format='%.6f')
    
    print(f"  OK Quartiles CSV: {quartiles_path.name}")
    print(f"     {len(quartiles_df)} metrics with per-metric quartiles (Q1, Q2, Q3)")
    
    return fc_df

def create_fc_distribution_plot(df, metric_name, dataset_name):
    """
    FC score distribution plot with:
    - Grey quartile bands
    - Algorithm-colored points (consistent style)
    - Quartile boundary lines
    - Side annotations labeling the performance regions
    """
    # Filter to specific metric
    metric_df = df[df['full_metric_name'] == metric_name].copy()
    if len(metric_df) == 0:
        return None

    # Compute z-scores
    pae_mean = metric_df['pae'].mean()
    pae_std = metric_df['pae'].std()
    metric_df['pae_z'] = (metric_df['pae'] - pae_mean) / pae_std

    metric_mean = metric_df['metric_value'].mean()
    metric_std = metric_df['metric_value'].std()
    metric_df['metric_z'] = (metric_df['metric_value'] - metric_mean) / metric_std

    # Preservation & FC
    metric_df['preservation_z'] = -metric_df['metric_z']
    metric_df['fc_score'] = metric_df['preservation_z'] - metric_df['pae_z']

    fc_df = metric_df[['algorithm', 'level', 'fc_score']].copy()

    # Quartiles
    p25 = np.percentile(fc_df['fc_score'], 25)
    p50 = np.percentile(fc_df['fc_score'], 50)
    p75 = np.percentile(fc_df['fc_score'], 75)

    # Y-domain with padding
    fc_min, fc_max = fc_df['fc_score'].min(), fc_df['fc_score'].max()
    fc_padding = (fc_max - fc_min) * 0.05 if fc_max > fc_min else 0.1
    fc_domain = [fc_min - fc_padding, fc_max + fc_padding]

    level_min, level_max = fc_df['level'].min(), fc_df['level'].max()
    level_domain = [level_min - 2, level_max + 2]

    # Grey quartile bands
    band_data = pd.DataFrame([
        {'y_min': p75, 'y_max': fc_domain[1], 'category': 'Excellent'},
        {'y_min': p50, 'y_max': p75,        'category': 'Good'},
        {'y_min': p25, 'y_max': p50,        'category': 'Fair'},
        {'y_min': fc_domain[0], 'y_max': p25, 'category': 'Poor'}
    ])

    band_order  = ['Excellent', 'Good', 'Fair', 'Poor']
    band_colors = ['#F0F0F0', '#CCCCCC', '#999999', '#666666']

    bands = alt.Chart(band_data).mark_rect(opacity=0.25).encode(
        y=alt.Y('y_min:Q', scale=alt.Scale(domain=fc_domain, nice=False)),
        y2='y_max:Q',
        color=alt.Color('category:N',
                       scale=alt.Scale(domain=band_order, range=band_colors),
                       legend=None)
    )

    # CONSISTENT MARK STYLE with other charts
    scatter = alt.Chart(fc_df).mark_circle(
        size=60,            # CONSISTENT
        opacity=0.6,        # CONSISTENT
        # stroke='white',     # CONSISTENT
        # strokeWidth=0.5     # CONSISTENT
    ).encode(
        x=alt.X('level:Q',
                title='Smoothing Level',
                scale=alt.Scale(domain=level_domain)),
        y=alt.Y('fc_score:Q',
                title='FC Score (Feature-Complexity Score)',
                scale=alt.Scale(domain=fc_domain)),
        color=alt.Color(
            'algorithm:N',
            scale=alt.Scale(
                domain=list(ALGORITHM_COLORS.keys()),
                range=list(ALGORITHM_COLORS.values())
            ),
            legend=None
        ),
        tooltip=[
            alt.Tooltip('algorithm:N'),
            alt.Tooltip('level:Q'),
            alt.Tooltip('fc_score:Q', format='.4f')
        ]
    )

    # Quartile divider lines
    quartile_lines_data = pd.DataFrame([
        {'y': p75}, {'y': p50}, {'y': p25}
    ])
    quartile_lines = alt.Chart(quartile_lines_data).mark_rule(
        strokeDash=[5, 5],
        color='black',
        opacity=0.6,
        strokeWidth=2
    ).encode(y='y:Q')

    # Side region labels (right side)
    labels_df = pd.DataFrame([
        {'y': (p75 + fc_domain[1]) / 2, 'label': 'Excellent'},
        {'y': (p50 + p75) / 2,          'label': 'Good'},
        {'y': (p25 + p50) / 2,          'label': 'Fair'},
        {'y': (fc_domain[0] + p25) / 2, 'label': 'Poor'}
    ])

    side_labels = alt.Chart(labels_df).mark_text(
        align='left',
        baseline='middle',
        dx=5,
        fontSize=12,
        fontWeight='bold'
    ).encode(
        x=alt.value(705),  # aligned to right outside chart area
        y='y:Q',
        text='label:N'
    )

    # Combine layers
    chart = alt.layer(
        bands,
        scatter,
        quartile_lines,
        side_labels
    ).properties(
        width=700,
        height=550
    ).resolve_scale(
        color='independent'
    )

        # ---- SEPARATE PERFORMANCE TIERS LEGEND ----
    legend_data = pd.DataFrame([
        {'category': 'Excellent', 'order': 1},
        {'category': 'Good',      'order': 2},
        {'category': 'Fair',      'order': 3},
        {'category': 'Poor',      'order': 4}
    ])

    legend_rects = alt.Chart(legend_data).mark_rect(
        width=20,
        height=20,
        opacity=0.35
    ).encode(
        x=alt.value(10),  # left margin for squares
        y=alt.Y(
            'category:N',
            sort=band_order,
            axis=None
        ),
        color=alt.Color(
            'category:N',
            scale=alt.Scale(domain=band_order, range=band_colors),
            legend=None
        )
    )

    legend_labels = alt.Chart(legend_data).mark_text(
        align='left',
        baseline='middle',
        dx=5,
        fontSize=12
    ).encode(
        x=alt.value(35),  # text a bit to the right of squares
        y=alt.Y(
            'category:N',
            sort=band_order,
            axis=None
        ),
        text='category:N',
        color=alt.value('black')
    )

    legend = (legend_rects + legend_labels).properties(
        width=160,
        height=110,
        title={
            'text': 'Performance Tiers',
            'fontSize': 14,
            'fontWeight': 'bold'
        }
    )


    return chart, legend




def main():
    """Generate all plots for a dataset."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate Vega-Lite SVG plots for feature preservation analysis')
    parser.add_argument('--breakdown', action='store_true',
                       help='Generate all 3 plots (raw + zscore_fc + ranking) instead of just 2 (zscore_fc + ranking)')
    parser.add_argument('--fc-distribution', action='store_true',
                       help='Generate FC score distribution plot across all metrics')
    parser.add_argument('--csv-only', action='store_true',
                       help='Only generate CSV files (fc_scores_all.csv and fc_scores_quartiles.csv), skip all plots')
    parser.add_argument('--dataset', type=str, default='stock_aapl_price',
                       help='Dataset name (default: stock_aapl_price)')
    args = parser.parse_args()
    
    dataset_name = args.dataset
    breakdown_mode = args.breakdown
    fc_distribution_mode = args.fc_distribution
    csv_only_mode = args.csv_only
    
    # Load ALL data (no sampling - we need all algorithms and metrics)
    print(f"Loading ALL precomputed data for {dataset_name}...")
    df = load_precomputed_data(dataset_name)  # Load all files
    
    # Create output directory with ranking subdirectory
    output_dir = Path(f"plots/{dataset_name}/ranking")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # If CSV-only mode, just generate CSV files and exit
    if csv_only_mode:
        print(f"\nCSV-ONLY MODE: Generating FC score CSV files only...")
        fc_df = save_fc_scores_to_csv(df, output_dir)
        print(f"\nDone! CSV files saved to: {output_dir.absolute()}")
        return
    
    # Get all unique metrics (excluding change_points l1/linf)
    metrics = sorted(df['full_metric_name'].unique())
    
    if breakdown_mode:
        num_plots = len(metrics) * 3
        print(f"\nBREAKDOWN MODE: Generating {num_plots} plots for {len(metrics)} metrics...")
        print(f"   (raw + zscore_fc + ranking for each metric)")
    else:
        num_plots = len(metrics) * 2
        print(f"\nSTANDARD MODE: Generating {num_plots} plots for {len(metrics)} metrics...")
        print(f"   (zscore_fc + ranking for each metric)")
        print(f"   Use --breakdown flag to include raw scatter plots")
    
    if fc_distribution_mode:
        num_plots += len(metrics)
        print(f"   FC DISTRIBUTION MODE: Will generate +{len(metrics)} FC distribution plots")
        print(f"   Total plots: {num_plots}")
    
    # Generate plots for ALL metrics
    for i, metric_name in enumerate(metrics, 1):
        print(f"\n[{i}/{len(metrics)}] Processing: {metric_name}")
        
        # Plot 1: Raw scatter (only in breakdown mode)
        if breakdown_mode:
            raw_chart = create_raw_scatter_plot(df, metric_name, dataset_name)
            if raw_chart:
                raw_path = output_dir / f"{metric_name}_raw.svg"
                raw_chart.save(str(raw_path))
                print(f"  OK Raw scatter: {raw_path.name}")
        
        # Plot 2: Z-score with FC contours (always generated)
        zscore_chart = create_zscore_plot(df, metric_name, dataset_name)
        if zscore_chart:
            zscore_path = output_dir / f"{metric_name}_zscore_fc.svg"
            zscore_chart.save(str(zscore_path))
            print(f"  OK Z-score FC: {zscore_path.name}")
        
        # Plot 3: Ranking (always generated)
        ranking_chart = create_ranking_plot(df, metric_name, dataset_name)
        if ranking_chart:
            ranking_path = output_dir / f"{metric_name}_ranking.svg"
            ranking_chart.save(str(ranking_path))
            print(f"  OK Ranking: {ranking_path.name}")
        
        # Plot 4: FC distribution (if flag enabled)
        if fc_distribution_mode:
            result = create_fc_distribution_plot(df, metric_name, dataset_name)
            if result:
                fc_dist_chart, fc_legend = result
                fc_dist_path = output_dir / f"{metric_name}_fc_distribution.svg"
                fc_dist_chart.save(str(fc_dist_path))
                print(f"  OK FC Distribution: {fc_dist_path.name}")
                
                # Save legend only once (for first metric)
                if i == 1:
                    fc_legend_path = output_dir / "fc_distribution_legend.svg"
                    fc_legend.save(str(fc_legend_path))
                    print(f"  OK FC Legend: {fc_legend_path.name}")
    
    print(f"\nOutput directory: {output_dir.absolute()}")
    print(f"\nALL PLOTS COMPLETE!")
    print(f"   Generated {num_plots} SVG files for {len(metrics)} metrics")
    
    # Create algorithm legend (single chart showing all algorithm colors)
    print(f"\nCreating algorithm color legend...")
    create_algorithm_legend(df, output_dir)
    
    # Save ranking data to CSV files
    print(f"\nExporting ranking data to CSV...")
    save_rankings_to_csv(df, output_dir)
    
    # Save FC scores to CSV (always - for future analysis)
    print(f"\nSaving FC scores to CSV...")
    fc_df = save_fc_scores_to_csv(df, output_dir)
    
    print(f"\nDone! All plots saved to: {output_dir.absolute()}")


if __name__ == "__main__":
    main()
