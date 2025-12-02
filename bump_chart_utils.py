"""
Shared bump chart utilities for algorithm ranking visualizations.

This module provides a standardized bump chart creation function used across
all ranking scripts to ensure visual consistency.
"""

import pandas as pd
import altair as alt


def create_bump_chart(
    bump_df: pd.DataFrame,
    column_order: list[str],
    column_name: str = 'dataset',
    rank_column: str = 'rank',
    overall_rank_column: str = 'overall_rank',
    avg_rank_column: str = 'avg_rank',
    average_label: str = 'Average rank',
) -> alt.Chart:
    """
    Create a standardized bump chart showing algorithm rankings across columns.
    
    Args:
        bump_df: DataFrame with columns:
            - algorithm: Algorithm identifier
            - algorithm_name: Display name for algorithm
            - color: Color for algorithm line
            - {column_name}: Column identifier (e.g., 'dataset', 'dataset_type', 'feature')
            - {rank_column}: Rank value for positioning
            - {overall_rank_column}: Overall rank (1-based) for final column
            - {avg_rank_column}: Average rank for tooltip
        column_order: Ordered list of column names (e.g., datasets, features)
            Last item should be 'Average rank'
        column_name: Name of the column field in bump_df (default: 'dataset')
        rank_column: Name of the rank field for y-positioning (default: 'rank')
        overall_rank_column: Name of overall rank field (default: 'overall_rank')
        avg_rank_column: Name of average rank field for tooltip (default: 'avg_rank')
        average_label: Label for the average column (default: 'Average rank')
    
    Returns:
        Altair Chart object with layered bump chart visualization
    
    Required DataFrame columns:
        - algorithm (str): Algorithm identifier
        - algorithm_name (str): Display name
        - color (str): Hex color code
        - {column_name} (str): Column identifier
        - {rank_column} (numeric): Rank for y-position
        - {overall_rank_column} (int): Overall rank (1-N)
        - {avg_rank_column} (float): Average rank for tooltip
    """
    
    # Create numeric x position for columns
    bump_df = bump_df.copy()
    bump_df['x_pos'] = bump_df[column_name].map(
        {col: i for i, col in enumerate(column_order)}
    )
    
    # Calculate chart dimensions
    num_columns = len(column_order)
    max_rank = int(bump_df[rank_column].max())
    
    # Identify column types for styling
    last_regular_column = column_order[-2] if len(column_order) > 1 else None
    
    bump_df['is_average'] = bump_df[column_name] == average_label
    bump_df['is_last_regular'] = (
        bump_df[column_name] == last_regular_column if last_regular_column else False
    )
    bump_df['is_regular'] = (~bump_df['is_average']) & (~bump_df['is_last_regular'])
    
    # Color encoding
    alg_order = bump_df['algorithm'].drop_duplicates().tolist()
    color_lookup = (
        bump_df.drop_duplicates('algorithm')[['algorithm', 'color']]
        .set_index('algorithm')['color']
        .reindex(alg_order)
        .tolist()
    )
    
    color_encoding = alt.Color(
        'algorithm:N',
        scale=alt.Scale(domain=alg_order, range=color_lookup),
        legend=None,
    )
    
    # Shared encodings
    x_enc = alt.X(
        'x_pos:Q',
        scale=alt.Scale(domain=[-0.5, num_columns + 1.5]),
        axis=None,
    )
    y_enc = alt.Y(
        f'{rank_column}:Q',
        scale=alt.Scale(reverse=True, domain=[-0.5, max_rank + 0.5]),
        axis=None,
    )
    
    # Lines connecting all points (with tooltips)
    lines = (
        alt.Chart(bump_df)
        .mark_line(strokeWidth=3.5, opacity=0.8)
        .encode(
            x=x_enc,
            y=y_enc,
            color=color_encoding,
            detail='algorithm:N',
            tooltip=[
                alt.Tooltip('algorithm_name:N', title='Algorithm'),
                alt.Tooltip(f'{column_name}:N', title=column_name.replace('_', ' ').title()),
                alt.Tooltip(f'{overall_rank_column}:Q', title='Rank'),
                alt.Tooltip(f'{avg_rank_column}:Q', title='Avg Rank', format='.2f'),
            ],
        )
    )
    
    # Regular column points (size 120)
    points_regular = (
        alt.Chart(bump_df[bump_df['is_regular']])
        .mark_point(size=120, filled=True)
        .encode(x=x_enc, y=y_enc, color=color_encoding, detail='algorithm:N')
    )
    
    # Last regular column points (size 160)
    points_last_regular = (
        alt.Chart(bump_df[bump_df['is_last_regular']])
        .mark_point(size=160, filled=True)
        .encode(x=x_enc, y=y_enc, color=color_encoding, detail='algorithm:N')
    )
    
    # Average rank column points (size 200, bold)
    points_average = (
        alt.Chart(bump_df[bump_df['is_average']])
        .mark_point(size=200, filled=True, strokeWidth=2)
        .encode(x=x_enc, y=y_enc, color=color_encoding, detail='algorithm:N')
    )
    
    # ========== RIGHT SIDE LABELS (Average rank column) ==========
    last_column = column_order[-1]
    labels_df = bump_df[bump_df[column_name] == last_column].copy()
    
    # Position labels to the right of the last column points
    labels_df['x_label'] = labels_df['x_pos'] + 0.45
    labels_df['x_rank'] = labels_df['x_pos'] + 0.15
    
    # Algorithm names
    labels = (
        alt.Chart(labels_df)
        .mark_text(align='left', baseline='middle', fontSize=16, fontWeight=500)
        .encode(
            x=alt.X('x_label:Q', scale=alt.Scale(domain=[-0.5, num_columns + 1.5]), axis=None),
            y=y_enc,
            text=alt.Text('algorithm_name:N'),
            color=alt.value('black'),
        )
    )
    
    # Rank numbers (bold)
    rank_numbers = (
        alt.Chart(labels_df)
        .mark_text(align='left', baseline='middle', fontSize=16, fontWeight='bold')
        .encode(
            x=alt.X('x_rank:Q', scale=alt.Scale(domain=[-0.5, num_columns + 1.5]), axis=None),
            y=y_enc,
            text=alt.Text(f'{overall_rank_column}:Q', format='d'),
            color=alt.value('#000'),
        )
    )
    
    # ========== TOP LABELS (Column names) ==========
    column_labels_df = pd.DataFrame({
        column_name: column_order,
        'x_pos': list(range(len(column_order))),
        'y_pos': [-0.3] * len(column_order),
    })
    
    # Regular column labels (315 degrees, left aligned, at x_pos)
    regular_labels = (
        alt.Chart(column_labels_df[column_labels_df[column_name] != average_label])
        .mark_text(
            align='left',
            baseline='bottom',
            fontSize=16,
            angle=315,
            dx=0,  # No offset - align with x_pos
            dy=0,
        )
        .encode(
            x=alt.X('x_pos:Q'),
            y=alt.Y('y_pos:Q'),
            text=alt.Text(f'{column_name}:N'),
            color=alt.value('#666'),
        )
    )
    
    # 'Average rank' label (315 degrees, left aligned, bold, at x_pos)
    average_column_label = (
        alt.Chart(column_labels_df[column_labels_df[column_name] == average_label])
        .mark_text(
            align='left',
            baseline='bottom',
            fontSize=16,
            fontWeight='bold',
            angle=315,
            dx=0,  # No offset - align with x_pos
            dy=0,
        )
        .encode(
            x=alt.X('x_pos:Q'),
            y=alt.Y('y_pos:Q'),
            text=alt.Text(f'{column_name}:N'),
            color=alt.value('#000'),
        )
    )
    
    # Combine all layers
    chart = (
        lines
        + points_regular
        + points_last_regular
        + points_average
        + labels
        + rank_numbers
        + regular_labels
        + average_column_label
    ).properties(
        width=120 * num_columns,
        height=450,
    ).configure_view(
        strokeWidth=0
    )
    
    return chart
