# Feature-Complexity (FC) Score Methodology

## Overview

The **Feature-Complexity (FC) Score** is a composite metric that quantifies the trade-off between **feature preservation quality** and **visual complexity** when simplifying time series data. It enables ranking of smoothing/downsampling algorithms based on how well they preserve important visual features while minimizing perceptual clutter.

**Key Principle**: Higher FC scores indicate algorithms that preserve features well while introducing minimal complexity.

---

## Mathematical Definition

### FC Score Formula

```
FC Score = Preservation_z - PAE_z
```

Where:
- **Preservation_z**: Z-normalized feature preservation (higher is better)
- **PAE_z**: Z-normalized Pixel Approximate Entropy (lower is better)

### Why This Works

1. **Preservation_z > 0**: Algorithm preserves feature better than average
2. **PAE_z < 0**: Algorithm introduces less complexity than average
3. **Combined**: `Preservation_z - PAE_z` rewards both goals
   - High preservation + low complexity → **High FC score**
   - Low preservation + high complexity → **Low FC score**

---

## Step-by-Step Computation

### Step 1: Z-Normalization of PAE

**Pixel Approximate Entropy (PAE)** measures visual complexity of the simplified time series. Lower PAE = simpler, smoother visualization.

```python
# For all smoothing levels of all algorithms on a dataset
pae_mean = df['pae'].mean()
pae_std = df['pae'].std()

pae_z = (pae - pae_mean) / pae_std
```

**Interpretation**:
- `pae_z = 0`: Average complexity
- `pae_z < 0`: **Simpler than average** (good)
- `pae_z > 0`: More complex than average (bad)

---

### Step 2: Z-Normalization of Feature Metric

Feature preservation metrics measure how well a specific visual feature is preserved. In our framework, **all metrics are errors** (lower is better):

- `level_l1`: L₁ error in point values
- `slope_l1`: L₁ error in local slopes
- `extrema_bottleneck`: Bottleneck distance for peaks/valleys
- `curvature_linf`: L∞ error in curvature
- etc.

```python
# For a specific metric (e.g., extrema_bottleneck)
metric_mean = df['metric_value'].mean()
metric_std = df['metric_value'].std()

metric_z = (metric_value - metric_mean) / metric_std
```

**Interpretation**:
- `metric_z = 0`: Average error
- `metric_z < 0`: **Lower error than average** (good)
- `metric_z > 0`: Higher error than average (bad)

---

### Step 3: Convert Error to Preservation

Since metrics are errors (lower is better), we flip the sign to get preservation (higher is better):

```python
preservation_z = -metric_z
```

**Interpretation**:
- `preservation_z > 0`: **Better preservation than average**
- `preservation_z < 0`: Worse preservation than average
- `preservation_z = 2.0`: Preserves feature **2 standard deviations better** than average

---

### Step 4: Compute FC Score

Combine preservation and complexity:

```python
fc_score = preservation_z - pae_z
```

**Interpretation**:
- **High FC score** (e.g., +3.0): Great preservation, low complexity → **Winner**
- **Medium FC score** (e.g., 0.0): Balanced trade-off
- **Low FC score** (e.g., -2.0): Poor preservation or high complexity → **Loser**

---

## Example Calculation

### Sample Data for `extrema_bottleneck` on `stock_aapl_price`

| Algorithm | PAE | Extrema Bottleneck | PAE_z | Metric_z | Preservation_z | **FC Score** |
|-----------|-----|-------------------|-------|----------|----------------|--------------|
| Gaussian  | 0.05 | 0.02 | -1.2 | -1.5 | **+1.5** | **+2.7** ✅ |
| LTTB      | 0.08 | 0.03 | +0.5 | -0.8 | **+0.8** | **+0.3** |
| M4        | 0.12 | 0.05 | +1.8 | +0.3 | **-0.3** | **-2.1** ❌ |

**Analysis**:
1. **Gaussian Filter**: Low PAE (smooth), low error (good preservation) → **High FC score** = Best
2. **LTTB**: Medium PAE, medium error → **Medium FC score** = OK
3. **M4**: High PAE (complex), high error (poor preservation) → **Low FC score** = Worst

---

## Aggregation Across Smoothing Levels

Each algorithm has ~100 smoothing levels (e.g., Gaussian with σ from 0.01 to 10). For each level, we compute an FC score. Then:

```python
# Aggregate FC scores for each algorithm
mean_fc_score = df.groupby('algorithm')['fc_score'].mean()
std_fc_score = df.groupby('algorithm')['fc_score'].std()
```

**Why aggregate?**
- Smoothing levels vary in aggressiveness (light smoothing vs heavy)
- Mean FC captures **average performance across all parameter settings**
- Std FC shows **consistency** (low std = reliable across settings)

---

## Ranking Algorithms

Algorithms are sorted by `mean_fc_score` in **descending order**:

```python
ranking = summary.sort_values('mean_fc_score', ascending=False)
ranking['rank'] = range(1, len(ranking) + 1)
```

**Top-ranked algorithm**: Highest mean FC score = Best feature preservation with lowest complexity

---

## Visualization: FC Score Plots

### 1. Z-Score Scatter Plot (with FC Contours)

- **X-axis**: PAE_z (complexity)
- **Y-axis**: Preservation_z (quality)
- **Diagonal lines**: Iso-FC contours (FC = 0, FC = 1, FC = 2, etc.)
- **Points**: Each smoothing level colored by algorithm

**Interpretation**:
- **Top-left quadrant**: Low complexity, high preservation → **Ideal**
- **Bottom-right quadrant**: High complexity, low preservation → **Avoid**
- Points farther from origin along FC=constant lines are better

### 2. Ranking Bar Chart

- **X-axis**: Mean FC score
- **Y-axis**: Algorithms (sorted by rank)
- **Error bars**: ±1 standard deviation
- **Colors**: Algorithm-specific color scheme

**Interpretation**:
- Longer bars to the right = better
- Small error bars = consistent performance
- Top algorithms have highest mean FC scores

---

## FC Score Properties

### Desirable Properties

1. **Scale-invariant**: Z-normalization removes units
2. **Interpretable**: FC = 2 means "2 standard deviations better than average"
3. **Balanced**: Equally weighs preservation and complexity
4. **Comparative**: Enables fair ranking across algorithms

### Limitations

1. **Metric-specific**: Different FC score for each feature metric (e.g., extrema vs slope)
2. **Dataset-specific**: Rankings can vary across datasets
3. **Assumes normality**: Z-scores work best when distributions are roughly Gaussian
4. **Equal weighting**: Treats preservation and complexity as equally important (could adjust with weights)

---

## Use Cases

### 1. Algorithm Selection for a Specific Feature

**Goal**: Preserve extrema (peaks/valleys) on stock price data

**Steps**:
1. Compute FC scores for `extrema_bottleneck` metric
2. Rank algorithms by mean FC score
3. Choose top-ranked algorithm (e.g., Gaussian Filter)

### 2. Multi-Metric Ranking

**Goal**: Find best all-around algorithm across all features

**Steps**:
1. Compute FC scores for all 23 metrics
2. Average ranks across metrics
3. Algorithm with lowest average rank = best overall

### 3. Dataset-Type Comparison

**Goal**: Find best algorithm for climate data (seasonal patterns)

**Steps**:
1. Aggregate FC scores across all climate datasets
2. Rank by mean FC score
3. Check if periodic-preserving algorithms (e.g., Savitzky-Golay) rank higher

---

## Implementation in `generate_vegalite_plots.py`

### Key Code Sections

```python
# Step 1: Load all precomputed levels
df = load_precomputed_data(dataset_name)  
# Returns: algorithm, level, pae, metric_name, metric_value

# Step 2: Filter for specific metric
metric_df = df[df['full_metric_name'] == 'extrema_bottleneck']

# Step 3: Z-normalize PAE
pae_mean = metric_df['pae'].mean()
pae_std = metric_df['pae'].std()
metric_df['pae_z'] = (metric_df['pae'] - pae_mean) / pae_std

# Step 4: Z-normalize metric (error)
metric_mean = metric_df['metric_value'].mean()
metric_std = metric_df['metric_value'].std()
metric_df['metric_z'] = (metric_df['metric_value'] - metric_mean) / metric_std

# Step 5: Convert error to preservation
metric_df['preservation_z'] = -metric_df['metric_z']

# Step 6: Compute FC score
metric_df['fc_score'] = metric_df['preservation_z'] - metric_df['pae_z']

# Step 7: Aggregate by algorithm
summary = metric_df.groupby('algorithm').agg({
    'fc_score': ['mean', 'std']
}).reset_index()

# Step 8: Rank
summary = summary.sort_values('mean_fc_score', ascending=False)
summary['rank'] = range(1, len(summary) + 1)
```

---

## Output Files

### Per-Dataset Rankings

For each dataset (e.g., `stock_aapl_price`), the script generates:

1. **`plots/stock_aapl_price/rankings_summary.csv`**
   - Long format: `algorithm, metric, fc_score, rank`
   - One row per algorithm-metric pair

2. **`plots/stock_aapl_price/rankings_wide.csv`**
   - Wide format: Algorithms as rows, metrics as columns
   - Values = FC scores

3. **`plots/stock_aapl_price/rankings_ranked.csv`**
   - Wide format: Algorithms as rows, metrics as columns
   - Values = **Ranks** (1 = best, higher = worse)

4. **SVG plots** (46 files for standard mode, 69 for breakdown mode)
   - `{metric}_zscore_fc.svg`: Z-score scatter with FC contours
   - `{metric}_ranking.svg`: Bar chart ranking
   - `{metric}_raw.svg`: Raw PAE vs metric scatter (breakdown mode only)

### Cross-Dataset Aggregation

`rank_algorithms_by_dataset_type.py` reads the `rankings_ranked.csv` files and aggregates across dataset types:

```python
# Load rankings for all stock datasets
all_rankings = []
for dataset in ['stock_aapl_price', 'stock_amzn_price', ...]:
    df = pd.read_csv(f'plots/{dataset}/rankings_ranked.csv')
    all_rankings.append(df)

combined = pd.concat(all_rankings)

# Average ranks across datasets
avg_rank = combined.groupby('algorithm')['rank'].mean()
```

**Output**: `plots/dataset_type_rankings/{type}_ranking.svg` and `.csv`

---

## Interpretation Guide

### What Makes a Good FC Score?

| FC Score Range | Interpretation | Action |
|---------------|----------------|---------|
| **FC > +2.0** | Excellent: 2+ std dev better than average | ✅ **Use this algorithm** |
| **+1.0 to +2.0** | Good: Better than average | ✅ Safe choice |
| **-1.0 to +1.0** | Average: Close to mean performance | ⚠️ Consider alternatives |
| **-2.0 to -1.0** | Below average | ❌ Avoid unless specific need |
| **FC < -2.0** | Poor: Much worse than average | ❌ Do not use |

### Reading Z-Score Scatter Plots

**Quadrants**:
- **Top-left** (low PAE_z, high preservation_z): **IDEAL** - Simple & accurate
- **Top-right** (high PAE_z, high preservation_z): Accurate but complex
- **Bottom-left** (low PAE_z, low preservation_z): Simple but inaccurate
- **Bottom-right** (high PAE_z, low preservation_z): **WORST** - Complex & inaccurate

**FC Contour Lines**:
- Points on the same diagonal line have equal FC score
- Move perpendicular to lines (toward top-left) to improve FC

---

## Comparison to Alternative Metrics

### Why Not Just Use Preservation Error?

**Problem**: Ignores visual complexity
- An algorithm could preserve features perfectly but create a jagged, unreadable chart
- PAE captures this complexity

**FC Score advantage**: Balances accuracy AND simplicity

### Why Not Just Use PAE?

**Problem**: Ignores feature loss
- Heavy smoothing reduces PAE but destroys important patterns
- Feature metrics capture this loss

**FC Score advantage**: Balances simplicity AND accuracy

### Why Not Use Weighted Sum?

**Alternative**: `FC = α*Preservation + β*PAE`

**Our choice** (α=1, β=-1):
- Symmetric weighting
- Simpler to interpret (no tuning parameters)
- Z-normalization makes metrics comparable

**Could customize**: Adjust α/β for applications prioritizing preservation (α>1) or simplicity (β<-1)

---

## Future Extensions

### 1. Multi-Metric FC Score
Aggregate across all features for an overall ranking:
```python
overall_fc = df.groupby(['algorithm', 'level'])[['fc_score']].mean()
```

### 2. Weighted FC Score
Prioritize certain features (e.g., extrema more important than noise):
```python
weights = {'extrema': 2.0, 'slope': 1.5, 'noise': 0.5}
weighted_fc = sum(w * fc_scores[metric] for metric, w in weights.items())
```

### 3. Pareto Frontier
Find algorithms on the Pareto front (can't improve one metric without harming another)

### 4. User Study Validation
Correlate FC scores with human perception of "best simplified chart"

---

## References

### Related Concepts

1. **Z-score normalization**: Standard statistical technique for comparing different scales
2. **Pareto efficiency**: Multi-objective optimization (preservation vs complexity)
3. **Approximate Entropy**: Pincus (1991) - measures regularity in time series
4. **Visual complexity metrics**: Rosenholtz et al. (2007) - perceptual clutter

### Implementation Details

- **Data source**: `precomputed/{dataset}/{algorithm}_level_{n}.json`
- **Metrics**: 23 feature preservation metrics (see `FEATURES_AND_METRICS.md`)
- **Algorithms**: 19 smoothing/downsampling methods (see `server/algorithms/`)
- **Visualization**: Vega-Lite via Altair (declarative grammar)

---

## Summary

The **Feature-Complexity (FC) Score** provides a **principled, quantitative method** for ranking time series simplification algorithms. By combining:

1. **Feature Preservation** (how well visual patterns are retained)
2. **Visual Complexity** (how cluttered the simplified chart appears)

We can identify algorithms that achieve the **optimal trade-off**: preserving important features while creating clean, readable visualizations.

**Key takeaway**: Higher FC score = Better algorithm for that specific feature on that dataset.
