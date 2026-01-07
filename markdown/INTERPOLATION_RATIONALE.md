# Interpolation Rationale for Feature Preservation Metrics

## Overview

When comparing features between original and simplified time series of different lengths, some features require interpolation while others do not. This document explains the reasoning behind each decision.

## Features Requiring Interpolation (6 features)

These features are **position-dependent** and require point-wise comparison at matching x-coordinates:

### 1. **Level** (Point Values)
- **Why interpolate**: Direct comparison of y-values at each x-position
- **Metric**: L1 (mean absolute error), L∞ (maximum error)
- **Rationale**: Level preservation means "do the simplified points match the original values at the same positions?"
- **Without interpolation**: Cannot compare arrays of different lengths point-wise

### 2. **Slope** (First Derivative)
- **Why interpolate**: Slope computed as `y[i+1] - y[i]` depends on uniform x-spacing
- **Metric**: L1 (mean slope error), L∞ (max slope error)
- **Rationale**: We want to know if the rate of change is preserved at each position
- **Without interpolation**: Different x-spacing yields incomparable slope values

### 3. **Curvature** (Second Derivative)
- **Why interpolate**: Curvature uses centered differences requiring uniform spacing
- **Metric**: L1 (mean curvature error), L∞ (max curvature error)
- **Rationale**: Bend preservation requires comparing kappa at matching positions
- **Without interpolation**: Formula assumes uniform x-spacing (Δx = 1)

### 4. **Regression** (Linear Fit)
- **Why interpolate**: Fitted line `y = α + βt` is evaluated at each time point
- **Metric**: L1 (mean fitted value error), L∞ (max fitted value error)
- **Rationale**: Trend line should match at every x-position, not just endpoints
- **Without interpolation**: Different series lengths give different fitted value arrays

### 5. **Trend** (Low-Frequency FFT Component)
- **Why interpolate**: FFT bins depend on series length (N determines frequency resolution)
- **Metric**: L1 (mean trend error), L∞ (max trend error)
- **Rationale**: Low-frequency components should align at matching x-coordinates
- **Without interpolation**: Different N → different frequency bins → incomparable spectra

### 6. **Noise** (High-Frequency FFT Component)
- **Why interpolate**: Same as trend - FFT resolution depends on series length
- **Metric**: L1 (mean noise error), L∞ (max noise error), AUC delta (total energy)
- **Rationale**: High-frequency residuals should match at each position
- **Without interpolation**: Different spectral resolutions prevent direct comparison

## Features NOT Requiring Interpolation (6 features)

These features use **topological distances**, **scalar comparisons**, or **count-based metrics** that handle different lengths natively:

### 7. **Extrema** (Local Minima/Maxima)
- **Why no interpolation**: Uses persistence diagrams + bottleneck/Wasserstein distances
- **Metric**: Bottleneck (L∞ matching), Wasserstein (L1 matching)
- **Rationale**: Topological distances compare **sets** of (birth, death) pairs, not arrays
- **Handles different lengths**: 15 extrema vs 8 extrema → optimal matching automatically computed
- **Key insight**: We care about "are the significant peaks/valleys preserved?" not "do they align exactly at same x-positions?"

### 8. **Spikes/Dips** (Outliers)
- **Why no interpolation**: Uses persistence diagrams + bottleneck/Wasserstein distances
- **Metric**: Bottleneck (L∞ matching), Wasserstein (L1 matching)
- **Rationale**: Same as extrema - compares sets of outliers, not point-wise arrays
- **Handles different lengths**: 12 spikes vs 5 spikes → optimal matching
- **Critical bug fixed (Nov 26, 2025)**: Previously wrongly recomputed on interpolated data (lines 1626-1631), which changed mean/std and created fake spikes

### 9. **Regimes** (Plateau Segments)
- **Why no interpolation**: Count-based metric (number of regimes)
- **Metric**: Delta (absolute difference in regime count)
- **Rationale**: "How many regimes were lost/gained?" is a scalar comparison
- **Handles different lengths**: 5 regimes vs 3 regimes → delta = 2

### 10. **Change Points** (Regime Boundaries)
- **Why no interpolation**: Count-based metric (number of change points)
- **Metric**: Delta (absolute difference in change point count)
- **Rationale**: Currently only counts CPs, doesn't compare positions
- **Handles different lengths**: 4 CPs vs 2 CPs → delta = 2
- **Future extension**: Position metrics (L1/L∞ displacement) could be added using x-coordinate mapping (see commented code at lines 1458-1520)

### 11. **Mean** (Average Value)
- **Why no interpolation**: Scalar comparison
- **Metric**: Delta (absolute difference)
- **Rationale**: Mean is a single number, independent of series length
- **Handles different lengths**: mean(1258 points) vs mean(100 points) → both yield single values

### 12. **Roughness** (Std of First Differences)
- **Why no interpolation**: Scalar comparison computed from actual data
- **Metric**: Delta (absolute difference in σ(ΔY))
- **Rationale**: Roughness measures high-frequency variation as a **summary statistic**, not point-wise
- **Handles different lengths**: Roughness is scale-invariant - std of differences works on any length
- **Key insight**: We want "is the overall jaggedness preserved?" not "does each individual wiggle match?"

### 13. **Periodicity** (Dominant Frequency)
- **Why no interpolation**: Scalar comparison (amplitude and period count)
- **Metric**: Amplitude delta, num_periods delta
- **Rationale**: Dominant frequency properties are summary statistics
- **Handles different lengths**: FFT finds dominant frequency regardless of series length
- **Note**: While FFT is recomputed on interpolated data (for consistent frequency bins), the final metric compares scalar values (amplitude, num_periods), not arrays

## Summary Table

| Feature | Interpolation? | Metric Type | Reason |
|---------|---------------|-------------|---------|
| Level | ✅ Yes | L1, L∞ | Point-wise comparison |
| Slope | ✅ Yes | L1, L∞ | Uniform spacing required |
| Curvature | ✅ Yes | L1, L∞ | Centered differences |
| Regression | ✅ Yes | L1, L∞ | Fitted values at each point |
| Trend | ✅ Yes | L1, L∞ | FFT bin alignment |
| Noise | ✅ Yes | L1, L∞, AUC | FFT bin alignment |
| Extrema | ❌ No | Bottleneck, Wasserstein | Topological distance |
| Spikes/Dips | ❌ No | Bottleneck, Wasserstein | Topological distance |
| Regimes | ❌ No | Delta | Count-based |
| Change Points | ❌ No | Delta | Count-based |
| Mean | ❌ No | Delta | Scalar |
| Roughness | ❌ No | Delta | Scalar |
| Periodicity | ❌ No | Delta (amplitude, periods) | Scalar |

## Methodology Implications

### For Publication
- **Interpolation bias**: 6 features (50% of features, ~85% of metrics when weighted by metric count) use interpolation
- **Potential concern**: Does interpolation artificially improve reducer performance? (e.g., 100 real points + 900 interpolated)
- **Defense**: Interpolation matches perceptual reality - humans see interpolated lines on screen
- **Alternative view**: Could report both interpolated and non-interpolated metrics for transparency

### Future Extensions
1. **Change point position metrics**: Add L1/L∞ displacement using x-coordinate mapping (infrastructure already exists)
2. **Hybrid approach**: Report both interpolated and raw metrics side-by-side
3. **New features**: Always check if topological/scalar comparison is possible before defaulting to interpolation

## Implementation Notes

- **Interpolation function**: `_interpolate_to_match_length()` at line 65 (linear interpolation via `np.interp`)
- **Interpolation block**: Lines 1595-1640 in `compute_feature_preservation_metrics()`
- **Topological distances**: `persim` library (`bottleneck()`, `wasserstein()`) handles different-length diagrams
- **Bug fix history**: Spikes/dips interpolation removed Nov 26, 2025 (was lines 1626-1631)

## References
- Persistence diagrams: Edelsbrunner & Harer, "Computational Topology" (2010)
- Wasserstein distance: Kantorovich optimal transport
- Bottleneck distance: Hausdorff-like metric for persistence diagrams
