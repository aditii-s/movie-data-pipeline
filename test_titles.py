
from etl import parse_title

examples = [
    "American President, The (1995)",
    "Seven (a.k.a. Se7en) (1995)",
    "Toy Story (1995)"
]

for title in examples:
    print(title, "->", parse_title(title))
