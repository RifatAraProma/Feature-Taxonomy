"""
Analyze algorithm consistency across datasets
Calculate variance of grades for each Algorithm × Metric combination
"""

import pandas as pd
import numpy as np
from pathlib import Path

def load_metric_grades():
    """Load per-metric grades"""
    print("📊 Loading metric-specific grades...")
    df = pd.read_csv('plots/fc_visualizations/dataset_algorithm_metric_grades.csv')
    print(f"   Loaded {len(df)} grade records")
    return df


def calculate_variance_analysis(df):
    """
    For each Algorithm × Metric combination:
    - Calculate variance of grades across 80 datasets
    - Calculate mean grade
    - Classify consistency
    """
    print("\n📊 Calculating variance for each Algorithm × Metric combination...")
    
    # Convert grades to numeric
    grade_map = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}
    df['grade_value'] = df['grade'].map(grade_map)
    
    # Group by algorithm and metric, calculate variance across datasets
    variance_stats = df.groupby(['algorithm', 'metric'])['grade_value'].agg([
        ('variance', 'var'),
        ('std', 'std'),
        ('count', 'count')
    ]).reset_index()
    
    # Classify data dependency based on variance only
    # Low variance: < 0.5 (consistent across datasets)
    # High variance: > 1.5 (data-dependent)
    def classify_consistency(row):
        var = row['variance']
        
        if var < 0.5:
            return 'Consistent'
        elif var < 1.5:
            return 'Moderately Data-Dependent'
        else:
            return 'Highly Data-Dependent'
    
    # Apply classification
    variance_stats['data_dependency'] = variance_stats.apply(classify_consistency, axis=1)
    
    print(f"   ✅ Calculated variance for {len(variance_stats)} Algorithm × Metric combinations")
    
    return variance_stats


def create_summary_tables(variance_stats, output_dir='plots/fc_visualizations'):
    """
    Create variance table: algorithms × metrics
    """
    print("\n📊 Creating variance table...")
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Pivot to create algorithm × metric table with variance values
    variance_table = variance_stats.pivot(index='algorithm', columns='metric', values='variance')
    
    # Save
    variance_csv = output_path / 'algorithm_metric_variance_table.csv'
    variance_table.to_csv(variance_csv)
    print(f"   ✅ Saved: {variance_csv.name}")
    print(f"   Table shape: {variance_table.shape[0]} algorithms × {variance_table.shape[1]} metrics")
    
    return variance_table


def print_insights(variance_stats, variance_table):
    """Print key insights"""
    
    print("\n" + "=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    
    # Overall statistics
    print(f"\n📊 Variance Statistics:")
    print(f"   Min variance: {variance_stats['variance'].min():.3f}")
    print(f"   Max variance: {variance_stats['variance'].max():.3f}")
    print(f"   Mean variance: {variance_stats['variance'].mean():.3f}")
    print(f"   Median variance: {variance_stats['variance'].median():.3f}")
    
    # Data dependency distribution
    print("\n📋 Data Dependency Distribution:")
    dependency_counts = variance_stats['data_dependency'].value_counts()
    for dependency, count in dependency_counts.items():
        pct = count / len(variance_stats) * 100
        print(f"   {dependency}: {count} ({pct:.1f}%)")
    
    # Most consistent algorithm-metric pairs
    print("\n⭐ Top 10 Most Consistent Algorithm-Metric Pairs (Lowest Variance):")
    for i, (_, row) in enumerate(variance_stats.nsmallest(10, 'variance').iterrows(), 1):
        print(f"   {i}. {row['algorithm']} on {row['metric']}: variance={row['variance']:.3f}")
    
    # Most data-dependent pairs
    print("\n📊 Top 10 Most Data-Dependent Algorithm-Metric Pairs (Highest Variance):")
    for i, (_, row) in enumerate(variance_stats.nlargest(10, 'variance').iterrows(), 1):
        print(f"   {i}. {row['algorithm']} on {row['metric']}: variance={row['variance']:.3f}")


def main():
    print("=" * 80)
    print("ALGORITHM CONSISTENCY ANALYSIS")
    print("=" * 80)
    
    # Load data
    df = load_metric_grades()
    
    # Calculate variance
    variance_stats = calculate_variance_analysis(df)
    
    # Create variance table
    variance_table = create_summary_tables(variance_stats)
    
    # Print insights
    print_insights(variance_stats, variance_table)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print("\nFile created in plots/fc_visualizations:")
    print("  algorithm_metric_variance_table.csv - 19 algorithms × 23 metrics variance table")
    print("=" * 80)


if __name__ == '__main__':
    main()
