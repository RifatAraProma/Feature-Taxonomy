"""
Rank algorithms on periodic datasets for periodicity metrics.

This script analyzes algorithm performance specifically on datasets with
true periodic patterns (climate seasonality, unemployment cycles, crime patterns)
for periodicity-related metrics.

Usage:
    python rank_algorithms_periodic_datasets.py --metric periodicity_num_periods_delta
    python rank_algorithms_periodic_datasets.py --metric periodicity_amplitude_delta
    python rank_algorithms_periodic_datasets.py --all
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


# Periodic datasets with true seasonal/cyclical patterns
PERIODIC_DATASETS = [
    # Crime data - monthly/weekly cycles
    'chi_homicide_monthly',
    'chi_homicide_weekly',
    
    # Climate data - seasonal patterns (6 airports × 2 metrics)
    'climate_atl_awnd',
    'climate_atl_tmax',
    'climate_jfk_awnd',
    'climate_jfk_tmax',
    'climate_lax_awnd',
    'climate_lax_tmax',
    'climate_ord_awnd',
    'climate_ord_tmax',
    'climate_sea_awnd',
    'climate_sea_tmax',
    'climate_slc_awnd',
    'climate_slc_tmax',
    
    # Unemployment data - seasonal employment patterns
    'unemployment_ag',
]

# Periodicity metrics to analyze
PERIODICITY_METRICS = {
    'periodicity_num_periods_delta': 'Number of Periods Preservation',
    'periodicity_amplitude_delta': 'Amplitude Preservation',
}


def load_ranking_data(dataset_name: str, metric_name: str) -> pd.DataFrame:
    """
    Load pre-computed FC score-based ranks for a single dataset and specific metric from:
        plots/{dataset}/ranking/rankings_ranked.csv
    
    These ranks are already computed using z-score normalization and FC scoring.

    Returns DataFrame with columns:
        algorithm, rank, dataset
    """
    ranking_file = Path('plots') / dataset_name / 'ranking' / 'rankings_ranked.csv'

    if not ranking_file.exists():
        print(f"⚠️  Ranking file not found: {ranking_file}")
        return pd.DataFrame()

    print(f"  Loading {metric_name} from {dataset_name}...")

    try:
        df = pd.read_csv(ranking_file)

        if metric_name not in df.columns:
            print(f"⚠️  Metric '{metric_name}' not found in {dataset_name}")
            return pd.DataFrame()

        # Extract algorithm and pre-computed rank (already FC score-based)
        df_subset = df[['algorithm', metric_name]].copy()
        df_subset = df_subset.rename(columns={metric_name: 'rank'})
        
        df_subset['dataset'] = dataset_name
        df_subset = df_subset[['algorithm', 'rank', 'dataset']]
        
        return df_subset

    except Exception as e:
        print(f"⚠️  Error loading {ranking_file}: {e}")
        return pd.DataFrame()


def compute_periodic_ranks(metric_name: str) -> pd.DataFrame:
    """
    For periodic datasets, compute algorithm rankings across datasets
    for the specified periodicity metric.

    Returns a long DataFrame with columns:
        dataset, algorithm, algorithm_name, color, rank, overall_rank, avg_rank
    """
    print(f"\n📊 Computing periodic dataset rankings for: {metric_name}")
    print(f"   Datasets ({len(PERIODIC_DATASETS)}): {', '.join(PERIODIC_DATASETS[:3])}...")

    rows = []

    for d in PERIODIC_DATASETS:
        df = load_ranking_data(d, metric_name)
        if df.empty:
            continue

        df['algorithm_name'] = df['algorithm'].apply(get_algorithm_name)
        df['color'] = df['algorithm'].apply(get_algorithm_color)
        rows.append(df)

    if not rows:
        print(f"❌ No ranking data found for metric: {metric_name}")
        return pd.DataFrame()

    combined = pd.concat(rows, ignore_index=True)

    # Compute average rank across datasets for each algorithm
    avg_stats = (
        combined.groupby(['algorithm', 'algorithm_name', 'color'])
        .agg(
            avg_rank=('rank', 'mean'),
            rank_std=('rank', 'std'),
            count=('rank', 'count'),
        )
        .reset_index()
        .sort_values('avg_rank', ascending=True)
    )

    # Assign overall rank (1 = best)
    avg_stats['overall_rank'] = range(1, len(avg_stats) + 1)

    # Merge overall_rank (and avg_rank) back to combined dataframe
    combined = combined.merge(
        avg_stats[['algorithm', 'overall_rank', 'avg_rank']],
        on='algorithm',
        how='left'
    )

    # "Average rank" pseudo-dataset:
    # use overall_rank for y-position (to avoid overlap),
    # but keep avg_rank for tooltips.
    avg_stats_for_dataset = avg_stats.copy()
    avg_stats_for_dataset['dataset'] = 'Average rank'
    avg_stats_for_dataset['rank'] = avg_stats_for_dataset['overall_rank']

    # Combine individual dataset ranks with average
    bump_df = pd.concat(
        [
            combined[['dataset', 'algorithm', 'algorithm_name', 'color',
                      'rank', 'overall_rank', 'avg_rank']],
            avg_stats_for_dataset[['dataset', 'algorithm', 'algorithm_name',
                                   'color', 'rank', 'overall_rank', 'avg_rank']],
        ],
        ignore_index=True,
    )

    print(f"\n✅ Computed rankings for {len(PERIODIC_DATASETS)} datasets")
    print(f"   Top 5 algorithms (by avg rank):")
    for i, row in avg_stats.head(5).iterrows():
        print(f"      {int(row['overall_rank'])}. {row['algorithm_name']}: {row['avg_rank']:.2f}")

    return bump_df


def create_bump_chart(bump_df: pd.DataFrame, metric_name: str, output_dir: Path = None) -> alt.Chart:
    """
    Create a bump chart showing algorithm rankings across periodic datasets.
    
    Wrapper around shared bump_chart_utils.create_bump_chart().
    """
    dataset_order = PERIODIC_DATASETS + ['Average rank']
    
    return create_bump_chart_base(
        bump_df=bump_df,
        column_order=dataset_order,
        column_name='dataset',
        rank_column='rank',
        overall_rank_column='overall_rank',
        avg_rank_column='avg_rank',
        average_label='Average rank',
    )


def main():

    """
    Create a bump chart showing algorithm rankings across periodic datasets.

    bump_df must contain:
        dataset, algorithm, algorithm_name, color, rank, overall_rank
    """
    # Order datasets: PERIODIC_DATASETS + "Average rank"
    dataset_order = PERIODIC_DATASETS + ['Average rank']

    bump_df = bump_df.copy()
    bump_df['x_pos'] = bump_df['dataset'].map(
        {d: i for i, d in enumerate(dataset_order)}
    )

    num_datasets = len(dataset_order)
    max_rank = int(bump_df['rank'].max())

    average_dataset = 'Average rank'
    last_regular_dataset = dataset_order[-2]  # last real dataset before "Average rank"

    bump_df['is_average'] = bump_df['dataset'] == average_dataset
    bump_df['is_last_regular'] = bump_df['dataset'] == last_regular_dataset
    bump_df['is_regular'] = (~bump_df['is_average']) & (~bump_df['is_last_regular'])

    # Color mapping
    alg_order = bump_df['algorithm'].drop_duplicates().tolist()
    color_lookup = (
        bump_df.drop_duplicates('algorithm')[['algorithm', 'color']]
        .set_index('algorithm')['color']
        .reindex(alg_order)
        .tolist()
    )

    color_encoding = alt.Color(
        'algorithm:N',
        scale=alt.Scale(
            domain=alg_order,
            range=color_lookup,
        ),
        legend=None,
    )

    x_enc = alt.X(
        'x_pos:Q',
        scale=alt.Scale(domain=[-0.5, num_datasets + 1.5]),
        axis=None,
    )
    y_enc = alt.Y(
        'rank:Q',
        scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]),
        axis=None,
    )

    # Base lines: go through all columns (including last + Average rank)
    lines = (
        alt.Chart(bump_df)
        .mark_line(strokeWidth=3.5, opacity=0.8)
        .encode(
            x=x_enc,
            y=y_enc,
            color=color_encoding,
            detail='algorithm:N',
        )
    )

    # Regular points
    points_regular = (
        alt.Chart(bump_df[bump_df['is_regular']])
        .mark_point(size=120, filled=True)
        .encode(
            x=x_enc,
            y=y_enc,
            color=color_encoding,
            detail='algorithm:N',
        )
    )

    # Last regular column – bigger points
    points_last_regular = (
        alt.Chart(bump_df[bump_df['is_last_regular']])
        .mark_point(size=160, filled=True)
        .encode(
            x=x_enc,
            y=y_enc,
            color=color_encoding,
            detail='algorithm:N',
        )
    )

    # Average rank column – biggest points
    points_average = (
        alt.Chart(bump_df[bump_df['is_average']])
        .mark_point(size=200, filled=True, strokeWidth=2)
        .encode(
            x=x_enc,
            y=y_enc,  # uses 'rank' = overall_rank (1..N)
            color=color_encoding,
            detail='algorithm:N',
        )
    )

    # Labels on the right (Average rank column)
    last_dataset = dataset_order[-1]
    labels_df = bump_df[bump_df['dataset'] == last_dataset].copy()

    labels = (
        alt.Chart(labels_df)
        .mark_text(align='left', baseline='middle', dx=35, fontSize=16, fontWeight=500)
        .encode(
            x=x_enc,
            y=y_enc,
            text=alt.Text('algorithm_name:N'),
            color=alt.value('black'),
        )
    )

    # Rank numbers next to labels
    rank_numbers = (
        alt.Chart(labels_df)
        .mark_text(align='left', baseline='middle', dx=15, fontSize=16, fontWeight='bold')
        .encode(
            x=x_enc,
            y=y_enc,
            text=alt.Text('overall_rank:Q', format='d'),
            color=alt.value('#333'),
        )
    )

    # Dataset labels at top
    dataset_labels_df = pd.DataFrame({
        'dataset': dataset_order,
        'x_pos': list(range(len(dataset_order))),
        'y_pos': [-0.3] * len(dataset_order),
    })

    dataset_labels = (
        alt.Chart(dataset_labels_df[dataset_labels_df['dataset'] != 'Average rank'])
        .mark_text(align='center', baseline='bottom', fontSize=16, angle=270, dy=3, dx=105)
        .encode(
            x=alt.X('x_pos:Q'),
            y=alt.Y('y_pos:Q'),
            text=alt.Text('dataset:N'),
            color=alt.value('#666'),
        )
    )

    average_label = (
        alt.Chart(dataset_labels_df[dataset_labels_df['dataset'] == 'Average rank'])
        .mark_text(align='center', baseline='bottom', fontSize=16, fontWeight='bold', angle=270, dy=3, dx=105)
        .encode(
            x=alt.X('x_pos:Q'),
            y=alt.Y('y_pos:Q'),
            text=alt.Text('dataset:N'),
            color=alt.value('#000'),
        )
    )

    chart = (
        lines
        + points_regular
        + points_last_regular
        + points_average
        + labels
        + rank_numbers
        + dataset_labels
        + average_label
    ).properties(
        width=120 * num_datasets,
        height=450,
        title=f'Algorithm Rankings: {PERIODICITY_METRICS.get(metric_name, metric_name)}',
    ).configure_view(
        strokeWidth=0
    )

    return chart


def main():
    parser = argparse.ArgumentParser(
        description='Rank algorithms on periodic datasets for periodicity metrics'
    )
    parser.add_argument(
        '--metric',
        choices=list(PERIODICITY_METRICS.keys()),
        help='Specific periodicity metric to analyze',
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Generate rankings for all periodicity metrics',
    )

    args = parser.parse_args()

    output_dir = Path('plots') / 'periodic_rankings'
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.all:
        metrics = list(PERIODICITY_METRICS.keys())
    elif args.metric:
        metrics = [args.metric]
    else:
        parser.print_help()
        return

    for metric in metrics:
        print('\n' + '=' * 80)
        
        # Compute rankings
        bump_df = compute_periodic_ranks(metric)
        if bump_df.empty:
            continue

        # Save bump data
        metric_short = metric.replace('periodicity_', '').replace('_delta', '')
        csv_path = output_dir / f'{metric_short}_bump_ranks.csv'
        bump_df.to_csv(csv_path, index=False)
        print(f"   ✅ Saved bump data CSV: {csv_path}")

        # Create and save bump chart
        chart = create_bump_chart(bump_df, metric)
        svg_path = output_dir / f'{metric_short}_bump_chart.svg'
        chart.save(str(svg_path))
        print(f"   ✅ Saved bump chart SVG: {svg_path}")

    print('\n' + '=' * 80)
    print(f"✅ Outputs saved to {output_dir}/")


if __name__ == '__main__':
    main()
