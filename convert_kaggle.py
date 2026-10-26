"""Convert the Kaggle "Wikipedia Movie Plots" CSV into movies_real.csv for movie_finder.py.

Dataset: https://www.kaggle.com/datasets/jrobischon/wikipedia-movie-plots
File:    wiki_movie_plots_deduped.csv
Columns: Release Year, Title, Origin/Ethnicity, Director, Cast, Genre, Wiki Page, Plot

usage: python convert_kaggle.py path/to/wiki_movie_plots_deduped.csv [min_year] [max_rows] [origin]
  min_year  default 1970
  max_rows  default 5000   (embedding runs on your CPU: time a small batch first, then go bigger)
  origin    default any    (e.g. American, British, Bollywood)

Plots here are often 300-700 words, but Chroma's default embedding model only reads the first
~256 word pieces and silently drops the rest. So each plot is trimmed to its opening sentences
(about 900 characters), which is the part that actually gets embedded anyway.
"""
import csv
import random
import re
import sys

MAX_CHARS = 900

path = sys.argv[1] if len(sys.argv) > 1 else "wiki_movie_plots_deduped.csv"
min_year = int(sys.argv[2]) if len(sys.argv) > 2 else 1970
max_rows = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
origin = sys.argv[4].lower() if len(sys.argv) > 4 else None


def trim_plot(text):
    """Keep whole sentences up to MAX_CHARS."""
    text = re.sub(r"\s+", " ", text).strip()
    out = ""
    for s in re.split(r"(?<=[.!?])\s+", text):
        if out and len(out) + len(s) + 1 > MAX_CHARS:
            break
        out = f"{out} {s}".strip()
    return out[:MAX_CHARS + 200]  # guard against one giant sentence


def first_genre(g):
    g = (g or "").strip()
    if not g or g.lower() == "unknown":
        return "Unknown"
    return re.split(r"[,/;]| and ", g)[0].strip().title()


with open(path, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    need = {"Release Year", "Title", "Genre", "Plot"}
    if not need <= set(reader.fieldnames or []):
        sys.exit(f"Expected columns {sorted(need)} but found {reader.fieldnames}. "
                 "Is this wiki_movie_plots_deduped.csv?")
    rows, seen = [], set()
    for r in reader:
        try:
            year = int(r["Release Year"])
        except (TypeError, ValueError):
            continue
        title, plot = (r["Title"] or "").strip(), trim_plot(r["Plot"] or "")
        if year < min_year or not title or len(plot) < 150:
            continue
        if origin and origin not in (r.get("Origin/Ethnicity") or "").lower():
            continue
        if (title, year) in seen:  # titles+years become Chroma ids, so they must be unique
            continue
        seen.add((title, year))
        rows.append({"title": title, "year": year, "genre": first_genre(r["Genre"]), "plot": plot})

random.seed(0)  # reproducible sample
if len(rows) > max_rows:
    rows = random.sample(rows, max_rows)
rows.sort(key=lambda r: (r["year"], r["title"]))

with open("movies_real.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["title", "year", "genre", "plot"])
    w.writeheader()
    w.writerows(rows)

unknown = sum(r["genre"] == "Unknown" for r in rows)
print(f"Wrote {len(rows)} movies to movies_real.csv (year >= {min_year}"
      f"{', origin ' + origin if origin else ''}). {unknown} have no genre listed.")
