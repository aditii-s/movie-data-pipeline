PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS movies (
    movie_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    release_year INTEGER,
    decade TEXT,
    imdb_id TEXT,
    director TEXT,
    plot TEXT,
    box_office TEXT,
    api_found INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS genres (
    genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
    genre_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,

    PRIMARY KEY (movie_id, genre_id),

    FOREIGN KEY (movie_id)
        REFERENCES movies(movie_id)
        ON DELETE CASCADE,

    FOREIGN KEY (genre_id)
        REFERENCES genres(genre_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ratings (
    user_id INTEGER NOT NULL,
    movie_id INTEGER NOT NULL,
    rating REAL NOT NULL,
    rating_timestamp INTEGER,

    FOREIGN KEY (movie_id)
        REFERENCES movies(movie_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ratings_movie
ON ratings(movie_id);

CREATE INDEX IF NOT EXISTS idx_movies_year
ON movies(release_year);

CREATE INDEX IF NOT EXISTS idx_movies_director
ON movies(director);