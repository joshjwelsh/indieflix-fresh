# Indieflix Daily Pipeline

Automated pipeline for scraping and enriching movie data from NYC arthouse theaters.

## Overview

The `daily.py` script runs all ingestion and enrichment tasks in sequence:

1. **Scrape Metrograph** - Get current movie schedules from Metrograph NYC
2. **Scrape Syndicated BK** - Get current movie schedules from Syndicated Bar Theater Kitchen
3. **Enrich with TMDB** - Add poster images, ratings, cast, and metadata from The Movie Database

## Usage

### Run Manually

```bash
# From project root
python3 deng/pipelines/daily.py

# Or make it executable
chmod +x deng/pipelines/daily.py
./deng/pipelines/daily.py
```

### Run as Cron Job

Add to your crontab to run daily at 2 AM:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * cd /path/to/indieflix-fresh && python3 deng/pipelines/daily.py >> /var/log/indieflix-daily.log 2>&1
```

### Render.com Deployment

For production on Render.com, use Render Shell to run manually when needed:

```bash
# SSH into Render
python3 deng/pipelines/daily.py
```

Or schedule via external cron service (GitHub Actions, etc.) to ping endpoint.

## Exit Codes

- `0` - Success (all steps completed)
- `1` - Partial failure (one or more steps failed, but pipeline completed)

## Output

The script provides detailed console output with emoji indicators:

```
==============================================================
INDIEFLIX DAILY PIPELINE
==============================================================
Started at: 2025-10-06 02:00:00
==============================================================

📽️  STEP 1: Scraping Metrograph...
------------------------------------------------------------
✅ Metrograph: 45 movies scraped

📽️  STEP 2: Scraping Syndicated BK...
------------------------------------------------------------
✅ Syndicated BK: 23 movies scraped

🎬 STEP 3: Enriching with TMDB data...
------------------------------------------------------------
✅ TMDB Enrichment: 68 movies enriched

==============================================================
PIPELINE SUMMARY
==============================================================
✅ Total movies scraped: 68
   - Metrograph: 45
   - Syndicated BK: 23
🎬 Total movies enriched: 68

Completed at: 2025-10-06 02:05:32
==============================================================
```

## Configuration

The pipeline uses environment variables from `.env`:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=indieflix
DB_USER=indieflix
DB_PASSWORD=your_password

# TMDB API
TMDB_API_KEY=your_tmdb_api_key
TMDB_BASE_IMAGE_URL=https://image.tmdb.org/t/p/
```

## Troubleshooting

### Script Fails to Run

- Verify Python 3 is installed: `python3 --version`
- Check dependencies are installed: `pip install -r requirements.txt`
- Ensure database is accessible

### Scraper Failures

- Check theater websites are accessible
- Verify date parsing for current year
- Review scraper logs for specific errors

### TMDB Enrichment Fails

- Verify TMDB_API_KEY is set in environment
- Check TMDB API quota (free tier: 40 requests per 10 seconds)
- Ensure movies have director/year metadata for matching

## Adding New Scrapers

To add a new theater scraper to the pipeline:

1. Create scraper in `deng/ingestion/new_theater.py`
2. Implement `scrape()` method returning list of movie dicts
3. Implement `save_to_db()` function
4. Add to `daily.py` pipeline:

```python
# In run_pipeline() function
try:
    from new_theater import NewTheaterScraper, save_to_db as save_new
    scraper = NewTheaterScraper()
    movies = scraper.scrape()
    save_new(movies)
    results['new_theater'] = {'success': True, 'count': len(movies)}
except Exception as e:
    results['new_theater'] = {'success': False, 'error': str(e)}
```

## Monitoring

### Log Files

Redirect output to log files for monitoring:

```bash
python3 deng/pipelines/daily.py >> /var/log/indieflix-$(date +\%Y\%m\%d).log 2>&1
```

### Exit Code Checking

In your cron or monitoring system:

```bash
#!/bin/bash
python3 deng/pipelines/daily.py
if [ $? -ne 0 ]; then
    echo "Pipeline failed" | mail -s "Indieflix Pipeline Alert" admin@example.com
fi
```

## Performance

- **Average runtime**: 2-5 minutes
- **Metrograph scrape**: ~30-60 seconds
- **Syndicated BK scrape**: ~20-40 seconds  
- **TMDB enrichment**: ~1-3 minutes (depends on number of movies)

## License

Part of the Indieflix project.
