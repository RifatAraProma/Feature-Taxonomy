"""
Test script to verify algorithms work with the new datasets
"""
from server.algorithms import transformers, reducers, aggregators
from server.util import load_series
import numpy as np

print("Testing algorithms with real datasets...")
print("=" * 60)

# Load a test dataset
series = load_series('stock_aapl_price')
y = series['y'][:100]  # Use first 100 points for quick testing
print(f"\nLoaded dataset: stock_aapl_price")
print(f"Using {len(y)} data points")
print(f"Data range: [{min(y):.2f}, {max(y):.2f}]")

print("\n" + "=" * 60)
print("\nTesting TRANSFORMERS:")
print("-" * 60)

# Test transformers
transformer_tests = [
    ("gaussian_filter", {"sigma": 3.0}),
    ("median_filter", {"window_size": 5}),
    ("mean_filter", {"window_size": 7}),
]

for method, params in transformer_tests:
    try:
        result = transformers.apply(method, y, **params)
        print(f"✓ {method}: {len(y)} → {len(result)} points")
        print(f"  Range: [{min(result):.2f}, {max(result):.2f}]")
    except Exception as e:
        print(f"✗ {method}: ERROR - {e}")

print("\n" + "=" * 60)
print("\nTesting REDUCERS:")
print("-" * 60)

# Test reducers
reducer_tests = [
    ("lttb_downsample", {"output_length": 30}),
    ("m4_downsample", {"output_length": 32}),
    ("rdp_downsample", {"output_length": 25}),
]

for method, params in reducer_tests:
    try:
        result = reducers.apply(method, y, **params)
        print(f"✓ {method}: {len(y)} → {len(result)} points")
        print(f"  Range: [{min(result):.2f}, {max(result):.2f}]")
    except Exception as e:
        print(f"✗ {method}: ERROR - {e}")

print("\n" + "=" * 60)
print("\nTesting AGGREGATORS:")
print("-" * 60)

# Test aggregators
aggregator_tests = [
    ("bin_average_aggregator", {"bins": 20}),
    ("asap_aggregator", {"max_window": 5}),
]

for method, params in aggregator_tests:
    try:
        result = aggregators.apply(method, y, **params)
        print(f"✓ {method}: {len(y)} → {len(result)} points")
        print(f"  Range: [{min(result):.2f}, {max(result):.2f}]")
    except Exception as e:
        print(f"✗ {method}: ERROR - {e}")

print("\n" + "=" * 60)
print("Algorithm testing complete!")
