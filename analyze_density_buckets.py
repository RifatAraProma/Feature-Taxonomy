"""Analyze dataset lengths and categorize into density buckets."""

import json
from pathlib import Path
import pandas as pd

# Collect all dataset lengths
datasets = {}
for data_dir in Path('data').iterdir():
    if data_dir.is_dir():
        for json_file in data_dir.glob('*.json'):
            data = json.load(open(json_file))
            # Handle both dict format {'id': ..., 'y': [...]} and list format
            if isinstance(data, dict):
                datasets[json_file.stem] = len(data['y'])
            elif isinstance(data, list):
                datasets[json_file.stem] = len(data)

# Create dataframe and sort by length
df = pd.DataFrame(list(datasets.items()), columns=['dataset', 'length']).sort_values('length')

print("=" * 80)
print("ALL DATASETS BY LENGTH")
print("=" * 80)
print(df.to_string(index=False))

# Statistics
min_len = df['length'].min()
max_len = df['length'].max()
mean_len = df['length'].mean()
median_len = df['length'].median()

print(f"\n{'=' * 80}")
print("STATISTICS")
print("=" * 80)
print(f"Total datasets: {len(df)}")
print(f"Min length:     {min_len:,}")
print(f"Max length:     {max_len:,}")
print(f"Mean length:    {mean_len:,.1f}")
print(f"Median length:  {median_len:,.1f}")

# Propose three buckets using tertiles (33rd and 67th percentiles)
p33 = df['length'].quantile(0.33)
p67 = df['length'].quantile(0.67)

print(f"\n{'=' * 80}")
print("PROPOSED BUCKETS (Using Tertiles)")
print("=" * 80)
print(f"LOW density:    length < {p33:,.0f}  (bottom 33%)")
print(f"MEDIUM density: {p33:,.0f} <= length < {p67:,.0f}")
print(f"HIGH density:   length >= {p67:,.0f}  (top 33%)")

# Categorize datasets
df['density_bucket'] = pd.cut(
    df['length'],
    bins=[0, p33, p67, float('inf')],
    labels=['low', 'medium', 'high']
)

print(f"\n{'=' * 80}")
print("BUCKET ASSIGNMENTS")
print("=" * 80)

for bucket in ['low', 'medium', 'high']:
    bucket_df = df[df['density_bucket'] == bucket]
    print(f"\n{bucket.upper()} DENSITY ({len(bucket_df)} datasets):")
    print(f"  Length range: {bucket_df['length'].min():,} - {bucket_df['length'].max():,}")
    print(f"  Datasets:")
    for _, row in bucket_df.iterrows():
        print(f"    - {row['dataset']:40} ({row['length']:6,} points)")

# Alternative: Round number buckets
print(f"\n\n{'=' * 80}")
print("ALTERNATIVE: ROUND NUMBER BUCKETS")
print("=" * 80)
print("LOW density:    length < 1,000")
print("MEDIUM density: 1,000 <= length < 5,000")
print("HIGH density:   length >= 5,000")

df['density_bucket_alt'] = pd.cut(
    df['length'],
    bins=[0, 1000, 5000, float('inf')],
    labels=['low', 'medium', 'high']
)

print(f"\nBucket counts:")
print(df['density_bucket_alt'].value_counts().sort_index())

for bucket in ['low', 'medium', 'high']:
    bucket_df = df[df['density_bucket_alt'] == bucket]
    if len(bucket_df) > 0:
        print(f"\n{bucket.upper()} DENSITY ({len(bucket_df)} datasets):")
        print(f"  Length range: {bucket_df['length'].min():,} - {bucket_df['length'].max():,}")
        print(f"  Datasets:")
        for _, row in bucket_df.iterrows():
            print(f"    - {row['dataset']:40} ({row['length']:6,} points)")
