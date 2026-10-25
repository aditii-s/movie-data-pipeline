
import os
import re
import time
import logging
import sqlite3
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# ---------------- Configuration ----------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "movies.db"
CACHE_PATH = DATA_DIR / "omdb_cache.csv"

load_dotenv(BASE_DIR / ".env")
API_KEY = os.getenv("OMDB_API_KEY")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ---------------- Extract ----------------

def extract_data():
    logging.info("Reading MovieLens CSV files")

    movies = pd.read_csv(DATA_DIR / "movies.csv")
    ratings = pd.read_csv(DATA_DIR / "ratings.csv")

    return movies, ratings


# ---------------- Transform ----------------

def parse_title(title):
    title = str(title).strip()

    # Extract a trailing release year.
    match = re.match(r"^(.*?)\s*\((\d{4})\)\s*$", title)

    if match:
        clean_title = match.group(1).strip()
        release_year = int(match.group(2))
    else:
        clean_title = title
        release_year = None

    # Remove alternate-title notes such as "(a.k.a. Se7en)".
    clean_title = re.sub(
        r"\s*\(a\.k\.a\..*?\)",
        "",
        clean_title,
        flags=re.IGNORECASE
    ).strip()

    # Convert titles such as "American President, The"
    # into "The American President".
    article_match = re.match(
        r"^(.*),\s*(The|A|An)$",
        clean_title,
        flags=re.IGNORECASE
    )

    if article_match:
        clean_title = (
            article_match.group(2) + " " + article_match.group(1)
        ).strip()

    return clean_title, release_year


def transform_movies(movies):
    movies = movies.copy()

    parsed = movies["title"].apply(parse_title)
    movies["clean_title"] = parsed.apply(lambda item: item[0])
    movies["release_year"] = parsed.apply(lambda item: item[1])

    movies["decade"] = movies["release_year"].apply(
        lambda year: f"{(int(year) // 10) * 10}s"
        if pd.notna(year) else None
    )

    return movies


def transform_ratings(ratings, valid_movie_ids):
    ratings = ratings.copy()

    ratings = ratings.dropna(
        subset=["userId", "movieId", "rating", "timestamp"]
    )

    ratings = ratings[
        ratings["rating"].between(0.5, 5.0)
        & ((ratings["rating"] * 2) % 1 == 0)
    ]

    ratings["userId"] = ratings["userId"].astype(int)
    ratings["movieId"] = ratings["movieId"].astype(int)
    ratings["timestamp"] = ratings["timestamp"].astype(int)

    ratings = ratings[
        ratings["movieId"].isin(valid_movie_ids)
    ]

    return ratings.drop_duplicates()


def split_genres(movies):
    genre_names = set()
    relationships = []

    for _, row in movies.iterrows():
        raw_genres = str(row["genres"])

        if raw_genres == "(no genres listed)":
            continue

        for genre in raw_genres.split("|"):
            genre = genre.strip()

            if genre:
                genre_names.add(genre)
                relationships.append(
                    (int(row["movieId"]), genre)
                )

    return sorted(genre_names), relationships


# ---------------- OMDb enrichment ----------------

def enrich_movie(title, year, session, cache):
    cache_key = f"{title}|{year or ''}"

    if cache_key in cache:
        return cache[cache_key]

    if not API_KEY:
        return {}

    params = {
        "apikey": API_KEY,
        "t": title
    }

    if year:
        params["y"] = year

    try:
        response = session.get(
            "https://www.omdbapi.com/",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if data.get("Response") == "True":
            result = {
                "imdb_id": data.get("imdbID"),
                "director": data.get("Director"),
                "plot": data.get("Plot"),
                "box_office": data.get("BoxOffice"),
                "api_found": 1
            }
        else:
            logging.warning(
                "OMDb did not find %s (%s): %s",
                title, year, data.get("Error")
            )
            result = {"api_found": 0}

        cache[cache_key] = result
        time.sleep(0.1)
        return result

    except (requests.RequestException, ValueError) as error:
        logging.warning(
            "OMDb request failed for %s: %s", title, error
        )
        return {}


def load_cache():
    if not CACHE_PATH.exists():
        return {}

    try:
        frame = pd.read_csv(CACHE_PATH).fillna("")
        cache = {}

        for _, row in frame.iterrows():
            cache[row["cache_key"]] = {
                "imdb_id": row["imdb_id"] or None,
                "director": row["director"] or None,
                "plot": row["plot"] or None,
                "box_office": row["box_office"] or None,
                "api_found": int(row["api_found"])
            }

        return cache

    except (OSError, ValueError, KeyError):
        logging.warning(
            "Could not read OMDb cache; starting a new cache"
        )
        return {}


def save_cache(cache):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for key, value in cache.items():
        rows.append({
            "cache_key": key,
            "imdb_id": value.get("imdb_id"),
            "director": value.get("director"),
            "plot": value.get("plot"),
            "box_office": value.get("box_office"),
            "api_found": value.get("api_found", 0)
        })

    pd.DataFrame(
        rows,
        columns=[
            "cache_key",
            "imdb_id",
            "director",
            "plot",
            "box_office",
            "api_found"
        ]
    ).to_csv(CACHE_PATH, index=False)


# ---------------- Load ----------------

def load_schema(connection):
    schema_path = BASE_DIR / "schema.sql"

    with open(schema_path, "r", encoding="utf-8") as file:
        connection.executescript(file.read())


def load_data(connection, movies, ratings, genres, relationships):
    cursor = connection.cursor()

    logging.info("Loading movies")

    for _, row in movies.iterrows():
        cursor.execute(
            """
            INSERT INTO movies (
                movie_id, title, release_year, decade,
                imdb_id, director, plot, box_office, api_found
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(movie_id) DO UPDATE SET
                title = excluded.title,
                release_year = excluded.release_year,
                decade = excluded.decade,
                imdb_id = COALESCE(excluded.imdb_id, movies.imdb_id),
                director = COALESCE(excluded.director, movies.director),
                plot = COALESCE(excluded.plot, movies.plot),
                box_office = COALESCE(excluded.box_office, movies.box_office),
                api_found = MAX(movies.api_found, excluded.api_found)
            """,
            (
                int(row["movieId"]),
                row["clean_title"],
                int(row["release_year"])
                if pd.notna(row["release_year"]) else None,
                row["decade"] if pd.notna(row["decade"]) else None,
                row.get("imdb_id"),
                row.get("director"),
                row.get("plot"),
                row.get("box_office"),
                int(row.get("api_found", 0))
            )
        )

    logging.info("Loading genres")

    cursor.executemany(
        """
        INSERT INTO genres (genre_name)
        VALUES (?)
        ON CONFLICT(genre_name) DO NOTHING
        """,
        [(genre,) for genre in genres]
    )

    genre_ids = {
        name: genre_id
        for genre_id, name in cursor.execute(
            "SELECT genre_id, genre_name FROM genres"
        ).fetchall()
    }

    logging.info("Loading movie-genre relationships")

    cursor.executemany(
        """
        INSERT INTO movie_genres (movie_id, genre_id)
        VALUES (?, ?)
        ON CONFLICT(movie_id, genre_id) DO NOTHING
        """,
        [
            (movie_id, genre_ids[genre])
            for movie_id, genre in relationships
        ]
    )

    logging.info("Loading ratings")

    cursor.executemany(
        """
        INSERT INTO ratings (
            user_id, movie_id, rating, rating_timestamp
        )
        SELECT ?, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM ratings
            WHERE user_id = ?
              AND movie_id = ?
              AND rating_timestamp = ?
              AND rating = ?
        )
        """,
        [
            (
                int(row.userId),
                int(row.movieId),
                float(row.rating),
                int(row.timestamp),
                int(row.userId),
                int(row.movieId),
                int(row.timestamp),
                float(row.rating)
            )
            for row in ratings.itertuples(index=False)
        ]
    )


# ---------------- Main ETL pipeline ----------------

def main():
    movies, ratings = extract_data()

    movies = transform_movies(movies)
    ratings = transform_ratings(
        ratings, set(movies["movieId"].astype(int))
    )

    genres, relationships = split_genres(movies)

    cache = load_cache()
    session = requests.Session()

    try:
        enriched = []

        if API_KEY:
            batch_size = max(
                0, int(os.getenv("OMDB_BATCH_SIZE", "25"))
            )
            new_requests = 0

            logging.info(
                "OMDb key found; request limit for this run: %s",
                batch_size
            )

            for _, row in movies.iterrows():
                year = (
                    int(row["release_year"])
                    if pd.notna(row["release_year"])
                    else None
                )
                cache_key = f"{row['clean_title']}|{year or ''}"

                if cache_key in cache:
                    result = cache[cache_key]
                elif new_requests < batch_size:
                    result = enrich_movie(
                        row["clean_title"],
                        year,
                        session,
                        cache
                    )
                    new_requests += 1
                else:
                    result = {}

                enriched.append(result)

            logging.info(
                "New OMDb requests attempted: %s", new_requests
            )

        else:
            logging.warning(
                "OMDB_API_KEY is missing. Loading without OMDb enrichment."
            )
            enriched = [{} for _ in range(len(movies))]

        enrichment_frame = pd.DataFrame(
            enriched, index=movies.index
        )

        columns = [
            "imdb_id", "director", "plot", "box_office", "api_found"
        ]

        for column in columns:
            if column not in enrichment_frame.columns:
                enrichment_frame[column] = None

        movies[columns] = enrichment_frame[columns]
        movies["api_found"] = (
            movies["api_found"].fillna(0).astype(int)
        )

        save_cache(cache)

        connection = sqlite3.connect(DB_PATH)

        try:
            connection.execute("PRAGMA foreign_keys = ON")
            load_schema(connection)

            with connection:
                load_data(
                    connection,
                    movies,
                    ratings,
                    genres,
                    relationships
                )

            logging.info("ETL pipeline completed successfully")

            for table in [
                "movies", "genres", "movie_genres", "ratings"
            ]:
                count = connection.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]
                logging.info("%s: %s rows", table, count)

            enriched_count = connection.execute(
                "SELECT COUNT(*) FROM movies WHERE api_found = 1"
            ).fetchone()[0]
            logging.info(
                "Movies with OMDb metadata: %s", enriched_count
            )

        finally:
            connection.close()

    finally:
        session.close()


if __name__ == "__main__":
    main()
