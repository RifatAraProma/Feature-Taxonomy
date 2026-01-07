"""
Summarize FC Score distributions across datasets, algorithms, and features.

This script analyzes the FC scores from all datasets and generates a CSV report
showing the percentage distribution of excellent/good/fair/poor ratings for each
dataset across algorithms and features.

Rating categories based on FC score quartiles:
- Excellent: FC score > 75th percentile
- Good: 50th percentile < FC score <= 75th percentile  
- Fair: 25th percentile < FC score <= 50th percentile
- Poor: FC score <= 25th percentile
"""

import pandas as pd
from pathlib import Path
import json
from server.util import list_datasets


def get_rating_category(fc_score, q25, q50, q75):
    """
    Categorize FC score into excellent/good/fair/poor based on quartiles.
    
    Args:
        fc_score: The FC score value
        q25: 25th percentile threshold
        q50: 50th percentile (median) threshold
        q75: 75th percentile threshold
    
    Returns:
        str: 'excellent', 'good', 'fair', or 'poor'
    """
    if fc_score > q75:
        return 'excellent'
    elif fc_score > q50:
        return 'good'
    elif fc_score > q25:
        return 'fair'
    else:
        return 'poor'


def analyze_dataset_fc_scores(dataset_id):
    """
    Analyze FC scores for a single dataset and return rating distributions.
    
    Args:
        dataset_id: Dataset identifier (e.g., 'stock_aapl_price')
    
    Returns:
        dict: Dictionary containing percentage distributions by algorithm and feature
    """
    base_path = Path('plots') / dataset_id / 'ranking'
    
    # Load per-metric quartiles (new format with columns: metric, q25, q50, q75)
    quartiles_file = base_path / 'fc_scores_quartiles.csv'
    if not quartiles_file.exists():
        print(f"  ⚠️  Missing quartiles: {dataset_id}")
        return None
    
    quartiles_df = pd.read_csv(quartiles_file)
    # Create lookup dictionary: {metric: {q25, q50, q75}}
    quartiles_dict = quartiles_df.set_index('metric')[['q25', 'q50', 'q75']].to_dict('index')
    
    # Load FC scores
    fc_scores_file = base_path / 'fc_scores_all.csv'
    if not fc_scores_file.exists():
        print(f"  ⚠️  Missing FC scores: {dataset_id}")
        return None
    
    fc_df = pd.read_csv(fc_scores_file)
    
    # Add rating category using metric-specific quartiles
    def get_rating_for_row(row):
        metric = row['metric']
        fc_score = row['fc_score']
        if metric not in quartiles_dict:
            return 'unknown'
        q = quartiles_dict[metric]
        return get_rating_category(fc_score, q['q25'], q['q50'], q['q75'])
    
    fc_df['rating'] = fc_df.apply(get_rating_for_row, axis=1)
    
    # Calculate overall distribution
    total_count = len(fc_df)
    overall_dist = fc_df['rating'].value_counts() / total_count * 100
    
    # Calculate distribution by algorithm
    algo_dist = fc_df.groupby('algorithm')['rating'].value_counts(normalize=True) * 100
    
    # Calculate distribution by feature (metric)
    feature_dist = fc_df.groupby('metric')['rating'].value_counts(normalize=True) * 100
    
    # Calculate average quartiles across all metrics (for summary purposes)
    avg_q25 = quartiles_df['q25'].mean()
    avg_q50 = quartiles_df['q50'].mean()
    avg_q75 = quartiles_df['q75'].mean()
    
    return {
        'dataset_id': dataset_id,
        'q25': avg_q25,
        'q50': avg_q50,
        'q75': avg_q75,
        'total_data_points': total_count,
        'overall_distribution': overall_dist.to_dict(),
        'algorithm_distribution': algo_dist,
        'feature_distribution': feature_dist,
    }


def generate_summary_csv(output_dir='plots'):
    """
    Generate comprehensive CSV summaries of FC score distributions.
    
    Creates three CSV files:
    1. dataset_fc_summary.csv - Overall distribution per dataset
    2. dataset_algorithm_fc_summary.csv - Distribution per dataset-algorithm
    3. dataset_feature_fc_summary.csv - Distribution per dataset-feature
    """
    print("=" * 80)
    print("FC SCORE DISTRIBUTION SUMMARY")
    print("=" * 80)
    
    # Discover all datasets
    datasets = list_datasets()
    print(f"📊 Found {len(datasets)} datasets\n")
    
    # Collect data
    dataset_summaries = []
    algorithm_summaries = []
    feature_summaries = []
    
    for i, dataset in enumerate(datasets, 1):
        dataset_id = dataset['id']
        print(f"[{i}/{len(datasets)}] Processing: {dataset_id}")
        
        result = analyze_dataset_fc_scores(dataset_id)
        if result is None:
            continue
        
        # Overall dataset summary
        overall = result['overall_distribution']
        dataset_summaries.append({
            'dataset': dataset_id,
            'q25': result['q25'],
            'q50': result['q50'],
            'q75': result['q75'],
            'total_data_points': result['total_data_points'],
            'excellent_pct': overall.get('excellent', 0),
            'good_pct': overall.get('good', 0),
            'fair_pct': overall.get('fair', 0),
            'poor_pct': overall.get('poor', 0),
        })
        
        # Algorithm-level summaries
        for (algorithm, rating), pct in result['algorithm_distribution'].items():
            algorithm_summaries.append({
                'dataset': dataset_id,
                'algorithm': algorithm,
                'rating': rating,
                'percentage': pct,
            })
        
        # Feature-level summaries
        for (feature, rating), pct in result['feature_distribution'].items():
            feature_summaries.append({
                'dataset': dataset_id,
                'feature': feature,
                'rating': rating,
                'percentage': pct,
            })
    
    print(f"\n✅ Processed {len(dataset_summaries)} datasets")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Save dataset-level summary
    dataset_df = pd.DataFrame(dataset_summaries)
    dataset_output = output_path / 'dataset_fc_summary.csv'
    dataset_df.to_csv(dataset_output, index=False, float_format='%.2f')
    print(f"📄 Dataset summary: {dataset_output}")
    print(f"   Columns: {', '.join(dataset_df.columns)}")
    print(f"   Rows: {len(dataset_df)}")
    
    # Save algorithm-level summary (pivot format)
    algorithm_df = pd.DataFrame(algorithm_summaries)
    algorithm_pivot = algorithm_df.pivot_table(
        index=['dataset', 'algorithm'],
        columns='rating',
        values='percentage',
        fill_value=0
    ).reset_index()
    
    # Ensure all rating columns exist
    for rating in ['excellent', 'good', 'fair', 'poor']:
        if rating not in algorithm_pivot.columns:
            algorithm_pivot[rating] = 0
    
    algorithm_pivot = algorithm_pivot[['dataset', 'algorithm', 'excellent', 'good', 'fair', 'poor']]
    algorithm_output = output_path / 'dataset_algorithm_fc_summary.csv'
    algorithm_pivot.to_csv(algorithm_output, index=False, float_format='%.2f')
    print(f"📄 Algorithm summary: {algorithm_output}")
    print(f"   Columns: {', '.join(algorithm_pivot.columns)}")
    print(f"   Rows: {len(algorithm_pivot)}")
    
    # Save feature-level summary (pivot format)
    feature_df = pd.DataFrame(feature_summaries)
    feature_pivot = feature_df.pivot_table(
        index=['dataset', 'feature'],
        columns='rating',
        values='percentage',
        fill_value=0
    ).reset_index()
    
    # Ensure all rating columns exist
    for rating in ['excellent', 'good', 'fair', 'poor']:
        if rating not in feature_pivot.columns:
            feature_pivot[rating] = 0
    
    feature_pivot = feature_pivot[['dataset', 'feature', 'excellent', 'good', 'fair', 'poor']]
    feature_output = output_path / 'dataset_feature_fc_summary.csv'
    feature_pivot.to_csv(feature_output, index=False, float_format='%.2f')
    print(f"📄 Feature summary: {feature_output}")
    print(f"   Columns: {', '.join(feature_pivot.columns)}")
    print(f"   Rows: {len(feature_pivot)}")
    
    # Print sample statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    
    print("\n📊 Overall Distribution Across All Datasets:")
    avg_dist = dataset_df[['excellent_pct', 'good_pct', 'fair_pct', 'poor_pct']].mean()
    print(f"   Excellent: {avg_dist['excellent_pct']:.1f}%")
    print(f"   Good:      {avg_dist['good_pct']:.1f}%")
    print(f"   Fair:      {avg_dist['fair_pct']:.1f}%")
    print(f"   Poor:      {avg_dist['poor_pct']:.1f}%")
    
    print("\n📊 Quartile Ranges Across Datasets:")
    print(f"   Q25 range: [{dataset_df['q25'].min():.3f}, {dataset_df['q25'].max():.3f}]")
    print(f"   Q50 range: [{dataset_df['q50'].min():.3f}, {dataset_df['q50'].max():.3f}]")
    print(f"   Q75 range: [{dataset_df['q75'].min():.3f}, {dataset_df['q75'].max():.3f}]")
    
    # Find best/worst datasets
    print("\n📊 Top 5 Datasets by Excellent %:")
    top5 = dataset_df.nlargest(5, 'excellent_pct')[['dataset', 'excellent_pct']]
    for _, row in top5.iterrows():
        print(f"   {row['dataset']:30s} {row['excellent_pct']:6.2f}%")
    
    print("\n📊 Bottom 5 Datasets by Excellent %:")
    bottom5 = dataset_df.nsmallest(5, 'excellent_pct')[['dataset', 'excellent_pct']]
    for _, row in bottom5.iterrows():
        print(f"   {row['dataset']:30s} {row['excellent_pct']:6.2f}%")
    
    print("\n✅ All summary files saved to:", output_path.absolute())
    print("=" * 80)


if __name__ == '__main__':
    generate_summary_csv()
