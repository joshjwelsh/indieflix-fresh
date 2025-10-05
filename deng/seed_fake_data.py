"""
Seed fake movie data for testing frontend
Run this to populate database with realistic test data
"""

import sys
from pathlib import Path
from datetime import datetime

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))
from storage.postgres import insert_many_db, create_tables, db_select

# Fake movie data for each theater
FAKE_MOVIES = {
    'ifc_center': [
        {
            'title': 'The Substance',
            'director': 'Coralie Fargeat',
            'year': 2024,
            'dates': 'Jan 5-12',
            'description': 'A fading celebrity decides to use a black market drug, a cell-replicating substance that temporarily creates a younger, better version of herself.'
        },
        {
            'title': 'All We Imagine as Light',
            'director': 'Payal Kapadia',
            'year': 2024,
            'dates': 'Now Playing',
            'description': 'Two nurses in Mumbai navigate life, love and longing in this poetic exploration of female friendship.'
        },
        {
            'title': 'The Brutalist',
            'director': 'Brady Corbet',
            'year': 2024,
            'dates': 'Jan 8-15',
            'description': 'Epic story of a visionary architect who flees post-war Europe for America, where he must grapple with the American Dream.'
        },
        {
            'title': 'Perfect Days',
            'director': 'Wim Wenders',
            'year': 2023,
            'dates': 'Jan 3-9',
            'description': 'Hirayama is content with his simple life as a cleaner of toilets in Tokyo, finding beauty in the everyday.'
        },
        {
            'title': 'Wicked Little Letters',
            'director': 'Thea Sharrock',
            'year': 2023,
            'dates': 'Check website for showtimes',
            'description': 'Based on a true story of poison pen letters in 1920s England that caused a scandal.'
        }
    ],
    'metrograph': [
        {
            'title': 'Anora',
            'director': 'Sean Baker',
            'year': 2024,
            'dates': 'Jan 1-7',
            'description': 'A young sex worker from Brooklyn gets her chance at a Cinderella story when she meets the son of an oligarch.'
        },
        {
            'title': 'Nosferatu',
            'director': 'Robert Eggers',
            'year': 2024,
            'dates': 'Now Playing',
            'description': 'A gothic tale of obsession between a haunted young woman and the terrifying vampire infatuated with her.'
        },
        {
            'title': 'A Complete Unknown',
            'director': 'James Mangold',
            'year': 2024,
            'dates': 'Jan 2-8',
            'description': "Bob Dylan's early years in New York and his meteoric rise to become a folk icon."
        },
        {
            'title': 'The Piano Lesson',
            'director': 'Malcolm Washington',
            'year': 2024,
            'dates': 'Jan 6-13',
            'description': 'A family dispute over an heirloom piano explodes, unleashing haunting truths about how the past is perceived.'
        },
        {
            'title': 'Sing Sing',
            'director': 'Greg Kwedar',
            'year': 2023,
            'dates': 'Check website for showtimes',
            'description': 'Divine G imprisoned at Sing Sing for a crime he did not commit finds purpose by acting in a theater group.'
        },
        {
            'title': 'The Wild Robot',
            'director': 'Chris Sanders',
            'year': 2024,
            'dates': 'Jan 4-10',
            'description': 'When a robot washes ashore on a deserted island, she must adapt to the harsh surroundings.'
        }
    ],
    'syndicated_bk': [
        {
            'title': 'Nickel Boys',
            'director': 'RaMell Ross',
            'year': 2024,
            'dates': 'Now Playing',
            'description': 'Based on Colson Whitehead\'s Pulitzer Prize-winning novel about a reform school in Jim Crow-era Florida.'
        },
        {
            'title': 'September 5',
            'director': 'Tim Fehlbaum',
            'year': 2024,
            'dates': 'Jan 5-11',
            'description': 'During the 1972 Munich Olympics, an American sports broadcasting crew must adapt to live coverage of Israeli athletes taken hostage.'
        },
        {
            'title': 'Emilia Pérez',
            'director': 'Jacques Audiard',
            'year': 2024,
            'dates': 'Jan 3-9',
            'description': 'A Mexican cartel leader undergoes gender-affirming surgery to become the woman she always wanted to be.'
        },
        {
            'title': 'Conclave',
            'director': 'Edward Berger',
            'year': 2024,
            'dates': 'Jan 7-14',
            'description': 'When the Pope dies, Cardinal Lawrence is tasked with managing the covert and ancient ritual of electing a new pope.'
        },
        {
            'title': 'Flow',
            'director': 'Gints Zilbalodis',
            'year': 2024,
            'dates': 'Check website for showtimes',
            'description': 'A cat embarks on an epic journey after a devastating flood submerges his home.'
        }
    ]
}

THEATER_INFO = {
    'ifc_center': {
        'name': 'IFC Center',
        'location': '323 Sixth Avenue, NYC',
        'website': 'https://www.ifccenter.com'
    },
    'metrograph': {
        'name': 'Metrograph',
        'location': '7 Ludlow Street, NYC',
        'website': 'https://metrograph.com'
    },
    'syndicated_bk': {
        'name': 'Syndicated BK',
        'location': '40 Bogart Street, Brooklyn',
        'website': 'https://syndicatedbk.com'
    }
}


def seed_fake_data():
    """Insert fake movie data into database"""
    print("=" * 60)
    print("SEEDING FAKE DATA FOR TESTING")
    print("=" * 60)
    
    # Ensure tables exist
    try:
        create_tables()
    except Exception as e:
        print(f"Warning: {e}")
    
    # Check if data already exists
    check_sql = "SELECT COUNT(*) FROM movies"
    try:
        result = db_select(check_sql)
        existing_count = result[0][0] if result else 0
        
        if existing_count > 0:
            print(f"\n⚠️  Database already contains {existing_count} movies.")
            response = input("Delete existing data and seed fresh? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled. No changes made.")
                return
            
            # Delete existing data
            from storage.postgres import db_execute
            db_execute("DELETE FROM movies")
            print("✅ Existing data deleted")
    except Exception as e:
        print(f"Note: {e}")
    
    # Prepare all data for bulk insert
    all_movies = []
    columns = ['title', 'theater', 'theater_id', 'location', 'website', 
               'director', 'year', 'dates', 'description', 'scraped_at']
    
    scraped_at = datetime.now().isoformat()
    
    for theater_id, movies in FAKE_MOVIES.items():
        theater_info = THEATER_INFO[theater_id]
        
        print(f"\n📽️  {theater_info['name']}: {len(movies)} movies")
        
        for movie in movies:
            all_movies.append((
                movie['title'],
                theater_info['name'],
                theater_id,
                theater_info['location'],
                theater_info['website'],
                movie.get('director'),
                movie.get('year'),
                movie.get('dates'),
                movie.get('description'),
                scraped_at
            ))
            print(f"   ✓ {movie['title']}")
    
    # Insert all data
    try:
        insert_many_db('movies', columns, all_movies)
        print(f"\n{'='*60}")
        print(f"✅ SUCCESS: Inserted {len(all_movies)} fake movies")
        print(f"{'='*60}")
        print("\nYou can now:")
        print("1. Start the backend: cd backend/api && python app.py")
        print("2. Start the frontend: cd frontend && python -m http.server 8000")
        print("3. Visit: http://localhost:8000")
        print()
    except Exception as e:
        print(f"\n❌ Error inserting data: {e}")


if __name__ == '__main__':
    seed_fake_data()
