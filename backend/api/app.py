"""
Indieflix Backend API
Flask API to serve movie theater schedules from PostgreSQL
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Load .env file FIRST (before other imports that might need it)
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Add deng utils to path to access database functions
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'deng' / 'utils'))
from storage.postgres import db_select_df, db_select, create_tables

# Configure Flask app
app = Flask(__name__, 
            static_folder='../../frontend',
            static_url_path='')
CORS(app)  # Enable CORS for frontend access

# Get admin secret from environment
ADMIN_SECRET = os.getenv('ADMIN_SECRET', 'change-me-in-production')

# Initialize database tables on startup
try:
    create_tables()
    print("✅ Database tables initialized")
except Exception as e:
    print(f"⚠️  Warning: Could not initialize database tables: {e}")


# Serve frontend
@app.route('/')
def serve_frontend():
    """Serve the frontend index.html"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve other static files"""
    return send_from_directory(app.static_folder, path)


# Health check endpoints (both /health and /api/health for compatibility)
@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render and monitoring"""
    try:
        # Test database connection
        db_select("SELECT 1")
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'indieflix-api',
        'database': db_status
    })


@app.route('/api/movies', methods=['GET'])
def get_movies():
    """
    Get all movies from database
    Query params:
    - theater: Filter by theater_id
    - limit: Limit number of results (default 100)
    - recent: If 'true', only get movies from most recent scrape
    """
    try:
        theater_filter = request.args.get('theater')
        limit = int(request.args.get('limit', 100))
        recent_only = request.args.get('recent', 'true').lower() == 'true'
        
        # Build SQL query
        if recent_only:
            # Get only the most recent scrape's data
            if theater_filter:
                sql = """
                    SELECT DISTINCT ON (title, theater_id) 
                        title, theater, theater_id, location, website,
                        director, year, dates, description, scraped_at,
                        poster_url, runtime, tmdb_rating, genres, 
                        cast_members, tmdb_overview, enriched_at
                    FROM movies
                    WHERE scraped_at >= (
                        SELECT MAX(scraped_at) - INTERVAL '1 day'
                        FROM movies
                    )
                    AND theater_id = %s
                    ORDER BY title, theater_id, scraped_at DESC
                    LIMIT %s
                """
                df = db_select_df(sql, (theater_filter, limit))
            else:
                sql = """
                    WITH recent_movies AS (
                        SELECT DISTINCT ON (title, theater_id) 
                            title, theater, theater_id, location, website,
                            director, year, dates, description, scraped_at,
                            poster_url, runtime, tmdb_rating, genres, 
                            cast_members, tmdb_overview, enriched_at
                        FROM movies
                        WHERE scraped_at >= (
                            SELECT MAX(scraped_at) - INTERVAL '1 day'
                            FROM movies
                        )
                        ORDER BY title, theater_id, scraped_at DESC
                    )
                    SELECT * FROM recent_movies
                    ORDER BY dates ASC NULLS LAST
                    LIMIT %s
                """
                df = db_select_df(sql, (limit,))
        else:
            if theater_filter:
                sql = """
                    SELECT title, theater, theater_id, location, website,
                           director, year, dates, description, scraped_at,
                           poster_url, runtime, tmdb_rating, genres, 
                           cast_members, tmdb_overview, enriched_at
                    FROM movies
                    WHERE theater_id = %s
                    ORDER BY scraped_at DESC
                    LIMIT %s
                """
                df = db_select_df(sql, (theater_filter, limit))
            else:
                sql = """
                    SELECT title, theater, theater_id, location, website,
                           director, year, dates, description, scraped_at,
                           poster_url, runtime, tmdb_rating, genres, 
                           cast_members, tmdb_overview, enriched_at
                    FROM movies
                    ORDER BY scraped_at DESC
                    LIMIT %s
                """
                df = db_select_df(sql, (limit,))
        
        # Convert to list of dicts and replace NaN with None
        movies = df.to_dict('records')
        
        # Convert datetime objects to ISO format strings and handle NaN values
        for movie in movies:
            # Handle datetime columns
            for datetime_col in ['scraped_at', 'enriched_at', 'created_at', 'updated_at']:
                if datetime_col in movie and movie[datetime_col]:
                    try:
                        movie[datetime_col] = movie[datetime_col].isoformat()
                    except (AttributeError, ValueError):
                        movie[datetime_col] = None
            
            # Replace NaN with None for JSON serialization
            for key, value in movie.items():
                if isinstance(value, float) and str(value) == 'nan':
                    movie[key] = None
                # Handle pandas NaT (Not a Time)
                elif value is None or (hasattr(value, '__class__') and 'NaTType' in str(value.__class__)):
                    movie[key] = None
        
        return jsonify({
            'success': True,
            'count': len(movies),
            'movies': movies
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/movies/by-theater', methods=['GET'])
def get_movies_by_theater():
    """Get movies grouped by theater"""
    try:
        # Get most recent movies for each theater
        sql = """
            SELECT DISTINCT ON (title, theater_id) 
                title, theater, theater_id, location, website,
                director, year, dates, description, scraped_at
            FROM movies
            WHERE scraped_at >= (
                SELECT MAX(scraped_at) - INTERVAL '1 day'
                FROM movies
            )
            ORDER BY title, theater_id, scraped_at DESC
        """
        
        df = db_select_df(sql)
        
        # Group by theater
        theaters = {}
        for _, row in df.iterrows():
            theater_id = row['theater_id']
            if theater_id not in theaters:
                theaters[theater_id] = {
                    'theater_id': theater_id,
                    'theater_name': row['theater'],
                    'location': row['location'],
                    'website': row['website'],
                    'movies': []
                }
            
            movie = {
                'title': row['title'],
                'director': row.get('director'),
                'year': row.get('year'),
                'dates': row.get('dates'),
                'description': row.get('description'),
                'scraped_at': row['scraped_at'].isoformat() if row['scraped_at'] else None
            }
            theaters[theater_id]['movies'].append(movie)
        
        return jsonify({
            'success': True,
            'theaters': list(theaters.values())
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/theaters', methods=['GET'])
def get_theaters():
    """Get list of all theaters with movie counts"""
    try:
        sql = """
            SELECT 
                theater_id,
                theater,
                location,
                website,
                COUNT(*) as movie_count,
                MAX(scraped_at) as last_updated
            FROM movies
            WHERE scraped_at >= (
                SELECT MAX(scraped_at) - INTERVAL '1 day'
                FROM movies
            )
            GROUP BY theater_id, theater, location, website
            ORDER BY theater
        """
        
        df = db_select_df(sql)
        
        theaters = []
        for _, row in df.iterrows():
            theaters.append({
                'id': row['theater_id'],
                'name': row['theater'],
                'location': row['location'],
                'website': row['website'],
                'movie_count': int(row['movie_count']),
                'last_updated': row['last_updated'].isoformat() if row['last_updated'] else None
            })
        
        return jsonify({
            'success': True,
            'count': len(theaters),
            'theaters': theaters
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/search', methods=['GET'])
def search_movies():
    """
    Search movies by title
    Query params:
    - q: Search query
    """
    try:
        query = request.args.get('q', '')
        
        if not query or len(query) < 2:
            return jsonify({
                'success': False,
                'error': 'Search query must be at least 2 characters'
            }), 400
        
        sql = """
            SELECT DISTINCT ON (title, theater_id) 
                title, theater, theater_id, location, website,
                director, year, dates, description, scraped_at,
                poster_url, runtime, tmdb_rating, genres, 
                cast_members, tmdb_overview, enriched_at
            FROM movies
            WHERE LOWER(title) LIKE LOWER(%s)
                AND scraped_at >= (
                    SELECT MAX(scraped_at) - INTERVAL '7 days'
                    FROM movies
                )
            ORDER BY title, theater_id, scraped_at DESC
            LIMIT 50
        """
        
        search_pattern = f'%{query}%'
        df = db_select_df(sql, (search_pattern,))
        
        movies = df.to_dict('records')
        
        # Convert datetime objects to ISO format strings and handle NaN values
        for movie in movies:
            if 'scraped_at' in movie and movie['scraped_at']:
                movie['scraped_at'] = movie['scraped_at'].isoformat()
            # Replace NaN with None for JSON serialization
            for key, value in movie.items():
                if isinstance(value, float) and str(value) == 'nan':
                    movie[key] = None
        
        return jsonify({
            'success': True,
            'query': query,
            'count': len(movies),
            'movies': movies
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about the database"""
    try:
        # Total movies
        total_sql = "SELECT COUNT(*) FROM movies"
        total_result = db_select(total_sql)
        total_movies = total_result[0][0] if total_result else 0
        
        # Recent movies
        recent_sql = """
            SELECT COUNT(*) FROM movies 
            WHERE scraped_at >= (
                SELECT MAX(scraped_at) - INTERVAL '1 day'
                FROM movies
            )
        """
        recent_result = db_select(recent_sql)
        recent_movies = recent_result[0][0] if recent_result else 0
        
        # Last scrape time
        last_scrape_sql = "SELECT MAX(scraped_at) FROM movies"
        last_scrape_result = db_select(last_scrape_sql)
        last_scrape = last_scrape_result[0][0].isoformat() if last_scrape_result and last_scrape_result[0][0] else None
        
        return jsonify({
            'success': True,
            'stats': {
                'total_movies_all_time': total_movies,
                'current_movies': recent_movies,
                'last_scrape': last_scrape
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/admin/trigger-enrichment', methods=['POST'])
def trigger_enrichment():
    """
    Manually trigger TMDB enrichment for unenriched movies
    Requires ADMIN_SECRET in X-Admin-Key header
    """
    # Check authentication
    admin_key = request.headers.get('X-Admin-Key')
    if not admin_key or admin_key != ADMIN_SECRET:
        return jsonify({
            'success': False,
            'error': 'Unauthorized'
        }), 401
    
    try:
        # Import enricher
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'deng' / 'enrichment'))
        from tmdb_enricher import TMDBEnricher
        
        # Get limit from request
        limit = request.json.get('limit', 50) if request.json else 50
        
        # Run enrichment
        enricher = TMDBEnricher()
        enriched_count = enricher.enrich_all_unenriched(limit=limit)
        
        return jsonify({
            'success': True,
            'enriched': enriched_count,
            'message': f'Successfully enriched {enriched_count} movies'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Ensure database tables exist
    try:
        create_tables()
        print("✅ Database tables verified")
    except Exception as e:
        print(f"⚠️  Warning: Could not verify database tables: {e}")
    
    print("\n" + "="*50)
    print("Indieflix API Server Starting")
    print("="*50)
    print("API Endpoints:")
    print("  GET  /health                    - Health check")
    print("  GET  /api/movies                - Get all movies")
    print("  GET  /api/movies/by-theater     - Movies grouped by theater")
    print("  GET  /api/theaters              - Get theater list")
    print("  GET  /api/search?q=query        - Search movies")
    print("  GET  /api/stats                 - Database statistics")
    print("")
    print("Admin Endpoints (requires X-Admin-Key header):")
    print("  POST /admin/trigger-enrichment  - Enrich with TMDB data")
    print("")
    print("💡 To run scrapers: Use Render Shell or SSH")
    print("   python3 deng/ingestion/metrograph_v2.py")
    print("   python3 deng/ingestion/syndicatedbk.py")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
