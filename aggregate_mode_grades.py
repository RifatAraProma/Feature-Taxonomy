"""
Aggregate mode grades across datasets and metrics.

Creates two CSV files:
1. By Metric: algorithm × metric with grade counts across 80 datasets
2. By Dataset: algorithm × dataset with grade counts across 23 metrics

Both include mode grade(s) with tie handling.
"""

import pandas as pd
from pathlib import Path
from collections import Counter


def list_datasets():
    """Get all dataset directories that have fc_score_datapoint_category_count.csv"""
    plots_dir = Path('plots')
    datasets = []
    for dataset_dir in plots_dir.iterdir():
        if dataset_dir.is_dir():
            count_file = dataset_dir / 'fc_score_datapoint_category_count.csv'
            if count_file.exists():
                datasets.append(dataset_dir.name)
    return sorted(datasets)


def load_all_grades():
    """Load grades from all dataset count files"""
    datasets = list_datasets()
    all_data = []
    
    print(f"\nLoading grades from {len(datasets)} datasets...")
    for dataset in datasets:
        count_file = Path('plots') / dataset / 'fc_score_datapoint_category_count.csv'
        df = pd.read_csv(count_file)
        df['dataset'] = dataset
        all_data.append(df)
    
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"✅ Loaded {len(combined_df)} rows (algorithm × metric × dataset)")
    return combined_df


def calculate_mode_grades(grade_counts):
    """Calculate mode grade(s), handling ties"""
    if len(grade_counts) == 0:
        return ''
    
    max_count = max(grade_counts.values())
    modes = [grade for grade, count in grade_counts.items() if count == max_count]
    return ', '.join(sorted(modes))


def aggregate_by_metric(grades_df):
    """Aggregate grades by algorithm and metric across all datasets"""
    print("\n" + "="*80)
    print("AGGREGATING BY METRIC (across 80 datasets)")
    print("="*80)
    
    results = []
    grouped = grades_df.groupby(['algorithm', 'metric'])
    
    for (algo, metric), group in grouped:
        grade_counts = Counter(group['grade'])
        mode = calculate_mode_grades(grade_counts)
        
        # Calculate deviation: % of datasets that did NOT achieve the mode frequency
        total = sum(grade_counts.values())
        # For ties, sum all tied grade frequencies
        mode_grades_list = mode.split(', ')
        mode_count_sum = sum(grade_counts.get(g, 0) for g in mode_grades_list)
        
        deviation = round(((total - mode_count_sum) / total) * 100, 2) if total > 0 else 0.0
        
        results.append({
            'algorithm': algo,
            'metric': metric,
            'A': grade_counts.get('A', 0),
            'B': grade_counts.get('B', 0),
            'C': grade_counts.get('C', 0),
            'D': grade_counts.get('D', 0),
            'F': grade_counts.get('F', 0),
            'mode': mode,
            'deviation': deviation
        })
    
    result_df = pd.DataFrame(results)
    
    # Sort by algorithm and metric
    result_df = result_df.sort_values(['algorithm', 'metric'])
    
    output_file = Path('plots/fc_visualizations/algorithm_metric_mode_grades.csv')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_file, index=False)
    
    print(f"✅ Created: {output_file}")
    print(f"   Rows: {len(result_df)} (19 algorithms × 23 metrics)")
    print(f"   Columns: algorithm, metric, A, B, C, D, F, mode, deviation")
    
    return result_df


def aggregate_by_dataset(grades_df):
    """Aggregate grades by algorithm and dataset across all metrics"""
    print("\n" + "="*80)
    print("AGGREGATING BY DATASET (across 23 metrics)")
    print("="*80)
    
    results = []
    grouped = grades_df.groupby(['algorithm', 'dataset'])
    
    for (algo, dataset), group in grouped:
        grade_counts = Counter(group['grade'])
        mode = calculate_mode_grades(grade_counts)
        
        results.append({
            'algorithm': algo,
            'dataset': dataset,
            'A': grade_counts.get('A', 0),
            'B': grade_counts.get('B', 0),
            'C': grade_counts.get('C', 0),
            'D': grade_counts.get('D', 0),
            'F': grade_counts.get('F', 0),
            'mode': mode
        })
    
    result_df = pd.DataFrame(results)
    
    # Sort by algorithm and dataset
    result_df = result_df.sort_values(['algorithm', 'dataset'])
    
    output_file = Path('plots/fc_visualizations/algorithm_dataset_mode_grades.csv')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_file, index=False)
    
    print(f"✅ Created: {output_file}")
    print(f"   Rows: {len(result_df)} (19 algorithms × 80 datasets)")
    print(f"   Columns: algorithm, dataset, A, B, C, D, F, mode")
    
    return result_df


def main():
    print("="*80)
    print("AGGREGATE MODE GRADES")
    print("="*80)
    print("\nCreating two CSVs:")
    print("  1. By Metric: Grade counts across 80 datasets")
    print("  2. By Dataset: Grade counts across 23 metrics")
    print("\nBoth include mode grade with tie handling (comma-separated)")
    
    # Load all grades
    grades_df = load_all_grades()
    
    # Create both aggregations
    metric_df = aggregate_by_metric(grades_df)
    dataset_df = aggregate_by_dataset(grades_df)
    
    print("\n" + "="*80)
    print("✅ COMPLETE!")
    print("="*80)
    print("\nOutput files:")
    print("  • plots/fc_visualizations/algorithm_metric_mode_grades.csv")
    print("  • plots/fc_visualizations/algorithm_dataset_mode_grades.csv")
    print("\nExample mode values:")
    print("  Single mode: 'A'")
    print("  Tie: 'A, B' or 'B, C'")
    print("="*80)


if __name__ == '__main__':
    main()
