# Analysis Results Guide

## Overview
This document summarizes the FC (Feature Complexity) score analysis framework and key findings from evaluating 19 smoothing algorithms across 80 datasets and 23 feature preservation metrics.

## Data Structure

### Datasets (80 total)
- **Stock Price** (10): AAPL, AMZN, BAC, GOOG, INTC, JPM, etc.
- **Stock Volume** (10): Same tickers as price
- **Climate AWND** (6): ATL, JFK, LAX, ORD, SEA, SLC
- **Climate PRCP** (6): Same locations
- **Climate TMAX** (6): Same locations
- **EEG Signals** (18): 6 channels × 3 lengths (500, 2500, 10000 points)
- **Astronomy** (5): Light curves
- **Chicago Homicide** (2): Monthly, weekly
- **Flights** (3): Daily, weekly, monthly
- **NZ Tourism** (2): Monthly, annually
- **Unemployment** (12): Various series

### Algorithms (19 total)

**Transformers (8)** - Preserve data length, modify values:
- `gaussian_filter`, `mean_filter`, `median_filter`, `savitzky_golay_filter`
- `butterworth_filter`, `chebyshev_filter`, `elliptical_filter`, `fft_cutoff_filter`

**Reducers (4)** - Downsample to fewer points:
- `lttb_downsample`, `m4_downsample`, `minmaxlttb_downsample`, `uniform_subsample`

**Aggregators (2)** - Adaptive binning:
- `asap_aggregator`, `bin_average_aggregator`

**Other (5)** - Specialized algorithms:
- `douglas_peucker_simplify`, `max_filter`, `min_filter`, `persistence_smooth`, `visvalingam_whyatt_simplify`

### Metrics (23 total)

**Level (2):**
- `level_l1`, `level_linf`

**Shape - Extrema (2):**
- `extrema_bottleneck`, `extrema_wasserstein`

**Shape - Regimes (1):**
- `regimes_delta`

**Shape - Change Points (1):**
- `change_points_delta`

**Shape - Spikes/Dips (2):**
- `spikes_dips_bottleneck`, `spikes_dips_wasserstein`

**Derivative - Slope (2):**
- `slope_l1`, `slope_linf`

**Derivative - Curvature (2):**
- `curvature_l1`, `curvature_linf`

**Derivative - Roughness (1):**
- `roughness_delta`

**Frequency - Trend (2):**
- `trend_l1`, `trend_linf`

**Frequency - Noise (3):**
- `noise_auc_delta`, `noise_l1`, `noise_linf`

**Frequency - Periodicity (2):**
- `periodicity_amplitude_delta`, `periodicity_num_periods_delta`

**Statistics - Mean (1):**
- `mean_delta`

**Statistics - Regression (2):**
- `regression_l1`, `regression_linf`

## Rating System

### FC Score Categorization
Uses **dataset-specific quartiles** for fair comparison:
- **Excellent**: FC score > 75th percentile
- **Good**: 50th < FC score ≤ 75th percentile
- **Fair**: 25th < FC score ≤ 50th percentile
- **Poor**: FC score ≤ 25th percentile

### Letter Grading Scale
Aggregates ratings across metrics into single grade:
- **A**: Excellent% > 40% OR (Excellent% + Good%) > 70%
- **B**: (Excellent% + Good%) > 50%
- **C**: (Excellent% + Good%) > 30%
- **D**: (Excellent% + Good%) > 15%
- **F**: Otherwise

### GPA Calculation
- A = 4.0, B = 3.0, C = 2.0, D = 1.0, F = 0.0
- Used for ranking and averaging performance

## Generated Visualizations

### Overall Performance (Averaged Across All 23 Metrics)

**Files:**
- `plots/fc_visualizations/algorithm_grades_by_dataset.svg/png` (greyscale)
- `plots/fc_visualizations/algorithm_grades_by_dataset_colored.svg/png` (colored)

**Layout:**
- 19 algorithms (rows) × 80 datasets (columns)
- Letter grades (A-F) in each cell
- Dataset names at top, algorithm names on left
- Figure size: 40×10 inches

**Color Schemes:**
- **Greyscale**: #2d2d2d (F) → #d6d6d6 (A)
- **Colored**: 
  - F: #E53935 (red)
  - D: #FF6F00 (dark orange)
  - C: #FFA726 (orange)
  - B: #66BB6A (light green)
  - A: #2E7D32 (dark green)

### Per-Metric Performance (23 Separate Heatmaps)

**Directory:** `plots/fc_visualizations/by_metric/`

**Files:** 46 total (23 metrics × 2 versions each)
- `{metric_name}_greyscale.svg/png`
- `{metric_name}_colored.svg/png`

**Layout:** Same as overall (19 algorithms × 80 datasets)

### Supporting Visualizations

**Grade Distribution:**
- `algorithm_grade_distribution.svg/png`
- Stacked bar chart showing A/B/C/D/F counts per algorithm

**Algorithm × Feature Category Heatmap:**
- `algorithm_by_category_greyscale.svg/png`
- `algorithm_by_category_colored.svg/png`
- Shows average GPA by feature category (13 categories)

## Key Findings

### Top Performing Algorithms (Overall GPA)

1. **Savitzky-Golay Filter**: 3.70 GPA (74 A's, 6 F's)
2. **Mean Filter**: 3.70 GPA (74 A's, 6 F's)
3. **Gaussian Filter**: 3.70 GPA (74 A's, 6 F's)
4. **Median Filter**: 3.66 GPA (72 A's, 1 B, 1 C, 6 F's)
5. **ASAP Aggregator**: 3.16 GPA (42 A's, 22 B's, 9 C's, 1 D, 6 F's)

### Algorithm Type Performance

**Transformers (filters):**
- Best overall: ~2.3-2.7 GPA across feature categories
- Excel at: Shape (Change Points, Regimes), Derivatives, Frequency
- GPA range: 0.59-3.07 across categories

**Aggregators:**
- Second best: ~2.2-3.2 GPA
- Strong at: Level (3.39), Frequency-Trend (3.16), Derivative-Roughness (3.04)
- Weak at: Shape features (1.18 for Regimes/Change Points)

**Reducers (downsamplers):**
- Weakest overall: 0.4-1.4 GPA
- Only decent at: Spikes/Dips (2.33), Slope (1.23)
- Struggle significantly with shape and frequency features

**Other:**
- Inconsistent: 0.59-2.82 GPA
- Max filter unexpectedly excels at Change Points and Regimes

### Feature Category Insights

**Best Performance by Category:**
- **Shape - Change Points**: Transformers excel (3.08 GPA), max_filter dominates (3.70)
- **Shape - Regimes**: Same pattern as Change Points
- **Derivatives**: All categories strong for transformers (2.32-2.57)
- **Frequency - Trend**: Transformers at 2.47, aggregators close at 3.16
- **Level**: Transformers best at 2.67

**Worst Performance by Category:**
- **Frequency - Trend**: Reducers at 1.14, "Other" at 0.59
- **Derivative - Roughness**: Reducers at 0.48
- **Shape - Change Points/Regimes**: Reducers at 0.43

### Metric Difficulty Rankings

**Top 5 Easiest Metrics to Preserve:**
1. `spikes_dips_bottleneck`: 2.55 avg GPA
2. `slope_linf`: 2.36
3. `slope_l1`: 2.29
4. `spikes_dips_wasserstein`: 2.20
5. `curvature_l1`: 2.17

**Top 5 Hardest Metrics to Preserve:**
1. `regression_l1`: 1.79 avg GPA
2. `mean_delta`: 1.78
3. `trend_linf`: 1.77
4. `regression_linf`: 1.76
5. `trend_l1`: 1.76

### Algorithm Specializations

**Significant Advantages (>0.5 GPA above average):**

**Trend Metrics** (hardest overall, avg 1.76-1.77):
- Traditional filters (Mean, Gaussian, Savitzky-Golay, Median) achieve 3.70
- **Advantage**: +1.93 to +1.94 GPA points

**Regression Metrics** (hardest overall, avg 1.76-1.79):
- Same traditional filters achieve 3.70
- **Advantage**: +1.91 to +1.94 GPA points

**Key Insight**: Filters massively outperform on statistics/frequency features where most algorithms fail.

### Top 3 Performers by Feature Category

**Derivative - Curvature:**
1. Mean Filter: 3.70
2. Gaussian Filter: 3.70
3. Savitzky-Golay: 3.66

**Derivative - Roughness:**
1. Mean Filter: 3.70
2. Gaussian Filter: 3.70
3. Savitzky-Golay: 3.70

**Derivative - Slope:**
1. Mean Filter: 3.70
2. Gaussian Filter: 3.70
3. Savitzky-Golay: 3.69

**Frequency - Noise:**
1. Mean Filter: 3.70
2. Gaussian Filter: 3.70
3. Savitzky-Golay: 3.70

**Frequency - Periodicity:**
1. Savitzky-Golay: 3.61
2. Gaussian Filter: 3.56
3. Mean Filter: 3.55

**Frequency - Trend:**
1. Mean Filter: 3.70
2. Gaussian Filter: 3.70
3. Savitzky-Golay: 3.70

**Level:**
1. Mean Filter: 3.70
2. Gaussian Filter: 3.70
3. Savitzky-Golay: 3.70

**Shape - Change Points:**
1. **Max Filter: 3.70** ⭐ (unexpected!)
2. Mean Filter: 3.59
3. Median Filter: 3.56

**Shape - Extrema:**
1. Savitzky-Golay: 3.44
2. Gaussian Filter: 3.39
3. Mean Filter: 3.38

**Shape - Regimes:**
1. **Max Filter: 3.70** ⭐ (unexpected!)
2. Mean Filter: 3.59
3. Median Filter: 3.56

**Shape - Spikes/Dips:**
1. Mean Filter: 3.56
2. Gaussian Filter: 3.56
3. Savitzky-Golay: 3.53

**Statistics - Mean:**
1. Mean Filter: 3.70
2. Gaussian Filter: 3.70
3. Savitzky-Golay: 3.70

**Statistics - Regression:**
1. Mean Filter: 3.70
2. Gaussian Filter: 3.70
3. Savitzky-Golay: 3.70

### Problematic Datasets

**6 datasets consistently receive F grades** across top algorithms (identity known to user).

## Generated Data Files

### CSV Files Location: `plots/fc_visualizations/`

**Overall Performance:**
1. `dataset_algorithm_grades.csv` - 1,520 rows (80 datasets × 19 algorithms)
   - Columns: dataset, algorithm, excellent%, good%, fair%, poor%, grade
   - Grades averaged across all 23 metrics

2. `algorithm_grade_summary.csv` - 19 rows (one per algorithm)
   - Columns: algorithm, A count, B count, C count, D count, F count, GPA
   - Sorted by GPA descending

**Per-Metric Performance:**
3. `dataset_algorithm_metric_grades.csv` - 34,960 rows (80 × 19 × 23)
   - Columns: dataset, algorithm, metric, excellent%, good%, fair%, poor%, grade
   - Grades computed per metric separately

**Feature Analysis:**
4. `algorithm_performance_by_category.csv` - 19 algorithms × 13 categories + Overall
   - Average GPA by feature category
   - Categories: Level, Shape (4 types), Derivative (3 types), Frequency (3 types), Statistics (2 types)

5. `metric_difficulty.csv` - 23 rows (one per metric)
   - Columns: metric, A count, B count, C count, D count, F count, avg_gpa
   - Shows which metrics are hardest/easiest to preserve

6. `algorithm_specializations.csv` - Variable rows
   - Columns: metric, algorithm, gpa, metric_avg, advantage
   - Lists algorithm-metric combinations where performance significantly exceeds average

7. `algorithm_type_comparison.csv` - 4 algorithm types × 13 categories
   - Rows: Transformer, Reducer, Aggregator, Other
   - Columns: Feature categories
   - Shows fundamental differences between algorithm approaches

### Per-Dataset FC Scores (in each dataset folder)

**Location:** `plots/{dataset_name}/ranking/fc_scores_all.csv`

**Structure:**
- Columns: level, algorithm, metric, fc_score
- Level: 0-99 (100 precomputed smoothing levels)
- 19 algorithms × 23 metrics × 101 levels = 44,137 rows per dataset

**Summary Statistics:**
- `plots/dataset_fc_summary.csv` - 80 rows
  - Columns: dataset, q25, q50, q75, total_data_points, excellent%, good%, fair%, poor%
  - Dataset-specific quartiles used for rating categorization

## Scripts for Analysis

### Core Grading Script
**File:** `grade_algorithms.py`

**Functions:**
- `load_detailed_fc_scores()` - Loads fc_scores_all.csv from all 80 datasets
- `categorize_fc_scores()` - Applies quartile-based rating categories
- `compute_grade_per_dataset_algorithm()` - Overall grades (averaged across metrics)
- `compute_grade_per_dataset_algorithm_metric()` - Per-metric grades
- `create_grade_heatmap()` - Greyscale overall heatmap
- `create_grade_heatmap_colored()` - Colored overall heatmap
- `create_metric_heatmaps()` - 46 per-metric heatmaps
- `create_grade_distribution_bar()` - Grade distribution bar chart
- `create_summary_table()` - Algorithm summary statistics

**Usage:** `python grade_algorithms.py`

**Output:** 7 items (5 files + 1 folder with 46 files)

### Metric Performance Analysis
**File:** `analyze_metric_performance.py`

**Functions:**
- `analyze_algorithm_by_feature_category()` - GPA by feature category
- `analyze_metric_difficulty()` - Easiest/hardest metrics
- `create_algorithm_category_heatmap()` - Algorithm × category heatmap
- `find_algorithm_specializations()` - Significant algorithm-metric advantages
- `compare_algorithm_types()` - Transformer vs Reducer vs Aggregator

**Usage:** `python analyze_metric_performance.py`

**Output:** 6 files (3 CSVs + 2 heatmaps)

### Supporting Scripts
**File:** `summarize_fc_scores.py` - Initial FC score distribution analysis
**File:** `visualize_fc_small_multiples.py` - Detailed small multiples (abandoned, too complex)
**File:** `visualize_fc_summaries.py` - Altair interactive visualizations (abandoned, needed static)

## Outstanding Research Questions

### Already Answered
✅ Which algorithms excel at specific feature types?
✅ Which metrics are hardest to preserve?
✅ Do algorithm types (transformer/reducer/aggregator) differ fundamentally?

### To Investigate
❓ **Dataset type patterns**: Do certain algorithms work better for stock data vs. climate data?
❓ **Why do downsamplers fail?**: Is it inherent to reducing point count or implementation issue?
❓ **Max filter anomaly**: Why does max_filter dominate Change Points and Regimes?
❓ **6 failing datasets**: What characteristics cause consistent failures?
❓ **Metric correlations**: Do algorithms that preserve extrema also preserve spikes/dips?
❓ **Optimal algorithm selection**: Can we predict best algorithm from dataset characteristics?
❓ **Banking aspect ratio impact**: How does visualization banking affect perceived quality?

### Potential Next Analyses

**Dataset Clustering:**
- Group datasets by FC score patterns
- Identify dataset characteristics that predict algorithm performance
- Create dataset type × algorithm type heatmap

**Metric Correlation Analysis:**
- Compute correlation matrix of metric preservation across algorithms
- Identify redundant vs. complementary metrics
- Cluster metrics by preservation patterns

**Failure Mode Analysis:**
- Deep dive into the 6 failing datasets
- Compare their characteristics vs. successful datasets
- Identify features that are fundamentally difficult

**Algorithm Recommendation System:**
- Build decision tree: dataset features → recommended algorithm
- Weight by feature importance (user-specified)
- Provide top-3 recommendations with confidence scores

**Comparative Visualization:**
- Side-by-side original vs. simplified for extreme cases (A vs. F grades)
- Show which features are lost in failed cases
- Validate that grades align with visual perception

## Visualization Guidelines

### Design Decisions
- **No legends, titles, or axis labels** - Clean for publication
- **Font size: 16pt** - Readable at paper scale
- **Dataset names at top** - Easier to scan across datasets
- **Algorithm names on left** - Standard convention
- **White gridlines** - Cell separation
- **40×10 inch figures** - Wide format for 80 datasets

### Color Palettes
**Greyscale (accessibility):**
- Best for printed papers
- Gradient from dark (#2d2d2d) to light (#d6d6d6)

**Colored (presentations):**
- Matches frontend UI colors (from MetricsBar.tsx)
- Red-orange-green gradient
- Better for slides and posters

## How to Return to This Analysis

### Quick Context Refresh
1. Review this document (ANALYSIS_RESULTS_GUIDE.md)
2. Check terminal output from last `analyze_metric_performance.py` run
3. Open `plots/fc_visualizations/algorithm_performance_by_category.csv`

### View Results
**Heatmaps:**
```powershell
# Overall performance
start plots/fc_visualizations/algorithm_grades_by_dataset_colored.png

# Feature category performance
start plots/fc_visualizations/algorithm_by_category_colored.png

# Specific metric (e.g., extrema)
start plots/fc_visualizations/by_metric/extrema_bottleneck_colored.png
```

**Data files:**
```powershell
# Summary statistics
cat plots/fc_visualizations/algorithm_grade_summary.csv

# Metric difficulty
cat plots/fc_visualizations/metric_difficulty.csv

# Specializations
cat plots/fc_visualizations/algorithm_specializations.csv
```

### Continue Analysis
**Run existing scripts:**
```powershell
python grade_algorithms.py              # Regenerate all heatmaps
python analyze_metric_performance.py    # Feature category analysis
```

**Next steps template:**
```powershell
# Create new analysis script
code analyze_dataset_types.py

# Common pattern:
# 1. Load dataset_algorithm_metric_grades.csv
# 2. Add dataset type column (extract from dataset name)
# 3. Group by dataset_type and algorithm
# 4. Generate heatmaps/tables
# 5. Save to plots/fc_visualizations/
```

## File Organization

```
plots/
├── fc_visualizations/                           # Main analysis output
│   ├── algorithm_grades_by_dataset.svg/png      # Overall greyscale
│   ├── algorithm_grades_by_dataset_colored.svg/png  # Overall colored
│   ├── algorithm_grade_distribution.svg/png     # Bar chart
│   ├── algorithm_by_category_greyscale.svg/png  # Category greyscale
│   ├── algorithm_by_category_colored.svg/png    # Category colored
│   ├── dataset_algorithm_grades.csv             # Overall grades
│   ├── dataset_algorithm_metric_grades.csv      # Per-metric grades
│   ├── algorithm_grade_summary.csv              # GPA summary
│   ├── algorithm_performance_by_category.csv    # Category breakdown
│   ├── metric_difficulty.csv                    # Metric rankings
│   ├── algorithm_specializations.csv            # Strengths
│   ├── algorithm_type_comparison.csv            # Type comparison
│   └── by_metric/                               # 46 heatmaps
│       ├── {metric}_greyscale.svg/png
│       └── {metric}_colored.svg/png
├── dataset_fc_summary.csv                       # Quartiles for all datasets
└── {dataset_name}/                              # Per-dataset folders
    └── ranking/
        └── fc_scores_all.csv                    # Raw FC scores
```

## Key Insights Summary

**Main Takeaway:** Traditional smoothing filters (Gaussian, Mean, Savitzky-Golay) dominate across nearly all feature types, with GPA 3.70. Downsamplers struggle significantly (GPA < 1.5), suggesting fundamental limitations in point reduction approaches.

**Surprising Findings:**
1. Max filter unexpectedly excels at Change Points and Regimes (3.70 GPA)
2. Hardest metrics (Trend, Regression) are where filters show biggest advantage (+1.9 GPA)
3. Aggregators outperform transformers on Level features (3.39 vs 2.67)
4. Spikes/Dips are easiest to preserve, not hardest as might be expected

**Practical Implications:**
- Use filters for general-purpose smoothing (consistent high performance)
- Avoid downsamplers unless point reduction is mandatory
- Max filter worth considering for regime detection tasks
- ASAP aggregator is best non-filter option (GPA 3.16)
