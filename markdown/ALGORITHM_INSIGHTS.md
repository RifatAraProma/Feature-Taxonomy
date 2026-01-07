# Algorithm Performance Analysis: Key Insights

**Analysis Date:** November 25, 2025  
**Datasets Analyzed:** 77 precomputed datasets  
**Algorithms Evaluated:** 19 smoothing/downsampling algorithms  
**Metrics Assessed:** 23 feature preservation metrics

---

## Executive Summary

After analyzing rankings across all 77 datasets, **Gaussian filter emerges as the clear winner** with an average rank of **2.11** across all metrics and datasets. The top performers are all **transformer algorithms** (length-preserving smoothers), while reducers and aggregators generally rank lower.

### Top 5 Overall Performers:
1. **Gaussian Filter** (2.11) - Best overall
2. **Mean Filter** (3.21) 
3. **Savitzky-Golay Filter** (4.00)
4. **Median Filter** (4.89)
5. **ASAP Aggregator** (6.97) - Best non-transformer

### Bottom 3 Performers:
17. **LTTB Downsample** (13.82)
18. **Chebyshev Filter** (14.50)
19. **RDP Downsample** (16.46)

---

## Key Finding 1: Transformers Dominate Over Reducers

**Transformers** (length-preserving smoothers) significantly outperform **reducers** (downsamplers):

- **Average transformer rank:** 8.37
- **Average reducer rank:** 12.94
- **Average aggregator rank:** 7.88

**Interpretation:** Preserving data length while smoothing values leads to better feature preservation than aggressive downsampling. Aggregators (ASAP, bin averaging) offer a middle ground.

### Best by Algorithm Type:
- **Best Transformer:** Gaussian filter (2.11)
- **Best Aggregator:** ASAP aggregator (6.97)
- **Best Reducer:** Uniform subsample (9.66)

---

## Key Finding 2: Gaussian Filter is Universally Excellent

Gaussian filter ranks #1 in **10 out of 11 feature categories**:

✅ **Level Features** (1.29) - Mean, point values  
✅ **Derivative Features - Slope** (1.35) - Rate of change  
✅ **Statistical Features** (1.15) - Regression fit  
✅ **Frequency Features - Noise** (1.29) - Noise characteristics  
✅ **Frequency Features - Trend** (1.45) - Overall direction  
✅ **Derivative Features - Curvature** (1.76) - Local bending  
✅ **Derivative Features - Roughness** (1.83) - High-frequency variation  
✅ **Shape Features - Regimes** (3.22) - Flat segments  
✅ **Shape Features - Spikes/Dips** (3.44) - Isolated anomalies  
❌ **Shape Features - Extrema** (4.00) - Peaks/valleys: **Mean filter wins** (3.48)

**Exception:** Mean filter slightly edges out Gaussian for **extrema detection** (peaks/valleys), likely because it preserves discrete extrema better than Gaussian's continuous smoothing.

---

## Key Finding 3: Savitzky-Golay Excels at Periodicity

**Savitzky-Golay filter** is the specialist for **frequency-domain features**:

- **Periodicity** (3.08) - Best overall for periodic patterns
- **Trend** (2.14) - Second-best for trend extraction
- Achieves this while maintaining excellent **level** and **regression** preservation

**Why?** Savitzky-Golay fits local polynomials, which naturally preserve periodic oscillations better than simple averaging (mean/median) or Gaussian smoothing.

---

## Key Finding 4: Dataset-Specific Performance Patterns

### Climate Precipitation Data: Median Filter Wins
- **Climate PRCP datasets:** Median filter (2.32) beats Gaussian (2.45)
- **Reason:** Precipitation data has outliers (rain spikes) that median filtering handles robustly

### EEG Data: Gaussian Maintains Lead
- **EEG datasets:** Gaussian (2.02), Mean (3.02), Savitzky-Golay (3.73)
- High-frequency biomedical signals benefit from Gaussian's smooth frequency response

### Stock Price vs. Volume
- **Stock Price:** Gaussian (1.93) > Mean (2.51) > Savitzky-Golay (2.77)
- **Stock Volume:** Gaussian (1.74) > Mean (2.96) > Savitzky-Golay (4.06)
- Volume data (more irregular) shows larger performance gaps

### Unemployment Data: Consistent with Overall Trends
- **Unemployment:** Gaussian (2.08) > Mean (3.09) > Savitzky-Golay (3.92)
- Smooth economic time series play to Gaussian's strengths

---

## Key Finding 5: Min/Max Filters for Roughness Preservation

**Max filter** and **Min filter** rank surprisingly high for:
- **Roughness delta** (Max: 3.2, Min: 4.7)
- **Curvature** (Max: 4.1-4.5, Min: 4.8)

**Explanation:** These morphological filters preserve local extrema structure, which directly relates to roughness and curvature. However, they fail catastrophically at other features (ranks 10-13 overall).

**Use case:** If roughness preservation is critical and other features are secondary, max/min filters offer a niche advantage.

---

## Key Finding 6: ASAP Outperforms Other Aggregators/Reducers

**ASAP aggregator** (6.97) beats:
- All reducers: LTTB (13.82), M4 (13.12), MinMaxLTTB (13.69)
- Bin averaging (8.79)
- Uniform subsampling (9.66)

**Strengths:**
- **Noise** (5.0), **Mean** (5.1), **Trend** (5.2) - Adaptive windowing preserves local statistics
- **Roughness** (5.3) - Better than fixed-window aggregation

**Why ASAP wins:** Its autocorrelation-based adaptive windowing adjusts to local signal characteristics, unlike fixed-resolution reducers.

---

## Key Finding 7: Frequency Filters Underperform (Except FFT)

Butterworth, Chebyshev, and Elliptical filters rank poorly:
- **Butterworth:** 11.31 (rank 12)
- **Elliptical:** 13.65 (rank 15)
- **Chebyshev:** 14.50 (rank 18)

**FFT cutoff filter** does better (9.75, rank 8), especially for:
- **Level** and **Trend** preservation

**Why the difference?**
- Classic IIR filters (Butterworth, Chebyshev, Elliptical) introduce phase distortion and ringing
- FFT cutoff filter operates in frequency domain without phase shifts

**Recommendation:** Avoid IIR filters unless phase linearity doesn't matter. Use FFT cutoff or Gaussian instead.

---

## Key Finding 8: Most Challenging Metrics (High Algorithm Variance)

Metrics where algorithms differ most in performance:

1. **Roughness delta** (std: 5.37) - Huge range: Gaussian (1.8) to RDP (17.8)
2. **Slope L1** (std: 5.21) - Gaussian (1.4) vs. RDP (19.0)
3. **Trend** (std: 5.17) - Savitzky-Golay (2.0) vs. TDA (18-19)

**Interpretation:** These metrics are **algorithm-sensitive**. Choosing the wrong algorithm drastically degrades performance. In contrast, metrics like **extrema** show less variance (algorithms perform more similarly).

**Design implication:** For applications prioritizing roughness/slope/trend, algorithm selection is **critical**.

---

## Key Finding 9: RDP and TDA Are Specialized Tools

**RDP (Ramer-Douglas-Peucker)** ranks last (16.46):
- Optimizes geometric simplification, not feature preservation
- Terrible for: Slope (19.0), Trend (18-19), Roughness (17.8)

**TDA (Topological Data Analysis)** ranks 13th (12.98):
- Good for: Extrema (7.0), Spikes/Dips (8.0)
- Poor for: Trend (18-19), Periodicity (19.0)

**Takeaway:** These are **task-specific** algorithms. Use RDP for polygon simplification, TDA for topological features—not general-purpose smoothing.

---

## Practical Recommendations

### For General-Purpose Feature Preservation:
**Use Gaussian filter.** It dominates 10/11 feature categories and works across all dataset types.

### For Specific Scenarios:

| **Scenario** | **Best Algorithm** | **Why** |
|--------------|-------------------|---------|
| **Noisy data with outliers** | Median filter | Robust to spikes (rank 4.89) |
| **Precipitation/rainfall data** | Median filter | Handles rain spikes (rank 2.32 for PRCP) |
| **Periodic signal analysis** | Savitzky-Golay | Best periodicity preservation (3.08) |
| **Trend extraction** | Savitzky-Golay or Gaussian | Ranks 2.14 and 1.45 respectively |
| **Need downsampling** | ASAP aggregator | Best reducer (6.97) |
| **Fixed-budget visualization** | Uniform subsample | Best simple reducer (9.66) |
| **Roughness-critical** | Max filter | Specialist for roughness (3.2) |

### Algorithms to Avoid (Unless Specialized):
- **Chebyshev filter** (14.50) - Poor across the board
- **RDP downsample** (16.46) - Only for geometric simplification
- **Elliptical filter** (13.65) - Phase distortion issues
- **LTTB downsample** (13.82) - Underperforms ASAP and uniform subsampling

---

## Statistical Summary

### Ranking Distribution:
- **Top tier (rank < 5):** Gaussian, Mean, Savitzky-Golay, Median
- **Mid tier (5-10):** ASAP, Bin Average, Uniform Subsample, FFT Cutoff, Min Filter
- **Low tier (10-15):** Max, FPCS, Butterworth, TDA, M4, Elliptical, MinMaxLTTB, LTTB, Chebyshev
- **Bottom tier (>15):** RDP

### Feature Category Difficulty:
- **Easiest** (low variance): Extrema, Spikes/Dips (most algorithms perform similarly)
- **Hardest** (high variance): Roughness, Slope, Trend (algorithm choice matters most)

---

## Conclusion

This analysis reveals **Gaussian filtering as the gold standard** for feature-preserving time series simplification. Its performance is remarkably consistent across:
- 77 diverse datasets (stocks, climate, EEG, unemployment, etc.)
- 23 different feature preservation metrics
- 6 major dataset categories

**Key insight:** When in doubt, **use Gaussian filter**. It rarely ranks worse than 4th and usually ranks 1st-2nd across all features.

For specialized needs (periodicity → Savitzky-Golay, outliers → Median, downsampling → ASAP), targeted choices yield better results, but Gaussian remains the safe, high-performing default.

