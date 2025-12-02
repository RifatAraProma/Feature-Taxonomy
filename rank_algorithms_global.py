"""
Global ranking of algorithms across ALL features and ALL datasets.

This script follows the EXACT same mechanism as rank_algorithms_by_dataset_type.py
but shows overall ranking aggregated across all features.

Usage:
    python rank_algorithms_global.py
"""

import sys
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


def load_all_ranking_data() -> pd.DataFrame:
    """
    Load ALL ranking data from all datasets.

    Returns long-form DataFrame with columns:
        dataset, algorithm, metric, rank
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
            
            # Melt to long form
            df_long = df.melt(
                id_vars=['algorithm'],
                var_name='metric',
                value_name='rank',
            )
            df_long['dataset'] = dataset_name
            
            rows.append(df_long)
            print(f"  ✅ Loaded {dataset_name}")
            
        except Exception as e:
            print(f"  ⚠️  Error loading {dataset_name}: {e}")
            continue
    
    if not rows:
        return pd.DataFrame()
    
    return pd.concat(rows, ignore_index=True)


def compute_global_ranks() -> pd.DataFrame:
    """
    Compute global algorithm rankings aggregated across ALL datasets, grouped by FEATURE.

    Returns DataFrame with columns:
        feature, algorithm, algorithm_name, color, rank_mean, overall_rank
    
    Where 'feature' cycles through all features + 'Average rank'
    """
    print("\n📊 Loading all ranking data...")
    df_long = load_all_ranking_data()
    
    if df_long.empty:
        print("❌ No ranking data found")
        return pd.DataFrame()
    
    print(f"\n   Loaded {len(df_long):,} ranking records")
    print(f"   Datasets: {df_long['dataset'].nunique()}")
    print(f"   Algorithms: {df_long['algorithm'].nunique()}")
    print(f"   Features: {df_long['metric'].nunique()}")
    
    print("\n📊 Computing per-feature global rankings...")
    
    features = sorted(df_long['metric'].unique())
    rows = []
    
    for feature in features:
        f_df = df_long[df_long['metric'] == feature].copy()
        
        # Aggregate across all datasets for this feature
        stats = f_df.groupby('algorithm').agg(
            rank_mean=('rank', 'mean'),
        ).reset_index()
        
        # Rank algorithms for this feature (1 = best)
        stats = stats.sort_values('rank_mean', ascending=True).reset_index(drop=True)
        stats['overall_rank'] = range(1, len(stats) + 1)
        
        stats['feature'] = feature
        stats['algorithm_name'] = stats['algorithm'].apply(get_algorithm_name)
        stats['color'] = stats['algorithm'].apply(get_algorithm_color)
        
        rows.append(stats)
    
    combined = pd.concat(rows, ignore_index=True)
    
    # Compute average rank across ALL features for each algorithm
    avg_stats = (
        combined.groupby(['algorithm'])
        .agg(avg_rank_mean=('rank_mean', 'mean'))
        .reset_index()
    )
    avg_stats = avg_stats.sort_values('avg_rank_mean', ascending=True).reset_index(drop=True)
    avg_stats['overall_rank'] = range(1, len(avg_stats) + 1)
    avg_stats['feature'] = 'Average rank'
    avg_stats['rank_mean'] = avg_stats['avg_rank_mean']
    avg_stats['algorithm_name'] = avg_stats['algorithm'].apply(get_algorithm_name)
    avg_stats['color'] = avg_stats['algorithm'].apply(get_algorithm_color)
    
    bump_df = pd.concat(
        [
            combined[['feature', 'algorithm', 'algorithm_name', 'color', 'rank_mean', 'overall_rank']],
            avg_stats[['feature', 'algorithm', 'algorithm_name', 'color', 'rank_mean', 'overall_rank']],
        ],
        ignore_index=True,
    )
    
    return bump_df


def create_bump_chart(bump_df: pd.DataFrame) -> alt.Chart:
    """
    Create a minimal, clean bump chart - EXACT same style as rank_algorithms_by_dataset_type.py

    bump_df must contain:
        feature, algorithm, algorithm_name, color, overall_rank
    """
    # Order features: all features alphabetically + "Average rank"
    features = sorted([f for f in bump_df['feature'].unique() if f != 'Average rank'])
    feature_order = features + ['Average rank']
    
    return create_bump_chart_base(
        bump_df=bump_df,
        column_order=feature_order,
        column_name='feature',
        rank_column='overall_rank',  # Use overall_rank for y-position
        overall_rank_column='overall_rank',
        avg_rank_column='rank_mean',  # Use rank_mean for tooltip
        average_label='Average rank',
    )


def main():
    """
    Create a minimal, clean bump chart - EXACT same style as rank_algorithms_by_dataset_type.py

    bump_df must contain:
        feature, algorithm, algorithm_name, color, overall_rank
    """
    # Order features: all features alphabetically + "Average rank"
    features = sorted([f for f in bump_df['feature'].unique() if f != 'Average rank'])
    feature_order = features + ['Average rank']
    
    # Create numeric x position
    bump_df = bump_df.copy()
    bump_df['x_pos'] = bump_df['feature'].map(
        {f: i for i, f in enumerate(feature_order)}
    )
    
    # Calculate chart dimensions
    num_features = len(feature_order)
    max_rank = int(bump_df['overall_rank'].max())
    
    # Add flags for styling
    bump_df['is_average'] = bump_df['feature'] == 'Average rank'
    bump_df['is_last_column'] = bump_df['feature'] == feature_order[-1]
    
    # Lines - regular features, non-last columns
    lines_regular = (
        alt.Chart(bump_df[~bump_df['is_average'] & ~bump_df['is_last_column']])
        .mark_line(point=alt.OverlayMarkDef(size=120, filled=True), strokeWidth=3.5, opacity=0.8)
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_features + 1.5]), axis=None),
            y=alt.Y('overall_rank:Q', scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]), axis=None),
            color=alt.Color('algorithm:N', scale=alt.Scale(
                domain=bump_df['algorithm'].unique().tolist(),
                range=bump_df.drop_duplicates('algorithm')['color'].tolist(),
            ), legend=None),
            detail='algorithm:N',
            tooltip=[
                alt.Tooltip('algorithm_name:N', title='Algorithm'),
                alt.Tooltip('feature:N', title='Feature'),
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
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_features + 1.5]), axis=None),
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
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_features + 1.5]), axis=None),
            y=alt.Y('overall_rank:Q', scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]), axis=None),
            color=alt.Color('algorithm:N', scale=alt.Scale(
                domain=bump_df['algorithm'].unique().tolist(),
                range=bump_df.drop_duplicates('algorithm')['color'].tolist(),
            ), legend=None),
            detail='algorithm:N',
        )
    )
    
    # Algorithm labels on the right
    last_feature = feature_order[-1]
    labels_df = bump_df[bump_df['feature'] == last_feature].copy()
    
    labels = (
        alt.Chart(labels_df)
        .mark_text(align='left', baseline='middle', dx=35, fontSize=16, fontWeight=500)
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_features + 1.5]), axis=None),
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
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_features + 1.5]), axis=None),
            y=alt.Y('overall_rank:Q', scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]), axis=None),
            text=alt.Text('overall_rank:Q', format='d'),
            color=alt.value('black'),
        )
    )
    
    # Feature labels at TOP
    feature_labels_df = pd.DataFrame({
        'feature': feature_order,
        'x_pos': range(len(feature_order)),
        'y_pos': [-0.3] * len(feature_order),
        'is_average': [f == 'Average rank' for f in feature_order],
    })
    
    # Regular feature labels (horizontal)
    feature_labels = (
        alt.Chart(feature_labels_df[~feature_labels_df['is_average']])
        .mark_text(align='center', baseline='bottom', fontSize=16, angle=315, dy=-6)
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_features + 1.5]), axis=None),
            y=alt.Y('y_pos:Q', scale=alt.Scale(domain=[-0.5, max_rank + 0.5]), axis=None),
            text=alt.Text('feature:N'),
            color=alt.value('black'),
        )
    )
    
    # 'Average rank' label (bold)
    average_label = (
        alt.Chart(feature_labels_df[feature_labels_df['is_average']])
        .mark_text(align='center', baseline='bottom', fontSize=16, fontWeight='bold', angle=0, dy=-3)
        .encode(
            x=alt.X('x_pos:Q', scale=alt.Scale(domain=[-0.5, num_features + 1.5]), axis=None),
            y=alt.Y('y_pos:Q', scale=alt.Scale(domain=[-0.5, max_rank + 0.5]), axis=None),
            text=alt.Text('feature:N'),
            color=alt.value('black'),
        )
    )
    
    # Combine all layers
    chart = (
        (lines_regular + lines_last_regular + lines_average + labels + rank_numbers + feature_labels + average_label)
        .properties(
            width=120 * num_features,  # Same spacing as dataset-type charts
            height=750,
        )
        .configure_view(strokeWidth=0)
    )
    
    return chart


def main():
    print("=" * 80)
    print("GLOBAL ALGORITHM RANKING")
    print("=" * 80)
    
    bump_df = compute_global_ranks()
    if bump_df.empty:
        return
    
    output_dir = Path('plots') / 'global_ranking'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    csv_path = output_dir / 'global_bump_ranks.csv'
    bump_df.to_csv(csv_path, index=False)
    print(f"\n✅ Saved bump data CSV: {csv_path}")
    
    # Create bump chart
    chart = create_bump_chart(bump_df)
    
    svg_path = output_dir / 'global_bump_chart.svg'
    html_path = output_dir / 'global_bump_chart.html'
    try:
        chart.save(str(svg_path), format='svg')
        print(f"✅ Saved bump chart SVG: {svg_path}")
    except Exception as e:
        print(f"⚠️  SVG export failed ({type(e).__name__}), saving HTML instead...")
        chart.save(str(html_path))
        print(f"✅ Saved bump chart HTML: {html_path}")
    
    print(f"\n✅ Outputs saved to {output_dir}/")
    print("=" * 80)


if __name__ == '__main__':
    main()
