#!/usr/bin/env python3
"""
IFC Center Scraper V2
Scrapes movie schedules from IFC Center's homepage and detail pages
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))
from storage.postgres import insert_many_db, create_tables


class IFCCenterScraperV2:
    """Scraper for IFC Center"""
    
    def __init__(self):
        self.name = 'IFC Center'
        self.theater_id = 'ifc_center'
        self.base_url = 'https://www.ifccenter.com'
        self.home_url = self.base_url
        self.location = '323 Sixth Avenue, NYC'
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
    
    def parse_day_to_date(self, day_str: str, year: int = 2025) -> Optional[str]:
        """
        Parse day string like 'Mon Oct 6' to YYYY-MM-DD
        
        Args:
            day_str: String like "Mon Oct 6"
            year: Year to use (defaults to 2025)
        
        Returns:
            Date in YYYY-MM-DD format
        """
        try:
            # Extract "Oct 6" from "Mon Oct 6"
            match = re.search(r'(\w+)\s+(\d+)', day_str)
            if not match:
                return None
            
            month = match.group(1)
            day = match.group(2)
            
            # Parse the date
            date_string = f"{month} {day} {year}"
            parsed_date = datetime.strptime(date_string, "%b %d %Y")
            
            return parsed_date.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"  ⚠️  Error parsing date '{day_str}': {e}")
            return None
    
    def extract_movie_details(self, film_url: str) -> Dict:
        """
        Fetch and parse movie detail page
        
        Returns:
            Dict with director, year, runtime, cast, description
        """
        details = {}
        
        soup = self.fetch_page(film_url)
        if not soup:
            return details
        
        # Find film details list
        details_list = soup.find('ul', class_='film-details')
        if details_list:
            for li in details_list.find_all('li'):
                strong = li.find('strong')
                if not strong:
                    continue
                
                label = self.clean_text(strong.get_text()).lower()
                # Get text after the <strong> tag
                value = self.clean_text(li.get_text().replace(strong.get_text(), ''))
                
                if 'director' in label:
                    details['director'] = value
                elif 'running time' in label or 'runtime' in label:
                    # Extract minutes from "99 minutes"
                    runtime_match = re.search(r'(\d+)', value)
                    if runtime_match:
                        details['runtime'] = int(runtime_match.group(1))
                elif 'cast' in label:
                    details['cast'] = value
                elif 'country' in label:
                    details['country'] = value
        
        # Extract year from multiple possible locations
        year = None
        
        # Try date-time element
        date_elem = soup.find('p', class_='date-time')
        if date_elem:
            year_match = re.search(r'\b(19|20)\d{2}\b', date_elem.get_text())
            if year_match:
                year = int(year_match.group())
        
        # Try description text
        if not year:
            desc_text = soup.get_text()
            year_match = re.search(r'\b(19|20)\d{2}\b', desc_text)
            if year_match:
                year = int(year_match.group())
        
        if year:
            details['year'] = year
        
        # Extract description (first paragraph after title)
        title_elem = soup.find('h1', class_='title')
        if title_elem:
            # Find next paragraph
            next_p = title_elem.find_next('p')
            if next_p:
                desc = self.clean_text(next_p.get_text())
                if len(desc) > 20:
                    details['description'] = desc[:500]
        
        time.sleep(0.5)  # Be polite
        return details
    
    def scrape(self) -> List[Dict]:
        """Scrape IFC Center schedule"""
        print(f"\n{'='*60}")
        print(f"IFC CENTER - MOVIE SCRAPER")
        print(f"{'='*60}")
        
        soup = self.fetch_page(self.home_url)
        
        if not soup:
            print("❌ Failed to fetch homepage")
            return []
        
        all_movies = []
        
        # Find showtimes widget in sidebar
        showtimes_widget = soup.find('div', id='js-showtimes-widget')
        
        if not showtimes_widget:
            print("❌ Could not find showtimes widget")
            return []
        
        # Find all daily schedule sections
        daily_schedules = showtimes_widget.find_all('div', class_='daily-schedule')
        
        print(f"\n📅 Found {len(daily_schedules)} days of schedules")
        
        processed_films = {}  # Track films we've already fetched details for
        
        for schedule_idx, schedule in enumerate(daily_schedules, 1):
            # Skip "coming soon" section
            if 'show-coming-soon' in schedule.get('class', []):
                continue
            
            # Get the date
            date_header = schedule.find('h3')
            if not date_header:
                continue
            
            date_str = self.clean_text(date_header.get_text())
            iso_date = self.parse_day_to_date(date_str)
            
            if not iso_date:
                print(f"  ⚠️  Could not parse date: {date_str}")
                continue
            
            print(f"\n[{schedule_idx}/{len(daily_schedules)}] 📅 Processing {date_str} ({iso_date})")
            
            # Find all film items for this day
            film_items = schedule.find_all('li')
            
            for film_item in film_items:
                try:
                    # Get film title and link
                    title_link = film_item.find('h3')
                    if not title_link:
                        continue
                    
                    link_elem = title_link.find('a')
                    if not link_elem:
                        continue
                    
                    title = self.clean_text(link_elem.get_text())
                    film_url = link_elem.get('href')
                    
                    if not title or len(title) < 2:
                        continue
                    
                    # Make URL absolute
                    if film_url and not film_url.startswith('http'):
                        film_url = f"{self.base_url}{film_url}"
                    
                    # Get showtimes for this day
                    times_ul = film_item.find('ul', class_='times')
                    if not times_ul:
                        continue
                    
                    showtimes = []
                    for time_link in times_ul.find_all('a'):
                        time_text = self.clean_text(time_link.get_text())
                        if time_text:
                            showtimes.append(time_text)
                    
                    if not showtimes:
                        continue
                    
                    # Format dates string
                    dates_str = f"{iso_date} ({', '.join(showtimes)})"
                    
                    # Get film details (only fetch once per film)
                    director = None
                    year = None
                    description = None
                    
                    if film_url and film_url not in processed_films:
                        print(f"  🎬 {title}")
                        details = self.extract_movie_details(film_url)
                        processed_films[film_url] = details
                    else:
                        details = processed_films.get(film_url, {})
                    
                    director = details.get('director')
                    year = details.get('year')
                    description = details.get('description')
                    
                    # Create movie entry
                    movie = {
                        'title': title,
                        'theater': self.name,
                        'theater_id': self.theater_id,
                        'location': self.location,
                        'website': self.website,
                        'film_link': film_url,
                        'director': director,
                        'year': year,
                        'dates': dates_str,
                        'description': description,
                        'scraped_at': datetime.now()
                    }
                    
                    all_movies.append(movie)
                    print(f"    ✓ {iso_date}: {', '.join(showtimes)}")
                    
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
    scraper = IFCCenterScraperV2()
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
            sys.path.insert(0, str(Path(__file__).parent.parent / 'enrichment'))
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
