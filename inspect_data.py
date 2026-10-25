
import pandas as pd

movies = pd.read_csv("data/movies.csv")
ratings = pd.read_csv("data/ratings.csv")

print("\n--- MOVIES DATASET ---")
print("Rows:", len(movies))
print("Columns:", movies.columns.tolist())
print(movies.head())
print("\nMissing values:")
print(movies.isnull().sum())

print("\n--- RATINGS DATASET ---")
print("Rows:", len(ratings))
print("Columns:", ratings.columns.tolist())
print(ratings.head())
print("\nMissing values:")
print(ratings.isnull().sum())

print("\n--- DATA TYPES ---")
print(movies.dtypes)
print(ratings.dtypes)

print("\n--- UNIQUE MOVIES IN RATINGS ---")
print(ratings["movieId"].nunique())
