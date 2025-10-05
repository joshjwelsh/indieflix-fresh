"""
Metrograph Theater Scraper V2
Scrapes movie schedules from Metrograph NYC with improved date handling
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
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


class MetrographScraperV2:
    """Enhanced scraper for Metrograph with date-specific scraping"""
    
    def __init__(self):
        self.name = 'Metrograph'
        self.theater_id = 'metrograph'
        self.base_url = 'https://metrograph.com'
        self.schedule_url = f'{self.base_url}/nyc/'
        self.location = '7 Ludlow Street, NYC'
        self.website = self.base_url
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
    
    def parse_metadata(self, metadata: str) -> tuple:
        """
        Parse metadata string to extract director and year
        
        Args:
            metadata: String like "Directed by Coralie Fargeat, 2024, 35mm"
        
        Returns:
            Tuple of (director, year)
        """
        director = None
        year = None
        
        if not metadata:
            return director, year
        
        # Extract year (4-digit number)
        year_match = re.search(r'\b(19|20)\d{2}\b', metadata)
        if year_match:
            year = int(year_match.group())
        
        # Extract director (text after "Directed by" or similar)
        director_match = re.search(
            r'(?:Directed by|Dir\.?|By)\s+([^,\d]+)',
            metadata,
            re.IGNORECASE
        )
        if director_match:
            director = self.clean_text(director_match.group(1))
        
        return director, year
    
    def get_available_dates(self) -> List[str]:
        """Get all future dates that have showtimes scheduled"""
        print(f"\n📅 Fetching available dates from {self.name}...")
        
        soup = self.fetch_page(self.schedule_url)
        if not soup:
            return []
        
        date_links = soup.find_all('a', class_='day-selector-day')
        
        available_dates = []
        for link in date_links:
            date = link.get('data-vars-ga-label')
            classes = link.get('class', [])
            
            # Only get dates that have showtimes
            if date and 'closed' not in classes and 'unscheduled' not in classes:
                available_dates.append(date)
        
        print(f"  ✓ Found {len(available_dates)} dates with showtimes")
        if available_dates:
            print(f"  📆 Date range: {available_dates[0]} to {available_dates[-1]}")
        
        return available_dates
    
    def get_movies_for_date(self, date_str: str) -> List[Dict]:
        """Get all movies for a specific date"""
        url = f"{self.schedule_url}?date={date_str}"
        soup = self.fetch_page(url)
        
        if not soup:
            return []
        
        # Find the specific date section
        day_section = soup.find('div', id=f'calendar-list-day-{date_str}')
        
        if not day_section:
            return []
        
        movies = []
        movie_items = day_section.find_all('div', class_='film-thumbnail')
        
        for item in movie_items:
            try:
                # Extract title
                title_elem = item.find('a', class_='title')
                if not title_elem:
                    continue
                
                title = self.clean_text(title_elem.get_text())
                if not title or len(title) < 2:
                    continue
                
                # Extract film link
                film_path = title_elem.get('href')
                film_link = urljoin(self.base_url, film_path) if film_path else None
                
                # Extract metadata (director, year, format)
                metadata_elem = item.find('div', class_='film-metadata')
                metadata = self.clean_text(metadata_elem.get_text()) if metadata_elem else None
                
                # Parse director and year from metadata
                director, year = self.parse_metadata(metadata)
                
                # Extract description (Q&A, intro, etc.)
                description_elem = item.find('div', class_='film-description')
                description = self.clean_text(description_elem.get_text()) if description_elem else None
                
                # Extract showtimes
                showtimes_div = item.find('div', class_='showtimes')
                showtimes = []
                if showtimes_div:
                    time_links = showtimes_div.find_all('a')
                    for link in time_links:
                        time_text = self.clean_text(link.get_text())
                        if time_text:
                            showtimes.append(time_text)
                
                # Format dates string
                dates_str = f"{date_str}"
                if showtimes:
                    dates_str += f" ({', '.join(showtimes[:3])})"  # Show first 3 showtimes
                
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
                
                movies.append(movie)
                
            except Exception as e:
                print(f"  ⚠️  Error parsing movie item: {e}")
                continue
        
        return movies
    
    def scrape(self) -> List[Dict]:
        """Scrape Metrograph schedule for all available dates"""
        print(f"\n{'='*60}")
        print(f"METROGRAPH NYC - MOVIE SCRAPER V2")
        print(f"{'='*60}")
        
        # Get all available dates
        available_dates = self.get_available_dates()
        
        if not available_dates:
            print("❌ No available dates found")
            return []
        
        # Fetch movies for each date
        all_movies = []
        
        for i, date in enumerate(available_dates, 1):
            print(f"\n[{i}/{len(available_dates)}] 🎬 Fetching movies for {date}...")
            movies = self.get_movies_for_date(date)
            
            if movies:
                all_movies.extend(movies)
                print(f"  ✓ Found {len(movies)} movies")
                for movie in movies:
                    print(f"    • {movie['title']}")
            else:
                print(f"  ⚠️  No movies found")
            
            # Be polite to the server
            if i < len(available_dates):
                time.sleep(0.5)
        
        print(f"\n{'='*60}")
        print(f"✅ TOTAL MOVIES FOUND: {len(all_movies)}")
        print(f"{'='*60}\n")
        
        return all_movies


def save_to_db(movies: List[Dict]) -> None:
    """Save movies to PostgreSQL database"""
    if not movies:
        print("⚠️  No movies to save")
        return
    
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
    
    try:
        insert_many_db('movies', columns, values)
        print(f"💾 Successfully saved {len(movies)} movies to database")
    except Exception as e:
        print(f"❌ Error saving to database: {e}")


def main():
    """Run scraper as standalone script"""
    # Ensure tables exist
    try:
        create_tables()
    except Exception as e:
        print(f"⚠️  Warning: Could not verify tables: {e}")
    
    # Run scraper
    scraper = MetrographScraperV2()
    movies = scraper.scrape()
    
    # Display summary
    if movies:
        print("\n📊 SUMMARY")
        print("=" * 60)
        unique_titles = len(set(m['title'] for m in movies))
        print(f"Total entries: {len(movies)}")
        print(f"Unique titles: {unique_titles}")
        print(f"Date range covered: {len(set(m['dates'] for m in movies))} unique date strings")
        
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
