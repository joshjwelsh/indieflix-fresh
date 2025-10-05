# Indieflix Quick Start Guide

Get Indieflix running in 5 minutes!

## 🚀 Quick Setup

### 1. Setup PostgreSQL Database

```bash
# Create database and user
sudo -u postgres psql
```

```sql
CREATE DATABASE indieflix;
CREATE USER indieflix WITH PASSWORD 'mypassword';
GRANT ALL PRIVILEGES ON DATABASE indieflix TO indieflix;
\q
```

### 2. Install Python Dependencies

```bash
cd indieflix-fresh

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Linux/Mac
# .venv\Scripts\activate   # On Windows (if needed)

# Install dependencies from pyproject.toml
cd backend
uv pip install -e .
```

Or install from pyproject.toml dependencies:
```bash
# Alternative: Use uv pip sync with the project
cd indieflix-fresh/backend
uv pip install $(grep -E '^\s*"' pyproject.toml | sed 's/[",]//g' | tr '\n' ' ')
```

### 3. Initialize Database

```bash
cd ../deng/utils/storage
python postgres.py
```

Expected output: `✅ Database tables created successfully`

### 4. Add Data (Choose One)

**Option A: Use Fake Data (Quick Testing)**

```bash
cd ../../
python seed_fake_data.py
```

This creates 16 realistic fake movies across all 3 theaters instantly.

**Option B: Scrape Real Data (Takes longer)**

```bash
cd ingestion
python ifc_center.py
python metrograph.py
python syndicatedbk.py
```

Note: Real scraping may not work if theater websites have changed.

### 5. Start Backend API

```bash
cd ../../../backend/api
python app.py
```

Keep this terminal running. API at `http://localhost:5000`

### 6. Start Frontend (New Terminal)

```bash
cd indieflix-fresh/frontend
python -m http.server 8000
```

### 7. Open Browser

Visit: `http://localhost:8000`

🎉 You should now see the Indieflix website with movie schedules!

## 📋 Daily Updates (Optional)

Setup cron for automatic daily scraping:

```bash
cd indieflix-fresh/deng
chmod +x setup_cron.sh
./setup_cron.sh
```

Follow instructions to add cron jobs.

## 🧪 Testing

Test individual components:

```bash
# Test database connection
cd deng/utils/storage && python postgres.py

# Test a scraper
cd deng/ingestion && python ifc_center.py

# Test API health
curl http://localhost:5000/api/health
```

## 📱 Features to Try

- **Search**: Type movie titles in search bar
- **Filter**: Click theater tabs to filter
- **Mobile**: Open on your phone - it's responsive!

## ⚠️ Troubleshooting

**"Connection refused" error?**
- Make sure PostgreSQL is running: `sudo systemctl status postgresql`

**No movies showing?**
- Run scrapers again (step 4)
- Check browser console for errors

**API not responding?**
- Ensure backend is running on port 5000
- Check for port conflicts

## 🔄 Updating Data

Re-run scrapers anytime:
```bash
cd indieflix-fresh/deng/ingestion
python ifc_center.py && python metrograph.py && python syndicatedbk.py
```

---

For detailed documentation, see [README.md](README.md)
