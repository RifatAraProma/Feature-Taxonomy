# ASAP Algorithm Analysis & Fix

## Problem
ASAP aggregator showed no variation across slider levels (all outputs were identical).

## Root Cause Analysis

### How ASAP Works
1. **Autocorrelation Function (ACF)**: Detects periodicities in the data
2. **Optimal Window Selection**: Finds window size that:
   - Preserves shape characteristics (kurtosis)
   - Minimizes roughness
3. **Simple Moving Average**: Applies SMA with chosen window

### Key Insight
ASAP has TWO parameters:
- `max_window`: **Constrains the search space** for optimal window
- `resolution`: **Controls output length** via pre-aggregation

The problem: We were using `max_window`, which doesn't control output!

## Test Results (Apple Stock, 1257 points)

### Testing max_window Parameter
```
max_window=  2 -> chosen_window=  1, output_length=1257
max_window=  5 -> chosen_window=  1, output_length=1257
max_window= 10 -> chosen_window=  1, output_length=1257
max_window= 20 -> chosen_window=  1, output_length=1257
max_window=100 -> chosen_window=  1, output_length=1257
```
❌ **No variation!** ASAP always picks `window=1` as optimal for this dataset.

### Testing resolution Parameter
```
resolution=1257 -> slide_size=  1, output_length=1257 (original)
resolution= 500 -> slide_size=  2, output_length= 628
resolution= 100 -> slide_size= 12, output_length= 104
resolution=  50 -> slide_size= 25, output_length=  50
resolution=  10 -> slide_size=125, output_length=  10
```
✅ **Dramatic variation!** This is what we need.

## Solution Implemented

### 1. Updated `precompute_100_levels.py`
```python
'asap_aggregator': {
    'param_name': 'resolution',
    'param_bounds': (10, None),  # Dynamic: (10, data_length)
    'param_type': 'int',
    'param_direction': 'direct',  # Higher resolution = less aggregation
    'algorithm_type': 'aggregator',
    'use_logscale': True,  # Exponential spacing
}
```

### 2. Updated `data_aggregator_algorithms.py`
Changed function signature from:
```python
def asap_aggregator(data: list[tuple], max_window: int) -> list[tuple]:
```
To:
```python
def asap_aggregator(data: list[tuple], resolution: int) -> list[tuple]:
```

### 3. Parameter Sampling Strategy
- **Level 0**: `resolution = data_length` (minimal aggregation, ~1257 points)
- **Level 100**: `resolution = 10` (heavy aggregation, ~10 points)
- **Scaling**: Exponential (log scale) for smooth progression

## How Resolution Works

When `resolution` is provided and `len(data) >= 2 * resolution`:
1. Calculate `slide_size = max(1, len(data) // resolution)`
2. Pre-aggregate data: `data_agg = SMA(data, slide_size, slide_size)`
3. Then run ASAP window selection on aggregated data
4. Final output length ≈ `resolution`

Example for 1257 points:
- `resolution=100` → `slide_size=12` → 104 aggregated points
- `resolution=50` → `slide_size=25` → 50 aggregated points
- `resolution=10` → `slide_size=125` → 10 aggregated points

## Expected Behavior After Fix

Slider interaction should now show:
- **Level 0**: Nearly original data (~1257 points)
- **Level 25**: Moderate aggregation (~300-500 points)
- **Level 50**: Significant aggregation (~100-200 points)
- **Level 75**: Heavy aggregation (~25-50 points)
- **Level 100**: Maximum aggregation (~10 points)

## Visualization
See `plots/asap_analysis.png` for detailed comparison showing:
- Top row: max_window has no effect
- Middle row: resolution parameter creates dramatic variation
- Bottom left: Chosen window vs max_window (flat line = no variation)
- Bottom middle: Output length vs resolution (steep curve = good variation)

## Next Steps
Run `python precompute_100_levels.py` to regenerate ASAP outputs with the resolution parameter.
