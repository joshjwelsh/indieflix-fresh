"""
Metrograph Theater Scraper
Scrapes movie schedules from Metrograph in NYC
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))
from storage.postgres import insert_many_db, create_tables


class MetrographScraper:
    """Scraper for Metrograph"""
    
    def __init__(self):
        self.name = 'Metrograph'
        self.url = 'https://metrograph.com/now-playing/'
        self.location = '7 Ludlow Street, NYC'
        self.website = 'https://metrograph.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page"""
        try:
            print(f"Fetching {url}...")
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def extract_year(self, text: str) -> Optional[int]:
        """Extract year from text"""
        match = re.search(r'\b(19|20)\d{2}\b', text)
        return int(match.group()) if match else None
    
    def scrape(self) -> List[Dict]:
        """Scrape Metrograph schedule"""
        print(f"\n{'='*50}")
        print(f"Scraping {self.name}")
        print(f"{'='*50}")
        
        soup = self.fetch_page(self.url)
        
        if not soup:
            print("Failed to fetch page")
            return []
        
        movies = []
        
        # Try multiple potential selectors specific to Metrograph
        selectors = [
            ('article', {'class': re.compile('film|movie|screening|card', re.I)}),
            ('div', {'class': re.compile('film|movie|screening|card', re.I)}),
            ('div', {'class': 'film-item'}),
            ('article', {}),  # Try all articles
        ]
        
        film_items = []
        for tag, attrs in selectors:
            film_items = soup.find_all(tag, attrs)
            if film_items:
                print(f"Found {len(film_items)} items using selector: {tag} {attrs}")
                break
        
        if not film_items:
            print("No film items found, trying generic approach...")
            film_items = soup.find_all(['div', 'article'])[:20]
        
        for item in film_items[:15]:
            try:
                # Try to find title
                title = None
                for tag in ['h1', 'h2', 'h3', 'h4']:
                    title_elem = item.find(tag)
                    if title_elem:
                        title = self.clean_text(title_elem.get_text())
                        break
                
                # Try link text if no header found
                if not title:
                    link = item.find('a', class_=re.compile('title|film|movie', re.I))
                    if link and link.get_text():
                        title = self.clean_text(link.get_text())
                
                # Fallback to any link
                if not title:
                    link = item.find('a')
                    if link and link.get_text():
                        title = self.clean_text(link.get_text())
                
                # Skip if title is too short or invalid
                if not title or len(title) < 3:
                    continue
                
                # Skip common navigation/header text
                skip_terms = ['home', 'about', 'contact', 'menu', 'search', 'login', 'cart', 'calendar', 'events']
                if any(term in title.lower() for term in skip_terms):
                    continue
                
                movie = {
                    'title': title,
                    'theater': self.name,
                    'theater_id': 'metrograph',
                    'location': self.location,
                    'website': self.website,
                    'scraped_at': datetime.now().isoformat()
                }
                
                # Try to extract director
                director_elem = item.find(['p', 'div', 'span'], class_=re.compile('director|filmmaker|by', re.I))
                if director_elem:
                    director_text = self.clean_text(director_elem.get_text())
                    director_text = re.sub(r'^(directed by|by|dir\.?)\s*', '', director_text, flags=re.I)
                    movie['director'] = director_text
                
                # Try to extract dates/showtimes
                date_elem = item.find(['p', 'div', 'span', 'time'], class_=re.compile('date|time|showing|screening|schedule|run', re.I))
                if date_elem:
                    movie['dates'] = self.clean_text(date_elem.get_text())
                else:
                    movie['dates'] = 'Check website for showtimes'
                
                # Try to extract year
                year = self.extract_year(item.get_text())
                if year:
                    movie['year'] = year
                
                # Try to extract description
                desc_elem = item.find(['p', 'div'], class_=re.compile('description|synopsis|summary|excerpt', re.I))
                if desc_elem:
                    desc = self.clean_text(desc_elem.get_text())
                    if len(desc) > 20:
                        movie['description'] = desc[:300]
                
                movies.append(movie)
                print(f"  ✓ {title}")
            
            except Exception as e:
                print(f"  ✗ Error parsing item: {e}")
                continue
        
        print(f"\n{'='*50}")
        print(f"Extracted {len(movies)} movies from {self.name}")
        print(f"{'='*50}\n")
        
        return movies


def save_to_db(movies: List[Dict]) -> None:
    """Save movies to PostgreSQL database"""
    if not movies:
        print("No movies to save")
        return
    
    # Prepare data for bulk insert
    columns = ['title', 'theater', 'theater_id', 'location', 'website', 
               'director', 'year', 'dates', 'description', 'scraped_at']
    
    values = []
    for movie in movies:
        values.append((
            movie.get('title'),
            movie.get('theater'),
            movie.get('theater_id'),
            movie.get('location'),
            movie.get('website'),
            movie.get('director'),
            movie.get('year'),
            movie.get('dates'),
            movie.get('description'),
            movie.get('scraped_at')
        ))
    
    try:
        insert_many_db('movies', columns, values)
        print(f"\n💾 Saved {len(movies)} movies to database")
    except Exception as e:
        print(f"\n❌ Error saving to database: {e}")


def main():
    """Run scraper as standalone script"""
    # Ensure tables exist
    try:
        create_tables()
    except Exception as e:
        print(f"Warning: Could not verify tables: {e}")
    
    scraper = MetrographScraper()
    movies = scraper.scrape()
    
    print("\nMovies found:")
    for i, movie in enumerate(movies, 1):
        print(f"\n{i}. {movie['title']}")
        if 'director' in movie:
            print(f"   Director: {movie['director']}")
        if 'year' in movie:
            print(f"   Year: {movie['year']}")
        print(f"   Dates: {movie['dates']}")
    
    # Save to database
    save_to_db(movies)


if __name__ == '__main__':
    main()
