"""
Generate Vega-Lite FC score distribution plot for all algorithms, levels, and features.
Shows overall distribution with quartile bands, matching generate_vegalite_plots.py style.
"""

import json
import glob
import numpy as np
import pandas as pd
from pathlib import Path
import altair as alt
import sys

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent / 'server'))
from algorithm_colors import ALGORITHM_COLORS


def load_precomputed_data(dataset_name):
    """
    Load all precomputed level files for a dataset.
    Returns DataFrame with columns: algorithm, level, pae, metric_name, metric_value, fc_score
    """
    data_rows = []
    
    pattern = f"precomputed/{dataset_name}/*_level_*.json"
    files = glob.glob(pattern)
    
    print(f"Loading {len(files)} precomputed files for {dataset_name}...")
    
    for filepath in files:
        try:
            with open(filepath, 'r') as f:
                level_data = json.load(f)
            
            # Extract algorithm name and level from filename
            filename = Path(filepath).stem
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
                            # Skip change_points l1 and linf (as in generate_vegalite_plots.py)
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
    print(f"Loaded {len(df)} metric samples")
    return df


def create_fc_distribution_plot(df, dataset_name):
    """
    Create FC score scatter plot for all algorithms, levels, and features.
    Each point is colored by algorithm, plot is segmented by quartile bands.
    """
    print(f"\nComputing FC scores for all metrics...")
    
    # Use only one metric to avoid overplotting
    # Choose level_l1 as it's the most commonly used
    metric_name = 'level_l1'
    metric_df = df[df['full_metric_name'] == metric_name].copy()
    
    if len(metric_df) == 0:
        print(f"Metric {metric_name} not found, using first available metric")
        metric_name = df['full_metric_name'].unique()[0]
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
    
    fc_df = metric_df[['algorithm', 'level', 'fc_score']].copy()
    
    print(f"Total data points: {len(fc_df)}")
    print(f"FC Score range: [{fc_df['fc_score'].min():.3f}, {fc_df['fc_score'].max():.3f}]")
    
    # Calculate quartiles
    p25 = np.percentile(fc_df['fc_score'], 25)
    p50 = np.percentile(fc_df['fc_score'], 50)
    p75 = np.percentile(fc_df['fc_score'], 75)
    
    print(f"Quartiles: 25th={p25:.3f}, 50th={p50:.3f}, 75th={p75:.3f}")
    
    # Add quartile bands as background rectangles
    bands_data = pd.DataFrame([
        {'y_start': p75, 'y_end': fc_df['fc_score'].max() + 1, 'category': 'Excellent'},
        {'y_start': p50, 'y_end': p75, 'category': 'Good'},
        {'y_start': p25, 'y_end': p50, 'category': 'Fair'},
        {'y_start': fc_df['fc_score'].min() - 1, 'y_end': p25, 'category': 'Poor'}
    ])
    
    # Define quartile color scheme
    quartile_colors = {
        'Excellent': '#eeeeee',
        'Good': "#bbb8b8",
        'Fair': "#7a7878",
        'Poor': "#434343"
    }
    
    # Create background bands
    bands = alt.Chart(bands_data).mark_rect(opacity=0.7).encode(
        y=alt.Y('y_start:Q', title=None),
        y2='y_end:Q',
        color=alt.Color('category:N',
                       scale=alt.Scale(
                           domain=['Excellent', 'Good', 'Fair', 'Poor'],
                           range=[quartile_colors['Excellent'], 
                                 quartile_colors['Good'],
                                 quartile_colors['Fair'],
                                 quartile_colors['Poor']]
                       ),
                       legend=None)
    )
    
    # Create scatter plot with algorithm colors
    scatter = alt.Chart(fc_df).mark_circle(size=20, opacity=0.6).encode(
        x=alt.X('level:Q',
                title='Smoothing Level',
                scale=alt.Scale(domain=[0, 100])),
        y=alt.Y('fc_score:Q',
                title='FC Score (Feature-Complexity Score)',
                scale=alt.Scale(nice=False)),
        color=alt.Color('algorithm:N',
                       scale=alt.Scale(
                           domain=list(ALGORITHM_COLORS.keys()),
                           range=list(ALGORITHM_COLORS.values())
                       ),
                       legend=None),
        tooltip=[
            alt.Tooltip('algorithm:N', title='Algorithm'),
            alt.Tooltip('level:Q', title='Level'),
            alt.Tooltip('fc_score:Q', title='FC Score', format='.3f')
        ]
    )
    
    # Add horizontal lines for quartile boundaries
    quartile_lines_data = pd.DataFrame([
        {'value': p25, 'label': f'25th'},
        {'value': p50, 'label': f'50th'},
        {'value': p75, 'label': f'75th'}
    ])
    
    quartile_lines = alt.Chart(quartile_lines_data).mark_rule(
        strokeDash=[5, 5],
        color='black',
        opacity=0.7,
        strokeWidth=2
    ).encode(
        y='value:Q'
    )
    
    # Combine layers (bands first, then scatter, then lines)
    chart = (bands + scatter + quartile_lines).properties(
        width=700,
        height=550,
        title={
            'text': f'FC Score Distribution: {dataset_name} ({metric_name})',
            'subtitle': f'All algorithms × levels (n={len(fc_df):,})',
            'fontSize': 16,
            'fontWeight': 'bold'
        }
    )
    
    # Create simple quartile legend
    legend_data = pd.DataFrame([
        {'category': 'Excellent', 'order': 1},
        {'category': 'Good', 'order': 2},
        {'category': 'Fair', 'order': 3},
        {'category': 'Poor', 'order': 4}
    ])
    
    legend = alt.Chart(legend_data).mark_rect(width=40, height=30).encode(
        y=alt.Y('order:O', 
                title=None,
                axis=None,
                sort='ascending'),
        color=alt.Color('category:N',
                       scale=alt.Scale(
                           domain=['Excellent', 'Good', 'Fair', 'Poor'],
                           range=[quartile_colors['Excellent'], 
                                 quartile_colors['Good'],
                                 quartile_colors['Fair'],
                                 quartile_colors['Poor']]
                       ),
                       legend=None)
    )
    
    legend_labels = alt.Chart(legend_data).mark_text(
        align='left',
        dx=50,
        fontSize=12,
        fontWeight='bold'
    ).encode(
        y=alt.Y('order:O', axis=None, sort='ascending'),
        text='category:N',
        color=alt.value('black')
    )
    
    legend_chart = (legend + legend_labels).properties(
        width=150,
        height=150,
        title={
            'text': 'Performance Tiers',
            'fontSize': 12,
            'fontWeight': 'bold'
        }
    )
    
    return chart, legend_chart


def main():
    # Dataset to analyze
    dataset_name = 'stock_aapl_price'
    
    # Load data
    df = load_precomputed_data(dataset_name)
    
    if len(df) == 0:
        print("No data loaded!")
        return
    
    # Create plots
    distribution_chart, legend_chart = create_fc_distribution_plot(df, dataset_name)
    
    # Save charts
    output_dir = Path('plots') / dataset_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    dist_path_html = output_dir / 'fc_distribution.svg'
    legend_path_html = output_dir / 'fc_distribution_legend.svg'
    
    distribution_chart.save(str(dist_path_html))
    legend_chart.save(str(legend_path_html))
    
    print(f"\n✅ Charts saved:")
    print(f"   Distribution: {dist_path_html}")
    print(f"   Legend: {legend_path_html}")


if __name__ == '__main__':
    main()
