
import pandas as pd

movies = pd.read_csv("data/movies_transformed.csv")

# Split the genre column into individual genre names.
movies["genre_list"] = movies["genres"].fillna("").apply(
    lambda value: [
        genre.strip()
        for genre in value.split("|")
        if genre.strip() and genre.strip() != "(no genres listed)"
    ]
)

# Create one row per movie-genre relationship.
movie_genres = movies[["movieId", "genre_list"]].explode("genre_list")
movie_genres = movie_genres.dropna(subset=["genre_list"])
movie_genres = movie_genres.rename(
    columns={"movieId": "movie_id", "genre_list": "genre_name"}
)

# Create a unique list of genres.
genres = pd.DataFrame({
    "genre_name": sorted(movie_genres["genre_name"].unique())
})
genres.insert(0, "genre_id", range(1, len(genres) + 1))

# Attach genre IDs to the movie-genre relationships.
movie_genres = movie_genres.merge(genres, on="genre_name", how="left")
movie_genres = movie_genres[["movie_id", "genre_id"]].drop_duplicates()

print("\n--- GENRES TABLE PREVIEW ---")
print(genres.head(10))
print("Total unique genres:", len(genres))

print("\n--- MOVIE-GENRE RELATIONSHIPS ---")
print(movie_genres.head(10))
print("Total relationships:", len(movie_genres))

# Save temporary CSV files for inspection.
genres.to_csv("data/genres_transformed.csv", index=False)
movie_genres.to_csv("data/movie_genres_transformed.csv", index=False)

print("\nSaved both transformed genre files successfully.")
