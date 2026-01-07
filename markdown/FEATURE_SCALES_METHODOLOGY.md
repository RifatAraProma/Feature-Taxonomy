# Feature Scales Methodology

## Overview

This document explains how we calculate the "Excellent", "Good", "Fair", and "Poor" thresholds for feature preservation metrics across different datasets and smoothing algorithms.

## Purpose

When evaluating time series simplification algorithms, we need **objective, data-driven thresholds** to classify the quality of feature preservation. Instead of arbitrary cutoffs, we compute these thresholds from the actual distribution of metric values across all smoothing levels (0-99) for a given dataset.

## Methodology

### 1. Data Collection

For each dataset (e.g., `stock_aapl_price`), we:

1. **Precompute 100 smoothing levels** for each algorithm (Gaussian filter, LTTB, etc.)
2. **Calculate feature preservation metrics** at each level (L1 error, extrema retention, etc.)
3. **Aggregate ~1,900 samples** per metric (100 levels × ~19 algorithms)

**Example**: For `stock_aapl_price`:
- Total samples: **24,700** metric values
- From: **1,900 precomputed files** (100 levels × 19 algorithms)
- For metrics: level_l1, level_linf, extrema_retention, etc.

### 2. Percentile-Based Thresholds

We use **percentile-based statistical analysis** to determine quality thresholds:

#### For Error Metrics (Lower is Better)
Examples: `level_l1`, `level_linf`, `mean_error`, `regression_error`

- **Excellent**: ≤ 25th percentile (top 25% lowest errors)
- **Good**: ≤ 50th percentile (median error)
- **Fair**: ≤ 75th percentile (75% of algorithms do better than this)
- **Poor**: > 75th percentile (worst 25% of results)

**Interpretation**: "Excellent" means the algorithm is in the top quartile for minimizing error.

#### For Correlation/Retention Metrics (Higher is Better)
Examples: `extrema_retention`, `slope_correlation`, `trend_correlation`

- **Poor**: < 25th percentile (worst 25% preservation)
- **Fair**: ≥ 25th percentile but < 50th percentile
- **Good**: ≥ 50th percentile but < 75th percentile
- **Excellent**: ≥ 75th percentile (top 25% preservation)

**Interpretation**: "Excellent" means the algorithm preserves features better than 75% of all smoothing levels.

#### For Ratio Metrics (1.0 is Perfect)
Examples: `roughness_ratio`, `noise_ratio`

We calculate **deviation from 1.0**:

- **Excellent**: Deviation ≤ 25th percentile (closest to 1.0)
- **Good**: Deviation ≤ 50th percentile
- **Fair**: Deviation ≤ 75th percentile
- **Poor**: Deviation > 75th percentile

**Interpretation**: "Excellent" means the ratio is in the top quartile for closeness to 1.0 (perfect preservation).

### 3. Example Calculation

For `stock_aapl_price` dataset, `level_l1` metric:

**Step 1**: Collect all L1 errors from precomputed outputs
```
[0.001, 0.003, 0.015, ..., 52.476]  // 24,700 values
```

**Step 2**: Sort values
```
[0.000, 0.001, 0.002, ..., 52.476]
```

**Step 3**: Calculate percentiles
```
25th percentile (p25) = 1.599
50th percentile (p50) = 6.481
75th percentile (p75) = 10.604
```

**Step 4**: Define thresholds
```json
{
  "level_l1": {
    "type": "error",
    "excellent": 1.599,    // ≤ 1.599 is excellent
    "good": 6.481,         // ≤ 6.481 is good
    "fair": 10.604,        // ≤ 10.604 is fair
    "min": 0.0,            // Best possible value
    "max": 52.477          // Worst observed value
  }
}
```

**Step 5**: Apply to new smoothing result
If a Gaussian filter with σ=2.5 produces L1 error = 3.2:
- 3.2 ≤ 6.481 (good threshold)
- 3.2 > 1.599 (excellent threshold)
- **Result**: Classified as "Good" ✅

## Implementation

### Precomputation Script
Located at: `precompute_100_levels.py`

```python
# For each dataset
for dataset_id in datasets:
    all_metric_values = defaultdict(list)
    
    # Collect all metric values across algorithms and levels
    for algorithm in algorithms:
        for level in range(100):
            metrics = compute_metrics(dataset_id, algorithm, level)
            for metric_name, metric_value in metrics.items():
                all_metric_values[metric_name].append(metric_value)
    
    # Calculate percentiles for each metric
    scales = {}
    for metric_name, values in all_metric_values.items():
        values = sorted(values)
        metric_type = get_metric_type(metric_name)  # 'error', 'correlation', or 'ratio'
        
        if metric_type == 'error':
            scales[metric_name] = {
                'type': 'error',
                'excellent': percentile(values, 25),
                'good': percentile(values, 50),
                'fair': percentile(values, 75),
                'min': min(values),
                'max': max(values)
            }
        # ... similar for correlation and ratio types
    
    # Save to _feature_scales.json
    save_scales(dataset_id, scales)
```

### Scale Files
Located at: `precomputed/{dataset_id}/_feature_scales.json`

Example for `stock_aapl_price`:
```json
{
  "dataset": "stock_aapl_price",
  "total_samples": 24700,
  "num_files": 1900,
  "scales": {
    "level_l1": {
      "type": "error",
      "excellent": 1.5985273674017852,
      "good": 6.4813961388225945,
      "fair": 10.60379556141896,
      "min": 0.0,
      "max": 52.47663137561883
    },
    "level_linf": {
      "type": "error",
      "excellent": 16.938341776191336,
      "good": 47.04219805260179,
      "fair": 80.029999,
      "min": 0.0,
      "max": 201.17999300000002
    }
  }
}
```

## Advantages of This Approach

### 1. **Dataset-Specific**
Thresholds are tailored to each dataset's characteristics:
- Stock prices have different error scales than EEG signals
- Climate data has different retention patterns than astronomical data

### 2. **Empirically Grounded**
Based on actual algorithm performance, not arbitrary choices:
- Reflects what algorithms can realistically achieve
- Avoids unrealistic expectations

### 3. **Statistically Robust**
Uses percentiles from large sample sizes:
- ~1,900-24,000 samples per metric
- Resistant to outliers
- Captures the full distribution

### 4. **Automatically Adaptive**
As we add more algorithms or smoothing levels:
- Scales can be recalculated
- Thresholds adjust to new performance baselines

### 5. **Interpretable**
Clear meaning for each category:
- **Excellent** = Top 25% of all smoothing results
- **Good** = Better than median
- **Fair** = Better than worst 25%
- **Poor** = Bottom 25%

## Limitations & Future Work

### Current Limitations

1. **Placeholder Metrics**: Some metrics have all zeros (not yet implemented):
   - `extrema_retention`, `regime_retention`, `spike_retention`, etc.
   - These will be populated once feature extraction is complete

2. **Single Dataset Scales**: Currently computed per-dataset
   - Could explore cross-dataset normalization
   - May need domain-specific scales (finance vs. medical vs. climate)

3. **Fixed Percentiles**: Using 25/50/75 percentiles
   - Could experiment with different cutoffs (e.g., 10/30/50/70/90 for 5 categories)
   - Could use clustering or natural breaks in distribution

### Future Enhancements

1. **Multi-Level Granularity**
   - Add "Very Poor" and "Outstanding" categories
   - Use finer-grained percentiles (deciles instead of quartiles)

2. **Context-Aware Thresholds**
   - Different scales for different use cases (compression vs. visualization vs. analysis)
   - User-adjustable threshold preferences

3. **Dynamic Scaling**
   - Real-time threshold updates as new algorithms are added
   - Confidence intervals around percentile estimates

4. **Cross-Dataset Comparison**
   - Normalize metrics across datasets for meta-analysis
   - Identify algorithms that excel universally vs. domain-specific winners

## Usage in Frontend

The `MetricsBar` component uses these scales to:

1. **Color-code metrics**:
   - Green (#2E7D32) = Excellent
   - Light Green (#66BB6A) = Good
   - Orange (#FFA726) = Fair
   - Red (#E53935) = Poor

2. **Display legends** with threshold values

3. **Show distribution charts** with colored zones and current value indicator

4. **Provide context** through explanatory text

## References

- **Precomputation Script**: `precompute_100_levels.py`
- **Scale Loader**: `server/precomputed_loader.py`
- **Frontend API**: `web/src/services/api.ts` → `fetchFeatureScales()`
- **Visualization**: `web/src/components/MetricsBar.tsx`
- **Scale Files**: `precomputed/{dataset_id}/_feature_scales.json`

---

**Last Updated**: November 12, 2025  
**Author**: Feature Taxonomy Research Team  
**Version**: 1.0
