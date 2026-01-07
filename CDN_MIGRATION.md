# CDN Migration Summary

## What Was Done

### 1. Uploaded Data to DigitalOcean Spaces CDN
- **Precomputed data**: 153,638 files (90.58 GB) 
  - All algorithm outputs for 100 smoothing levels across 80+ datasets
- **Plots**: 4,757 files (2.28 GB)
  - Original dataset visualizations
  - PAE analysis plots
  - Ranking bump charts (global, category, feature, density, periodic)
  - Grading heatmaps and distributions
  - Paper figures (PDFs)

### 2. Updated Frontend to Use CDN

**Created**: `web/src/config/cdn.ts`
- CDN base URL: `https://feature-taxonomy-precomputed.sfo3.cdn.digitaloceanspaces.com`
- Helper functions: `getPrecomputedUrl()`, `getPlotUrl()`

**Updated Components**:
- `api.ts` - Fetches precomputed data directly from CDN
- `GradingPlotsGallery.tsx` - Loads grading plots from CDN
- `PaperFiguresGallery.tsx` - Loads paper figures from CDN
- `OriginalPlotsGallery.tsx` - Loads original plots from CDN
- `PlotsGallery.tsx` - Loads ranking plots from CDN
- `RankingsViewer.tsx` - Loads bump charts from CDN
- `PrecomputedPlotsGallery.tsx` - Loads PAE plots from CDN

### 3. Updated Backend

**Added CORS Support**:
- Installed `flask-cors>=3.0.0`
- Enabled CORS for all routes to allow CDN access
- Backend now serves only dynamic content (smoothing computations, feature extraction)

## CDN URLs

### Public Access
- **Precomputed data**: `https://feature-taxonomy-precomputed.sfo3.cdn.digitaloceanspaces.com/precomputed/`
  - Example: `.../precomputed/stock_aapl_price/gaussian_filter.json`
  
- **Plots**: `https://feature-taxonomy-precomputed.sfo3.cdn.digitaloceanspaces.com/plots/`
  - Example: `.../plots/stock_aapl_price/ranking/level_l1_ranking.svg`
  - Example: `.../plots/paper  figures/Fig 5 a.pdf`

### Environment Configuration
**Frontend** (`web/.env`):
```
VITE_CDN_URL=https://feature-taxonomy-precomputed.sfo3.cdn.digitaloceanspaces.com
```

**Backend** (`.env`):
```
DO_SPACE_NAME=feature-taxonomy-precomputed
DO_REGION=sfo3
DO_ACCESS_KEY=DO8014FJXUEBGP9LGQZ7
DO_SECRET_KEY=[redacted]
```

## Benefits

1. **Fast Loading**: CDN delivers static content globally with low latency
2. **Reduced Backend Load**: Backend only handles dynamic computations
3. **Scalability**: CDN handles concurrent requests efficiently
4. **Cost Effective**: $5/month for 250GB storage + 1TB bandwidth
5. **Easy Deployment**: Frontend can be deployed as static site, backend as API only

## Next Steps for Deployment

### Option 1: Separate Static + API Deployment
1. **Frontend**: Deploy to Vercel/Netlify/DO App Platform (static)
   - Build: `cd web && npm run build`
   - Deploy `web/dist/` folder
   - Set env var: `VITE_CDN_URL`

2. **Backend**: Deploy to Heroku/DO App Platform/Railway (API)
   - Deploy Flask app with gunicorn
   - Set env vars for CDN credentials
   - Backend serves only /smooth, /series, /datasets endpoints

### Option 2: Single App Platform Deployment
1. Deploy both frontend and backend to DigitalOcean App Platform
2. Frontend serves static files from `web/dist/`
3. Backend API at `/api/*` routes
4. Configure build commands and environment variables

## Testing

To test locally with CDN:
```bash
# Frontend (should load data from CDN)
cd web && npm run dev

# Backend (optional, only for smoothing)
python -m server.app
```

Access at `http://localhost:5173` - all plots and precomputed data should load from CDN.
