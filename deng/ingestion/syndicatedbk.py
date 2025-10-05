"""
Syndicated Bar Theater Kitchen Scraper
Scrapes movie schedules from Syndicated BK in Brooklyn
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))
from storage.postgres import insert_many_db, create_tables

# Add enrichment to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'enrichment'))


class SyndicatedBKScraper:
    """Scraper for Syndicated Bar Theater Kitchen"""
    
    def __init__(self):
        self.name = 'Syndicated BK'
        self.theater_id = 'syndicated_bk'
        self.base_url = 'https://ticketing.useast.veezi.com'
        self.sessions_url = f'{self.base_url}/sessions/?siteToken=dxdq5wzbef6bz2sjqt83ytzn1c'
        self.location = '40 Bogart St, Brooklyn, NY'
        self.website = 'http://syndicatedbk.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page"""
        try:
            print(f"  Fetching {url}...")
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"  ❌ Error fetching {url}: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def parse_date_to_iso(self, date_str: str, year: int = 2025) -> Optional[str]:
        """
        Parse date string to YYYY-MM-DD format
        
        Args:
            date_str: Date like "Friday 10, October" or "Sunday 5, October"
            year: Year to use (defaults to 2025)
        
        Returns:
            Date in YYYY-MM-DD format or None
        """
        try:
            # Extract day and month from format like "Friday 10, October"
            match = re.search(r'(\d+),\s+(\w+)', date_str)
            if not match:
                return None
            
            day = match.group(1)
            month = match.group(2)
            
            # Create date string and parse
            date_string = f"{day} {month} {year}"
            parsed_date = datetime.strptime(date_string, "%d %B %Y")
            
            return parsed_date.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"  ⚠️  Error parsing date '{date_str}': {e}")
            return None
    
    def parse_metadata(self, description: str) -> tuple:
        """
        Parse description to extract director and year
        
        Args:
            description: Full movie description text
        
        Returns:
            Tuple of (director, year)
        """
        director = None
        year = None
        
        if not description:
            return director, year
        
        # Extract year (4-digit number)
        year_match = re.search(r'\b(19|20)\d{2}\b', description)
        if year_match:
            year = int(year_match.group())
        
        # Extract director (look for common patterns)
        director_patterns = [
            r'[Dd]irected by\s+([^,.\n]+)',
            r'[Dd]irector[:\s]+([^,.\n]+)',
            r'[Dd]ir\.?\s+([^,.\n]+)',
        ]
        
        for pattern in director_patterns:
            director_match = re.search(pattern, description)
            if director_match:
                director = self.clean_text(director_match.group(1))
                # Clean up common trailing text
                director = re.sub(r'\s+(stars?|starring|features?|with).*$', '', director, flags=re.IGNORECASE)
                break
        
        return director, year
    
    def scrape(self) -> List[Dict]:
        """Scrape Syndicated BK schedule for all movies and dates"""
        print(f"\n{'='*60}")
        print(f"SYNDICATED BK - MOVIE SCRAPER")
        print(f"{'='*60}")
        
        soup = self.fetch_page(self.sessions_url)
        
        if not soup:
            print("❌ Failed to fetch sessions page")
            return []
        
        # Find the "Sort by film" section which has complete data
        by_film_section = soup.find('div', id='sessionsByFilmConent')
        
        if not by_film_section:
            print("❌ Could not find 'by film' section")
            return []
        
        all_movies = []
        film_items = by_film_section.find_all('div', class_='film')
        
        print(f"\n📅 Found {len(film_items)} unique films")
        
        for film_idx, film in enumerate(film_items, 1):
            try:
                # Extract title
                title_elem = film.find('h3', class_='title')
                if not title_elem:
                    continue
                
                title = self.clean_text(title_elem.get_text())
                if not title or len(title) < 2:
                    continue
                
                print(f"\n[{film_idx}/{len(film_items)}] 🎬 Processing: {title}")
                
                # Extract description
                desc_elem = film.find('p', class_='film-desc')
                description = self.clean_text(desc_elem.get_text()) if desc_elem else None
                
                # Parse metadata from description
                director, year = self.parse_metadata(description)
                
                # Extract rating/censor
                censor_elem = film.find('span', class_='censor')
                rating = self.clean_text(censor_elem.get_text()) if censor_elem else None
                
                # Find all date containers for this film
                date_containers = film.find_all('div', class_='date-container')
                
                if not date_containers:
                    print(f"  ⚠️  No dates found")
                    continue
                
                # Process each date
                for date_container in date_containers:
                    # Get the date
                    date_header = date_container.find('h4', class_='date')
                    if not date_header:
                        continue
                    
                    date_str = self.clean_text(date_header.get_text())
                    iso_date = self.parse_date_to_iso(date_str)
                    
                    if not iso_date:
                        print(f"  ⚠️  Could not parse date: {date_str}")
                        continue
                    
                    # Extract all showtimes for this date
                    session_times = date_container.find('ul', class_='session-times')
                    if not session_times:
                        continue
                    
                    time_links = session_times.find_all('a')
                    showtimes = []
                    film_link = None
                    
                    for link in time_links:
                        time_elem = link.find('time')
                        if time_elem:
                            showtime = self.clean_text(time_elem.get_text())
                            if showtime:
                                showtimes.append(showtime)
                        
                        # Get film link from first showtime link
                        if not film_link and link.get('href'):
                            href = link.get('href')
                            if href.startswith('http'):
                                film_link = href
                            else:
                                film_link = f"{self.base_url}{href}"
                    
                    if not showtimes:
                        continue
                    
                    # Format dates string with showtimes
                    dates_str = f"{iso_date} ({', '.join(showtimes)})"
                    
                    # Create movie entry for this specific date
                    movie = {
                        'title': title,
                        'theater': self.name,
                        'theater_id': self.theater_id,
                        'location': self.location,
                        'website': self.website,
                        'film_link': film_link,
                        'director': director,
                        'year': year,
                        'dates': dates_str,
                        'description': description,
                        'scraped_at': datetime.now()
                    }
                    
                    all_movies.append(movie)
                    print(f"  ✓ {iso_date}: {', '.join(showtimes)}")
                
            except Exception as e:
                print(f"  ⚠️  Error parsing film: {e}")
                continue
        
        print(f"\n{'='*60}")
        print(f"✅ TOTAL ENTRIES CREATED: {len(all_movies)}")
        print(f"{'='*60}\n")
        
        return all_movies


def save_to_db(movies: List[Dict]) -> None:
    """Save movies to PostgreSQL database"""
    if not movies:
        print("⚠️  No movies to save")
        return
    
    print(f"💾 Preparing to save {len(movies)} entries...")
    
    # Prepare data for bulk insert
    columns = ['title', 'theater', 'theater_id', 'location', 'website', 'film_link',
               'director', 'year', 'dates', 'description', 'scraped_at']
    
    values = []
    for movie in movies:
        values.append((
            movie.get('title'),
            movie.get('theater'),
            movie.get('theater_id'),
            movie.get('location'),
            movie.get('website'),
            movie.get('film_link'),
            movie.get('director'),
            movie.get('year'),
            movie.get('dates'),
            movie.get('description'),
            movie.get('scraped_at')
        ))
    
    print(f"  ✓ Data prepared. Columns: {len(columns)}, Rows: {len(values)}")
    print(f"  ✓ First row sample: {values[0][:3]}...")
    
    try:
        print("  → Calling insert_many_db()...")
        insert_many_db('movies', columns, values)
        print(f"💾 Successfully saved {len(movies)} entries to database")
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")


def main():
    """Run scraper as standalone script"""
    # Ensure tables exist
    try:
        create_tables()
    except Exception as e:
        print(f"⚠️  Warning: Could not verify tables: {e}")
    
    # Run scraper
    scraper = SyndicatedBKScraper()
    movies = scraper.scrape()
    
    # Display summary
    if movies:
        print("\n📊 SUMMARY")
        print("=" * 60)
        unique_titles = len(set(m['title'] for m in movies))
        unique_dates = len(set(m['dates'].split()[0] for m in movies))
        print(f"Total entries: {len(movies)}")
        print(f"Unique titles: {unique_titles}")
        print(f"Unique dates: {unique_dates}")
        
        # Save to database
        print("\n💾 Saving to database...")
        save_to_db(movies)
        
        # Enrich with TMDB data
        print("\n🎬 Enriching with TMDB data...")
        try:
            from tmdb_enricher import TMDBEnricher
            enricher = TMDBEnricher()
            enricher.enrich_recent(hours=1)
        except Exception as e:
            print(f"⚠️  TMDB enrichment failed (non-critical): {e}")
            print("   Movies saved successfully without enrichment")
    else:
        print("❌ No movies scraped")


if __name__ == '__main__':
    main()
