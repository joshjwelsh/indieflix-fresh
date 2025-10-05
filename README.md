# Indieflix 🎬

A fresh, lightweight web application to track arthouse movie theater schedules in New York City.

## Overview

Indieflix scrapes movie schedules from NYC arthouse theaters and displays them on a clean, mobile-responsive website. Built with Python, Flask, PostgreSQL, and vanilla JavaScript - simple, efficient, and cost-effective.

## Architecture

```
indieflix-fresh/
├── backend/
│   ├── api/
│   │   └── app.py              # Flask API server
│   └── pyproject.toml          # Python dependencies (uv)
├── frontend/
│   ├── index.html              # Main HTML page
│   ├── styles.css              # Responsive CSS
│   └── app.js                  # Frontend JavaScript
├── deng/                       # Data Engineering
│   ├── ingestion/
│   │   ├── ifc_center.py       # IFC Center scraper
│   │   ├── metrograph.py       # Metrograph scraper
│   │   └── syndicatedbk.py     # Syndicated BK scraper
│   ├── utils/
│   │   └── storage/
│   │       └── postgres.py     # PostgreSQL utilities
│   └── setup_cron.sh           # Cron job setup script
├── .env                        # Database credentials
└── .gitignore
```

## Features

- 🎭 **Theater Coverage**: IFC Center, Metrograph, Syndicated BK
- 🔍 **Search**: Search movies by title or director
- 🎫 **Filter**: Filter by theater
- 📱 **Mobile-Responsive**: Works great on phones
- 🔄 **Auto-Updates**: Cron jobs scrape daily at 2 AM
- 💾 **PostgreSQL**: No ORM, direct SQL for efficiency

## Prerequisites

- Python 3.9+
- PostgreSQL 12+
- uv (Python package manager)

## Setup

### 1. Database Setup

Create PostgreSQL database and user:

```sql
CREATE DATABASE indieflix;
CREATE USER indieflix WITH PASSWORD 'mypassword';
GRANT ALL PRIVILEGES ON DATABASE indieflix TO indieflix;
```

### 2. Environment Configuration

The `.env` file is already configured with default values:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=indieflix
DB_USER=indieflix
DB_PASSWORD=mypassword
```

Update these values if your setup differs.

### 3. Install Dependencies

Using uv (already installed):

```bash
cd indieflix-fresh/backend
uv pip install -e .
```

This installs:
- Flask & Flask-CORS
- psycopg2-binary
- pandas
- requests
- beautifulsoup4
- lxml
- python-dotenv

### 4. Initialize Database

Create the database tables:

```bash
cd indieflix-fresh/deng/utils/storage
python postgres.py
```

You should see: `✅ Database tables created successfully`

### 5. Run Initial Scrape

Scrape data from all theaters:

```bash
cd indieflix-fresh/deng/ingestion

# Run each scraper
python ifc_center.py
python metrograph.py
python syndicatedbk.py
```

### 6. Setup Cron Jobs (Optional)

For automated daily scraping:

```bash
cd indieflix-fresh/deng
chmod +x setup_cron.sh
./setup_cron.sh
```

Follow the instructions to add cron jobs that run scrapers daily at 2 AM.

## Running the Application

### Start the Backend API

```bash
cd indieflix-fresh/backend/api
python app.py
```

API will be available at `http://localhost:5000`

### Serve the Frontend

Using Python's built-in server:

```bash
cd indieflix-fresh/frontend
python -m http.server 8000
```

Or use any static file server. Open `http://localhost:8000` in your browser.

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/movies` - Get all movies
  - Query params: `theater`, `limit`, `recent`
- `GET /api/movies/by-theater` - Movies grouped by theater
- `GET /api/theaters` - List of theaters with counts
- `GET /api/search?q=query` - Search movies
- `GET /api/stats` - Database statistics

## Database Schema

**movies** table:
```sql
- id (SERIAL PRIMARY KEY)
- title (VARCHAR)
- theater (VARCHAR)
- theater_id (VARCHAR)
- location (VARCHAR)
- website (VARCHAR)
- director (VARCHAR)
- year (INTEGER)
- dates (VARCHAR)
- description (TEXT)
- scraped_at (TIMESTAMP)
- created_at (TIMESTAMP)
```

## Data Engineering Utilities

The `deng/utils/storage/postgres.py` module provides:

- `db_conn()` - Get database connection
- `db_execute(sql, params)` - Execute SQL
- `db_select(sql, params)` - SELECT query
- `db_select_df(sql, params)` - SELECT as pandas DataFrame
- `insert_db(table, data)` - Insert single row
- `insert_many_db(table, columns, values)` - Bulk insert
- `insert_df(df, table)` - Insert DataFrame
- `update_db(table, data, where, params)` - Update rows
- `delete_db(table, where, params)` - Delete rows
- `create_tables()` - Initialize schema

## Adding More Theaters

1. Create a new scraper in `deng/ingestion/`:

```python
# deng/ingestion/new_theater.py
class NewTheaterScraper:
    def __init__(self):
        self.name = 'Theater Name'
        self.url = 'https://theater-website.com'
        # ...
    
    def scrape(self):
        # Implement scraping logic
        return movies
```

2. Add to cron jobs for daily scraping
3. Update frontend tabs in `frontend/index.html`

## Development

### Testing Scrapers

Run individual scrapers to test:

```bash
python deng/ingestion/ifc_center.py
```

### Testing Database Functions

```bash
python deng/utils/storage/postgres.py
```

### Frontend Development

The frontend uses vanilla JavaScript with no build step - just edit and refresh.

## Production Deployment

For production:

1. Use a production-grade WSGI server (gunicorn) instead of Flask dev server
2. Set up proper PostgreSQL backups
3. Use nginx to serve frontend static files
4. Configure cron jobs on server
5. Use environment variables for sensitive data
6. Set up monitoring and logging

## Troubleshooting

**Database connection fails:**
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify credentials in `.env`
- Ensure database exists: `psql -l`

**Scrapers return no data:**
- Theater websites may have changed structure
- Check network connectivity
- Review scraper selectors in ingestion scripts

**Frontend can't connect to API:**
- Ensure backend is running on port 5000
- Check CORS settings in `backend/api/app.py`
- Verify `API_BASE_URL` in `frontend/app.js`

## License

MIT

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Contact

For issues or questions, please open an issue on GitHub.

---

Built with ❤️ for NYC cinema lovers
