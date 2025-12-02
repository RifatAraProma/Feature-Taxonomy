"""
Rank algorithms across dataset types and create bump charts.

This script aggregates algorithm performance across multiple datasets of the same type
(e.g., all EEG 500-sample datasets) and creates a bump chart showing how algorithm
rankings change across those datasets.

Usage:
    python rank_algorithms_by_dataset_type.py --type eeg_500
    python rank_algorithms_by_dataset_type.py --type climate_tmax
    python rank_algorithms_by_dataset_type.py --all
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


# Dataset type groupings
DATASET_TYPES = {
    'eeg_500': ['eeg_chan05_500', 'eeg_chan10_500', 'eeg_chan15_500',
                'eeg_chan20_500', 'eeg_chan25_500', 'eeg_chan30_500'],
    'eeg_2500': ['eeg_chan05_2500', 'eeg_chan10_2500', 'eeg_chan15_2500',
                 'eeg_chan20_2500', 'eeg_chan25_2500', 'eeg_chan30_2500'],
    'eeg_10000': ['eeg_chan05_10000', 'eeg_chan10_10000', 'eeg_chan15_10000',
                  'eeg_chan20_10000', 'eeg_chan25_10000', 'eeg_chan30_10000'],
    'climate_tmax': ['climate_atl_tmax', 'climate_jfk_tmax', 'climate_lax_tmax',
                     'climate_ord_tmax', 'climate_sea_tmax', 'climate_slc_tmax'],
    'climate_awnd': ['climate_atl_awnd', 'climate_jfk_awnd', 'climate_lax_awnd',
                     'climate_ord_awnd', 'climate_sea_awnd', 'climate_slc_awnd'],
    'climate_prcp': ['climate_atl_prcp', 'climate_jfk_prcp', 'climate_lax_prcp',
                     'climate_ord_prcp', 'climate_sea_prcp', 'climate_slc_prcp'],
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
    'flights': ['flights_daily', 'flights_monthly', 'flights_weekly'],
    'nz_tourism': ['nz_tourist_annually', 'nz_tourist_monthly'],
    'crime': ['chi_homicide_monthly', 'chi_homicide_weekly'],
    'astro': ['astro_115_120', 'astro_115_123', 'astro_115_128',
              'astro_116_124', 'astro_116_134'],
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
        print(f"⚠️  Ranking file not found: {ranking_file}")
        return pd.DataFrame()

    print(f"  Loading rankings from {dataset_name}...")

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
        print(f"⚠️  Error loading {ranking_file}: {e}")
        return pd.DataFrame()


def compute_datasetwise_ranks(dataset_type: str) -> pd.DataFrame:
    """
    For a dataset type (e.g., 'eeg_500'), compute algorithm rankings
    separately for each dataset, plus an overall average rank.

    Returns a long DataFrame with columns:
        dataset, algorithm, algorithm_name, color,
        rank_mean, rank_std, count, overall_rank
    """
    datasets = DATASET_TYPES.get(dataset_type, [])
    if not datasets:
        print(f"❌ Unknown dataset type: {dataset_type}")
        return pd.DataFrame()

    print(f"\n📊 Computing per-dataset rankings for type: {dataset_type}")
    print(f"   Datasets: {', '.join(datasets)}")

    rows = []

    for d in datasets:
        df_long = load_ranking_data(d)
        if df_long.empty:
            continue

        # Aggregate across metrics for this dataset
        stats = df_long.groupby('algorithm').agg(
            rank_mean=('rank', 'mean'),
            rank_std=('rank', 'std'),
            count=('rank', 'count'),
        ).reset_index()

        # Standard error (optional)
        stats['rank_stderr'] = stats['rank_std'] / np.sqrt(stats['count'])

        # Rank algorithms for this dataset (1 = best)
        stats = stats.sort_values('rank_mean', ascending=True).reset_index(drop=True)
        stats['overall_rank'] = range(1, len(stats) + 1)

        stats['dataset'] = d
        stats['algorithm_name'] = stats['algorithm'].apply(get_algorithm_name)
        stats['color'] = stats['algorithm'].apply(get_algorithm_color)

        rows.append(stats)

    if not rows:
        print(f"❌ No ranking data found for any dataset in type: {dataset_type}")
        return pd.DataFrame()

    combined = pd.concat(rows, ignore_index=True)

    # Compute average rank across datasets for each algorithm
    avg_stats = (
        combined.groupby(['algorithm', 'algorithm_name', 'color'])
        .agg(avg_rank_mean=('rank_mean', 'mean'))
        .reset_index()
    )
    avg_stats = avg_stats.sort_values('avg_rank_mean', ascending=True).reset_index(drop=True)
    avg_stats['overall_rank'] = range(1, len(avg_stats) + 1)
    avg_stats['dataset'] = 'Average rank'
    avg_stats['rank_mean'] = avg_stats['avg_rank_mean']

    # For consistency with combined columns
    avg_stats['rank_std'] = np.nan
    avg_stats['count'] = combined.groupby('algorithm')['dataset'].nunique().values
    avg_stats['rank_stderr'] = np.nan

    bump_df = pd.concat(
        [
            combined[
                [
                    'dataset',
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
                    'dataset',
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


def create_bump_chart(bump_df: pd.DataFrame, dataset_type: str) -> alt.Chart:
    """
    Create a minimal, clean bump chart with algorithm labels embedded.

    bump_df must contain:
        dataset, algorithm, algorithm_name, color, overall_rank
    """
    # Order datasets: explicit order from DATASET_TYPES + "Average rank"
    base_order = DATASET_TYPES.get(dataset_type, [])
    dataset_order = base_order + ['Average rank']
    
    return create_bump_chart_base(
        bump_df=bump_df,
        column_order=dataset_order,
        column_name='dataset',
        rank_column='overall_rank',  # Use overall_rank for y-position
        overall_rank_column='overall_rank',
        avg_rank_column='rank_mean',  # Use rank_mean for tooltip
        average_label='Average rank',
    )


def main():
    """
    Create a minimal, clean bump chart with algorithm labels embedded.

    bump_df must contain:
        dataset, algorithm, algorithm_name, color, overall_rank
    """
    # Order datasets: explicit order from DATASET_TYPES + "Average rank"
    base_order = DATASET_TYPES.get(dataset_type, [])
    dataset_order = base_order + ['Average rank']

    # Create numeric x position for easier positioning
    bump_df = bump_df.copy()
    bump_df['x_pos'] = bump_df['dataset'].map(
        {d: i for i, d in enumerate(dataset_order)}
    )

    # Calculate chart dimensions
    num_datasets = len(dataset_order)
    max_rank = int(bump_df['overall_rank'].max())
    
    # Add flags for styling
    bump_df['is_average'] = bump_df['dataset'] == 'Average rank'
    bump_df['is_last_column'] = bump_df['dataset'] == dataset_order[-1]
    
    # Lines connecting ranks across datasets - regular datasets, non-last columns
    lines_regular = (
        alt.Chart(bump_df[~bump_df['is_average'] & ~bump_df['is_last_column']])
        .mark_line(point=alt.OverlayMarkDef(size=120, filled=True), strokeWidth=3.5, opacity=0.8)
        .encode(
            x=alt.X(
                'x_pos:Q',
                scale=alt.Scale(domain=[-0.5, num_datasets + 1.5]),  # Extended for labels
                axis=None,
            ),
            y=alt.Y(
                'overall_rank:Q',
                scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]),  # Space for top labels
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
                alt.Tooltip('dataset:N', title='Dataset'),
                alt.Tooltip('overall_rank:Q', title='Rank'),
                alt.Tooltip('rank_mean:Q', title='Avg Rank', format='.2f'),
            ],
        )
    )
    
    # Last column before average (BIGGER POINTS but not bold)
    lines_last_regular = (
        alt.Chart(bump_df[~bump_df['is_average'] & bump_df['is_last_column']])
        .mark_line(point=alt.OverlayMarkDef(size=160, filled=True), strokeWidth=3.5, opacity=0.8)
        .encode(
            x=alt.X(
                'x_pos:Q',
                scale=alt.Scale(domain=[-0.5, num_datasets + 1.5]),
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
                alt.Tooltip('dataset:N', title='Dataset'),
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
                scale=alt.Scale(domain=[-0.5, num_datasets + 1.5]),
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
                alt.Tooltip('dataset:N', title='Dataset'),
                alt.Tooltip('overall_rank:Q', title='Rank'),
                alt.Tooltip('rank_mean:Q', title='Avg Rank', format='.2f'),
            ],
        )
    )

    # Add algorithm labels on the right side - MORE TO THE RIGHT
    last_dataset = dataset_order[-1]
    labels_df = bump_df[bump_df['dataset'] == last_dataset].copy()

    labels = (
        alt.Chart(labels_df)
        .mark_text(
            align='middle',
            baseline='middle',
            dx=35,  # Increased from 8 to move further right
            fontSize=16,
            fontWeight=500,
        )
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_datasets + 1.5]), axis=None),
            y=alt.Y('overall_rank:Q', scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]), axis=None),
            text='algorithm_name:N',
            color=alt.value('black'),  # Black text for all algorithm names
        )
    )
    
    # Add rank numbers for average column
    rank_numbers = (
        alt.Chart(labels_df)
        .mark_text(
            align='left',
            baseline='middle',
            dx=15,  # Position to the left of the points
            fontSize=16,
            fontWeight='bold',
        )
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_datasets + 1.5]), axis=None),
            y=alt.Y('overall_rank:Q', scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]), axis=None),
            text=alt.Text('overall_rank:Q', format='d'),
            color=alt.value('black'),
        )
    )

    # Dataset labels at TOP with special styling for 'Average rank'
    dataset_labels_df = pd.DataFrame({
        'dataset': dataset_order,
        'x_pos': range(len(dataset_order)),
        'y_pos': [-0.3] * len(dataset_order),  # Negative y to place at top
        'is_average': [d == 'Average rank' for d in dataset_order],
    })

    # Regular dataset labels (black)
    dataset_labels = (
        alt.Chart(dataset_labels_df[~dataset_labels_df['is_average']])
        .mark_text(
            align='center',
            baseline='bottom',
            fontSize=16,
            angle=315,  # Horizontal text at top
            dy=0,
            dx = 55
        )
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_datasets + 1.5]), axis=None),
            y=alt.Y('y_pos:Q', scale=alt.Scale(domain=[-0.5, max_rank + 0.5]), axis=None),
            text=alt.Text('dataset:N'),
            color=alt.value('black'),
        )
    )
    
    # 'Average rank' label (bold black)
    average_label = (
        alt.Chart(dataset_labels_df[dataset_labels_df['is_average']])
        .mark_text(
            align='center',
            baseline='bottom',
            fontSize=16,
            fontWeight='bold',
            angle=0,
            dy=-3,
        )
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_datasets + 1.5]), axis=None),
            y=alt.Y('y_pos:Q', scale=alt.Scale(domain=[-0.5, max_rank + 0.5]), axis=None),
            text=alt.Text('dataset:N'),
            color=alt.value('black'),
        )
    )

    # Combine all layers - SHORTER DISTANCE (increased width per dataset)
    chart = (
        (lines_regular + lines_last_regular + lines_average + labels + rank_numbers + dataset_labels + average_label)
        .properties(
            width=120 * num_datasets,  # Increased spacing between datasets
            height=450,
        )
        .configure_view(
            strokeWidth=0,  # No border
        )
    )

    return chart


def main():
    parser = argparse.ArgumentParser(
        description='Rank algorithms across dataset types and create bump charts'
    )
    parser.add_argument(
        '--type',
        type=str,
        help='Dataset type to analyze (e.g., eeg_500, climate_tmax, stock_price)',
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Analyze all dataset types',
    )

    args = parser.parse_args()

    if not args.type and not args.all:
        print("❌ Please specify --type or --all")
        print(f"Available types: {', '.join(DATASET_TYPES.keys())}")
        return

    types_to_process = list(DATASET_TYPES.keys()) if args.all else [args.type]

    output_dir = Path('plots') / 'dataset_type_rankings'
    output_dir.mkdir(parents=True, exist_ok=True)

    for dataset_type in types_to_process:
        if dataset_type not in DATASET_TYPES:
            print(f"❌ Unknown dataset type: {dataset_type}")
            continue

        bump_df = compute_datasetwise_ranks(dataset_type)
        if bump_df.empty:
            continue

        # Save CSV with all per-dataset ranks (including Average rank)
        csv_path = output_dir / f'{dataset_type}_bump_ranks.csv'
        bump_df.to_csv(csv_path, index=False)
        print(f"   ✅ Saved bump data CSV: {csv_path}")

        # Create bump chart
        chart = create_bump_chart(bump_df, dataset_type)

        svg_path = output_dir / f'{dataset_type}_bump_chart.svg'
        html_path = output_dir / f'{dataset_type}_bump_chart.html'
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
