# Algorithm Ranking Methodology

## Objective

Rank time series simplification algorithms by their **efficiency**: how much visual feature preservation they achieve per unit of perceptual complexity (PAE).

## The Feature-Complexity (FC) Score

### Formula

For each algorithm-metric-level combination:

$$\text{FC Score} = z_{\text{feature}} - z_{\text{PAE}}$$

Where:
- $z_{\text{feature}} = \frac{\text{feature} - \mu_{\text{feature}}}{\sigma_{\text{feature}}}$ (standardized feature preservation)
- $z_{\text{PAE}} = \frac{\text{PAE} - \mu_{\text{PAE}}}{\sigma_{\text{PAE}}}$ (standardized perceptual complexity)

### Interpretation

- **First term** ($z_{\text{feature}}$): How much more feature preservation compared to other algorithms (positive = better)
- **Second term** ($-z_{\text{PAE}}$): How much less perceptual complexity compared to others (negative = better, so we subtract)
- **High FC Score**: High feature preservation with low PAE cost = efficient
- **Low FC Score**: Low feature preservation or high PAE cost = inefficient

### Error Metrics Adjustment

For error-based metrics (`level_l1`, `level_linf`, `extrema_delta`, `extrema_bottleneck`, `extrema_wasserstein`):
- Raw metric values are errors (higher = worse preservation)
- We negate the z-score: $\text{FC Score} = -z_{\text{error}} - z_{\text{PAE}}$
- This ensures consistent interpretation across all metrics

### Algorithm Ranking

**Per-metric ranking**: Sort by mean FC score across 100 smoothing levels (descending)

$$\text{Rank}_{\text{metric}} = \text{argsort}\left(-\frac{1}{100}\sum_{i=1}^{100} \text{FC Score}_i\right)$$

**Why this works**:
1. ✅ **Scale-invariant**: Z-scores normalize different feature scales
2. ✅ **Balanced**: Equal weight to feature preservation and PAE
3. ✅ **Interpretable**: Units of standard deviation from mean
4. ✅ **Principled**: Standard multi-objective optimization approach
5. ✅ **No arbitrary choices**: No regression lines, distance metrics, or hand-tuned weights

## Alternatives Considered (and why rejected)

### ❌ Regression-based distance
- **Problem**: Assumes linear relationship between PAE and features
- **Problem**: Distance to line is arbitrary (depends on line slope)
- **Problem**: Not interpretable across different metrics

### ❌ Simple ratio (Feature/PAE)
- **Problem**: Unstable when PAE ≈ 0
- **Problem**: No account for variability across algorithms
- **Problem**: Not comparable across datasets

### ❌ MinMax normalization
- **Problem**: Sensitive to outliers
- **Problem**: Not robust to scale differences
- **Problem**: No probabilistic interpretation

## Visualization Strategy

### Z-Score Scatter Plots
- **X-axis**: PAE z-score (standardized complexity)
- **Y-axis**: Feature z-score (standardized preservation)
- **Diagonal lines**: Iso-FC contours (same FC score)
- **Interpretation**: Upper-left quadrant = ideal (low PAE, high feature)

### Trajectory Plots (Recommended Enhancement)
Connect all 100 levels per algorithm with lines to show:
- **Smoothing progression**: How trade-off changes as parameter increases
- **Efficiency patterns**: Steep upward = good, flat = wasteful
- **Consistency**: Smooth curves = predictable behavior

### Pareto Frontier (Alternative View)
Identify non-dominated algorithms:
- No other algorithm has both lower PAE AND higher feature preservation
- Visualizes optimal trade-off set
- Useful for decision-making when selecting algorithms

## Implementation

See `generate_vegalite_plots.py`:
- Lines 450-462: FC score calculation
- Lines 464-476: Algorithm aggregation
- Lines 225-330: Z-score scatter plot generation
- Lines 124-220: Ranking bar chart generation

## References

- Multi-objective optimization: Deb, K. (2001). *Multi-Objective Optimization using Evolutionary Algorithms*
- Z-score standardization: Standard statistical practice
- Perceptual metrics: Approximate Entropy (ApEn) for time series complexity
