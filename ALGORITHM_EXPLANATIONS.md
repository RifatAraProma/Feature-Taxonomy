# 🧠 **COMPREHENSIVE ALGORITHM EXPLANATIONS**

## 📊 **Dataset Used for Examples**
**Original**: `[1.0, 4.5, 2.3, 7.8, 3.1, 6.9, 4.2, 8.5, 5.7, 2.8]` (10 points)

---

# 🔄 **TRANSFORMERS (Signal Processing - Compute New Values)**

## **🌊 Smoothing & Filtering Algorithms**

### **1. `gaussian_filter`** - Gaussian Smoothing
**How it works:**
- Applies a Gaussian (bell curve) kernel to smooth the signal
- Each output point is a weighted average of nearby points
- Weights follow a Gaussian distribution (more weight to closer points)
- `sigma` controls the width of the Gaussian kernel

**Example Output:** `[1.95, 3.09, 4.15, 5.06, 5.2, 5.44, 5.92, 6.34, 5.43, 3.82]`
- **Type:** TRANSFORMED (new computed values)
- **Use:** Noise reduction, trend extraction

### **2. `mean_filter`** - Moving Average Filter  
**How it works:**
- Slides a window across the data
- Each output point is the arithmetic mean of values in that window
- Uniform weighting within the window

**Example Output:** `[2.17, 2.6, 4.87, 4.4, 5.93, 4.73, 6.53, 6.13, 5.67, 3.77]`
- **Type:** TRANSFORMED (computed averages)
- **Use:** Basic smoothing, trend following

### **3. `moving_average`** - Simple Moving Average
**How it works:**
- Similar to mean_filter but with edge handling
- Computes average of `w` consecutive points
- Handles boundaries by padding or truncation

**Example Output:** `[1.83, 2.6, 4.87, 4.4, 5.93, 4.73, 6.53, 6.13, 5.67, 2.83]`
- **Type:** TRANSFORMED (computed averages)
- **Use:** Trend analysis, noise reduction

### **4. `savitzky_golay_filter`** - Polynomial Smoothing
**How it works:**
- Fits a polynomial of degree `polyorder` to local data points
- Uses least squares fitting within each window
- Preserves features like peaks better than moving average
- `window_size` must be odd and > `polyorder`

**Example Output:** `[2.09, 2.56, 4.98, 4.66, 5.99, 4.46, 6.57, 6.69, 6.04, 3.31]`
- **Type:** TRANSFORMED (polynomial fitted values)
- **Use:** Smoothing while preserving peaks and shapes

### **5. `butterworth_filter`** - Low-Pass IIR Filter
**How it works:**
- Infinite Impulse Response (IIR) digital filter
- Removes high-frequency components above cutoff
- Smooth frequency response, no ripples in passband
- `cutoff_freq_normalized`: 0.1 = heavy smoothing, 0.9 = light smoothing

**Example Output:** `[0.13, 0.95, 2.29, 3.67, 4.87, 5.39, 5.47, 5.74, 6.33, 6.15]`
- **Type:** TRANSFORMED (filtered values)
- **Use:** Anti-aliasing, trend extraction

### **6. `chebyshev_filter`** - Chebyshev Type I Filter
**How it works:**
- IIR filter with ripples in the passband
- Sharper cutoff than Butterworth for same order
- `ripple_db` controls amount of passband ripple
- Trades passband smoothness for steeper rolloff

**Example Output:** `[0.14, 1.01, 2.42, 3.81, 4.9, 5.18, 4.99, 5.11, 5.71, 5.54]`
- **Type:** TRANSFORMED (filtered values)  
- **Use:** Sharp frequency separation

### **7. `fft_cutoff_filter`** - Frequency Domain Filter
**How it works:**
- Transforms signal to frequency domain using FFT
- Zeroes out frequencies above the cutoff
- Transforms back to time domain using inverse FFT
- Hard cutoff (brick wall filter)

**Example Output:** `[2.99, 2.89, 3.48, 4.53, 5.63, 6.37, 6.47, 5.88, 4.83, 3.73]`
- **Type:** TRANSFORMED (frequency filtered)
- **Use:** Precise frequency control, spectral analysis

---

# 📉 **REDUCERS (Data Selection & Downsampling - Select Subsets)**

## **🎯 Intelligent Downsampling Algorithms**

### **1. `lttb_downsample`** - Largest Triangle Three Buckets
**How it works:**
- Divides data into buckets, keeps first and last points
- For each bucket, selects the point that forms the largest triangle 
- Triangle formed by: previous selected point, candidate point, next bucket average
- Preserves visual shape and trends very well

**Example Output:** `[1.0, 4.5, 7.8, 8.5, 2.8]` (5 points from 10)
- **Type:** SUBSET (original data points)
- **Use:** Time series visualization, chart downsampling

### **2. `m4_downsample`** - Min-Max-Min-Max Aggregation  
**How it works:**
- Divides data into segments
- From each segment, extracts: min, max, first, last values
- Always outputs multiple of 4 points (min 8)
- Preserves extreme values and trends

**Example Output:** `[1.0, 1.0, 7.8, 3.1, 6.9, 8.5, 2.8, 2.8]` (8 points)
- **Type:** SUBSET (extrema and endpoints)
- **Use:** Preserving peaks and valleys in visualization

### **3. `uniform_subsample_downsample`** - Uniform Spacing
**How it works:**
- Selects points at evenly spaced intervals
- Forces inclusion of first and last points
- Uses linear interpolation to determine indices
- Handles edge cases by adding extra evenly spaced points

**Example Output:** `[1.0, 2.3, 3.1, 8.5, 2.8]` (5 points)
- **Type:** SUBSET (evenly spaced originals)
- **Use:** Regular sampling, time series resampling

### **4. `rdp_downsample`** - Ramer-Douglas-Peucker
**How it works:**
- Geometric algorithm that preserves shape
- Finds the point farthest from line between endpoints
- If distance > threshold, keeps point and recurses on segments  
- Iteratively reduces to target point count
- Excellent for preserving geometric features

**Example Output:** `[1.0, 7.8, 3.1, 8.5, 2.8]` (5 points)
- **Type:** SUBSET (geometrically important points)
- **Use:** Map/path simplification, shape preservation

### **5. `fpcs_downsample`** - Fast Peak and Corner Sampling
**How it works:**
- Streaming algorithm that detects extrema (peaks/corners)
- Maintains a window of recent points
- Emits points when local extrema are confirmed
- `rate` parameter controls sensitivity (lower = more points)

**Example Output:** `[1.0, 7.8, 3.1, 8.5]` (4 points)  
- **Type:** SUBSET (extrema points)
- **Use:** Real-time peak detection, feature extraction

### **6. `tda_downsample`** - Topological Data Analysis
**How it works:**
- Uses persistent homology to identify topological features
- Builds a hierarchy of peaks and valleys by importance
- `threshold` controls how many features to keep (0=few, 1=all)
- Preserves topologically significant structures

**Example Output:** `[4.5, 2.3, 6.9, 4.2, 7.8, 3.1, 8.5, 2.8, 2.8, 1.0]` (10 points - reordered)
- **Type:** SUBSET (topologically important points)
- **Use:** Feature analysis, pattern recognition

### **7. `EveryNthPoint`** - Simple Uniform Sampling
**How it works:**
- Takes every Nth point from the original sequence
- Starts at index 0, then step, 2*step, etc.
- Simple and fast, but may miss important features
- No intelligence about data characteristics

**Example Output:** `[1.0, 2.3, 3.1, 4.2, 5.7]` (every 2nd point)
- **Type:** SUBSET (regular intervals)
- **Use:** Basic downsampling, regular time intervals

## **🔍 Window-Based Selection Filters (Moved from Transformers)**

### **8. `median_filter` (now reducer)** - Median Selection
**How it works:**
- Slides a window across the data
- Finds the median value within each window
- Selects the actual data point closest to that median
- Removes noise while preserving original data points

**Example Output:** `[1.0, 2.3, 4.5, 3.1, 6.9, 4.2, 6.9, 5.7, 5.7, 2.8]`
- **Type:** SUBSET (median-selected originals)
- **Use:** Noise reduction, outlier removal

### **9. `min_filter` (now reducer)** - Minimum Selection  
**How it works:**
- Slides a window across the data
- Finds the minimum value within each window
- Selects those actual minimum data points
- Extracts local minima and baseline

**Example Output:** `[1.0, 1.0, 2.3, 2.3, 3.1, 3.1, 4.2, 4.2, 2.8, 2.8]`
- **Type:** SUBSET (local minima)
- **Use:** Baseline extraction, trough detection

### **10. `max_filter` (now reducer)** - Maximum Selection
**How it works:**  
- Slides a window across the data
- Finds the maximum value within each window
- Selects those actual maximum data points
- Extracts local maxima and peaks

**Example Output:** `[4.5, 4.5, 7.8, 7.8, 7.8, 6.9, 8.5, 8.5, 8.5, 5.7]`
- **Type:** SUBSET (local maxima)  
- **Use:** Peak detection, envelope extraction

---

# 📊 **AGGREGATORS (Data Binning - Compute Statistics)**

## **📦 Binning & Statistical Aggregation**

### **1. `bin_average_aggregator`** - Simple Bin Averaging
**How it works:**
- Divides data into equal-sized bins
- Computes the arithmetic mean of values in each bin
- Each output value represents the average of multiple input points
- Reduces data size while preserving overall trends

**Example Output:** `[2.75, 5.05, 5.0, 6.35, 4.25]` (5 bins from 10 points)
- **Type:** TRANSFORMED (computed bin averages)
- **Use:** Data compression, trend analysis

### **2. `asap_aggregator`** - Adaptive Segmentation Aggregation  
**How it works:**
- Uses adaptive segmentation to find natural breakpoints
- Creates variable-width segments based on data characteristics
- Computes statistics (mean/median) for each segment
- More segments where data changes rapidly, fewer where stable

**Example Output:** `[2.75, 3.4, 5.05, 5.45, 5.0, 5.55, 6.35, 7.1, 4.25]` (9 segments)
- **Type:** TRANSFORMED (adaptive segment averages)
- **Use:** Intelligent data summarization, pattern detection

### **3. `asap_smoother`** - ASAP Smoothing Version
**How it works:**
- Similar to asap_aggregator but optimized for smoothing
- Uses same adaptive segmentation principle
- May apply additional smoothing within segments
- Balances compression with smoothness

**Example Output:** `[2.75, 3.4, 5.05, 5.45, 5.0, 5.55, 6.35, 7.1, 4.25]` (9 segments)  
- **Type:** TRANSFORMED (smoothed segment averages)
- **Use:** Adaptive smoothing, intelligent trend extraction

---

# 🎯 **ALGORITHM CLASSIFICATION SUMMARY**

## **🔄 TRANSFORMERS** (Compute New Values)
- **Purpose:** Signal processing, noise reduction, feature enhancement
- **Output Length:** Same as input (10 → 10)
- **Output Type:** TRANSFORMED (new computed values)
- **Examples:** Gaussian filter, Butterworth filter, moving average

## **📉 REDUCERS** (Select Subsets)  
- **Purpose:** Data compression, feature extraction, downsampling
- **Output Length:** Reduced (10 → 4-8 typically)
- **Output Type:** SUBSET (selected original values)
- **Examples:** LTTB, RDP, uniform sampling, extrema selection

## **📊 AGGREGATORS** (Compute Statistics)
- **Purpose:** Data summarization, trend extraction, compression
- **Output Length:** Configurable (10 → 5-9 typically)  
- **Output Type:** TRANSFORMED (computed statistics)
- **Examples:** Bin averaging, adaptive segmentation

This classification ensures that:
- **Transformers** = Signal processing that computes new values
- **Reducers** = Data selection that picks existing values  
- **Aggregators** = Statistical computation that creates summary values