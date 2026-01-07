# Precompute All Unified - Usage Guide

## Overview

`precompute_all_unified.py` is a unified script that combines output generation AND feature preservation computation in a single pass. It now uses **EXACT SAME LOGIC** as `precompute_feature_preservation.py` for feature computation.

## Key Changes Made

### ✅ 1. Exact Feature Computation Logic
- **SAME** `extract_y_values()` function for handling transformer/reducer outputs
- **SAME** `split_features_by_dependency()` for selective interpolation
- **SAME** `compute_all_features()` workflow (no pre-interpolation)
- **SAME** perfect preservation metrics for level 0
- **SAME** `compute_feature_preservation_metrics()` call pattern

### ✅ 2. JSON Field Names
- Changed `featurePreservation` → `feature_preservation` (snake_case to match backend)
- Ensures consistency with `precompute_feature_preservation.py` output format

### ✅ 3. Directory Processing Support
- **NEW**: `--dir` flag to process all datasets in a directory
- **NEW**: `find_datasets_in_directory()` function
- Process entire directories like `stock_price/`, `climate_awnd/`, etc.

### ✅ 4. Feature Scales Computation
- **EXACT SAME** logic as `calculate_and_save_scales()` from `precompute_feature_preservation.py`
- Percentile-based thresholds (25th, 50th, 75th)
- Distribution statistics for each metric
- Saves to `_feature_scales.json`

### ✅ 5. Error Handling
- Prints errors instead of silent failures
- Continues processing other levels/algorithms on error
- Detailed summary of failures at end

## Usage Examples

### Single Dataset (Original Mode)
```powershell
# Process all algorithms for one dataset
python precompute_all_unified.py stock_aapl_price

# With parallel processing (4 workers)
python precompute_all_unified.py stock_aapl_price --parallel 4

# Specific algorithm only
python precompute_all_unified.py stock_aapl_price --algorithm gaussian_filter

# Force re-computation (ignore existing files)
python precompute_all_unified.py stock_aapl_price --no-resume
```

### Directory Mode (NEW!)
```powershell
# Process ALL datasets in stock_price directory
python precompute_all_unified.py stock_price --dir

# With parallel processing
python precompute_all_unified.py stock_price --dir --parallel 4

# Process climate_awnd directory (all 6 datasets)
python precompute_all_unified.py climate_awnd --dir

# Process eeg_500 directory with specific algorithm
python precompute_all_unified.py eeg_500 --dir --algorithm gaussian_filter
```

## What Gets Computed

For each dataset and each algorithm:

1. **Level 0 (Original Data)**:
   - PAE value
   - All 12 visual features
   - Perfect preservation metrics (all zeros)

2. **Levels 1-100 (Smoothed)**:
   - Smoothed output (100 parameter levels)
   - PAE value for each level
   - All 12 visual features for simplified series
   - Feature preservation metrics comparing original vs simplified

3. **Global Feature Scales**:
   - Percentile thresholds for all metrics
   - Distribution statistics
   - Saved to `_feature_scales.json`

## Output Structure

```
precomputed/
├── stock_aapl_price/
│   ├── gaussian_filter_level_0.json
│   ├── gaussian_filter_level_1.json
│   ├── ...
│   ├── gaussian_filter_level_100.json
│   ├── median_filter_level_0.json
│   ├── ...
│   └── _feature_scales.json
├── stock_amzn_price/
│   └── ...
└── ...
```

Each level file contains:
```json
{
  "dataset_name": "stock_aapl_price",
  "algorithm": "gaussian_filter",
  "level": 50,
  "parameter_name": "sigma",
  "parameter_value": 50.12,
  "pae": 0.008,
  "output": [...],  // Smoothed series
  "features": {     // All 12 features
    "level": {...},
    "mean": {...},
    "extrema": {...},
    ...
  },
  "feature_preservation": {  // Preservation metrics
    "level": {"l1": 12.5, "linf": 45.2},
    "extrema": {"bottleneck": 0.5, "wasserstein": 1.2},
    "change_points": {"delta": 2, "l1": 5.3, "linf": 12.1},
    ...
  }
}
```

## Verification

To verify the logic matches `precompute_feature_preservation.py`:

1. **Check feature computation**:
   ```powershell
   # Run unified script
   python precompute_all_unified.py stock_aapl_price --algorithm gaussian_filter
   
   # Compare with existing precomputed data
   # Features and metrics should be identical
   ```

2. **Check directory processing**:
   ```powershell
   # Process all stock_price datasets
   python precompute_all_unified.py stock_price --dir
   
   # Verify all 6 datasets processed:
   # - stock_aapl_price
   # - stock_amzn_price
   # - stock_bac_price
   # - stock_goog_price
   # - stock_intc_price
   # - stock_jpm_price
   ```

3. **Check feature scales**:
   ```powershell
   # Look for _feature_scales.json in output directory
   cat precomputed/stock_aapl_price/_feature_scales.json
   ```

## Performance

- **Resume mode** (default): Skips already completed levels
- **Parallel processing**: Use `--parallel N` to process N algorithms simultaneously
- **Directory mode**: Processes datasets sequentially, algorithms per dataset can be parallel

Example timing for stock_price directory (6 datasets × 20 algorithms × 101 levels):
- Sequential: ~45-60 minutes
- Parallel (4 workers): ~15-20 minutes

## Common Issues

### Issue: "Directory not found"
```powershell
# Make sure directory exists under data/
ls data/stock_price/  # Should show JSON files
```

### Issue: "Dataset not found"
```powershell
# Check exact filename (without .json extension)
ls data/stock_price/  # Shows: stock_aapl_price.json
python precompute_all_unified.py stock_aapl_price  # Use: stock_aapl_price (no .json)
```

### Issue: Feature preservation missing
```powershell
# Use --no-resume to force re-computation
python precompute_all_unified.py stock_aapl_price --no-resume
```

## Differences from Old Version

| Feature | Old `precompute_all_unified.py` | New Version |
|---------|--------------------------------|-------------|
| Feature computation | Basic implementation | **EXACT** same as `precompute_feature_preservation.py` |
| JSON field names | `featurePreservation` (camelCase) | `feature_preservation` (snake_case) ✅ |
| Directory support | ❌ No | ✅ Yes (`--dir` flag) |
| Feature scales | Basic percentiles | ✅ Full distribution statistics |
| Error handling | Silent failures | ✅ Detailed error messages |
| Level 0 metrics | Computed via comparison | ✅ Perfect preservation (hardcoded zeros) |
| Interpolation logic | Pre-interpolation | ✅ Selective (matches backend) |

## Recommended Workflow

1. **Test with single dataset first**:
   ```powershell
   python precompute_all_unified.py stock_aapl_price
   ```

2. **Process entire directory** (if test succeeds):
   ```powershell
   python precompute_all_unified.py stock_price --dir --parallel 4
   ```

3. **Verify output**:
   - Check `precomputed/<dataset_name>/` directories created
   - Check `_feature_scales.json` exists
   - Spot-check a few level files for completeness

4. **Resume if interrupted**:
   ```powershell
   # Automatically skips completed files
   python precompute_all_unified.py stock_price --dir --parallel 4
   ```
