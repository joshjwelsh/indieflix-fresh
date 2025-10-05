"""
TMDB Movie Enricher
Enriches movie data with posters and metadata from The Movie Database (TMDB)
"""

import os
import sys
import requests
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path
from dotenv import load_dotenv

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))
from storage.postgres import db_select, update_db, create_tables

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)


class TMDBEnricher:
    """Enrich movie data with TMDB metadata"""
    
    def __init__(self):
        self.api_key = os.getenv('TMDB_API_KEY')
        if not self.api_key:
            raise ValueError("TMDB_API_KEY not found in environment variables")
        
        self.base_url = 'https://api.themoviedb.org/3'
        self.image_base_url = os.getenv('TMDB_BASE_IMAGE_URL', 'https://image.tmdb.org/t/p/')
        self.poster_size = 'w342'  # Smaller size for faster loading
        self.backdrop_size = 'w780'
        
        # Rate limiting: 40 requests per 10 seconds
        self.request_times = []
        self.max_requests_per_window = 40
        self.window_seconds = 10
    
    def _wait_if_needed(self):
        """Implement rate limiting"""
        now = time.time()
        
        # Remove requests older than the window
        self.request_times = [t for t in self.request_times if now - t < self.window_seconds]
        
        # If we're at the limit, wait
        if len(self.request_times) >= self.max_requests_per_window:
            sleep_time = self.window_seconds - (now - self.request_times[0])
            if sleep_time > 0:
                print(f"  ⏳ Rate limit reached, waiting {sleep_time:.1f}s...")
                time.sleep(sleep_time)
                self.request_times = []
        
        self.request_times.append(time.time())
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with rate limiting"""
        self._wait_if_needed()
        
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  ⚠️  API request failed: {e}")
            return None
    
    def search_movie(self, title: str, year: Optional[int] = None, 
                     director: Optional[str] = None) -> Optional[Dict]:
        """
        Search for movie on TMDB using multiple strategies
        
        Args:
            title: Movie title
            year: Release year (optional)
            director: Director name (optional)
        
        Returns:
            Movie data dict or None if not found
        """
        # Strategy 1: Search with title and year (most accurate)
        if year:
            params = {'query': title, 'year': year}
            data = self._make_request('search/movie', params)
            
            if data and data.get('results'):
                result = data['results'][0]
                # Verify year matches
                if result.get('release_date', '').startswith(str(year)):
                    return result
        
        # Strategy 2: Search with title and verify director
        if director:
            params = {'query': title}
            data = self._make_request('search/movie', params)
            
            if data and data.get('results'):
                for result in data['results'][:3]:  # Check top 3 results
                    # Get movie details to check director
                    movie_id = result['id']
                    credits = self._make_request(f'movie/{movie_id}/credits')
                    
                    if credits and credits.get('crew'):
                        directors = [
                            person['name'] for person in credits['crew']
                            if person.get('job') == 'Director'
                        ]
                        
                        # Check if director matches (case-insensitive partial match)
                        if any(director.lower() in d.lower() or d.lower() in director.lower() 
                               for d in directors):
                            return result
        
        # Strategy 3: Search by title only (fallback)
        params = {'query': title}
        data = self._make_request('search/movie', params)
        
        if data and data.get('results'):
            # Return first result if it has good popularity
            result = data['results'][0]
            if result.get('popularity', 0) > 5:  # Basic quality filter
                return result
        
        return None
    
    def get_movie_details(self, tmdb_id: int) -> Optional[Dict]:
        """Get full movie details including credits"""
        movie = self._make_request(f'movie/{tmdb_id}')
        
        if not movie:
            return None
        
        # Get credits for cast
        credits = self._make_request(f'movie/{tmdb_id}/credits')
        
        return {
            'movie': movie,
            'credits': credits
        }
    
    def format_runtime(self, minutes: int) -> str:
        """Format runtime in minutes to human readable string"""
        if not minutes:
            return None
        
        hours = minutes // 60
        mins = minutes % 60
        
        if hours > 0:
            return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
        return f"{mins}m"
    
    def enrich_movie(self, movie_id: int, title: str, year: Optional[int] = None,
                     director: Optional[str] = None) -> bool:
        """
        Enrich a single movie with TMDB data
        
        Args:
            movie_id: Database movie ID
            title: Movie title
            year: Release year (optional)
            director: Director name (optional)
        
        Returns:
            True if enrichment successful, False otherwise
        """
        # Search for movie
        search_result = self.search_movie(title, year, director)
        
        if not search_result:
            print(f"  ❌ No TMDB match found for: {title}")
            return False
        
        tmdb_id = search_result['id']
        
        # Get full details
        details = self.get_movie_details(tmdb_id)
        
        if not details:
            print(f"  ❌ Could not fetch details for TMDB ID {tmdb_id}")
            return False
        
        movie_data = details['movie']
        credits_data = details.get('credits', {})
        
        # Extract data
        poster_path = movie_data.get('poster_path')
        backdrop_path = movie_data.get('backdrop_path')
        
        poster_url = f"{self.image_base_url}{self.poster_size}{poster_path}" if poster_path else None
        backdrop_url = f"{self.image_base_url}{self.backdrop_size}{backdrop_path}" if backdrop_path else None
        
        runtime = movie_data.get('runtime')
        rating = movie_data.get('vote_average')
        
        # Get genres
        genres = ', '.join([g['name'] for g in movie_data.get('genres', [])])
        
        # Get top 3 cast members
        cast_list = credits_data.get('cast', [])[:3]
        cast_members = ', '.join([person['name'] for person in cast_list])
        
        overview = movie_data.get('overview')
        
        # Update database
        update_data = {
            'tmdb_id': tmdb_id,
            'poster_url': poster_url,
            'backdrop_url': backdrop_url,
            'runtime': runtime,
            'tmdb_rating': rating,
            'genres': genres,
            'cast_members': cast_members,
            'tmdb_overview': overview,
            'enriched_at': datetime.now()
        }
        
        try:
            update_db('movies', update_data, 'id = %s', (movie_id,))
            print(f"  ✓ Enriched: {title}")
            return True
        except Exception as e:
            print(f"  ❌ Database update failed: {e}")
            return False
    
    def enrich_all_unenriched(self, limit: Optional[int] = None) -> int:
        """
        Enrich all movies that haven't been enriched yet
        
        Args:
            limit: Maximum number of movies to enrich (None for all)
        
        Returns:
            Number of movies enriched
        """
        print(f"\n{'='*60}")
        print("TMDB ENRICHMENT - ALL UNENRICHED MOVIES")
        print(f"{'='*60}\n")
        
        # Get unenriched movies
        sql = """
            SELECT id, title, year, director
            FROM movies
            WHERE enriched_at IS NULL
            ORDER BY scraped_at DESC
        """
        
        if limit:
            sql += f" LIMIT {limit}"
        
        movies = db_select(sql)
        
        if not movies:
            print("✅ No unenriched movies found")
            return 0
        
        print(f"📊 Found {len(movies)} unenriched movies\n")
        
        enriched_count = 0
        
        for idx, (movie_id, title, year, director) in enumerate(movies, 1):
            print(f"[{idx}/{len(movies)}] Processing: {title}")
            
            if self.enrich_movie(movie_id, title, year, director):
                enriched_count += 1
            
            # Small delay between movies
            time.sleep(0.2)
        
        print(f"\n{'='*60}")
        print(f"✅ ENRICHMENT COMPLETE")
        print(f"   Enriched: {enriched_count}/{len(movies)}")
        print(f"{'='*60}\n")
        
        return enriched_count
    
    def enrich_recent(self, hours: int = 24) -> int:
        """
        Enrich movies scraped in the last N hours
        
        Args:
            hours: Number of hours to look back
        
        Returns:
            Number of movies enriched
        """
        print(f"\n{'='*60}")
        print(f"TMDB ENRICHMENT - RECENT MOVIES (last {hours}h)")
        print(f"{'='*60}\n")
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        sql = """
            SELECT id, title, year, director
            FROM movies
            WHERE scraped_at >= %s
                AND enriched_at IS NULL
            ORDER BY scraped_at DESC
        """
        
        movies = db_select(sql, (cutoff,))
        
        if not movies:
            print(f"✅ No unenriched movies from last {hours} hours")
            return 0
        
        print(f"📊 Found {len(movies)} unenriched movies\n")
        
        enriched_count = 0
        
        for idx, (movie_id, title, year, director) in enumerate(movies, 1):
            print(f"[{idx}/{len(movies)}] Processing: {title}")
            
            if self.enrich_movie(movie_id, title, year, director):
                enriched_count += 1
            
            time.sleep(0.2)
        
        print(f"\n{'='*60}")
        print(f"✅ ENRICHMENT COMPLETE")
        print(f"   Enriched: {enriched_count}/{len(movies)}")
        print(f"{'='*60}\n")
        
        return enriched_count
    
    def re_enrich_stale(self, days: int = 30, limit: Optional[int] = None) -> int:
        """
        Re-enrich movies that were enriched more than N days ago
        
        Args:
            days: Age threshold in days
            limit: Maximum number to re-enrich
        
        Returns:
            Number of movies re-enriched
        """
        print(f"\n{'='*60}")
        print(f"TMDB RE-ENRICHMENT - STALE DATA (>{days} days old)")
        print(f"{'='*60}\n")
        
        cutoff = datetime.now() - timedelta(days=days)
        
        sql = """
            SELECT id, title, year, director
            FROM movies
            WHERE enriched_at < %s
            ORDER BY enriched_at ASC
        """
        
        if limit:
            sql += f" LIMIT {limit}"
        
        movies = db_select(sql, (cutoff,))
        
        if not movies:
            print(f"✅ No stale enrichment data found")
            return 0
        
        print(f"📊 Found {len(movies)} movies with stale data\n")
        
        enriched_count = 0
        
        for idx, (movie_id, title, year, director) in enumerate(movies, 1):
            print(f"[{idx}/{len(movies)}] Re-enriching: {title}")
            
            if self.enrich_movie(movie_id, title, year, director):
                enriched_count += 1
            
            time.sleep(0.2)
        
        print(f"\n{'='*60}")
        print(f"✅ RE-ENRICHMENT COMPLETE")
        print(f"   Re-enriched: {enriched_count}/{len(movies)}")
        print(f"{'='*60}\n")
        
        return enriched_count


def main():
    """Run enricher as standalone script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich movie data with TMDB')
    parser.add_argument('--recent', type=int, metavar='HOURS',
                       help='Enrich movies from last N hours')
    parser.add_argument('--all', action='store_true',
                       help='Enrich all unenriched movies')
    parser.add_argument('--stale', type=int, metavar='DAYS',
                       help='Re-enrich movies older than N days')
    parser.add_argument('--limit', type=int,
                       help='Limit number of movies to process')
    
    args = parser.parse_args()
    
    # Ensure tables exist
    try:
        create_tables()
    except Exception as e:
        print(f"⚠️  Warning: Could not verify tables: {e}")
    
    # Create enricher
    try:
        enricher = TMDBEnricher()
    except ValueError as e:
        print(f"❌ {e}")
        print("Please set TMDB_API_KEY in your .env file")
        return
    
    # Run appropriate enrichment
    if args.recent:
        enricher.enrich_recent(hours=args.recent)
    elif args.all:
        enricher.enrich_all_unenriched(limit=args.limit)
    elif args.stale:
        enricher.re_enrich_stale(days=args.stale, limit=args.limit)
    else:
        # Default: enrich recent (last 24 hours)
        enricher.enrich_recent(hours=24)


if __name__ == '__main__':
    main()
