CREATE TABLE IF NOT EXISTS comics (
    id INTEGER PRIMARY KEY,
    year INTEGER,
    month INTEGER,
    day INTEGER,
    title TEXT NOT NULL,
    safe_title TEXT,
    alt TEXT,
    transcript TEXT,
    image_url TEXT NOT NULL,
    comic_url TEXT,
    search_text TEXT
);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_comics_search
ON comics USING GIN (
    to_tsvector('english', COALESCE(search_text, ''))
);

-- Additional filtering index
CREATE INDEX IF NOT EXISTS idx_comics_year
ON comics(year);