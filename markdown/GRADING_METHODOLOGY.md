# Grading Methodology

## Why We Grade

### Problem: Multi-Dimensional Complexity
Evaluating smoothing algorithms involves:
- **80 datasets** with diverse characteristics (stock prices, climate data, EEG signals, etc.)
- **19 algorithms** with different approaches (filters, downsamplers, aggregators)
- **23 feature preservation metrics** across 5 categories (level, shape, derivative, frequency, statistics)

This creates a **35,880-dimensional problem space** (80 × 19 × 23) that is impossible to interpret directly.

### Solution: Hierarchical Grading System
We grade to **compress complexity** while preserving interpretability:

1. **FC Scores → Ratings** (Dataset-specific quartiles)
   - 35,880 continuous FC scores → 4 discrete ratings (Excellent/Good/Fair/Poor)
   - Enables fair comparison across datasets with different difficulty levels

2. **Ratings → Letter Grades** (Percentage-based thresholds)
   - Distribution of ratings → Single letter grade (A-F)
   - Summarizes performance while maintaining nuance

3. **Letter Grades → GPA** (Numeric ranking)
   - A/B/C/D/F → 4.0/3.0/2.0/1.0/0.0
   - Enables statistical analysis (mean, variance, ranking)

### Research Goals Enabled by Grading
- **Algorithm Selection**: Identify top performers for specific datasets or features
- **Performance Comparison**: Rank algorithms objectively across diverse conditions
- **Pattern Discovery**: Reveal which algorithms excel at which feature categories
- **Consistency Analysis**: Measure variance in grades to identify data-dependent vs. consistent algorithms
- **Visual Communication**: Create interpretable heatmaps for publication

## How We Grade

### Step 1: FC Score Calculation
**Input**: Original time series + Simplified time series  
**Process**: Feature extraction + preservation metrics (see `FEATURES_AND_METRICS.md`)  
**Output**: FC score (0-100) for each Dataset × Algorithm × Metric combination

**Note**: FC scores are already computed and stored in `plots/{dataset}/ranking/fc_scores_all.csv`

### Step 2: Rating Assignment (Dataset-Specific Quartiles)

**Why Dataset-Specific?**
Different datasets have different "difficulty levels":
- Stock prices are easier to smooth (high median FC scores)
- EEG signals are harder to smooth (low median FC scores)

Using global thresholds would unfairly penalize algorithms on hard datasets or inflate scores on easy datasets.

**Process:**
For each dataset, compute quartiles (Q1, Q2, Q3) of all FC scores across algorithms and metrics:

```python
def get_rating(row):
    dataset = row['dataset']
    fc_score = row['fc_score']
    
    q = dataset_quartiles[dataset]
    
    if fc_score > q['q75']:        # Top 25%
        return 'excellent'
    elif fc_score > q['q50']:      # 50th-75th percentile
        return 'good'
    elif fc_score > q['q25']:      # 25th-50th percentile
        return 'fair'
    else:                          # Bottom 25%
        return 'poor'
```

**Output**: 35,880 ratings (one per Dataset × Algorithm × Metric)

**Quartile File**: `plots/dataset_fc_summary.csv` contains Q1/Q2/Q3 for each dataset

### Step 3: Letter Grade Assignment

**Two Grading Modes:**

#### Mode 1: Per-Metric Grades
**Scope**: Each Dataset × Algorithm × Metric combination  
**Input**: Ratings for that specific metric only (1 rating per level = 1 data point? No, 100 levels)  
**Output**: 34,960 grades (80 datasets × 19 algorithms × 23 metrics)  

**Wait, how do we get a distribution from a single metric?**
- Each algorithm has **100 precomputed smoothing levels** (see `precomputed_outputs.json`)
- For each level, we compute FC score → rating
- For a given Dataset × Algorithm × Metric: 100 ratings (one per smoothing level)
- Grade based on distribution of these 100 ratings

**Grading Scale:**
```python
def assign_grade(rating_percentages):
    excellent = rating_percentages['excellent']
    good = rating_percentages['good']
    combined = excellent + good
    
    if excellent > 40 or combined > 70:
        return 'A'  # Dominantly excellent or overwhelming positive
    elif combined > 50:
        return 'B'  # Majority positive
    elif combined > 30:
        return 'C'  # Plurality positive
    elif combined > 15:
        return 'D'  # Some positive performance
    else:
        return 'F'  # Predominantly poor
```

**Rationale:**
- **A grade**: Requires either very high excellence (>40%) OR very high combined positive (>70%)
- **F grade**: Almost all levels perform poorly (<15% excellent+good)
- Grades reflect **consistency across smoothing levels**, not single best/worst case

**File**: `plots/fc_visualizations/dataset_algorithm_metric_grades.csv`

#### Mode 2: Overall Grades
**Scope**: Each Dataset × Algorithm combination (averaged across all 23 metrics)  
**Input**: Ratings across ALL metrics and ALL smoothing levels (100 levels × 23 metrics = 2,300 ratings)  
**Output**: 1,520 grades (80 datasets × 19 algorithms)  

**Same grading scale as Mode 1**, but aggregated across all features.

**Purpose**: 
- Per-metric grades answer: "How well does algorithm X preserve feature Y on dataset Z?"
- Overall grades answer: "How well does algorithm X perform on dataset Z overall?"

**File**: `plots/fc_visualizations/dataset_algorithm_grades.csv`

### Step 4: GPA Calculation

**Numeric Conversion:**
- A = 4.0
- B = 3.0
- C = 2.0
- D = 1.0
- F = 0.0

**Usage:**
- **Ranking**: Sort algorithms by mean GPA
- **Category Analysis**: Compare algorithm types (Transformers vs. Reducers)
- **Variance Analysis**: Measure consistency across datasets (see `VARIANCE_INTERPRETATION.md`)

## Grading Scale Rationale

### Why These Thresholds (40%, 70%, 50%, 30%, 15%)?

**A Grade (Excellent > 40% OR Combined > 70%)**
- Two paths to excellence:
  - **Path 1**: More than 40% of smoothing levels are "excellent" (top quartile performance)
  - **Path 2**: More than 70% of levels are "excellent" or "good" (consistently strong)
- Ensures A's are reserved for truly outstanding performance

**B Grade (Combined > 50%)**
- Majority of smoothing levels perform well (above median)
- Solid, reliable performance

**C Grade (Combined > 30%)**
- Plurality of levels are acceptable
- Mixed performance, some strengths

**D Grade (Combined > 15%)**
- Minimal competence
- Mostly poor performance with occasional bright spots

**F Grade (Combined ≤ 15%)**
- Almost no smoothing levels perform acceptably
- Fundamentally unsuitable for this dataset/metric

### Design Principles
1. **Non-linear thresholds**: Harder to get A than to avoid F (excellence requires consistency)
2. **Dual criteria for A**: Recognizes both peak performance and broad reliability
3. **Percentage-based**: Independent of number of smoothing levels or datasets
4. **Interpretable**: Maps to familiar academic grading intuitions

## What Grades Mean

### For Algorithm Selection
- **A/B grades**: Safe choices for this dataset/metric
- **C grades**: Acceptable, but investigate why performance is mixed
- **D/F grades**: Avoid unless you understand the failure mode

### For Research Analysis
- **High variance in grades** (across datasets): Algorithm is data-dependent
- **Low variance in grades**: Algorithm has consistent behavior (good or bad)
- **High mean + high variance**: Algorithm adapts well to certain data types
- **Low mean + low variance**: Algorithm consistently performs poorly

### For Visualization
- **Heatmaps**: Letter grades create discrete, scannable patterns
- **Color schemes**: 
  - Greyscale for publication
  - Colored (green=good, red=bad) for presentations
- **Patterns reveal**: Which datasets are hard, which algorithms are specialists vs. generalists

## Implementation Details

### File Structure
```
grade_algorithms.py (541 lines)
├── load_detailed_fc_scores()           # Load all 35,880 FC scores
├── categorize_fc_scores()              # Apply quartile-based ratings
├── compute_grade_per_dataset_algorithm_metric()  # Mode 1: Per-metric grades
├── compute_grade_per_dataset_algorithm()         # Mode 2: Overall grades
├── create_grade_heatmap()              # Greyscale visualization
├── create_grade_heatmap_colored()      # Colored visualization
└── create_metric_heatmaps()            # 23 per-metric heatmaps × 2 versions
```

### Data Flow
```
fc_scores_all.csv (per dataset)
    ↓
Combined DataFrame (35,880 rows)
    ↓
Rated DataFrame (35,880 rows with 'rating' column)
    ↓
Graded DataFrames:
    - Per-metric: 34,960 grades (80 × 19 × 23)
    - Overall: 1,520 grades (80 × 19)
    ↓
Visualizations:
    - 2 overall heatmaps (greyscale + colored)
    - 46 per-metric heatmaps (23 × 2)
    - 1 grade distribution chart
```

### Outputs
**CSV Files:**
- `dataset_algorithm_grades.csv` - Overall grades (1,520 rows)
- `dataset_algorithm_metric_grades.csv` - Per-metric grades (34,960 rows)

**Visualizations:**
- `algorithm_grades_by_dataset.svg/png` (greyscale + colored)
- `by_metric/{metric_name}_greyscale.svg/png` (23 metrics)
- `by_metric/{metric_name}_colored.svg/png` (23 metrics)
- `algorithm_grade_distribution.svg/png`

## Common Questions

### Q: Why not use raw FC scores instead of grades?
**A**: FC scores are continuous (0-100) and dataset-dependent. Grades provide:
- Discrete categories for pattern recognition
- Dataset-independent interpretation
- Easier visual communication (heatmap readability)

### Q: Why dataset-specific quartiles instead of global thresholds?
**A**: Dataset difficulty varies dramatically:
- **Easy dataset**: Median FC = 95 → Global "excellent" threshold would give everyone A's
- **Hard dataset**: Median FC = 40 → Global thresholds would give everyone F's
- **Quartiles**: Ensure ratings reflect relative performance within dataset context

### Q: Why 100 smoothing levels per algorithm?
**A**: To capture performance across the full parameter range:
- Too few levels → Miss optimal smoothing strength
- 100 levels → Dense enough to see performance curve (from under-smoothing to over-smoothing)
- Grades aggregate across levels → Measure robustness to parameter choice

### Q: Can an algorithm get different grades on different datasets?
**A**: Absolutely! This is intentional:
- **gaussian_filter** might get A on stock prices, F on EEG signals
- Reveals algorithm specialization and data-dependency
- See `VARIANCE_INTERPRETATION.md` for analysis of grade consistency

### Q: What if an algorithm gets A on one metric but F on another?
**A**: This is visible in per-metric grades:
- **Overall grade** (Mode 2) averages across all metrics → Shows general-purpose performance
- **Per-metric grades** (Mode 1) → Reveals which features are preserved well
- Example: Downsamplers often get A on trend, F on extrema

### Q: How do you handle missing data or failures?
**A**: 
- Algorithms that fail to run on a dataset are excluded from quartile calculation
- Missing FC scores don't contribute to rating distributions
- Grade reflects performance on successfully computed smoothing levels only

## Related Documentation
- `FEATURES_AND_METRICS.md` - Details on FC score calculation
- `VARIANCE_INTERPRETATION.md` - How to interpret grade variance across datasets
- `ANALYSIS_RESULTS_GUIDE.md` - Summary of grading results and key findings
- `precompute_100_levels.py` - How 100 smoothing levels are generated
