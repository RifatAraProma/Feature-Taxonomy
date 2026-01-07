# AI Coding Agent Instructions: Adaptive Smoothing Framework

## Project Overview
A research framework for evaluating time series simplification algorithms through visual feature preservation. Flask backend + React/Vega-Lite frontend with precomputed outputs for 100 smoothing levels across 80+ datasets.

## Architecture & Data Flow

### Three-Tier Algorithm Architecture
Algorithms are categorized by output characteristics (see `server/algorithms/`):

1. **Transformers** (`transformers.py`) - Preserve data length, modify values
   - Smoothers: `gaussian_filter`, `mean_filter`, `median_filter`, `savitzky_golay_filter`
   - Frequency filters: `butterworth_filter`, `chebyshev_filter`, `elliptical_filter`, `fft_cutoff_filter`
   - Return: `[y1, y2, y3, ...]` (same length as input)

2. **Reducers** (`reducers.py`) - Downsample to fewer points
   - `lttb_downsample`, `m4_downsample`, `minmaxlttb_downsample`, `uniform_subsample`
   - Return: `[(x1, y1), (x2, y2), ...]` (tuples, reduced length)

3. **Aggregators** (`aggregators.py`) - Adaptive binning/windowing
   - `asap_aggregator`, `bin_average_aggregator`
   - Return: `[(x1, y1), (x2, y2), ...]` (variable length)

**Critical**: The `extract_y_values()` helper in `app.py` handles this dual format.

### Precomputed Outputs Strategy
To enable instant slider interaction, outputs are precomputed offline:
- **File**: `precomputed_outputs.json` (~3GB, gitignored)
- **Generation**: `precompute_100_levels.py` generates 100 parameter levels per dataset/algorithm
- **Structure**: `{dataset_id: {algorithm_name: {param_name, param_values[], outputs[], pae_values[]}}}`
- **Access**: `server/precomputed_loader.py` provides lazy-loaded singleton access
- **API**: `GET /precomputed/<dataset>/<algorithm>` returns metadata + all levels

**Parameter Sampling Pattern** (from `precompute_100_levels.py`):
- Filters: Exponential scale (`sigma: 0.001 → dataLength/10`, `cutoff: 0.99 → 0.01`)
- Downsamplers: Linear scale (`output_length: dataLength → dataLength*0.05`)
- Window-based: Log scale (`window_size: 1 → dataLength/4`)

### Feature Extraction Pipeline
12 visual features computed for original AND simplified series (see `server/features/compute_features.py`):
```python
# Always compute BOTH for metrics comparison
orig_features = compute_all_features(y, FeatureConfig())
simp_features = compute_all_features(yhat, FeatureConfig())
metrics = compute_feature_preservation_metrics(orig_features, simp_features)
```

**Feature Categories** (defined in `FEATURES_AND_METRICS.md`):
- **Level**: Point values, interval averages
- **Shape**: Extrema, regimes, change points, spikes/dips
- **Derivatives**: Slope, curvature, roughness
- **Frequency**: Trend, noise, periodicity (via FFT)
- **Statistics**: Mean, regression fit

**Preservation Metrics**: Retention ratios, correlations, MAE for each feature type.

### Banking Aspect Ratio
`median_slope_aspect()` in `banking.py` computes aspect ratio for 45° banking:
```python
aspect = median(|Δy|) where Δx=1  # Clamped to (0.2, 5.0)
```
Applied to simplified series when `banking=true` in request.

## Critical Development Patterns

### Adding a New Algorithm
1. **Implement in vendor** (`server/algorithms/vendor/data_transformer_algorithms.py` or `data_reducer_algorithms.py`):
   ```python
   def my_smoother(data: list[tuple], param: float) -> list[tuple]:
       x, y = _xy_from_pairs(data)
       # ... algorithm logic ...
       return _pairs(x, y_smoothed)  # Transformers return same length
   ```

2. **Router adds it automatically** - `transformers.py`/`reducers.py` use dynamic imports:
   ```python
   CALLS = {name: fn for name in dir(vendor_module) if callable(getattr(vendor_module, name))}
   ```

3. **Add to precomputation config** in `precompute_100_levels.py`:
   ```python
   'my_smoother': {
       'param_name': 'strength',
       'param_bounds': (0.1, 10.0),
       'param_type': 'float',
       'param_direction': 'direct',  # or 'inverse' if higher param = less smoothing
       'use_logscale': True
   }
   ```

4. **Run precomputation**: `python precompute_100_levels.py` (generates outputs for all 80 datasets)

### Data Format Convention
**Input**: Always `list[tuple]` of `(x, y)` pairs in vendor algorithms
**Storage**: JSON files as `{"id": "dataset_name", "y": [...]}`  (x assumed sequential)
**API**: `server/util.py` handles discovery in `data/` subfolders (e.g., `data/stock_price/`, `data/climate_awnd/`)

### Frontend-Backend Contract
**POST /smooth** request:
```json
{
  "seriesId": "stock_aapl_price",
  "method": "gaussian_filter",
  "sliderLevel": 50,           // 0-99 index into precomputed levels
  "usePrecomputed": true,
  "returnFeatures": ["extrema", "regimes"]
}
```

**Response includes**:
- `yhat`: Simplified data as `[{t, y}, {t, y}, ...]`
- `pae`: Perceptual error (from precomputed if available)
- `metrics`: Point-wise errors + `featurePreservation` object
- `precomputedInfo`: `{paramName, paramValues[], paeValues[], numLevels}`

**Key**: `sliderLevel` is 0-based index, NOT the parameter value. Backend maps level→param.

## Development Workflows

### Running the Stack
```powershell
# Backend (Flask)
python -m venv .venv; .venv\Scripts\activate
pip install -r requirements.txt
$env:FLASK_APP="server/app.py"; flask run

# Frontend (React + Vite)
cd web; npm install; npm run dev
```

### Testing Algorithm Changes
1. Edit vendor algorithm in `server/algorithms/vendor/`
2. Test with single call: `curl -X POST http://localhost:5000/smooth -H "Content-Type: application/json" -d "{\"seriesId\":\"stock_aapl_price\",\"method\":\"my_algorithm\",\"params\":{\"my_param\":5}}"`
3. Check output format (array of y-values for transformers, array of [x,y] for reducers)
4. Re-run precomputation if satisfied: `python precompute_100_levels.py`

### Debugging Precomputed Data
**Symptom**: Slider shows incorrect outputs
**Check**:
1. `precomputed_loader.py` fuzzy matching: `print(f"Looking for: {dataset_id}, Found: {matched_key}")`
2. Parameter direction: `inverse` means level 0 = max param, `direct` means level 0 = min param
3. Output format: Transformers must return y-values, reducers must return (x,y) tuples

**Common Issues**:
- **Scipy validation errors**: Normalized frequencies must be `0 < Wn < 1` (use 0.99, not 1.0)
- **Deduplication**: Exponential parameter scales on narrow ranges create duplicates → use linear scale
- **Minimum constraints**: M4 needs `≥8 points`, MinMax needs even count, LTTB needs `≥3`

## Project-Specific Conventions

### Error Handling Philosophy
- Algorithms fail gracefully: `try transformer → try reducer → try aggregator → raise`
- Precomputed fallback: Runtime computation if `usePrecomputed=false` or data missing
- Different-length metrics: Return `None` for point-wise metrics, compute roughness-based metrics only

### Naming Conventions
- Algorithms: `{operation}_{type}` (e.g., `gaussian_filter`, `lttb_downsample`, `asap_aggregator`)
- Features: camelCase in JSON (`changePoints`, `spikesDips`), snake_case in Python (`change_points`)
- Metrics: `{feature}_{metric_type}` (e.g., `extrema_retention_ratio`, `trend_correlation`)

### TypeScript Integration
Vega-Lite specs in `web/src/vega/` define chart rendering. Key pattern:
```typescript
// Handle both transformer (y-values) and reducer (x,y tuples) formats
const yhat = levelData.output.map((item: any, idx: number) => 
  Array.isArray(item) ? {t: item[0] + 1, y: item[1]} : {t: idx + 1, y: item}
);
```

## External Dependencies

### Vendor Algorithms
Third-party implementations in `server/algorithms/vendor/`:
- **topology/**: Topological Data Analysis (TDA) smoothing via persistence diagrams
- **asap/**: ASAP adaptive smoothing (ACF-based window selection)
- **fpcs/**: FPCS streaming downsampling
- **douglas_peucker/**: Ramer-Douglas-Peucker simplification

**Integration**: Import in `data_*_algorithms.py`, expose as top-level functions

### Python Packages with Special Usage
- **pae**: Custom ApEn (Approximate Entropy) package for perceptual error
- **tsdownsample**: Rust-backed downsamplers (LTTB, M4, MinMax) - requires contiguous arrays
- **plotly_resampler**: EveryNthPoint class for uniform subsampling

## Performance & Caching

### Current Caching Strategy
`precomputed_loader.py` implements basic in-memory caching:
- **Metadata cache**: `(dataset, algorithm) → {num_levels, param_name}`
- **Level cache**: `(dataset, algorithm, level) → output data`
- **No eviction policy**: Unbounded growth (manageable at ~160MB for full dataset)
- **Singleton pattern**: One shared loader instance across all requests

**Memory footprint**: 80 datasets × 10 algorithms × 100 levels × ~2KB ≈ 160MB max

### Future Optimizations (deferred)
- LRU eviction for memory-constrained environments
- Lazy loading for `get_algorithm_info()` (currently loads all 100 levels)
- Cache statistics/monitoring
- Response compression for bulk endpoints

## Known Gotchas

1. **PAE computation is slow** - Precompute it offline, serve from JSON
2. **Reducer outputs are tuples** - Always call `extract_y_values()` before metrics
3. **Window sizes must be odd** - Use `_ensure_odd_window()` helper
4. **FFT filters need power-of-2** - Pad if necessary in `fft_cutoff_filter()`
5. **Banking affects visualization only** - Not stored in simplified data
6. **Cache has no size limits** - Current implementation caches indefinitely (acceptable for research use)

## Key Files to Reference
- `FEATURES_AND_METRICS.md` - Complete feature definitions and metric interpretations
- `IMPLEMENTATION_STATUS.md` - Precomputation status and known issues
- `ALGORITHM_OUTPUT_ANALYSIS.md` - Algorithm behavior on sample data
- `precompute_100_levels.py` - Parameter sampling patterns for new algorithms
