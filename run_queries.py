
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "movies.db"
QUERIES_PATH = BASE_DIR / "queries.sql"

with open(QUERIES_PATH, "r", encoding="utf-8") as file:
    sql_content = file.read()

# Split the file into individual SQL statements.
statements = [
    statement.strip()
    for statement in sql_content.split(";")
    if statement.strip()
]

connection = sqlite3.connect(DB_PATH)

try:
    for index, statement in enumerate(statements, start=1):
        print(f"\n{'=' * 60}")
        print(f"QUERY {index}")
        print("=" * 60)

        cursor = connection.execute(statement)
        columns = [item[0] for item in cursor.description]
        rows = cursor.fetchall()

        print(" | ".join(columns))
        print("-" * 60)

        for row in rows:
            print(" | ".join(
                str(value) if value is not None else "NULL"
                for value in row
            ))

        if not rows:
            print("No results found.")

finally:
    connection.close()
