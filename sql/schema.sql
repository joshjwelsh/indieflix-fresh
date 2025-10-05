-- Indieflix Database Schema
-- PostgreSQL table definitions

-- Movies table
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
    tmdb_id INTEGER,
    poster_url VARCHAR(500),
    backdrop_url VARCHAR(500),
    runtime INTEGER,
    tmdb_rating DECIMAL(3,1),
    genres TEXT,
    cast_members TEXT,
    tmdb_overview TEXT,
    enriched_at TIMESTAMP,
    UNIQUE(title, theater, scraped_at)
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_movies_theater 
ON movies(theater_id);

CREATE INDEX IF NOT EXISTS idx_movies_scraped 
ON movies(scraped_at DESC);

CREATE INDEX IF NOT EXISTS idx_movies_tmdb_id
ON movies(tmdb_id);

CREATE INDEX IF NOT EXISTS idx_movies_enriched
ON movies(enriched_at DESC);

-- Trigger function to auto-update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at on row modification
DROP TRIGGER IF EXISTS update_movies_updated_at ON movies;
CREATE TRIGGER update_movies_updated_at
    BEFORE UPDATE ON movies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE movies IS 'Stores movie screening information from NYC arthouse theaters';
COMMENT ON COLUMN movies.title IS 'Movie title';
COMMENT ON COLUMN movies.theater IS 'Theater name (e.g., "Metrograph")';
COMMENT ON COLUMN movies.theater_id IS 'Theater identifier (e.g., "metrograph")';
COMMENT ON COLUMN movies.location IS 'Theater address';
COMMENT ON COLUMN movies.website IS 'Theater website URL';
COMMENT ON COLUMN movies.film_link IS 'Direct link to film page on theater website';
COMMENT ON COLUMN movies.director IS 'Film director name(s)';
COMMENT ON COLUMN movies.year IS 'Release year';
COMMENT ON COLUMN movies.dates IS 'Showing dates as text (e.g., "Jan 10-15")';
COMMENT ON COLUMN movies.description IS 'Additional information about the screening';
COMMENT ON COLUMN movies.scraped_at IS 'Timestamp when data was scraped';
COMMENT ON COLUMN movies.created_at IS 'Timestamp when record was created';
COMMENT ON COLUMN movies.updated_at IS 'Timestamp when record was last modified (auto-updated)';
COMMENT ON COLUMN movies.tmdb_id IS 'The Movie Database (TMDB) unique identifier';
COMMENT ON COLUMN movies.poster_url IS 'TMDB poster image URL (w342 size)';
COMMENT ON COLUMN movies.backdrop_url IS 'TMDB backdrop image URL';
COMMENT ON COLUMN movies.runtime IS 'Movie runtime in minutes';
COMMENT ON COLUMN movies.tmdb_rating IS 'TMDB user rating (0-10 scale)';
COMMENT ON COLUMN movies.genres IS 'Comma-separated list of genres';
COMMENT ON COLUMN movies.cast_members IS 'Comma-separated list of top cast members';
COMMENT ON COLUMN movies.tmdb_overview IS 'TMDB plot overview/synopsis';
COMMENT ON COLUMN movies.enriched_at IS 'Timestamp when TMDB enrichment was performed';
