# Deployment Guide

## Frontend Deployment (Vercel)

### Step 1: Push to GitHub
```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit with CDN integration"

# Create GitHub repo and push
git remote add origin https://github.com/YOUR_USERNAME/feature-taxonomy.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Vercel
1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `web`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

4. Add Environment Variable:
   - Key: `VITE_CDN_URL`
   - Value: `https://feature-taxonomy-precomputed.sfo3.cdn.digitaloceanspaces.com`

5. Click "Deploy"

Your frontend will be live at: `https://your-project.vercel.app`

---

## Backend Deployment (Railway)

### Step 1: Deploy to Railway
1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect Python app

### Step 2: Configure Environment Variables
Add these in Railway dashboard:
```
FLASK_APP=server.app
FLASK_ENV=production
PYTHON_VERSION=3.10.0
```

### Step 3: Configure Start Command
In Railway settings, set:
```
gunicorn server.app:app --bind 0.0.0.0:$PORT
```

Your backend will be live at: `https://your-app.up.railway.app`

### Step 4: Update Frontend API Endpoint
After Railway deployment, update Vercel environment variable:
- Key: `VITE_API_URL`  
- Value: `https://your-app.up.railway.app`

Then redeploy frontend on Vercel.

---

## Alternative: Backend on Render.com

If Railway doesn't work, use Render.com (also free):

1. Go to https://render.com/
2. Click "New +" → "Web Service"
3. Connect GitHub repo
4. Configure:
   - **Name**: feature-taxonomy-api
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn server.app:app --bind 0.0.0.0:$PORT`
   - **Plan**: Free

5. Your API will be at: `https://feature-taxonomy-api.onrender.com`

---

## Testing Deployment

### Test Frontend
1. Visit your Vercel URL
2. Check browser console for errors
3. Verify plots load from CDN
4. Test dataset selection

### Test Backend
```bash
curl https://your-app.up.railway.app/datasets
```

Should return list of datasets.

### Test Integration
1. Go to frontend URL
2. Select a dataset
3. Try smoothing with different algorithms
4. Verify metrics are calculated

---

## Troubleshooting

### Frontend: "Failed to fetch"
- Check VITE_CDN_URL is set correctly
- Verify CDN files are publicly accessible
- Check browser console for CORS errors

### Backend: 500 Internal Server Error
- Check Railway logs: `railway logs`
- Verify all dependencies in requirements.txt
- Check environment variables are set

### API Connection Issues
- Verify VITE_API_URL matches Railway URL
- Check CORS is enabled in Flask (already done)
- Test API endpoint directly with curl

---

## Cost Summary

- **DigitalOcean Spaces**: $5/month (CDN + storage)
- **Vercel**: Free (100GB bandwidth/month)
- **Railway**: Free (500 hours/month, $5 credit)
- **Total**: ~$5/month

Free tier limits:
- Vercel: Unlimited projects, 100GB bandwidth
- Railway: 500 compute hours, $5 monthly credit (auto-suspends after inactivity)
