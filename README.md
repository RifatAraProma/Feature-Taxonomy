# Adaptive Smoothing — Experiment + UI

A reproducible framework to evaluate how different smoothing / reduction / aggregation algorithms
preserve visual features in line charts — with a Flask backend and a React + Vega-Lite frontend.

## What’s inside
- **Flask API** (in `server/`) to load series, run algorithms (wrapping your modules),
  compute 45° banking, basic features (extrema, regimes, periodicity), and metrics.
- **React + Vega-Lite** (in `web/`) to explore original vs smoothed charts, toggle overlays,
  match methods at a target PAE, and inspect metrics.
- **Data stubs** (in `data/`) — add your own JSON series as `{"id": "...", "y": [...]}`.

## Quick start

### 1) Backend (Flask)
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export FLASK_APP=server/app.py && flask run  # Windows: set FLASK_APP=server/app.py
# API at http://127.0.0.1:5000
```

### 2) Frontend (React + Vite + Vega-Lite)
```bash
cd web
npm i
npm run dev
# UI at http://127.0.0.1:5173
```

### 3) Data format
Put JSON files into `data/` like:
```json
{"id":"series_001","y":[1,2,1,3,2,2.5,1.8,2.2,2.1]}
```

## Notes
- The backend wraps your vendor modules placed into `server/algorithms/vendor/` and tries to call
  known function names. If not found, it falls back to a basic moving-average smoother.
- PAE here is a light placeholder; swap with your preferred implementation in `server/features/pae.py`.
- The UI demonstrates: side-by-side banking-aware charts, overlays (extrema/change-points),
  matched-PAE comparison, and a live metrics bar.
