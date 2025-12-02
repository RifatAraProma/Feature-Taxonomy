"""
Rank algorithms by category (Transformers, Reducers, Aggregators).

This script follows the EXACT same mechanism as rank_algorithms_by_dataset_type.py
but groups algorithms by their category instead of dataset type.

Usage:
    python rank_algorithms_by_category.py --all
    python rank_algorithms_by_category.py --category transformer
    python rank_algorithms_by_category.py --category reducer
    python rank_algorithms_by_category.py --category aggregator
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


# Algorithm categories
ALGORITHM_CATEGORIES = {
    'transformer': [
        'gaussian_filter',
        'mean_filter',
        'median_filter',
        'savitzky_golay_filter',
        'butterworth_filter',
        'chebyshev_filter',
        'elliptical_filter',
        'fft_cutoff_filter',
        'max_filter',
        'min_filter',
    ],
    'reducer': [
        'lttb_downsample',
        'm4_downsample',
        'minmaxlttb_downsample',
        'uniform_subsample',
        'rdp_downsample',
        'fpcs_downsample',
        'tda_downsample',
    ],
    'aggregator': [
        'asap_aggregator',
        'bin_average_aggregator',
    ],
}

# Dataset type groupings (same as other scripts)
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


def get_algorithm_category(algorithm: str) -> str:
    """Map algorithm to its category."""
    for category, algorithms in ALGORITHM_CATEGORIES.items():
        if algorithm in algorithms:
            return category
    return 'other'


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


def compute_category_ranks(category: str = None) -> pd.DataFrame:
    """
    Compute algorithm rankings across dataset types, optionally filtered by category.
    
    If category is specified, only rank algorithms within that category.
    Otherwise, rank all algorithms but mark their categories.

    Returns DataFrame with columns:
        dataset_type, algorithm, algorithm_name, color, category,
        rank_mean, rank_std, count, overall_rank
    """
    if category:
        print(f"\n📊 Computing rankings for category: {category.upper()}")
        algorithms_to_include = ALGORITHM_CATEGORIES.get(category, [])
        if not algorithms_to_include:
            print(f"❌ Unknown category: {category}")
            return pd.DataFrame()
    else:
        print(f"\n📊 Computing rankings across all categories")
        algorithms_to_include = None
    
    # Use all dataset types as columns (for consistent x-axis)
    type_order = list(DATASET_TYPES.keys())
    print(f"   Dataset types: {len(type_order)} types")
    
    rows = []
    
    for dtype in type_order:
        datasets = DATASET_TYPES[dtype]
        
        # Load data for all datasets in this type
        type_rows = []
        for d in datasets:
            df_long = load_ranking_data(d)
            if df_long.empty:
                continue
            
            # Filter by category if specified
            if algorithms_to_include:
                df_long = df_long[df_long['algorithm'].isin(algorithms_to_include)]
            
            if df_long.empty:
                continue
            
            type_rows.append(df_long)
        
        if not type_rows:
            continue
        
        # Combine all datasets in this type
        type_df = pd.concat(type_rows, ignore_index=True)
        
        # Aggregate across metrics and datasets for this type
        stats = type_df.groupby('algorithm').agg(
            rank_mean=('rank', 'mean'),
            rank_std=('rank', 'std'),
            count=('rank', 'count'),
        ).reset_index()
        
        # Standard error
        stats['rank_stderr'] = stats['rank_std'] / np.sqrt(stats['count'])
        
        # Rank algorithms for this dataset type (1 = best)
        stats = stats.sort_values('rank_mean', ascending=True).reset_index(drop=True)
        stats['overall_rank'] = range(1, len(stats) + 1)
        
        stats['dataset_type'] = dtype
        stats['algorithm_name'] = stats['algorithm'].apply(get_algorithm_name)
        stats['color'] = stats['algorithm'].apply(get_algorithm_color)
        stats['category'] = stats['algorithm'].apply(get_algorithm_category)
        
        rows.append(stats)
    
    if not rows:
        print(f"❌ No ranking data found")
        return pd.DataFrame()
    
    combined = pd.concat(rows, ignore_index=True)
    
    # Compute average rank across dataset types for each algorithm
    avg_stats = (
        combined.groupby(['algorithm', 'algorithm_name', 'color', 'category'])
        .agg(avg_rank_mean=('rank_mean', 'mean'))
        .reset_index()
    )
    avg_stats = avg_stats.sort_values('avg_rank_mean', ascending=True).reset_index(drop=True)
    avg_stats['overall_rank'] = range(1, len(avg_stats) + 1)
    avg_stats['dataset_type'] = 'Average rank'
    avg_stats['rank_mean'] = avg_stats['avg_rank_mean']
    
    # For consistency with combined columns
    avg_stats['rank_std'] = np.nan
    avg_stats['count'] = combined.groupby('algorithm')['dataset_type'].nunique().values
    avg_stats['rank_stderr'] = np.nan
    
    bump_df = pd.concat(
        [
            combined[
                [
                    'dataset_type',
                    'algorithm',
                    'algorithm_name',
                    'color',
                    'category',
                    'rank_mean',
                    'rank_std',
                    'count',
                    'rank_stderr',
                    'overall_rank',
                ]
            ],
            avg_stats[
                [
                    'dataset_type',
                    'algorithm',
                    'algorithm_name',
                    'color',
                    'category',
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


def create_bump_chart(bump_df: pd.DataFrame, category: str = None) -> alt.Chart:
    """
    Create a minimal, clean bump chart - EXACT same style as rank_algorithms_by_dataset_type.py

    bump_df must contain:
        dataset_type, algorithm, algorithm_name, color, overall_rank
    """
    # Order dataset types: explicit order from DATASET_TYPES + "Average rank"
    type_order = list(DATASET_TYPES.keys()) + ['Average rank']
    
    return create_bump_chart_base(
        bump_df=bump_df,
        column_order=type_order,
        column_name='dataset_type',  # FIXED: was density_bucket
        rank_column='overall_rank',  # Use overall_rank for y-position
        overall_rank_column='overall_rank',
        avg_rank_column='rank_mean',  # Use rank_mean for tooltip
        average_label='Average rank',
    )


def main():
    """
    Create a minimal, clean bump chart - EXACT same style as rank_algorithms_by_dataset_type.py

    bump_df must contain:
        dataset_type, algorithm, algorithm_name, color, overall_rank
    """
    # Order dataset types: explicit order from DATASET_TYPES + "Average rank"
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
            x=alt.X(
                'x_pos:Q',
                scale=alt.Scale(domain=[-0.5, num_types + 1.5]),
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
                alt.Tooltip('dataset_type:N', title='Dataset Type'),
                alt.Tooltip('category:N', title='Category'),
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
                scale=alt.Scale(domain=[-0.5, num_types + 1.5]),
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
                alt.Tooltip('dataset_type:N', title='Dataset Type'),
                alt.Tooltip('category:N', title='Category'),
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
                scale=alt.Scale(domain=[-0.5, num_types + 1.5]),
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
                alt.Tooltip('dataset_type:N', title='Dataset Type'),
                alt.Tooltip('category:N', title='Category'),
                alt.Tooltip('overall_rank:Q', title='Rank'),
                alt.Tooltip('rank_mean:Q', title='Avg Rank', format='.2f'),
            ],
        )
    )
    
    # Algorithm labels on the right
    last_type = type_order[-1]
    labels_df = bump_df[bump_df['dataset_type'] == last_type].copy()
    
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
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_types + 1.5]), axis=None),
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
        .mark_text(
            align='center',
            baseline='bottom',
            fontSize=16,
            angle=315,
            dy=-6,
        )
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_types + 1.5]), axis=None),
            y=alt.Y('y_pos:Q', scale=alt.Scale(domain=[-0.5, max_rank + 0.5]), axis=None),
            text=alt.Text('dataset_type:N'),
            color=alt.value('black'),
        )
    )
    
    # 'Average rank' label (bold)
    average_label = (
        alt.Chart(type_labels_df[type_labels_df['is_average']])
        .mark_text(
            align='center',
            baseline='bottom',
            fontSize=16,
            fontWeight='bold',
            angle=0,
            dy=-3,
        )
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
            height=450,
        )
        .configure_view(
            strokeWidth=0,
        )
    )
    
    return chart


def main():
    parser = argparse.ArgumentParser(
        description='Rank algorithms by category (Transformers, Reducers, Aggregators)'
    )
    parser.add_argument(
        '--category',
        type=str,
        help='Category to analyze (transformer, reducer, aggregator)',
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Analyze all categories and overall rankings',
    )
    
    args = parser.parse_args()
    
    if not args.category and not args.all:
        print("❌ Please specify --category or --all")
        print(f"Available categories: {', '.join(ALGORITHM_CATEGORIES.keys())}")
        return
    
    output_dir = Path('plots') / 'category_rankings'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process categories
    if args.all:
        categories_to_process = list(ALGORITHM_CATEGORIES.keys()) + ['overall']
    else:
        categories_to_process = [args.category]
    
    for cat in categories_to_process:
        if cat == 'overall':
            # Overall ranking (all algorithms, marked by category)
            print("\n" + "="*80)
            bump_df = compute_category_ranks(category=None)
            filename_prefix = 'overall'
        else:
            if cat not in ALGORITHM_CATEGORIES:
                print(f"❌ Unknown category: {cat}")
                continue
            print("\n" + "="*80)
            bump_df = compute_category_ranks(category=cat)
            filename_prefix = cat
        
        if bump_df.empty:
            continue
        
        # Save CSV
        csv_path = output_dir / f'{filename_prefix}_bump_ranks.csv'
        bump_df.to_csv(csv_path, index=False)
        print(f"   ✅ Saved bump data CSV: {csv_path}")
        
        # Create bump chart
        chart = create_bump_chart(bump_df, category=cat if cat != 'overall' else None)
        
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
