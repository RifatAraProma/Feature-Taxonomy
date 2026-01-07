# Regime Detection: Penalty Selection Guide

## Overview
The PELT (Pruned Exact Linear Time) algorithm detects change points where the mean shifts. The **penalty parameter** controls the trade-off between:
- **Low penalty**: More change points detected (more sensitive, may overfit)
- **High penalty**: Fewer change points detected (more conservative, may underfit)

## Implementation

### 1. **BIC (Bayesian Information Criterion)** - DEFAULT
**Recommended for most use cases** - data-driven and theoretically principled.

```python
config = FeatureConfig(regime_penalty=None)  # None = use BIC
result = compute_regimes(y, config)
```

**Formula**: `penalty = log(n) * d²`
- `n` = series length
- `d` = dimension (1 for univariate, 2+ for multivariate)

**Example**:
- For n=100: penalty = log(100) * 1² ≈ 4.61
- For n=1000: penalty = log(1000) * 1² ≈ 6.91
- For n=10000: penalty = log(10000) * 1² ≈ 9.21

**Advantages**:
✓ Automatic - no manual tuning required
✓ Theoretically grounded (minimizes BIC)
✓ Scales with data size
✓ Works well in practice

**When BIC works well**:
- General-purpose regime detection
- When you don't have domain knowledge about expected number of regimes
- Stock prices, sensor data, most time series

### 2. **Manual Penalty** - For fine-tuning

```python
config = FeatureConfig(regime_penalty=5.0)  # Specify manually
result = compute_regimes(y, config)
```

**Use when**:
- You have domain knowledge (e.g., "expect ~3 regimes in this 1000-point series")
- BIC is too sensitive or too conservative for your data
- You want consistent behavior across datasets of varying lengths

**Guidelines**:
- **penalty = 1-3**: Very sensitive (many change points)
- **penalty = 5-10**: Moderate (BIC range for typical data)
- **penalty = 15+**: Conservative (few change points)

### 3. **Other Methods** (Not Implemented)

#### AIC (Akaike Information Criterion)
Similar to BIC but with penalty = `2 * d²` (constant, not data-driven)
- Generally detects more change points than BIC
- Less popular for change point detection

#### Cross-Validation
Most robust but computationally expensive:
1. Split data into train/validation
2. Try multiple penalties
3. Choose penalty with best validation performance
- **Pro**: Most accurate
- **Con**: Very slow

#### Elbow Method
Visual/heuristic approach:
1. Compute cost (residual sum of squares) for different penalties
2. Plot penalty vs. cost
3. Choose "elbow" point where cost stops decreasing rapidly
- **Pro**: Intuitive
- **Con**: Subjective, requires manual inspection

## Comparison Table

| Method | Auto? | Speed | Accuracy | Use Case |
|--------|-------|-------|----------|----------|
| **BIC** | ✓ | Fast | Good | Default choice |
| Manual | ✗ | Fast | Varies | Fine-tuning |
| AIC | ✓ | Fast | OK | More sensitive alternative |
| CV | ✓ | Slow | Best | When accuracy critical |
| Elbow | ✗ | Medium | OK | Visual exploration |

## Debugging

Check what penalty was used:
```python
result = compute_regimes(y, config)
print(f"Penalty used: {result['penalty_used']}")
```

Compare BIC vs manual:
```python
# BIC
cfg_auto = FeatureConfig(regime_penalty=None)
result_auto = compute_regimes(y, cfg_auto)
print(f"BIC penalty: {result_auto['penalty_used']:.2f}")
print(f"BIC regimes: {result_auto['num_regimes']}")

# Manual
cfg_manual = FeatureConfig(regime_penalty=5.0)
result_manual = compute_regimes(y, cfg_manual)
print(f"Manual regimes: {result_manual['num_regimes']}")
```

## Examples

### Example 1: Stock Price Data (n=1000)
```python
y = load_stock_data()[:1000]

# BIC automatically chooses penalty ≈ 6.91
config = FeatureConfig(regime_penalty=None)
result = compute_regimes(y, config)
# → Detects 5-8 regimes (typical for stock data)
```

### Example 2: Sensor Data (noisy, n=500)
```python
y = load_sensor_data()

# BIC penalty ≈ 6.21 may be too sensitive for noisy data
# Increase penalty to reduce false positives
config = FeatureConfig(regime_penalty=10.0)
result = compute_regimes(y, config)
# → Fewer, more robust regimes
```

### Example 3: Simple Synthetic (n=10)
```python
y = [1, 1, 1, 5, 5, 5, 2, 2, 2, 2]

# BIC penalty = log(10) ≈ 2.30 (quite sensitive)
config = FeatureConfig(regime_penalty=None)
result = compute_regimes(y, config)
# → Should detect 3 clear regimes at [0-2], [3-5], [6-9]
```

## Best Practices

1. **Start with BIC** (penalty=None) - it's data-driven and works well
2. **Check output**: Does number of regimes make sense?
3. **If too many regimes**: Increase penalty manually (try 1.5×BIC, then 2×BIC)
4. **If too few regimes**: Decrease penalty (try 0.5×BIC)
5. **For consistency**: Use same penalty across similar datasets
6. **For exploration**: Try range [BIC*0.5, BIC*2.0]

## References

- Killick, R., Fearnhead, P., & Eckley, I. A. (2012). "Optimal detection of changepoints with a linear computational cost." *Journal of the American Statistical Association*, 107(500), 1590-1598.
- ruptures documentation: https://centre-borelli.github.io/ruptures-docs/
- BIC: Schwarz, G. (1978). "Estimating the dimension of a model." *The Annals of Statistics*, 6(2), 461-464.
