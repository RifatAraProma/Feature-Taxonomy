"""
Rank algorithms by individual features across all datasets.

This script follows the EXACT same mechanism as rank_algorithms_by_dataset_type.py
but groups by FEATURE instead of dataset type.

Usage:
    python rank_algorithms_by_feature.py --feature extrema_retention_ratio
    python rank_algorithms_by_feature.py --all
"""

import sys
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import altair as alt

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent / 'server'))
from algorithm_colors import get_algorithm_color
from algorithm_names import get_algorithm_name

# Import shared bump chart utility
from bump_chart_utils import create_bump_chart as create_bump_chart_base


# All features (metrics) used in the ranking system
# These come from the ranking CSV files: plots/{dataset}/ranking/rankings_ranked.csv
FEATURES = [
    'change_points_delta',
    'curvature_l1',
    'curvature_linf',
    'extrema_bottleneck',
    'extrema_wasserstein',
    'level_l1',
    'level_linf',
    'mean_delta',
    'noise_auc_delta',
    'noise_l1',
    'noise_linf',
    'periodicity_amplitude_delta',
    'periodicity_num_periods_delta',
    'regimes_delta',
    'regression_l1',
    'regression_linf',
    'roughness_delta',
    'slope_l1',
    'slope_linf',
    'spikes_dips_bottleneck',
    'spikes_dips_wasserstein',
    'trend_l1',
    'trend_linf',
]

# Dataset type groupings (same as rank_algorithms_by_dataset_type.py)
DATASET_TYPES = {
    'astro': ['astro_115_120', 'astro_115_123', 'astro_115_128',
              'astro_116_124', 'astro_116_134'],
    'climate_awnd': ['climate_atl_awnd', 'climate_jfk_awnd', 'climate_lax_awnd',
                     'climate_ord_awnd', 'climate_sea_awnd', 'climate_slc_awnd'],
    'climate_prcp': ['climate_atl_prcp', 'climate_jfk_prcp', 'climate_lax_prcp',
                     'climate_ord_prcp', 'climate_sea_prcp', 'climate_slc_prcp'],
    'climate_tmax': ['climate_atl_tmax', 'climate_jfk_tmax', 'climate_lax_tmax',
                     'climate_ord_tmax', 'climate_sea_tmax', 'climate_slc_tmax'],
    'crime': ['chi_homicide_monthly', 'chi_homicide_weekly'],
    'eeg_500': ['eeg_chan05_500', 'eeg_chan10_500', 'eeg_chan15_500',
                'eeg_chan20_500', 'eeg_chan25_500', 'eeg_chan30_500'],
    'eeg_2500': ['eeg_chan05_2500', 'eeg_chan10_2500', 'eeg_chan15_2500',
                 'eeg_chan20_2500', 'eeg_chan25_2500', 'eeg_chan30_2500'],
    'eeg_10000': ['eeg_chan05_10000', 'eeg_chan10_10000', 'eeg_chan15_10000',
                  'eeg_chan20_10000', 'eeg_chan25_10000', 'eeg_chan30_10000'],
    'flights': ['flights_daily', 'flights_monthly', 'flights_weekly'],
    'nz_tourism': ['nz_tourist_annually', 'nz_tourist_monthly'],
    'stock_price': ['stock_aapl_price', 'stock_amzn_price', 'stock_bac_price',
                    'stock_goog_price', 'stock_intc_price', 'stock_jpm_price',
                    'stock_msft_price', 'stock_tm_price', 'stock_tsla_price'],
    'stock_volume': ['stock_aapl_volume', 'stock_amzn_volume', 'stock_bac_volume',
                     'stock_goog_volume', 'stock_intc_volume', 'stock_jpm_volume',
                     'stock_msft_volume', 'stock_tm_volume', 'stock_tsla_volume'],
    'unemployment': ['unemployment_ag', 'unemployment_business', 'unemployment_construction',
                     'unemployment_edu_health', 'unemployment_finance', 'unemployment_govt',
                     'unemployment_hospitality', 'unemployment_info', 'unemployment_manufacturing',
                     'unemployment_mining', 'unemployment_other', 'unemployment_self_emp',
                     'unemployment_trade', 'unemployment_transport'],
}


def get_dataset_type(dataset_name: str) -> str:
    """Map dataset name to its type."""
    for dtype, datasets in DATASET_TYPES.items():
        if dataset_name in datasets:
            return dtype
    return 'other'


def load_all_datasets_for_feature(feature: str) -> pd.DataFrame:
    """
    Load rankings for a specific feature across ALL datasets.

    Returns long-form DataFrame with columns:
        dataset, algorithm, rank
    """
    plots_dir = Path('plots')
    rows = []

    for dataset_dir in plots_dir.iterdir():
        if not dataset_dir.is_dir():
            continue
        
        ranking_file = dataset_dir / 'ranking' / 'rankings_ranked.csv'
        if not ranking_file.exists():
            continue
        
        dataset_name = dataset_dir.name
        
        try:
            df = pd.read_csv(ranking_file)
            
            if feature not in df.columns:
                print(f"No feature found named {feature}")
                continue
            
            # Extract just this feature
            feature_df = df[['algorithm', feature]].copy()
            feature_df.columns = ['algorithm', 'rank']
            feature_df['dataset_type'] = dataset_name
            
            rows.append(feature_df)
            
        except Exception as e:
            print(f"⚠️  Error loading {dataset_name}: {e}")
            continue
    
    if not rows:
        return pd.DataFrame()
    
    return pd.concat(rows, ignore_index=True)


def compute_datasetwise_ranks_for_feature(feature: str) -> pd.DataFrame:
    """
    For a specific feature, compute algorithm rankings by DATASET TYPE (not individual datasets),
    plus an overall average rank.

    Returns DataFrame with columns:
        dataset_type, algorithm, algorithm_name, color, rank, overall_rank
    """
    print(f"\n📊 Computing per-dataset-type rankings for feature: {feature}")
    
    df_long = load_all_datasets_for_feature(feature)
    
    if df_long.empty:
        print(f"❌ No data found for feature: {feature}")
        return pd.DataFrame()
    
    # Add dataset type
    df_long['dataset_type'] = df_long['dataset_type'].apply(get_dataset_type)
    
    dataset_types = sorted(df_long['dataset_type'].unique())
    print(f"   Dataset types: {len(dataset_types)} types")
    
    rows = []
    
    for dtype in dataset_types:
        dtype_df = df_long[df_long['dataset_type'] == dtype].copy()
        
        # Aggregate across all datasets in this type
        type_stats = dtype_df.groupby('algorithm').agg(
            rank=('rank', 'mean')
        ).reset_index()
        
        # Rank algorithms for this dataset type (1 = best)
        type_stats = type_stats.sort_values('rank', ascending=True).reset_index(drop=True)
        type_stats['overall_rank'] = range(1, len(type_stats) + 1)
        type_stats['dataset_type'] = dtype
        type_stats['algorithm_name'] = type_stats['algorithm'].apply(get_algorithm_name)
        type_stats['color'] = type_stats['algorithm'].apply(get_algorithm_color)
        
        rows.append(type_stats)
    
    combined = pd.concat(rows, ignore_index=True)
    
    # Compute average rank across dataset types for each algorithm
    avg_stats = (
        combined.groupby(['algorithm'])
        .agg(avg_rank=('rank', 'mean'))
        .reset_index()
    )
    avg_stats = avg_stats.sort_values('avg_rank', ascending=True).reset_index(drop=True)
    avg_stats['overall_rank'] = range(1, len(avg_stats) + 1)
    avg_stats['dataset_type'] = 'Average rank'
    avg_stats['rank'] = avg_stats['avg_rank']
    avg_stats['algorithm_name'] = avg_stats['algorithm'].apply(get_algorithm_name)
    avg_stats['color'] = avg_stats['algorithm'].apply(get_algorithm_color)
    
    bump_df = pd.concat(
        [
            combined[['dataset_type', 'algorithm', 'algorithm_name', 'color', 'rank', 'overall_rank']],
            avg_stats[['dataset_type', 'algorithm', 'algorithm_name', 'color', 'rank', 'overall_rank']],
        ],
        ignore_index=True,
    )
    
    return bump_df


def create_bump_chart(bump_df: pd.DataFrame, feature: str) -> alt.Chart:
    """
    Create a minimal, clean bump chart - EXACT same style as rank_algorithms_by_dataset_type.py

    bump_df must contain:
        dataset_type, algorithm, algorithm_name, color, overall_rank
    """
    # Order dataset types: use ALL DATASET_TYPES keys (maintain consistent x-axis) + "Average rank"
    type_order = list(DATASET_TYPES.keys()) + ['Average rank']
    
    return create_bump_chart_base(
        bump_df=bump_df,
        column_order=type_order,
        column_name='dataset_type',
        rank_column='overall_rank',  # Use overall_rank for y-position
        overall_rank_column='overall_rank',
        avg_rank_column='rank',  # Use rank for tooltip
        average_label='Average rank',
    )


def main():
    """
    Create a minimal, clean bump chart - EXACT same style as rank_algorithms_by_dataset_type.py

    bump_df must contain:
        dataset_type, algorithm, algorithm_name, color, overall_rank
    """
    # Order dataset types: use ALL DATASET_TYPES keys (maintain consistent x-axis) + "Average rank"
    # This ensures proper spacing and correct alphabetical order (eeg_500, eeg_2500, eeg_10000)
    type_order = list(DATASET_TYPES.keys()) + ['Average rank']
    
    # Create numeric x position
    bump_df = bump_df.copy()
    bump_df['x_pos'] = bump_df['dataset_type'].map(
        {d: i for i, d in enumerate(type_order)}
    )
    
    # Calculate chart dimensions
    num_types = len(type_order)
    max_rank = int(bump_df['overall_rank'].max())
    
    # Add flags for styling
    bump_df['is_average'] = bump_df['dataset_type'] == 'Average rank'
    bump_df['is_last_column'] = bump_df['dataset_type'] == type_order[-1]
    
    # Lines - regular datasets, non-last columns
    lines_regular = (
        alt.Chart(bump_df[~bump_df['is_average'] & ~bump_df['is_last_column']])
        .mark_line(point=alt.OverlayMarkDef(size=120, filled=True), strokeWidth=3.5, opacity=0.8)
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_types + 1.5]), axis=None),
            y=alt.Y('overall_rank:Q', scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]), axis=None),
            color=alt.Color('algorithm:N', scale=alt.Scale(
                domain=bump_df['algorithm'].unique().tolist(),
                range=bump_df.drop_duplicates('algorithm')['color'].tolist(),
            ), legend=None),
            detail='algorithm:N',
            tooltip=[
                alt.Tooltip('algorithm_name:N', title='Algorithm'),
                alt.Tooltip('dataset:N', title='dataset_type'),
                alt.Tooltip('overall_rank:Q', title='Rank'),
                alt.Tooltip('rank:Q', title='Feature Rank', format='.2f'),
            ],
        )
    )
    
    # Last column before average (BIGGER POINTS)
    lines_last_regular = (
        alt.Chart(bump_df[~bump_df['is_average'] & bump_df['is_last_column']])
        .mark_line(point=alt.OverlayMarkDef(size=160, filled=True), strokeWidth=3.5, opacity=0.8)
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_types + 1.5]), axis=None),
            y=alt.Y('overall_rank:Q', scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]), axis=None),
            color=alt.Color('algorithm:N', scale=alt.Scale(
                domain=bump_df['algorithm'].unique().tolist(),
                range=bump_df.drop_duplicates('algorithm')['color'].tolist(),
            ), legend=None),
            detail='algorithm:N',
        )
    )
    
    # Average rank column (BOLD and BIGGEST)
    lines_average = (
        alt.Chart(bump_df[bump_df['is_average']])
        .mark_line(point=alt.OverlayMarkDef(size=200, filled=True, strokeWidth=2), strokeWidth=5, opacity=1)
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_types + 1.5]), axis=None),
            y=alt.Y('overall_rank:Q', scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]), axis=None),
            color=alt.Color('algorithm:N', scale=alt.Scale(
                domain=bump_df['algorithm'].unique().tolist(),
                range=bump_df.drop_duplicates('algorithm')['color'].tolist(),
            ), legend=None),
            detail='algorithm:N',
        )
    )
    
    # Algorithm labels on the right
    last_type = type_order[-1]
    labels_df = bump_df[bump_df['dataset_type'] == last_type].copy()
    
    labels = (
        alt.Chart(labels_df)
        .mark_text(align='left', baseline='middle', dx=35, fontSize=16, fontWeight=500)
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_types + 1.5]), axis=None),
            y=alt.Y('overall_rank:Q', scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]), axis=None),
            text='algorithm_name:N',
            color=alt.value('black'),
        )
    )
    
    # Rank numbers
    rank_numbers = (
        alt.Chart(labels_df)
        .mark_text(align='left', baseline='middle', dx=15, fontSize=16, fontWeight='bold')
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_types + 1.5]), axis=None),
            y=alt.Y('overall_rank:Q', scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]), axis=None),
            text=alt.Text('overall_rank:Q', format='d'),
            color=alt.value('black'),
        )
    )
    
    # Dataset type labels at TOP
    type_labels_df = pd.DataFrame({
        'dataset_type': type_order,
        'x_pos': range(len(type_order)),
        'y_pos': [-0.3] * len(type_order),
        'is_average': [d == 'Average rank' for d in type_order],
    })
    
    # Regular dataset type labels (diagonal)
    type_labels = (
        alt.Chart(type_labels_df[~type_labels_df['is_average']])
        .mark_text(align='left', baseline='middle', fontSize=16, angle=315, dx=-5, dy=-5)
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_types + 1.5]), axis=None),
            y=alt.Y('y_pos:Q', scale=alt.Scale(domain=[-0.5, max_rank + 0.5]), axis=None),
            text=alt.Text('dataset_type:N'),
            color=alt.value('black'),
        )
    )
    
    # 'Average rank' label (bold, diagonal)
    average_label = (
        alt.Chart(type_labels_df[type_labels_df['is_average']])
        .mark_text(align='left', baseline='middle', fontSize=16, fontWeight='bold', angle=0, dx=-5, dy=-5)
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_types + 1.5]), axis=None),
            y=alt.Y('y_pos:Q', scale=alt.Scale(domain=[-0.5, max_rank + 0.5]), axis=None),
            text=alt.Text('dataset_type:N'),
            color=alt.value('black'),
        )
    )
    
    # Combine all layers
    chart = (
        (lines_regular + lines_last_regular + lines_average + labels + rank_numbers + type_labels + average_label)
        .properties(
            width=120 * num_types,
            height=450
        )
        .configure_view(strokeWidth=0)
    )
    
    return chart


def main():
    parser = argparse.ArgumentParser(
        description='Rank algorithms by individual features across all datasets'
    )
    parser.add_argument(
        '--feature',
        type=str,
        help='Feature to analyze (e.g., extrema_retention_ratio, trend_lf_power)',
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Analyze all features',
    )
    
    args = parser.parse_args()
    
    if not args.feature and not args.all:
        print("❌ Please specify --feature or --all")
        print(f"Available features: {', '.join(FEATURES)}")
        return
    
    features_to_process = FEATURES if args.all else [args.feature]
    
    output_dir = Path('plots') / 'feature_rankings'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for feature in features_to_process:
        if feature not in FEATURES and not args.all:
            print(f"❌ Unknown feature: {feature}")
            continue
        
        bump_df = compute_datasetwise_ranks_for_feature(feature)
        if bump_df.empty:
            continue
        
        # Save CSV
        csv_path = output_dir / f'{feature}_bump_ranks.csv'
        bump_df.to_csv(csv_path, index=False)
        print(f"   ✅ Saved bump data CSV: {csv_path}")
        
        # Create bump chart
        chart = create_bump_chart(bump_df, feature)
        
        svg_path = output_dir / f'{feature}_bump_chart.svg'
        html_path = output_dir / f'{feature}_bump_chart.html'
        try:
            chart.save(str(svg_path), format='svg')
            print(f"   ✅ Saved bump chart SVG: {svg_path}")
        except Exception as e:
            print(f"   ⚠️  SVG export failed ({type(e).__name__}), saving HTML instead...")
            chart.save(str(html_path))
            print(f"   ✅ Saved bump chart HTML: {html_path}")
    
    print(f"\n✅ Outputs saved to {output_dir}/")


if __name__ == '__main__':
    main()

