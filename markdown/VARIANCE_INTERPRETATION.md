# Variance Interpretation Rationale

## What Does Variance Measure?

Variance measures **consistency of algorithm behavior across datasets**, not performance quality.

- **Low variance** = Algorithm produces similar grades across all 80 datasets (could be consistently good OR consistently poor)
- **High variance** = Algorithm produces different grades depending on dataset characteristics (data-dependent behavior)

**Important**: Variance is independent of grade quality. An algorithm can have low variance because it consistently gets F's, or high variance because it gets A's on some datasets and F's on others.

## Grade Scale Context

Grades are converted to numeric values for variance calculation:
- A = 4.0
- B = 3.0
- C = 2.0
- D = 1.0
- F = 0.0

Scale range: 0-4 (fixed)

## Variance Thresholds

We use **absolute thresholds** based on the fixed 0-4 grade scale:

### Threshold 1: Variance < 0.5 → **Consistent**
- Standard deviation: √0.5 = 0.71
- **Interpretation**: Grades vary by less than ±0.7 points across datasets
- **Example**: Algorithm consistently gets B's and A's (3.0-4.0 range), or consistently gets F's and D's (0.0-1.0 range)
- **Meaning**: Algorithm behavior does not depend on dataset characteristics

### Threshold 2: Variance 0.5-1.5 → **Moderately Data-Dependent**
- Standard deviation: 0.71-1.22
- **Interpretation**: Grades vary by ±0.7 to ±1.2 points (roughly 1-2 letter grades)
- **Example**: Algorithm ranges from B to D (1.0-3.0 range)
- **Meaning**: Algorithm adapts somewhat to dataset characteristics

### Threshold 3: Variance > 1.5 → **Highly Data-Dependent**
- Standard deviation: > 1.22
- **Interpretation**: Grades vary by more than ±1.2 points (spans 2+ letter grades)
- **Example**: Algorithm gets A's on some datasets, F's on others (wide 0.0-4.0 range)
- **Meaning**: Algorithm performance strongly depends on dataset characteristics

## Why These Thresholds?

1. **Tied to Letter Grade Variation**: Each threshold corresponds to meaningful variation in letter grades
   - < 0.5: Within 1 letter grade
   - 0.5-1.5: Within 1-2 letter grades
   - \> 1.5: Spans 2+ letter grades

2. **Fixed Scale**: Since grades are on a 0-4 scale, variance has absolute meaning (unlike unbounded metrics where relative scaling matters)

3. **Maximum Possible Variance**: Theoretical max ≈ 4.0 (half A's, half F's). Our observed max is 3.949, confirming we see near-maximum variation.

4. **Interpretable**: Researchers can directly understand "varies by less than 1 letter grade" vs. "varies by 2+ letter grades"

## Alternative Approaches Considered

### ❌ Coefficient of Variation (CV = std/mean)
**Rejected** because:
- Breaks when mean is near zero (common for poorly-performing algorithms)
- Adds unnecessary normalization to already-normalized 0-4 scale
- Makes interpretation harder without adding value

### ✓ Percentile-Based Thresholds
**Could work** but less interpretable:
- 25th percentile, median, 75th percentile from our 437 observations
- Would be data-driven but harder to explain ("why is this percentile meaningful?")
- Our observed distribution: Median = 1.124 (close to our 1.5 threshold anyway)

### ✓ Practical Range Interpretation
**Similar to our approach**:
- Variance 0-1.0 = Low (< 25% of max)
- Variance 1.0-2.5 = Medium (25-62% of max)
- Variance > 2.5 = High (> 62% of max)
- Less tied to letter grade meaning than our thresholds

## Observed Distribution

From 437 Algorithm × Metric combinations:
- **Consistent** (< 0.5): 51 pairs (11.7%)
- **Moderately Data-Dependent** (0.5-1.5): 243 pairs (55.6%)
- **Highly Data-Dependent** (> 1.5): 143 pairs (32.7%)

Most algorithms show moderate to high data-dependency, meaning their performance varies significantly across dataset types.

## Key Insights

1. **Low variance ≠ good algorithm**: rdp_downsample has lowest variance (0.012-0.154) but performs poorly overall (consistently gets low grades)

2. **High variance ≠ bad algorithm**: Some high-performing algorithms (like min/max/median filters) show high variance because they excel on certain dataset types but struggle on others

3. **Variance reveals adaptation**: Algorithms with high variance are data-dependent - they may be excellent choices for specific dataset characteristics but require careful selection

## Usage

When selecting an algorithm:
1. Check **mean grade** (from grade_algorithms.py) for overall performance
2. Check **variance** (from this analysis) for consistency

**Ideal scenarios**:
- **Low variance + High mean** = Reliable, consistently good
- **High variance + High mean** = Potentially excellent, but dataset-dependent (check if dataset matches algorithm strengths)
- **Low variance + Low mean** = Consistently poor, avoid
- **High variance + Low mean** = Unpredictable and often poor, avoid
