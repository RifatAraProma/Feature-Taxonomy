"""
Test script to verify datasets can be loaded properly
"""
from server.util import list_datasets, load_series

print("Testing dataset loading...")
print("=" * 60)

# List all datasets
datasets = list_datasets()
print(f"\nFound {len(datasets)} datasets:")
print("-" * 60)

# Group by category
categories = {}
for ds in datasets:
    cat = ds.get('category', 'unknown')
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(ds)

# Display by category
for cat, dss in sorted(categories.items()):
    print(f"\n{cat.upper()} ({len(dss)} datasets):")
    for ds in dss[:5]:  # Show first 5 per category
        print(f"  - {ds['id']}: {ds['n']} points")
    if len(dss) > 5:
        print(f"  ... and {len(dss) - 5} more")

# Test loading a few datasets
print("\n" + "=" * 60)
print("\nTesting data loading:")
print("-" * 60)

test_ids = ['series_001', 'stock_aapl_price', 'climate_atl_awnd']
for test_id in test_ids:
    try:
        series = load_series(test_id)
        y_data = series.get('y', [])
        print(f"\n✓ {test_id}: Loaded {len(y_data)} data points")
        if len(y_data) > 0:
            print(f"  First 5 values: {y_data[:5]}")
            print(f"  Data range: [{min(y_data):.2f}, {max(y_data):.2f}]")
    except Exception as e:
        print(f"\n✗ {test_id}: ERROR - {e}")

print("\n" + "=" * 60)
print("Test complete!")
