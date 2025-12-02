"""
Rank algorithms by density bucket (Low, Medium, High).

This script follows the EXACT same mechanism as rank_algorithms_by_dataset_type.py
but groups datasets by their data point density instead of dataset type.

Density buckets (based on tertiles):
- LOW:    < 1,257 points (44 datasets)
- MEDIUM: 1,257 - 2,499 points (11 datasets)
- HIGH:   >= 2,500 points (25 datasets)

Usage:
    python rank_algorithms_by_density.py --all
    python rank_algorithms_by_density.py --density low
    python rank_algorithms_by_density.py --density medium
    python rank_algorithms_by_density.py --density high
"""

import sys
import json
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


# Density buckets based on data length (using tertiles)
DENSITY_THRESHOLDS = {
    'low': (0, 1257),      # < 1,257 points
    'medium': (1257, 2500), # 1,257 - 2,499 points
    'high': (2500, float('inf')),  # >= 2,500 points
}

# Dataset assignments by density bucket
DENSITY_BUCKETS = {
    'low': [
        'nz_tourist_annually', 'unemployment_info', 'unemployment_transport',
        'unemployment_trade', 'unemployment_mining', 'unemployment_manufacturing',
        'unemployment_self_emp', 'unemployment_other', 'unemployment_hospitality',
        'unemployment_edu_health', 'unemployment_govt', 'unemployment_finance',
        'unemployment_construction', 'unemployment_business', 'unemployment_ag',
        'chi_homicide_monthly', 'flights_monthly',
        'eeg_chan10_500', 'eeg_chan30_500', 'eeg_chan05_500',
        'eeg_chan15_500', 'eeg_chan25_500', 'eeg_chan20_500',
        'chi_homicide_weekly', 'flights_weekly', 'nz_tourist_monthly',
        'stock_aapl_price', 'stock_amzn_price', 'stock_intc_price',
        'stock_jpm_price', 'stock_bac_price', 'stock_goog_price',
        'stock_tm_volume', 'stock_tsla_volume', 'stock_intc_volume',
        'stock_goog_volume', 'stock_bac_volume', 'stock_amzn_volume',
        'stock_msft_volume', 'stock_jpm_volume', 'stock_tm_price',
        'stock_msft_price', 'stock_aapl_volume', 'stock_tsla_price',
    ],
    'medium': [
        'astro_116_124', 'astro_115_128', 'astro_115_120',
        'astro_115_123', 'astro_116_134',
        'eeg_chan05_2500', 'eeg_chan25_2500', 'eeg_chan20_2500',
        'eeg_chan15_2500', 'eeg_chan30_2500', 'eeg_chan10_2500',
    ],
    'high': [
        'climate_slc_awnd', 'climate_jfk_awnd', 'climate_ord_awnd',
        'climate_lax_awnd', 'climate_sea_awnd', 'climate_atl_awnd',
        'climate_jfk_prcp', 'climate_atl_prcp', 'climate_lax_prcp',
        'climate_sea_tmax', 'climate_slc_tmax', 'climate_slc_prcp',
        'climate_sea_prcp', 'climate_jfk_tmax', 'climate_lax_tmax',
        'climate_ord_tmax', 'climate_ord_prcp', 'climate_atl_tmax',
        'flights_daily',
        'eeg_chan15_10000', 'eeg_chan20_10000', 'eeg_chan25_10000',
        'eeg_chan30_10000', 'eeg_chan10_10000', 'eeg_chan05_10000',
    ],
}


def load_ranking_data(dataset_name: str) -> pd.DataFrame:
    """
    Load ranking CSV data for a single dataset from:
        plots/{dataset}/ranking/rankings_ranked.csv

    Returns long-form DataFrame with columns:
        algorithm, metric, rank, dataset
    """
    ranking_file = Path('plots') / dataset_name / 'ranking' / 'rankings_ranked.csv'

    if not ranking_file.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(ranking_file)

        id_vars = ['algorithm']
        value_vars = [c for c in df.columns if c not in id_vars]

        df_long = df.melt(
            id_vars=id_vars,
            value_vars=value_vars,
            var_name='metric',
            value_name='rank',
        )
        df_long['dataset'] = dataset_name
        return df_long

    except Exception as e:
        print(f"⚠️  Error loading {dataset_name}: {e}")
        return pd.DataFrame()


def compute_density_ranks(density: str = None) -> pd.DataFrame:
    """
    Compute algorithm rankings across density buckets, optionally filtered by density.
    
    If density is specified, only rank algorithms within that density bucket.
    Otherwise, rank all algorithms across all density buckets.

    Returns DataFrame with columns:
        density_bucket, algorithm, algorithm_name, color,
        rank_mean, rank_std, count, overall_rank
    """
    if density:
        print(f"\n📊 Computing rankings for density: {density.upper()}")
        densities_to_include = [density]
    else:
        print(f"\n📊 Computing rankings across all density buckets")
        densities_to_include = ['low', 'medium', 'high']
    
    # Use all density buckets as columns (for consistent x-axis)
    density_order = ['low', 'medium', 'high']
    print(f"   Density buckets: {len(density_order)} buckets")
    
    rows = []
    
    for dens in density_order:
        if density and dens != density:
            # Skip this density if we're filtering
            continue
            
        datasets = DENSITY_BUCKETS[dens]
        
        # Load data for all datasets in this density bucket
        bucket_rows = []
        for d in datasets:
            df_long = load_ranking_data(d)
            if df_long.empty:
                continue
            bucket_rows.append(df_long)
        
        if not bucket_rows:
            continue
        
        # Combine all datasets in this density bucket
        bucket_df = pd.concat(bucket_rows, ignore_index=True)
        
        # Aggregate across metrics and datasets for this density
        stats = bucket_df.groupby('algorithm').agg(
            rank_mean=('rank', 'mean'),
            rank_std=('rank', 'std'),
            count=('rank', 'count'),
        ).reset_index()
        
        # Standard error
        stats['rank_stderr'] = stats['rank_std'] / np.sqrt(stats['count'])
        
        # Rank algorithms for this density bucket (1 = best)
        stats = stats.sort_values('rank_mean', ascending=True).reset_index(drop=True)
        stats['overall_rank'] = range(1, len(stats) + 1)
        
        stats['density_bucket'] = dens
        stats['algorithm_name'] = stats['algorithm'].apply(get_algorithm_name)
        stats['color'] = stats['algorithm'].apply(get_algorithm_color)
        
        rows.append(stats)
    
    if not rows:
        print(f"❌ No ranking data found")
        return pd.DataFrame()
    
    combined = pd.concat(rows, ignore_index=True)
    
    # Compute average rank across density buckets for each algorithm
    avg_stats = (
        combined.groupby(['algorithm', 'algorithm_name', 'color'])
        .agg(avg_rank_mean=('rank_mean', 'mean'))
        .reset_index()
    )
    avg_stats = avg_stats.sort_values('avg_rank_mean', ascending=True).reset_index(drop=True)
    avg_stats['overall_rank'] = range(1, len(avg_stats) + 1)
    avg_stats['density_bucket'] = 'Average rank'
    avg_stats['rank_mean'] = avg_stats['avg_rank_mean']
    
    # For consistency with combined columns
    avg_stats['rank_std'] = np.nan
    avg_stats['count'] = combined.groupby('algorithm')['density_bucket'].nunique().values
    avg_stats['rank_stderr'] = np.nan
    
    bump_df = pd.concat(
        [
            combined[
                [
                    'density_bucket',
                    'algorithm',
                    'algorithm_name',
                    'color',
                    'rank_mean',
                    'rank_std',
                    'count',
                    'rank_stderr',
                    'overall_rank',
                ]
            ],
            avg_stats[
                [
                    'density_bucket',
                    'algorithm',
                    'algorithm_name',
                    'color',
                    'rank_mean',
                    'rank_std',
                    'count',
                    'rank_stderr',
                    'overall_rank',
                ]
            ],
        ],
        ignore_index=True,
    )
    
    return bump_df


def create_bump_chart(bump_df: pd.DataFrame, density: str = None) -> alt.Chart:
    """
    Create a minimal, clean bump chart - EXACT same style as rank_algorithms_by_dataset_type.py

    bump_df must contain:
        density_bucket, algorithm, algorithm_name, color, overall_rank
    """
    # Order density buckets: explicit order + "Average rank"
    density_order = ['low', 'medium', 'high', 'Average rank']
    
    return create_bump_chart_base(
        bump_df=bump_df,
        column_order=density_order,
        column_name='density_bucket',
        rank_column='overall_rank',  # Use overall_rank for y-position
        overall_rank_column='overall_rank',
        avg_rank_column='rank_mean',  # Use rank_mean for tooltip
        average_label='Average rank',
    )


def main():
    """
    Create a minimal, clean bump chart - EXACT same style as rank_algorithms_by_dataset_type.py

    bump_df must contain:
        density_bucket, algorithm, algorithm_name, color, overall_rank
    """
    # Order density buckets: explicit order + "Average rank"
    density_order = ['low', 'medium', 'high', 'Average rank']
    
    # Create numeric x position
    bump_df = bump_df.copy()
    bump_df['x_pos'] = bump_df['density_bucket'].map(
        {d: i for i, d in enumerate(density_order)}
    )
    
    # Calculate chart dimensions
    num_densities = len(density_order)
    max_rank = int(bump_df['overall_rank'].max())
    
    # Add flags for styling
    bump_df['is_average'] = bump_df['density_bucket'] == 'Average rank'
    bump_df['is_last_column'] = bump_df['density_bucket'] == density_order[-1]
    
    # Lines - regular density buckets, non-last columns
    lines_regular = (
        alt.Chart(bump_df[~bump_df['is_average'] & ~bump_df['is_last_column']])
        .mark_line(point=alt.OverlayMarkDef(size=120, filled=True), strokeWidth=3.5, opacity=0.8)
        .encode(
            x=alt.X(
                'x_pos:Q',
                scale=alt.Scale(domain=[-0.5, num_densities + 1.5]),
                axis=None,
            ),
            y=alt.Y(
                'overall_rank:Q',
                scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]),
                axis=None,
            ),
            color=alt.Color(
                'algorithm:N',
                scale=alt.Scale(
                    domain=bump_df['algorithm'].unique().tolist(),
                    range=bump_df.drop_duplicates('algorithm')['color'].tolist(),
                ),
                legend=None,
            ),
            detail='algorithm:N',
            tooltip=[
                alt.Tooltip('algorithm_name:N', title='Algorithm'),
                alt.Tooltip('density_bucket:N', title='Density Bucket'),
                alt.Tooltip('overall_rank:Q', title='Rank'),
                alt.Tooltip('rank_mean:Q', title='Avg Rank', format='.2f'),
            ],
        )
    )
    
    # Last column before average (BIGGER POINTS)
    lines_last_regular = (
        alt.Chart(bump_df[~bump_df['is_average'] & bump_df['is_last_column']])
        .mark_line(point=alt.OverlayMarkDef(size=160, filled=True), strokeWidth=3.5, opacity=0.8)
        .encode(
            x=alt.X(
                'x_pos:Q',
                scale=alt.Scale(domain=[-0.5, num_densities + 1.5]),
                axis=None,
            ),
            y=alt.Y(
                'overall_rank:Q',
                scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]),
                axis=None,
            ),
            color=alt.Color(
                'algorithm:N',
                scale=alt.Scale(
                    domain=bump_df['algorithm'].unique().tolist(),
                    range=bump_df.drop_duplicates('algorithm')['color'].tolist(),
                ),
                legend=None,
            ),
            detail='algorithm:N',
            tooltip=[
                alt.Tooltip('algorithm_name:N', title='Algorithm'),
                alt.Tooltip('density_bucket:N', title='Density Bucket'),
                alt.Tooltip('overall_rank:Q', title='Rank'),
                alt.Tooltip('rank_mean:Q', title='Avg Rank', format='.2f'),
            ],
        )
    )
    
    # Average rank column (BOLD and BIGGEST)
    lines_average = (
        alt.Chart(bump_df[bump_df['is_average']])
        .mark_line(point=alt.OverlayMarkDef(size=200, filled=True, strokeWidth=2), strokeWidth=5, opacity=1)
        .encode(
            x=alt.X(
                'x_pos:Q',
                scale=alt.Scale(domain=[-0.5, num_densities + 1.5]),
                axis=None,
            ),
            y=alt.Y(
                'overall_rank:Q',
                scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]),
                axis=None,
            ),
            color=alt.Color(
                'algorithm:N',
                scale=alt.Scale(
                    domain=bump_df['algorithm'].unique().tolist(),
                    range=bump_df.drop_duplicates('algorithm')['color'].tolist(),
                ),
                legend=None,
            ),
            detail='algorithm:N',
            tooltip=[
                alt.Tooltip('algorithm_name:N', title='Algorithm'),
                alt.Tooltip('density_bucket:N', title='Density Bucket'),
                alt.Tooltip('overall_rank:Q', title='Rank'),
                alt.Tooltip('rank_mean:Q', title='Avg Rank', format='.2f'),
            ],
        )
    )
    
    # Algorithm labels on the right
    last_density = density_order[-1]
    labels_df = bump_df[bump_df['density_bucket'] == last_density].copy()
    
    labels = (
        alt.Chart(labels_df)
        .mark_text(
            align='left',
            baseline='middle',
            dx=35,
            fontSize=16,
            fontWeight=500,
        )
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_densities + 1.5]), axis=None),
            y=alt.Y('overall_rank:Q', scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]), axis=None),
            text='algorithm_name:N',
            color=alt.value('black'),
        )
    )
    
    # Rank numbers
    rank_numbers = (
        alt.Chart(labels_df)
        .mark_text(
            align='left',
            baseline='middle',
            dx=15,
            fontSize=16,
            fontWeight='bold',
        )
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_densities + 1.5]), axis=None),
            y=alt.Y('overall_rank:Q', scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]), axis=None),
            text=alt.Text('overall_rank:Q', format='d'),
            color=alt.value('black'),
        )
    )
    
    # Density bucket labels at TOP
    density_labels_df = pd.DataFrame({
        'density_bucket': density_order,
        'density_label': [d.capitalize() for d in density_order if d != 'Average rank'] + ['Average rank'],
        'x_pos': range(len(density_order)),
        'y_pos': [-0.3] * len(density_order),
        'is_average': [d == 'Average rank' for d in density_order],
    })
    
    # Regular density bucket labels (no rotation for short labels)
    density_labels = (
        alt.Chart(density_labels_df[~density_labels_df['is_average']])
        .mark_text(
            align='center',
            baseline='bottom',
            fontSize=16,
            angle=0,
            dy=-3,
        )
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_densities + 1.5]), axis=None),
            y=alt.Y('y_pos:Q', scale=alt.Scale(domain=[-0.5, max_rank + 0.5]), axis=None),
            text='density_label:N',
            color=alt.value('black'),
        )
    )
    
    # 'Average rank' label (bold)
    average_label = (
        alt.Chart(density_labels_df[density_labels_df['is_average']])
        .mark_text(
            align='center',
            baseline='bottom',
            fontSize=16,
            fontWeight='bold',
            angle=0,
            dy=-3,
        )
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_densities + 1.5]), axis=None),
            y=alt.Y('y_pos:Q', scale=alt.Scale(domain=[-0.5, max_rank + 0.5]), axis=None),
            text=alt.Text('density_bucket:N'),
            color=alt.value('black'),
        )
    )
    
    # Combine all layers
    chart = (
        (lines_regular + lines_last_regular + lines_average + labels + rank_numbers + density_labels + average_label)
        .properties(
            width=120 * num_densities,
            height=450,
        )
        .configure_view(
            strokeWidth=0,
        )
    )
    
    return chart


def main():
    parser = argparse.ArgumentParser(
        description='Rank algorithms by data point density (Low, Medium, High)'
    )
    parser.add_argument(
        '--density',
        type=str,
        choices=['low', 'medium', 'high'],
        help='Density bucket to analyze (low, medium, high)',
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Analyze all density buckets and overall rankings',
    )
    
    args = parser.parse_args()
    
    if not args.density and not args.all:
        print("❌ Please specify --density or --all")
        print(f"Available densities: low, medium, high")
        return
    
    output_dir = Path('plots') / 'density_rankings'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process densities
    if args.all:
        densities_to_process = ['low', 'medium', 'high', 'overall']
    else:
        densities_to_process = [args.density]
    
    for dens in densities_to_process:
        if dens == 'overall':
            # Overall ranking (all densities)
            print("\n" + "="*80)
            bump_df = compute_density_ranks(density=None)
            filename_prefix = 'overall'
        else:
            print("\n" + "="*80)
            bump_df = compute_density_ranks(density=dens)
            filename_prefix = dens
        
        if bump_df.empty:
            continue
        
        # Save CSV
        csv_path = output_dir / f'{filename_prefix}_bump_ranks.csv'
        bump_df.to_csv(csv_path, index=False)
        print(f"   ✅ Saved bump data CSV: {csv_path}")
        
        # Create bump chart
        chart = create_bump_chart(bump_df, density=dens if dens != 'overall' else None)
        
        svg_path = output_dir / f'{filename_prefix}_bump_chart.svg'
        html_path = output_dir / f'{filename_prefix}_bump_chart.html'
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
