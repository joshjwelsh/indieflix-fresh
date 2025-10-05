"""
PostgreSQL Database Utilities for Indieflix
No ORM - direct SQL with psycopg2 and pandas support
"""

import os
import psycopg2
import pandas as pd
from typing import Optional, List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)


def get_db_config() -> Dict[str, Any]:
    """Get database configuration from environment variables"""
    return {
        'host': os.getenv('DB_HOST', 'indieflix-db'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'indieflix'),
        'user': os.getenv('DB_USER', 'indieflix'),
        'password': os.getenv('DB_PASSWORD', 'mypassword')
    }


def db_conn():
    """
    Create and return a database connection
    
    Returns:
        psycopg2 connection object
    
    Example:
        conn = db_conn()
        try:
            # use connection
            pass
        finally:
            conn.close()
    """
    config = get_db_config()
    return psycopg2.connect(**config)


def db_execute(sql: str, params: Optional[tuple] = None, fetch: bool = False) -> Optional[List[tuple]]:
    """
    Execute SQL statement (INSERT, UPDATE, DELETE, or SELECT)
    
    Args:
        sql: SQL statement to execute
        params: Optional tuple of parameters for parameterized query
        fetch: If True, fetch and return results (for SELECT queries)
    
    Returns:
        List of tuples if fetch=True, None otherwise
    
    Example:
        # Insert
        db_execute(
            "INSERT INTO movies (title, theater) VALUES (%s, %s)",
            ("The Substance", "IFC Center")
        )
        
        # Select
        results = db_execute(
            "SELECT * FROM movies WHERE theater = %s",
            ("IFC Center",),
            fetch=True
        )
    """
    conn = db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            
            if fetch:
                results = cur.fetchall()
                return results
            else:
                conn.commit()
                return None
    finally:
        conn.close()


def db_select(sql: str, params: Optional[tuple] = None) -> List[tuple]:
    """
    Execute SELECT query and return results
    
    Args:
        sql: SELECT SQL statement
        params: Optional tuple of parameters for parameterized query
    
    Returns:
        List of tuples containing query results
    
    Example:
        movies = db_select("SELECT * FROM movies WHERE year = %s", (2024,))
    """
    return db_execute(sql, params, fetch=True)


def db_select_df(sql: str, params: Optional[tuple] = None) -> pd.DataFrame:
    """
    Execute SELECT query and return results as pandas DataFrame
    
    Args:
        sql: SELECT SQL statement
        params: Optional tuple of parameters for parameterized query
    
    Returns:
        pandas DataFrame containing query results
    
    Example:
        df = db_select_df("SELECT * FROM movies WHERE theater = %s", ("IFC Center",))
        print(df.head())
    """
    conn = db_conn()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
        return df
    finally:
        conn.close()


def insert_db(table: str, data: Dict[str, Any]) -> None:
    """
    Insert a single row into a table
    
    Args:
        table: Table name
        data: Dictionary of column:value pairs
    
    Example:
        insert_db('movies', {
            'title': 'The Substance',
            'theater': 'IFC Center',
            'year': 2024
        })
    """
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    
    db_execute(sql, tuple(data.values()))


def insert_many_db(table: str, columns: List[str], values: List[tuple]) -> None:
    """
    Insert multiple rows into a table
    
    Args:
        table: Table name
        columns: List of column names
        values: List of tuples containing values for each row
    
    Example:
        insert_many_db(
            'movies',
            ['title', 'theater', 'year'],
            [
                ('Anora', 'Metrograph', 2024),
                ('Nosferatu', 'BAM', 2024)
            ]
        )
    """
    conn = db_conn()
    try:
        with conn.cursor() as cur:
            columns_str = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            sql = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
            
            cur.executemany(sql, values)
            conn.commit()
    finally:
        conn.close()


def insert_df(df: pd.DataFrame, table: str, if_exists: str = 'append') -> None:
    """
    Insert pandas DataFrame into database table
    
    Args:
        df: pandas DataFrame to insert
        table: Table name
        if_exists: How to behave if table exists ('fail', 'replace', 'append')
    
    Example:
        df = pd.DataFrame({
            'title': ['Movie 1', 'Movie 2'],
            'theater': ['IFC Center', 'Metrograph']
        })
        insert_df(df, 'movies', if_exists='append')
    """
    conn = db_conn()
    try:
        df.to_sql(table, conn, if_exists=if_exists, index=False)
    finally:
        conn.close()


def update_db(table: str, data: Dict[str, Any], where: str, where_params: tuple) -> None:
    """
    Update rows in a table
    
    Args:
        table: Table name
        data: Dictionary of column:value pairs to update
        where: WHERE clause (without 'WHERE' keyword)
        where_params: Tuple of parameters for WHERE clause
    
    Example:
        update_db(
            'movies',
            {'dates': 'Jan 10-15'},
            'title = %s AND theater = %s',
            ('The Substance', 'IFC Center')
        )
    """
    set_clause = ', '.join([f"{col} = %s" for col in data.keys()])
    sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
    
    params = tuple(data.values()) + where_params
    db_execute(sql, params)


def delete_db(table: str, where: str, where_params: tuple) -> None:
    """
    Delete rows from a table
    
    Args:
        table: Table name
        where: WHERE clause (without 'WHERE' keyword)
        where_params: Tuple of parameters for WHERE clause
    
    Example:
        delete_db('movies', 'scraped_at < %s', ('2024-01-01',))
    """
    sql = f"DELETE FROM {table} WHERE {where}"
    db_execute(sql, where_params)


def table_exists(table_name: str) -> bool:
    """
    Check if a table exists in the database
    
    Args:
        table_name: Name of the table to check
    
    Returns:
        True if table exists, False otherwise
    """
    sql = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = %s
        )
    """
    result = db_select(sql, (table_name,))
    return result[0][0] if result else False


def create_tables():
    """
    Create necessary tables for Indieflix if they don't exist
    """
    conn = db_conn()
    try:
        with conn.cursor() as cur:
            # Movies table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(500) NOT NULL,
                    theater VARCHAR(200) NOT NULL,
                    theater_id VARCHAR(100) NOT NULL,
                    location VARCHAR(300),
                    website VARCHAR(300),
                    film_link VARCHAR(500),
                    director VARCHAR(300),
                    year INTEGER,
                    dates VARCHAR(200),
                    description TEXT,
                    scraped_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(title, theater, scraped_at)
                )
            """)
            
            # Create indexes for faster queries
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_movies_theater 
                ON movies(theater_id)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_movies_scraped 
                ON movies(scraped_at DESC)
            """)
            
            # Add updated_at column if it doesn't exist (needed for trigger)
            cur.execute("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='movies' AND column_name='updated_at'
                    ) THEN
                        ALTER TABLE movies ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                    END IF;
                END $$;
            """)
            
            # Add TMDB enrichment columns if they don't exist
            cur.execute("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='movies' AND column_name='tmdb_id'
                    ) THEN
                        ALTER TABLE movies ADD COLUMN tmdb_id INTEGER;
                        ALTER TABLE movies ADD COLUMN poster_url VARCHAR(500);
                        ALTER TABLE movies ADD COLUMN backdrop_url VARCHAR(500);
                        ALTER TABLE movies ADD COLUMN runtime INTEGER;
                        ALTER TABLE movies ADD COLUMN tmdb_rating DECIMAL(3,1);
                        ALTER TABLE movies ADD COLUMN genres TEXT;
                        ALTER TABLE movies ADD COLUMN cast_members TEXT;
                        ALTER TABLE movies ADD COLUMN tmdb_overview TEXT;
                        ALTER TABLE movies ADD COLUMN enriched_at TIMESTAMP;
                    END IF;
                END $$;
            """)
            
            # Create indexes for TMDB columns
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_movies_tmdb_id
                ON movies(tmdb_id)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_movies_enriched
                ON movies(enriched_at DESC)
            """)
            
            # Create trigger function for auto-updating updated_at
            cur.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql'
            """)
            
            # Create trigger
            cur.execute("""
                DROP TRIGGER IF EXISTS update_movies_updated_at ON movies
            """)
            
            cur.execute("""
                CREATE TRIGGER update_movies_updated_at
                    BEFORE UPDATE ON movies
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column()
            """)
            
            conn.commit()
            print("✅ Database tables created successfully")
    finally:
        conn.close()


if __name__ == '__main__':
    # Test database connection and create tables
    print("Testing database connection...")
    try:
        conn = db_conn()
        print(f"✅ Connected to database: {get_db_config()['database']}")
        conn.close()
        
        # Create tables
        create_tables()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
