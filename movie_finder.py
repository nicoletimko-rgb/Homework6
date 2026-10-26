"""Movie Finder: search movies by meaning, not keywords, using ChromaDB.

One item = one movie (its title, year, genre and plot summary, about 2-3 sentences).
What the app does with retrieved items = ranks them, drops weak matches, and explains
each match by pulling out the sentence of the plot closest to what the user asked.
"""
import csv
import json
import os
import re
import sys
import time

import chromadb
from chromadb.utils import embedding_functions

DB_PATH = "./chroma_store"
COLLECTION = "movies"
# Prefer the real Wikipedia-based data (built by convert_movies.py) over the tiny hand-written seed.
SEED_FILE = "movies_real.csv" if os.path.exists("movies_real.csv") else "movies_seed.csv"
WATCHLIST_FILE = "watchlist.json"

# Cosine distance: 0 = identical meaning, ~1 = unrelated. Tuned in README (Step 5).
MAX_DISTANCE = 0.75

ef = embedding_functions.DefaultEmbeddingFunction()  # same model Chroma uses by default
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(
    name=COLLECTION,
    embedding_function=ef,
    metadata={"hnsw:space": "cosine"},
)


# ---------- storing ----------

def make_id(title, year):
    return re.sub(r"[^a-z0-9]+", "-", f"{title}-{year}".lower()).strip("-")


def make_document(title, year, genre, plot):
    # Whatever is stored as the document is what gets embedded, so the plot goes here
    # (not hidden in metadata). Title/genre are included for extra context.
    return f"{title} ({year}). {genre}. {plot}"


def load_csv(path, batch_size=100):
    """Load a CSV with columns title,year,genre,plot in batches. Safe to re-run (upsert)."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    start = time.time()
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        collection.upsert(
            ids=[make_id(r["title"], r["year"]) for r in batch],
            documents=[make_document(r["title"], r["year"], r["genre"], r["plot"]) for r in batch],
            metadatas=[{"title": r["title"], "year": int(r["year"]),
                        "genre": r["genre"], "plot": r["plot"], "source": "file"} for r in batch],
        )
        print(f"  loaded {min(i + batch_size, len(rows))}/{len(rows)} "
              f"({time.time() - start:.1f}s)")
    return len(rows)


def add_movie(title, year, genre, plot):
    # upsert so re-adding the same movie replaces it instead of silently being ignored
    collection.upsert(
        ids=[make_id(title, year)],
        documents=[make_document(title, year, genre, plot)],
        metadatas=[{"title": title, "year": int(year), "genre": genre, "plot": plot,
                    "source": "user"}],  # "user" movies survive a data-file reload
    )


# ---------- searching ----------

def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def best_sentence(query, plot):
    """The plot sentence whose meaning is closest to the query: the 'why it matched'."""
    sentences = split_sentences(plot)
    if len(sentences) <= 1:
        return plot
    vecs = ef([query] + sentences)
    q = vecs[0]
    scores = [sum(a * b for a, b in zip(q, v)) for v in vecs[1:]]  # vectors are normalized
    return sentences[max(range(len(scores)), key=scores.__getitem__)]


def search(query, n=5, genre=None):
    where = {"genre": genre} if genre else None
    res = collection.query(query_texts=[query], n_results=n, where=where)
    hits = []
    for meta, dist in zip(res["metadatas"][0], res["distances"][0]):
        hits.append({**meta, "distance": dist})
    return hits


def more_like(title, n=4):
    """Use a stored movie's own text as the query to find similar ones."""
    found = collection.get(where={"title": title}, include=["documents"])
    if not found["ids"]:
        return None
    res = collection.query(query_texts=[found["documents"][0]], n_results=n + 1)
    return [{**m, "distance": d} for m, d in zip(res["metadatas"][0], res["distances"][0])
            if m["title"] != title][:n]


# ---------- watch list ----------
# Stored in a small JSON file (not in Chroma) so reloading/upserting movies never wipes it.

def load_watchlist():
    try:
        with open(WATCHLIST_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_watchlist(wl):
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(wl, f, indent=2)


def set_status(movie, status, rating=None):
    wl = load_watchlist()
    wl[make_id(movie["title"], movie["year"])] = {
        "title": movie["title"], "year": movie["year"], "genre": movie["genre"],
        "status": status, "rating": rating,
    }
    save_watchlist(wl)


def status_tag(movie):
    """Short label shown next to a movie anywhere it appears in results."""
    entry = load_watchlist().get(make_id(movie["title"], movie["year"]))
    if not entry:
        return ""
    if entry["status"] == "watched":
        r = f", you rated it {entry['rating']}/5" if entry.get("rating") else ""
        return f"  << WATCHED{r}"
    return "  << ON YOUR WATCH LIST"


def result_actions(shown):
    """After any search: let the user add a shown movie to the list or mark it watched."""
    if not shown:
        return
    while True:
        pick = input("\nAdd a movie to your watch list? Enter a result number (or press Enter to skip): ").strip()
        if not pick:
            return
        if not (pick.isdigit() and 1 <= int(pick) <= len(shown)):
            print(f"Please enter a number from 1 to {len(shown)}.")
            continue
        movie = shown[int(pick) - 1]
        act = input(f"  {movie['title']}: (a) add to watch list, (w) mark watched, "
                    "(Enter) cancel: ").strip().lower()
        if act == "a":
            set_status(movie, "to_watch")
            print(f"  Added {movie['title']} to your watch list.")
        elif act == "w":
            mark_watched(movie)

def mark_watched(movie):
    r = input("  Your rating 0-5 (Enter to skip): ").strip()

    try:
        rating = int(r)
        if not 0 <= rating <= 5:
            rating = None
    except ValueError:
        rating = None

    set_status(movie, "watched", rating)

    if rating is not None:
        print(
            f"  Marked {movie['title']} as watched "
            f"({rating}/5)."
        )
    elif r:
        print(
            f"  Marked {movie['title']} as watched. "
            "Rating must be a whole number from 0–5, "
            "so added as unrated."
        )
    else:
        print(
            f"  Marked {movie['title']} as watched "
            "without a rating."
        )

def show_watchlist():
    wl = load_watchlist()
    if not wl:
        print("\nYour watch list is empty. Search for movies and add some!")
        return []

    to_watch = sorted(
        (e for e in wl.values() if e["status"] == "to_watch"),
        key=lambda e: e["title"]
    )
    watched = sorted(
        (e for e in wl.values() if e["status"] == "watched"),
        key=lambda e: -(e.get("rating") or 0)
    )

    shown = []

    print(f"\nTO WATCH ({len(to_watch)})")
    for movie in to_watch:
        shown.append(movie)
        print(
            f"  [{len(shown)}] {movie['title']} "
            f"({movie['year']}) [{movie['genre']}]"
        )
    if not to_watch:
        print("  (nothing queued)")

    print(f"\nWATCHED ({len(watched)})")
    for movie in watched:
        shown.append(movie)
        rating = (
            f"{movie['rating']}/5"
            if movie.get("rating")
            else "not rated"
        )
        print(
            f"  [{len(shown)}] {movie['title']} "
            f"({movie['year']}) [{movie['genre']}]  {rating}"
        )
    if not watched:
        print("  (nothing yet)")

    return shown


def manage_watchlist():
    """Select a movie by number to mark watched, re-rate, or remove."""
    shown = show_watchlist()
    if not shown:
        return

    while True:
        pick = input(
            "\nEnter a movie number to update it "
            "(or press Enter to go back): "
        ).strip()

        if not pick:
            return

        if not (pick.isdigit() and 1 <= int(pick) <= len(shown)):
            print(f"Please enter a number from 1 to {len(shown)}.")
            continue

        movie = shown[int(pick) - 1]
        break

    act = input(
        f"  {movie['title']}: (w) mark watched / re-rate, "
        "(r) remove, (Enter) cancel: "
    ).strip().lower()

    if act == "w":
        mark_watched(movie)
    elif act == "r":
        wl = load_watchlist()
        del wl[make_id(movie["title"], movie["year"])]
        save_watchlist(wl)
        print(f"  Removed {movie['title']} from your list.")


def confidence(distance):
    """Display cosine similarity as a percentage."""
    similarity = 1 - distance
    return f"{similarity:.2%} similarity"


def pick_double_feature(good):
    """Pair the top pick with the best result from a DIFFERENT genre, for variety."""
    top = good[0]
    for h in good[1:]:
        if h["genre"] != top["genre"]:
            return h
    return None


def recommend(query, n=6, genre=None):
    hits = search(query, n=n, genre=genre)

    if not hits:
        print("\nNo movies found. Try another description or genre.")
        return []

    good = [h for h in hits if h["distance"] <= MAX_DISTANCE]

    if not good:
        print(
            f'\nNothing in the collection is a close match for "{query}". '
            f"Closest result: {confidence(hits[0]['distance'])}. "
            "Try describing the plot or feeling differently."
        )
        return []

    print(f'\nMovies matching "{query}":')

    for i, movie in enumerate(good, start=1):
        print(
            f"\n  [{i}] {movie['title']} ({movie['year']}) "
            f"[{movie['genre']}] - "
            f"{confidence(movie['distance'])}{status_tag(movie)}"
        )
        print(f"      Why: {best_sentence(query, movie['plot'])}")

    if len(good) < len(hits):
        print(f"\n({len(hits) - len(good)} weaker result(s) hidden)")

    return good


def find_near_duplicate(title, year, genre, plot, threshold=0.15):
    """Before adding, check whether a very similar movie is already stored."""
    if collection.count() == 0:
        return None
    res = collection.query(query_texts=[make_document(title, year, genre, plot)], n_results=1)
    meta, dist = res["metadatas"][0][0], res["distances"][0][0]
    same_id = res["ids"][0][0] == make_id(title, year)
    if dist <= threshold and not same_id:
        return meta
    return None


# ---------- CLI ----------

def show_all():
    data = collection.get(include=["metadatas"])
    items = sorted(data["metadatas"], key=lambda m: (m["genre"], m["title"]))
    print(f"\n{len(items)} movies stored:")
    for m in items:
        print(f"  {m['title']} ({m['year']}) - {m['genre']}")


def menu():
    print(f"\nMovie Finder: {collection.count()} movies in the database")
    while True:
        print("\n--- Movie Finder ---")
        print("1. Find movies (describe what you're in the mood for)")
        print("2. Find movies similar to one in the database")
        print("3. Add a movie")
        print("4. Show everything stored")
        #print("5. Load a CSV file (title,year,genre,plot)")
        print("6. My watch list")
        print("7. Quit")
        choice = input("\nChoose an option: ").strip()
        if choice == "1":
            q = input("What are you looking for? ").strip()
            if not q:
                continue
            g = input("Limit to a genre? (press Enter for any): ").strip() or None
            result_actions(recommend(q, genre=g))
        elif choice == "2":
            t = input("Movie title (exact): ").strip()
            sims = more_like(t)
            if sims is None:
                print("That title isn't in the database. Use option 4 to see what is.")
            else:
                print(f"\nIf you liked {t}, try:")
                for i, s in enumerate(sims, 1):
                    print(
                        f"\n  [{i}] {s['title']} ({s['year']}) "
                        f"[{s['genre']}] - "
                        f"{confidence(s['distance'])}{status_tag(s)}"
                    )
                    print(f"      Description: {s['plot']}")
                result_actions(sims)
        elif choice == "3":
            title = input("Title: ").strip()
            year = input("Year: ").strip()
            genre = input("Genre: ").strip()
            plot = input("Plot summary (2-3 sentences): ").strip()
            if title and year.isdigit() and genre and plot:
                dup = find_near_duplicate(title, year, genre, plot)
                if dup and input(f"This looks a lot like {dup['title']} ({dup['year']}), "
                                 "already stored. Add anyway? (y/N) ").strip().lower() != "y":
                    print("Skipped.")
                    continue
                add_movie(title, year, genre, plot)
                print(f"Added {title}. It's searchable now.")
            else:
                print("Need a title, numeric year, genre and plot. Nothing added.")
        elif choice == "4":
            show_all()
        # elif choice == "5":
        #     path = input("CSV path: ").strip()
        #     try:
        #         print(f"Loaded {load_csv(path)} rows.")
        #     except (OSError, KeyError, ValueError) as e:
        #         print(f"Couldn't load that file: {e}")
        elif choice == "6":
            manage_watchlist()
        elif choice == "7":
            print("Bye!")
            break
        else:
            print("Please choose 1-7.")


LOADED_FILE = "loaded_sources.json"  # remembers which data files were already loaded


def ensure_data_loaded():
    """Load the data file if it hasn't been loaded yet (not just when the DB is empty).

    When the data file is new or changed (e.g. you swapped in a different dataset), every
    movie that came from an earlier data file is removed first, so datasets never mix.
    Movies you added yourself (option 3) are kept.
    """
    try:
        with open(LOADED_FILE, encoding="utf-8") as f:
            loaded = json.load(f)
    except (OSError, ValueError):
        loaded = []
    stamp = f"{SEED_FILE}:{os.path.getmtime(SEED_FILE):.0f}"
    if stamp in loaded:
        return
    everything = collection.get(include=["metadatas"])
    stale = [i for i, m in zip(everything["ids"], everything["metadatas"])
             if m.get("source") != "user"]
    for i in range(0, len(stale), 500):  # delete in batches
        collection.delete(ids=stale[i:i + 500])
    if stale:
        print(f"Removed {len(stale)} movies from the previous data file.")
    print(f"Loading {SEED_FILE} (first time only; downloads a small embedding model once)...")
    load_csv(SEED_FILE)
    with open(LOADED_FILE, "w", encoding="utf-8") as f:
        json.dump(loaded + [stamp], f)


if __name__ == "__main__":
    ensure_data_loaded()
    if len(sys.argv) > 1:  # non-interactive: python movie_finder.py "your query"
        recommend(" ".join(sys.argv[1:]))
    else:
        menu()
