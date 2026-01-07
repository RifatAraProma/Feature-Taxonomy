import pandas as pd
import glob

results = []
feature_files = glob.glob('plots/feature_rankings/*_bump_ranks.csv')

for f in feature_files:
    df = pd.read_csv(f)
    feature = f.split('\\')[-1].replace('_bump_ranks.csv', '')
    
    avg_df = df[df['dataset_type'] == 'Average rank']
    
    if 'category' not in avg_df.columns or len(avg_df) == 0:
        continue
    
    transformers = avg_df[avg_df['category'] == 'transformer']['rank_mean'].mean()
    reducers = avg_df[avg_df['category'] == 'reducer']['rank_mean'].mean()
    
    if pd.notna(transformers) and pd.notna(reducers) and reducers < transformers:
        results.append({
            'feature': feature,
            'reducer_avg': round(reducers, 2),
            'transformer_avg': round(transformers, 2),
            'difference': round(transformers - reducers, 2)
        })

results_df = pd.DataFrame(results).sort_values('difference', ascending=False)

print('\n' + '='*80)
print('FEATURES WHERE REDUCERS OUTPERFORM TRANSFORMERS')
print('='*80)
print('\nNote: Lower rank = better performance')
print(f'\nFound {len(results_df)} features where reducers perform better:\n')
print(results_df.to_string(index=False))
print('\n' + '='*80)
