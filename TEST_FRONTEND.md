# Testing Frontend with Fake Data

Quick guide to get the Indieflix frontend running with fake data in under 2 minutes!

## Prerequisites

- PostgreSQL installed and running
- Python 3.9+ installed
- uv package manager installed

## Step-by-Step Testing

### 1. Setup Database (One-time)

```bash
# Create PostgreSQL database
sudo -u postgres psql -c "CREATE DATABASE indieflix;"
sudo -u postgres psql -c "CREATE USER indieflix WITH PASSWORD 'mypassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE indieflix TO indieflix;"
```

### 2. Install Dependencies (One-time)

```bash
cd indieflix-fresh/backend
uv pip install -e .
```

### 3. Initialize Database & Seed Fake Data

```bash
# Initialize tables
cd ../deng/utils/storage
python postgres.py

# Seed fake movie data (16 movies)
cd ../..
python seed_fake_data.py
```

You should see output like:
```
📽️  IFC Center: 5 movies
   ✓ The Substance
   ✓ All We Imagine as Light
   ...
📽️  Metrograph: 6 movies
   ✓ Anora
   ✓ Nosferatu
   ...
📽️  Syndicated BK: 5 movies
   ✓ Nickel Boys
   ✓ September 5
   ...
✅ SUCCESS: Inserted 16 fake movies
```

### 4. Start Backend (Terminal 1)

```bash
cd indieflix-fresh/backend/api
python app.py
```

Keep this running. You should see:
```
Indieflix API Server Starting
API will be available at http://localhost:5000
```

### 5. Start Frontend (Terminal 2)

```bash
cd indieflix-fresh/frontend
python -m http.server 8000
```

Keep this running.

### 6. Open Browser

Visit: **http://localhost:8000**

## What You Should See

### Homepage
- 16 movie cards displayed in a grid
- Search bar at the top
- Theater filter tabs (All, IFC Center, Metrograph, Syndicated BK)
- Stats showing "Movies: 16" and last update time

### Test Features

1. **Search Functionality**
   - Type "Anora" → Should show only Anora
   - Type "Robert Eggers" → Should show Nosferatu
   - Type "2024" → Should show most movies

2. **Theater Filtering**
   - Click "IFC Center" → Shows 5 movies
   - Click "Metrograph" → Shows 6 movies
   - Click "Syndicated BK" → Shows 5 movies
   - Click "All Theaters" → Shows all 16 movies

3. **Movie Cards**
   Each card should display:
   - Theater badge (colored)
   - Movie title
   - Director name
   - Year
   - Showing dates
   - Description
   - Location link

4. **Mobile Responsive**
   - Resize browser window → Layout adapts
   - Try on phone → Should work perfectly

## Fake Data Included

**IFC Center (5 movies):**
- The Substance (2024)
- All We Imagine as Light (2024)
- The Brutalist (2024)
- Perfect Days (2023)
- Wicked Little Letters (2023)

**Metrograph (6 movies):**
- Anora (2024)
- Nosferatu (2024)
- A Complete Unknown (2024)
- The Piano Lesson (2024)
- Sing Sing (2023)
- The Wild Robot (2024)

**Syndicated BK (5 movies):**
- Nickel Boys (2024)
- September 5 (2024)
- Emilia Pérez (2024)
- Conclave (2024)
- Flow (2024)

## API Endpoints to Test

Open these URLs in browser:

- Health Check: http://localhost:5000/api/health
- All Movies: http://localhost:5000/api/movies
- By Theater: http://localhost:5000/api/movies/by-theater
- Theaters List: http://localhost:5000/api/theaters
- Stats: http://localhost:5000/api/stats
- Search: http://localhost:5000/api/search?q=anora

## Troubleshooting

**No movies showing?**
```bash
# Check if data was inserted
cd indieflix-fresh/deng
python -c "from utils.storage.postgres import db_select; print(db_select('SELECT COUNT(*) FROM movies'))"
```

**API errors?**
- Make sure PostgreSQL is running
- Check .env file has correct credentials
- Verify backend is running on port 5000

**Frontend not loading?**
- Check browser console for errors (F12)
- Verify API_BASE_URL in frontend/app.js is http://localhost:5000/api

## Re-seeding Data

To reset and re-seed:
```bash
cd indieflix-fresh/deng
python seed_fake_data.py
# Answer 'yes' when prompted to delete existing data
```

---

Enjoy testing! 🎬
