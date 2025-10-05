# Indieflix Deployment Guide

Complete guide for deploying Indieflix to production on Render.com

## 📋 Prerequisites

- GitHub account
- Render.com account (free)
- TMDB API key (from https://www.themoviedb.org/settings/api)

## 🚀 Quick Deploy to Render.com

### Step 1: Push Code to GitHub

```bash
cd project/indieflix-fresh

# If you haven't already, initialize git
git init
git add .
git commit -m "Initial commit"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/indieflix-nyc.git
git branch -M main
git push -u origin main
```

### Step 2: Connect to Render

1. Go to https://render.com and sign in
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` and configure everything!

### Step 3: Set Environment Variables

In Render dashboard, set the **TMDB_API_KEY** environment variable:

1. Go to your web service
2. Click **"Environment"** tab
3. Add: `TMDB_API_KEY` = `55cf761dcbb8f798bf6319a147140626`
4. Click **"Save Changes"**

The other environment variables (database connection, ADMIN_SECRET) are automatically configured!

### Step 4: Deploy!

Render will automatically:
- ✅ Create PostgreSQL database
- ✅ Build your application
- ✅ Deploy to production
- ✅ Give you a public URL (e.g., `https://indieflix-web.onrender.com`)

**First deployment takes ~5 minutes**

## 🎬 Post-Deployment Tasks

### 1. Run Initial Data Collection

After deployment, populate your database with movies:

```bash
# SSH into Render (or use the Shell tab in dashboard)
python3 deng/ingestion/metrograph_v2.py
python3 deng/ingestion/syndicatedbk.py
```

### 2. Enrich with TMDB Data

Trigger enrichment via API:

```bash
curl -X POST https://YOUR_APP.onrender.com/admin/trigger-enrichment \
  -H "X-Admin-Key: YOUR_ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'
```

(Get `ADMIN_SECRET` from Render dashboard → Environment variables)

## 🏠 Local Development with Docker

### Setup

```bash
cd project/indieflix-fresh

# Copy environment template
cp .env.example .env

# Edit .env with your TMDB API key
# (Keep other values as-is for local development)
```

### Run Locally

```bash
# Start everything (database + backend + frontend)
docker-compose up

# Access app at:
# - Frontend: http://localhost:5000
# - API: http://localhost:5000/api/movies
```

### Stop

```bash
# Stop containers
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v
```

## 📊 Manual Enrichment Trigger

### Via API

```bash
# Enrich up to 50 movies
curl -X POST http://localhost:5000/admin/trigger-enrichment \
  -H "X-Admin-Key: your-admin-secret" \
  -H "Content-Type: application/json" \
  -d '{"limit": 50}'
```

### Via Command Line (Local)

```bash
cd project/indieflix-fresh

# Enrich all unenriched movies
python3 deng/enrichment/tmdb_enricher.py --all

# Enrich recent movies
python3 deng/enrichment/tmdb_enricher.py --recent 24

# Re-enrich stale data
python3 deng/enrichment/tmdb_enricher.py --stale 30
```

## 🔧 Render.com Configuration

Your `render.yaml` defines:

### Web Service
- **Type**: Python web service
- **Build**: `pip install -r requirements.txt`
- **Start**: `gunicorn -w 4 -b 0.0.0.0:$PORT backend.api.app:app`
- **Health Check**: `/health`
- **Region**: Oregon (free tier)

### Database
- **Type**: PostgreSQL
- **Plan**: Free (90-day trial, then $7/month)
- **Region**: Oregon

### Environment Variables (Auto-configured)
- Database connection strings (auto from database)
- `ADMIN_SECRET` (auto-generated)
- `TMDB_API_KEY` (you set manually)

## 💰 Costs

**Free Tier Limits:**
- Web service: Sleeps after 15 min inactivity
- PostgreSQL: Free for 90 days, then $7/month
- Bandwidth: 100GB/month free

**Upgrade Options:**
- $7/month: Always-on web service + PostgreSQL
- Perfect for showing friends!

## 🐛 Troubleshooting

### "Service Unavailable" Error
- Wait 30-60 seconds (free tier wakes from sleep)
- Check Render logs for errors

### Database Connection Error
- Verify environment variables are set
- Check database is running in Render dashboard

### TMDB Enrichment Not Working
- Verify `TMDB_API_KEY` is set
- Check API quota (free tier: 40 req/10 sec)

### Frontend Shows No Movies
- Run scrapers first to populate database
- Check `/api/movies` endpoint returns data

## 📱 Sharing with Friends

Once deployed:

1. **Share URL**: `https://your-app-name.onrender.com`
2. **First visit warning**: Tell them it takes 30-60s to wake up (free tier)
3. **Keep it alive**: Visit regularly or upgrade to always-on

## 🔄 Updates & Redeployment

Render auto-deploys on git push:

```bash
# Make changes to code
git add .
git commit -m "Update feature"
git push origin main

# Render automatically detects and deploys!
```

## 🎯 Next Steps

- [ ] Deploy to Render.com
- [ ] Run scrapers to populate database
- [ ] Trigger TMDB enrichment
- [ ] Share with friends!
- [ ] Set up regular scraping (manual for now)

## 📚 Additional Resources

- [Render Docs](https://render.com/docs)
- [TMDB API Docs](https://developers.themoviedb.org/3)
- [Docker Compose Docs](https://docs.docker.com/compose/)

---

**Need help?** Check the logs in Render dashboard or run `docker-compose logs` locally.
