"""
Verify deviation calculation from algorithm_metric_mode_grades.csv
Adds deviation column to the CSV for verification
"""

import pandas as pd
from pathlib import Path

def calculate_deviation(row):
    """Calculate deviation percentage from mode grades"""
    
    # Get counts for each grade
    counts = {
        'A': int(row['A']),
        'B': int(row['B']),
        'C': int(row['C']),
        'D': int(row['D']),
        'F': int(row['F'])
    }
    
    total = sum(counts.values())
    
    # Handle ties - mode column may contain comma-separated values
    mode_str = str(row['mode'])
    if ',' in mode_str:
        # Tie - count both grades as mode
        mode_grades = [g.strip() for g in mode_str.split(',')]
        mode_count = sum(counts.get(g, 0) for g in mode_grades)
    else:
        # Single mode
        mode_count = counts.get(mode_str.strip(), 0)
    
    # Calculate deviation: percentage that did NOT get the mode grade
    deviation_pct = ((total - mode_count) / total) * 100 if total > 0 else 0
    
    return deviation_pct, total, mode_count

def main():
    # Load data
    input_file = Path('plots/fc_visualizations/algorithm_metric_mode_grades.csv')
    df = pd.read_csv(input_file)
    
    print(f"Loaded {len(df)} rows from {input_file}")
    
    # Calculate deviation for each row
    deviations = []
    totals = []
    mode_counts = []
    
    for _, row in df.iterrows():
        dev, total, mode_count = calculate_deviation(row)
        deviations.append(dev)
        totals.append(total)
        mode_counts.append(mode_count)
    
    # Add columns
    df['total_datasets'] = totals
    df['mode_count'] = mode_counts
    df['deviation_pct'] = deviations
    
    # Save with deviation column
    output_file = Path('plots/fc_visualizations/algorithm_metric_mode_grades_with_deviation.csv')
    df.to_csv(output_file, index=False)
    
    print(f"\n✅ Saved: {output_file}")
    
    # Show specific example: ASAP + curvature_l1
    print("\n" + "="*80)
    print("EXAMPLE: ASAP + curvature_l1")
    print("="*80)
    
    example = df[(df['algorithm'] == 'asap_aggregator') & (df['metric'] == 'curvature_l1')]
    if not example.empty:
        row = example.iloc[0]
        print(f"Algorithm: {row['algorithm']}")
        print(f"Metric: {row['metric']}")
        print(f"A: {row['A']}, B: {row['B']}, C: {row['C']}, D: {row['D']}, F: {row['F']}")
        print(f"Mode: {row['mode']}")
        print(f"Total datasets: {row['total_datasets']}")
        print(f"Mode count: {row['mode_count']}")
        print(f"Deviation: {row['deviation_pct']:.2f}%")
        print(f"\nManual calculation: ({row['total_datasets']} - {row['mode_count']}) / {row['total_datasets']} * 100 = {((row['total_datasets'] - row['mode_count']) / row['total_datasets'] * 100):.2f}%")
    
    # Show statistics
    print("\n" + "="*80)
    print("DEVIATION STATISTICS")
    print("="*80)
    print(f"Min: {df['deviation_pct'].min():.2f}%")
    print(f"Max: {df['deviation_pct'].max():.2f}%")
    print(f"Mean: {df['deviation_pct'].mean():.2f}%")
    print(f"Median: {df['deviation_pct'].median():.2f}%")
    
    # Show first 10 rows
    print("\n" + "="*80)
    print("FIRST 10 ROWS WITH DEVIATION")
    print("="*80)
    print(df[['algorithm', 'metric', 'A', 'B', 'C', 'D', 'F', 'mode', 'total_datasets', 'mode_count', 'deviation_pct']].head(10).to_string(index=False))

if __name__ == '__main__':
    main()
