"""
Export FC Score Datapoint Category Counts
Simple script: read fc_scores_all.csv, calculate quartiles, count buckets
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, 'server')
from util import list_datasets


def process_dataset(dataset_id):
    """Read fc_scores_all.csv, determine quartiles, count buckets"""
    fc_file = Path('plots') / dataset_id / 'ranking' / 'fc_scores_all.csv'
    
    if not fc_file.exists():
        print(f"   ⚠️  Skipping {dataset_id}: fc_scores_all.csv not found")
        return False
    
    # Load data
    df = pd.read_csv(fc_file)
    
    # Process each metric separately
    results = []
    
    for metric in df['metric'].unique():
        metric_df = df[df['metric'] == metric].copy()
        
        # Drop NaN values before calculating quartiles
        metric_df = metric_df.dropna(subset=['fc_score'])
        
        if len(metric_df) == 0:
            continue
        
        # Calculate quartiles
        p25 = np.percentile(metric_df['fc_score'], 25)
        p50 = np.percentile(metric_df['fc_score'], 50)
        p75 = np.percentile(metric_df['fc_score'], 75)
        
        # Categorize
        def categorize(score):
            if score > p75:
                return 'excellent'
            elif score > p50:
                return 'good'
            elif score > p25:
                return 'fair'
            else:
                return 'poor'
        
        metric_df['category'] = metric_df['fc_score'].apply(categorize)
        
        # Count per algorithm
        for algo in metric_df['algorithm'].unique():
            algo_df = metric_df[metric_df['algorithm'] == algo]
            counts = algo_df['category'].value_counts()
            
            excellent_count = counts.get('excellent', 0)
            good_count = counts.get('good', 0)
            fair_count = counts.get('fair', 0)
            poor_count = counts.get('poor', 0)
            
            # Calculate GPA-style score
            total = excellent_count + good_count + fair_count + poor_count
            if total > 0:
                score = (excellent_count * 4 + good_count * 3 + fair_count * 2 + poor_count * 1) / total
            else:
                score = 0
            
            # Assign letter grade
            if score >= 3.4:
                grade = 'A'
            elif score >= 2.8:
                grade = 'B'
            elif score >= 2.2:
                grade = 'C'
            elif score >= 1.6:
                grade = 'D'
            else:
                grade = 'F'
            
            results.append({
                'algorithm': algo,
                'metric': metric,
                'excellent': excellent_count,
                'good': good_count,
                'fair': fair_count,
                'poor': poor_count,
                'score': round(score, 2),
                'grade': grade
            })
    
    # Save
    output_df = pd.DataFrame(results)
    output_file = Path('plots') / dataset_id / 'fc_score_datapoint_category_count.csv'
    output_df.to_csv(output_file, index=False)
    
    return True


def main():
    datasets = list_datasets()
    print(f"Processing {len(datasets)} datasets...")
    
    success_count = 0
    for i, dataset_info in enumerate(datasets, 1):
        dataset_id = dataset_info['id'] if isinstance(dataset_info, dict) else dataset_info
        print(f"[{i}/{len(datasets)}] {dataset_id}...", end=" ")
        
        if process_dataset(dataset_id):
            print("✅")
            success_count += 1
    
    print(f"\n✅ Done! Processed {success_count}/{len(datasets)} datasets")


if __name__ == '__main__':
    main()
