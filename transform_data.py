
import pandas as pd
import re

movies = pd.read_csv("data/movies.csv")

def extract_title_and_year(title):
    """
    Extract a trailing four-digit year from titles such as
    Toy Story (1995). Preserve titles without a year.
    """
    match = re.match(r"^(.*?)\s*\((\d{4})\)\s*$", str(title))

    if match:
        clean_title = match.group(1).strip()
        release_year = int(match.group(2))
        return clean_title, release_year

    return str(title).strip(), None


movies[["clean_title", "release_year"]] = movies["title"].apply(
    lambda title: pd.Series(extract_title_and_year(title))
)


movies["decade"] = movies["release_year"].apply(
    lambda year: f"{int(year // 10) * 10}s"
    if pd.notna(year) else None
)


print("\n--- TRANSFORMED MOVIES ---")
print(movies[["movieId", "title", "clean_title", "release_year", "decade"]].head(10))

print("\nMovies with missing release years:", movies["release_year"].isna().sum())
print("Total movies:", len(movies))
print("Unique movie IDs:", movies["movieId"].nunique())

# Save a temporary output so we can inspect the transformation.
movies.to_csv("data/movies_transformed.csv", index=False)

print("\nSaved transformed data to data/movies_transformed.csv")
