"""
Remove level 0 rows from all fc_scores_all.csv files
"""

import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, 'server')
from util import list_datasets


def main():
    datasets = list_datasets()
    print(f"Removing level 0 from {len(datasets)} datasets...")
    
    success_count = 0
    total_removed = 0
    
    for i, dataset_info in enumerate(datasets, 1):
        dataset_id = dataset_info['id'] if isinstance(dataset_info, dict) else dataset_info
        fc_file = Path('plots') / dataset_id / 'ranking' / 'fc_scores_all.csv'
        
        if not fc_file.exists():
            continue
        
        df = pd.read_csv(fc_file)
        original_count = len(df)
        
        # Remove level 0
        df = df[df['level'] != 0]
        removed = original_count - len(df)
        
        # Save
        df.to_csv(fc_file, index=False)
        
        print(f"[{i}/{len(datasets)}] {dataset_id}: Removed {removed} rows")
        success_count += 1
        total_removed += removed
    
    print(f"\n✅ Done! Processed {success_count} datasets, removed {total_removed} total rows")


if __name__ == '__main__':
    main()
