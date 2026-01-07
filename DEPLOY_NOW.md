# Quick Deployment Steps

## ✅ What's Ready
- Frontend built and ready to deploy
- Backend has CORS enabled
- CDN has all data uploaded (precomputed + plots)
- All code updated to use CDN

## 🚀 Deploy Now

### Step 1: Push to GitHub
```bash
# Initialize git (if not done)
git init
git add .
git commit -m "CDN migration complete - ready for deployment"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/feature-taxonomy.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy Frontend to Vercel

1. Go to https://vercel.com/new
2. Sign in with GitHub
3. Click "Import Project"
4. Select your `feature-taxonomy` repository
5. Configure:
   - **Root Directory**: `web`
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `dist` (auto-detected)
   - **Install Command**: `npm install` (auto-detected)

6. **Environment Variables** - Add these:
   ```
   VITE_CDN_URL=https://feature-taxonomy-precomputed.sfo3.cdn.digitaloceanspaces.com
   ```

7. Click **Deploy** (takes ~2 minutes)

Your app will be live at: `https://your-project-name.vercel.app`

### Step 3: Deploy Backend to Railway

1. Go to https://railway.app/new
2. Sign in with GitHub
3. Click "Deploy from GitHub repo"
4. Select your `feature-taxonomy` repository
5. Railway auto-detects Python app

6. **Settings** → **Environment Variables**:
   ```
   FLASK_APP=server.app
   FLASK_ENV=production
   ```

7. **Settings** → **Deploy Settings**:
   - **Start Command**: `gunicorn server.app:app --bind 0.0.0.0:$PORT`

8. Deploy (takes ~3-5 minutes)

Your API will be live at: `https://feature-taxonomy-api.up.railway.app`

### Step 4: Connect Frontend to Backend

1. In Vercel dashboard, go to your project
2. **Settings** → **Environment Variables**
3. Add:
   ```
   VITE_API_URL=https://your-backend.up.railway.app
   ```
4. **Deployments** → **Redeploy** (to pick up new env var)

## ✅ Done!

Visit your Vercel URL - the app should now:
- ✅ Load all datasets
- ✅ Show plots from CDN
- ✅ Load precomputed data from CDN
- ✅ Compute live smoothing via Railway API

## 🧪 Test Deployment

```bash
# Test CDN access
curl https://feature-taxonomy-precomputed.sfo3.cdn.digitaloceanspaces.com/plots/original/stock_aapl_price.svg

# Test backend
curl https://your-backend.up.railway.app/datasets

# Test frontend
# Open browser to your Vercel URL
```

## 💰 Monthly Cost

- **DigitalOcean Spaces**: $5/month
- **Vercel**: Free (100GB bandwidth)
- **Railway**: Free ($5 credit/month, ~500 hours)
- **Total**: ~$5/month

## 🔧 Troubleshooting

**Frontend 404 on refresh**
- Vercel handles this automatically for SPAs

**API CORS errors**
- Already fixed - flask-cors is installed

**CDN files not loading**
- Check browser console for exact error
- Verify CDN URL in environment variables

**Backend not responding**
- Check Railway logs
- Verify gunicorn is running
- Check $PORT is used in bind address

## 📝 Notes

- Frontend is 100% static - can deploy anywhere
- Backend only needed for live smoothing computations
- All precomputed data and plots served from CDN
- No database needed - everything is file-based
