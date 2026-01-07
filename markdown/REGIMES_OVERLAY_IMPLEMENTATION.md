# Regimes & Change Points Overlay - Implementation Summary

## What was added:

### 1. New Overlay Option in Controls
**File**: `web/src/components/Controls.tsx`

Added a new option "Regimes & Change Points (Combined)" in the Feature Overlay dropdown, positioned at the top of the Structural Features group:

```tsx
<optgroup label="Structural Features">
  <option value="regimesAndChangePoints">Regimes & Change Points (Combined)</option>
  <option value="changePoints">Change Points Only (Regime Boundaries)</option>
  <option value="regimes">Regimes Only (Mean Plateaus)</option>
  <option value="spikesDips">Spikes & Dips (Outliers)</option>
</optgroup>
```

### 2. New Overlay Function
**File**: `web/src/vega/overlayFeatures.ts`

Created `overlayRegimesAndChangePoints()` that combines 4 visual layers (like the standalone visualization):

1. **Shaded regime regions** - Color-coded background rectangles for each regime
2. **Regime baseline lines** - Horizontal lines showing the mean value of each regime
3. **Change point markers (vertical)** - Red dashed vertical lines at regime boundaries
4. **Change point markers (top)** - Red triangular markers at the top of the chart

### 3. Handler in ChartPanel
**File**: `web/src/components/ChartPanel.tsx`

Added case handler for `'regimesAndChangePoints'` that:
- Extracts regimes and change points from features.regimes
- Calculates y-extent for proper vertical scaling
- Creates 3 datasets:
  - Regime shading (colored rectangles)
  - Baseline lines (horizontal mean lines)
  - Change point markers (vertical lines + triangles)
- Calls the combined overlay function

## Visual Design (matches standalone visualization):

**Color Scheme**:
- Each regime: Different color from Vega's categorical palette
- Regime baselines: Thick horizontal lines (3px, 80% opacity)
- Change points: Red (`#dc3545`) dashed vertical lines with triangle markers

**Layout**:
- Regime shading: Light opacity (10%) background
- Baselines: Prominent horizontal lines at each regime's mean
- Change points: Dashed vertical lines spanning full height
- Markers: Triangle-down shapes positioned 5% above max y-value

## How to use:

1. Load the app and select a dataset (e.g., stock_aapl_price)
2. Choose an algorithm (e.g., gaussian_filter)
3. Select "Regimes & Change Points (Combined)" from Feature Overlay dropdown
4. Move the slider to see how regimes change with different smoothing levels

## Expected behavior:

- **Level 0** (no smoothing): Should show many regimes (25-30) with frequent change points
- **Higher levels** (more smoothing): Fewer regimes as data becomes smoother
- **Hover tooltips**: Show regime number, start/end, mean value, and change point indices

## Data requirements:

The feature expects `features.regimes` to have this structure:
```typescript
{
  regimes: [
    {a: startIndex, b: endIndex, baseline: meanValue},
    ...
  ],
  change_points: [index1, index2, ...],
  num_regimes: count,
  num_change_points: count
}
```

This structure is already produced by the optimized ruptures-based `compute_regimes()` function.
