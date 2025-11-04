# Algorithm Output Analysis

## Overview
This document provides a comprehensive analysis of all implemented algorithms using a sample dataset of 10 data points. The algorithms are categorized into three main types: **Transformers**, **Reducers**, and **Aggregators**.

## Sample Dataset
**Original Dataset**: `[1.0, 4.5, 2.3, 7.8, 3.1, 6.9, 4.2, 8.5, 5.7, 2.8]`
- **Length**: 10 points
- **Range**: 1.0 to 8.5
- **Mean**: 4.58

---

## 🔄 TRANSFORMERS
*Transformers preserve the original data length while modifying the values through smoothing, filtering, or other signal processing operations.*

### Gaussian Filter
- **Parameters**: `sigma=1.0`
- **Output Length**: 10 (same as input)
- **Output Type**: TRANSFORMED
- **Result**: `[1.95, 3.09, 4.15, 5.06, 5.2, 5.44, 5.92, 6.34, 5.43, 3.82]`
- **Description**: Applies Gaussian smoothing to reduce noise while preserving overall signal shape.

### Mean Filter
- **Parameters**: `window_size=3`
- **Output Length**: 10 (same as input)
- **Output Type**: TRANSFORMED
- **Result**: `[2.17, 2.6, 4.87, 4.4, 5.93, 4.73, 6.53, 6.13, 5.67, 3.77]`
- **Description**: Replaces each point with the average of surrounding points within the window.

### Moving Average
- **Parameters**: `w=3`
- **Output Length**: 10 (same as input)
- **Output Type**: TRANSFORMED
- **Result**: `[1.83, 2.6, 4.87, 4.4, 5.93, 4.73, 6.53, 6.13, 5.67, 2.83]`
- **Description**: Simple moving average that smooths the signal by averaging neighboring points.

### Savitzky-Golay Filter
- **Parameters**: `window_size=5, polyorder=2`
- **Output Length**: 10 (same as input)
- **Output Type**: TRANSFORMED
- **Result**: `[2.09, 2.56, 4.98, 4.66, 5.99, 4.46, 6.57, 6.69, 6.04, 3.31]`
- **Description**: Polynomial smoothing that preserves peaks and features better than simple averaging.

### Butterworth Filter
- **Parameters**: `cutoff_freq_normalized=0.3, order=2`
- **Output Length**: 10 (same as input)
- **Output Type**: TRANSFORMED
- **Result**: `[0.13, 0.95, 2.29, 3.67, 4.87, 5.39, 5.47, 5.74, 6.33, 6.15]`
- **Description**: Low-pass filter that removes high-frequency components while maintaining smooth transitions.

### Chebyshev Filter
- **Parameters**: `cutoff_freq_normalized=0.3, order=2, ripple_db=1.0`
- **Output Length**: 10 (same as input)
- **Output Type**: TRANSFORMED
- **Result**: `[0.14, 1.01, 2.42, 3.81, 4.9, 5.18, 4.99, 5.11, 5.71, 5.54]`
- **Description**: Low-pass filter with steeper roll-off than Butterworth, allowing some ripple in passband.

### Elliptical Filter
- **Parameters**: `cutoff_freq_normalized=0.3, order=2, ripple_db=1.0, max_atten_db=40.0`
- **Output Length**: 10 (same as input)
- **Output Type**: TRANSFORMED
- **Result**: `[0.22, 1.03, 2.09, 3.06, 4.01, 4.84, 5.12, 5.22, 5.77, 6.28]`
- **Description**: Most efficient filter design with both passband ripple and stopband attenuation.

### FFT Cutoff Filter
- **Parameters**: `cutoff_freq_normalized=0.3`
- **Output Length**: 10 (same as input)
- **Output Type**: TRANSFORMED
- **Result**: `[2.99, 2.89, 3.48, 4.53, 5.63, 6.37, 6.47, 5.88, 4.83, 3.73]`
- **Description**: Frequency domain filtering that removes high-frequency components using FFT.

---

## 📉 REDUCERS
*Reducers reduce the number of data points while preserving the essential shape and characteristics of the original signal.*

### LTTB Downsample
- **Parameters**: `output_length=5`
- **Output Length**: 5
- **Output Type**: SUBSET
- **Result**: `[1.0, 4.5, 7.8, 8.5, 2.8]`
- **Description**: Largest-Triangle-Three-Buckets algorithm that preserves visual characteristics efficiently.

### M4 Downsample
- **Parameters**: `output_length=8`
- **Output Length**: 8
- **Output Type**: SUBSET
- **Result**: `[1.0, 1.0, 7.8, 3.1, 6.9, 8.5, 2.8, 2.8]`
- **Description**: Min-Max-Min-Max algorithm that captures extreme values in each segment.

### MinMaxLTTB Downsample
- **Parameters**: `output_length=5`
- **Output Length**: 5
- **Output Type**: SUBSET
- **Result**: `[1.0, 4.5, 7.8, 8.5, 2.8]`
- **Description**: Combination of MinMax and LTTB algorithms for optimal visual preservation.

### Uniform Subsample
- **Parameters**: `output_length=5`
- **Output Length**: 5
- **Output Type**: SUBSET
- **Result**: `[1.0, 2.3, 3.1, 8.5, 2.8]`
- **Description**: Evenly spaced sampling that maintains temporal distribution.

### RDP Downsample
- **Parameters**: `output_length=5`
- **Output Length**: 5
- **Output Type**: SUBSET
- **Result**: `[1.0, 7.8, 3.1, 8.5, 2.8]`
- **Description**: Ramer-Douglas-Peucker algorithm that preserves geometric shape characteristics.

### TDA Downsample
- **Parameters**: `threshold=0.5`
- **Output Length**: 10 (no reduction with this threshold)
- **Output Type**: SUBSET
- **Result**: `[4.5, 2.3, 6.9, 4.2, 7.8, 3.1, 8.5, 2.8, 2.8, 1.0]`
- **Description**: Topological Data Analysis that preserves persistent features based on threshold.

### FPCS Downsample
- **Parameters**: `rate=2`
- **Output Length**: 4
- **Output Type**: SUBSET
- **Result**: `[1.0, 7.8, 3.1, 8.5]`
- **Description**: Fast Point Cloud Sampling that identifies and preserves extrema.

### Every Nth Point
- **Parameters**: `step=2`
- **Output Length**: 5
- **Output Type**: SUBSET
- **Result**: `[1.0, 2.3, 3.1, 4.2, 5.7]`
- **Description**: Simple uniform sampling every nth point.

### Median Filter Downsample
- **Parameters**: `window_size=3`
- **Output Length**: 10 (same as input)
- **Output Type**: SUBSET
- **Result**: `[1.0, 2.3, 4.5, 3.1, 6.9, 4.2, 6.9, 5.7, 5.7, 2.8]`
- **Description**: Selects median values within sliding windows (reclassified from transformers).

### Min Filter Downsample
- **Parameters**: `window_size=3`
- **Output Length**: 10 (same as input)
- **Output Type**: SUBSET
- **Result**: `[1.0, 1.0, 2.3, 2.3, 3.1, 3.1, 4.2, 4.2, 2.8, 2.8]`
- **Description**: Selects minimum values within sliding windows (reclassified from transformers).

### Max Filter Downsample
- **Parameters**: `window_size=3`
- **Output Length**: 10 (same as input)
- **Output Type**: SUBSET
- **Result**: `[4.5, 4.5, 7.8, 7.8, 7.8, 6.9, 8.5, 8.5, 8.5, 5.7]`
- **Description**: Selects maximum values within sliding windows (reclassified from transformers).

---

## 📊 AGGREGATORS
*Aggregators group data into bins and compute statistics, creating new representative values.*

### Bin Average Aggregator
- **Parameters**: `bins=5`
- **Output Length**: 5
- **Output Type**: TRANSFORMED
- **Result**: `[2.75, 5.05, 5.0, 6.35, 4.25]`
- **Description**: Divides data into equal bins and computes the average value for each bin.

### ASAP Aggregator
- **Parameters**: `max_window=5`
- **Output Length**: 9
- **Output Type**: TRANSFORMED
- **Result**: `[2.75, 3.4, 5.05, 5.45, 5.0, 5.55, 6.35, 7.1, 4.25]`
- **Description**: Adaptive Streaming Aggregation Protocol that creates variable-sized aggregations.

### ASAP Smoother
- **Parameters**: `max_window=5`
- **Output Length**: 9
- **Output Type**: TRANSFORMED
- **Result**: `[2.75, 3.4, 5.05, 5.45, 5.0, 5.55, 6.35, 7.1, 4.25]`
- **Description**: ASAP algorithm with additional smoothing for temporal data streams.

---

## Summary Statistics

### Algorithm Count by Category
- **Transformers**: 8 algorithms
- **Reducers**: 11 algorithms  
- **Aggregators**: 3 algorithms
- **Total**: 22 working algorithms

### Output Type Distribution
- **SUBSET** (selecting from original): 11 algorithms
- **TRANSFORMED** (computing new values): 11 algorithms

### Length Behavior
- **Preserve Length** (10 → 10): 11 algorithms
- **Reduce Length** (10 → 4-9): 21 algorithms

---

## Key Insights

### Transformers
- All transformers maintain the original data length
- Most create new computed values except median, min, max filters (now reclassified)
- Excellent for noise reduction and signal smoothing

### Reducers  
- Highly effective at data compression (typical reduction: 50-80%)
- Always preserve original data values (SUBSET type)
- Various strategies: shape preservation (LTTB), extreme capture (M4), geometric (RDP)

### Aggregators
- Create entirely new statistical representations
- Most efficient for creating summary statistics
- Variable output lengths based on binning strategy

---

*Generated on: November 3, 2025*  
*Dataset: 10-point sample with range 1.0-8.5*