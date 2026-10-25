
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "movies.db"

connection = sqlite3.connect(DB_PATH)

try:
    print("\nDATABASE VERIFICATION")
    print("-" * 40)

    tables = [
        "movies",
        "genres",
        "movie_genres",
        "ratings"
    ]

    for table in tables:
        count = connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        print(f"{table}: {count:,} rows")

    print("\nSAMPLE ENRICHED MOVIES")
    print("-" * 40)

    rows = connection.execute("""
        SELECT title, release_year, director, api_found
        FROM movies
        WHERE api_found = 1
        LIMIT 5
    """).fetchall()

    if rows:
        for row in rows:
            print(row)
    else:
        print("No OMDb-enriched movies found yet.")

    print("\nDATABASE CHECK COMPLETE")

finally:
    connection.close()
