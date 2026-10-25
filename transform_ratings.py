
import pandas as pd

ratings = pd.read_csv("data/ratings.csv")

print("--- ORIGINAL RATINGS ---")
print("Rows:", len(ratings))
print(ratings.head())

# Convert columns to appropriate data types.
ratings["userId"] = pd.to_numeric(ratings["userId"], errors="coerce")
ratings["movieId"] = pd.to_numeric(ratings["movieId"], errors="coerce")
ratings["rating"] = pd.to_numeric(ratings["rating"], errors="coerce")
ratings["timestamp"] = pd.to_numeric(ratings["timestamp"], errors="coerce")

# Remove rows missing required values.
ratings = ratings.dropna(
    subset=["userId", "movieId", "rating"]
)

# Keep only valid MovieLens ratings (0.5 to 5.0, in 0.5 increments).
ratings = ratings[
    ratings["rating"].between(0.5, 5.0)
    & ((ratings["rating"] * 2) % 1 == 0)
]

# Convert IDs to integers after removing invalid rows.
ratings["userId"] = ratings["userId"].astype(int)
ratings["movieId"] = ratings["movieId"].astype(int)

# Remove duplicate rating records if the complete records are identical.
ratings = ratings.drop_duplicates()

# Rename columns to match our database schema.
ratings = ratings.rename(
    columns={
        "userId": "user_id",
        "movieId": "movie_id",
        "timestamp": "rating_timestamp"
    }
)

# Save the cleaned data.
ratings.to_csv("data/ratings_transformed.csv", index=False)

print("\n--- CLEANED RATINGS ---")
print("Rows:", len(ratings))
print("Missing values:")
print(ratings.isnull().sum())
print("\nPreview:")
print(ratings.head())

print("\nSaved data/ratings_transformed.csv")
