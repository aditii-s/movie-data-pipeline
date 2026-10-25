# Movie Data Pipeline

## Overview

This project implements an ETL (Extract, Transform, Load) pipeline using the MovieLens dataset and the OMDb API. It extracts movie and rating data from CSV files, cleans and transforms the data, enriches movie records with available OMDb metadata, and loads the results into a relational SQLite database for analysis.

## Objectives

- Extract movie and rating data from MovieLens CSV files.
- Clean movie titles and derive release years and decades.
- Normalize genres into relational tables.
- Validate and transform rating records.
- Enrich movie metadata using the OMDb API.
- Store transformed data in SQLite.
- Answer analytical questions using SQL.

## Technology Stack

- Python
- Pandas
- Requests
- SQLite
- SQL
- python-dotenv
- OMDb API

## Project Structure

```text
movie-data-pipeline/
├── data/
│   ├── movies.csv
│   ├── ratings.csv
│   ├── movies_transformed.csv
│   ├── ratings_transformed.csv
│   ├── genres_transformed.csv
│   └── movie_genres_transformed.csv
├── etl.py
├── transform_data.py
├── transform_genres.py
├── transform_ratings.py
├── schema.sql
├── queries.sql
├── run_queries.py
├── verify_database.py
├── test_titles.py
├── inspect_data.py
├── requirements.txt
├── .gitignore
└── README.md
```

The `omdb_cache.csv` file is generated when API results are cached. The SQLite database and environment configuration are local files and are excluded from version control.

## Database Design

The SQLite database contains four tables:

- **movies:** Movie titles, release years, decades, OMDb IMDb IDs, directors, plots, box office information, and API enrichment status.
- **genres:** Unique genre names.
- **movie_genres:** Junction table representing the many-to-many relationship between movies and genres.
- **ratings:** User ratings and rating timestamps associated with movies.

The schema defines relationships between movies, genres, movie genres, and ratings.

## ETL Process

### 1. Extract

The pipeline reads `movies.csv` and `ratings.csv` from the MovieLens dataset.

### 2. Transform

- Parses movie titles to derive clean titles and release years.
- Derives decade values from release years.
- Validates rating records and handles duplicate records.
- Splits genre values into normalized genre records and movie-genre relationships.

### 3. Enrich

The pipeline uses the OMDb API to retrieve available movie metadata, including IMDb IDs, directors, plots, and box office information. Cached API results are reused to reduce repeated requests.

The number of new OMDb requests per run is configurable through the `OMDB_BATCH_SIZE` environment variable, which defaults to 25. Enrichment coverage depends on API availability, title matching, and request limits.

### 4. Load

The pipeline creates the database schema and loads movie, genre, movie-genre, and rating records into SQLite. Movie records can be updated when the pipeline is rerun, and duplicate rating records are avoided.

## Setup

### Prerequisites

- Python 3.10 or later
- A valid OMDb API key

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file in the project root:

```text
OMDB_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///movies.db
```

Replace the placeholder with your own API key. Never commit `.env` or expose your API key publicly.

### Run the pipeline

```bash
python etl.py
```

### Verify the database

```bash
python verify_database.py
```

### Run analytical queries

```bash
python run_queries.py
```

## SQL Analysis

The `queries.sql` file answers four analytical questions:

1. Which movie has the highest average rating?
2. Which five genres have the highest average rating?
3. Which director entry appears most frequently in the enriched dataset?
4. What is the average rating for each release year?

The highest-rated movie query also reports the number of ratings to provide context for the result.

**Note:** The director query groups records by the director field as stored. When OMDb returns multiple directors in a single field, they are treated as one combined entry rather than counted individually.

## Validation

The database was successfully populated and verified with the following row counts:

| Table | Rows |
|---|---:|
| Movies | 9,742 |
| Genres | 19 |
| Movie genres | 22,050 |
| Ratings | 100,836 |

These counts were confirmed during the successful ETL run and database verification.

In the latest reported run, 26 movies had OMDb metadata available in the database. This is partial enrichment, not complete metadata coverage for all movies.

## Future Improvements

- Expand OMDb enrichment while respecting API quotas and request limits.
- Improve matching for alternate and international movie titles.
- Add automated tests for transformations, database constraints, and SQL results.
- Add detailed logging and data-quality reports for API matches and unmatched titles.
- Consider query performance improvements and indexes as the dataset grows.
