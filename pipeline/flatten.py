"""Stage 3: flatten the nested TMDb responses into tables with a stated grain.

Each table holds one kind of thing, and its grain (what one row means) is
checked before it is returned:
- films:       one row per film (TMDb id)
- film_genres: one row per film per genre
- cast:        one row per film per cast credit (an actor can appear once per role)
- directors:   one row per film per director (most films have one, some two or three)

Only the crew members whose job is Director are kept. The rest of the crew
(about 25,000 rows for 112 films) is not used by any question in the brief.
Columns are renamed once, here, so generated names such as
"belongs_to_collection.name" never reach the analysis or the memo.
"""
import pandas as pd

# The columns kept from each film record, and their names in our tables
FILM_COLUMNS = {
    "id": "tmdb_id",
    "imdb_id": "imdb_id",
    "title": "title",
    "original_title": "original_title",
    "release_date": "release_date",
    "budget": "budget",
    "revenue": "revenue",
    "runtime": "runtime",
    "status": "status",
    "original_language": "original_language",
    "belongs_to_collection.id": "collection_id",
    "belongs_to_collection.name": "collection_name",
    "vote_average": "vote_average",
    "vote_count": "vote_count",
}


def check_grain(table: pd.DataFrame, key: list[str], name: str) -> None:
    """Stop the run if the table has more than one row per key."""
    repeats = table.duplicated(subset=key, keep=False)
    if repeats.any():
        raise ValueError(
            f"{name}: {int(repeats.sum())} rows break the grain {key}; "
            f"first examples:\n{table.loc[repeats, key].head()}"
        )
    print(f"  {name}: {len(table)} rows, one per {' + '.join(key)}")


def flatten_films(details: dict, fetch_log: pd.DataFrame) -> pd.DataFrame:
    """One row per film, with the fetch time of its details response."""
    films = pd.json_normalize(list(details.values()))
    # A film with no collection has belongs_to_collection = None, so the
    # collection columns may be missing entirely if no film had one.
    for column in FILM_COLUMNS:
        if column not in films.columns:
            films[column] = pd.NA
    films = films[list(FILM_COLUMNS)].rename(columns=FILM_COLUMNS)
    films["tmdb_id"] = films["tmdb_id"].astype("string")
    films["collection_id"] = films["collection_id"].astype("Int64").astype("string")
    films["release_date"] = films["release_date"].replace("", pd.NA)

    fetched_at = (fetch_log[fetch_log["endpoint"].eq("movie")]
                  .set_index("tmdb_id")["fetched_at"])
    films["details_fetched_at"] = films["tmdb_id"].map(fetched_at)
    check_grain(films, ["tmdb_id"], "films")
    return films


def flatten_genres(details: dict) -> pd.DataFrame:
    """One row per film per genre. Films with no genres have no rows here."""
    genres = pd.json_normalize(list(details.values()), record_path="genres",
                               meta="id", meta_prefix="film_")
    genres = genres.rename(columns={"film_id": "tmdb_id", "id": "genre_id",
                                    "name": "genre"})
    genres = genres[["tmdb_id", "genre_id", "genre"]].astype({"tmdb_id": "string"})
    check_grain(genres, ["tmdb_id", "genre_id"], "film_genres")
    return genres


def flatten_cast(credits: dict) -> pd.DataFrame:
    """One row per film per cast credit. order 0 is the top-billed actor."""
    cast = pd.json_normalize(list(credits.values()), record_path="cast",
                             meta="id", meta_prefix="film_")
    cast = cast.rename(columns={"film_id": "tmdb_id", "id": "person_id",
                                "name": "person_name", "order": "billing_order"})
    cast = cast[["tmdb_id", "person_id", "person_name", "character",
                 "billing_order", "credit_id"]].astype({"tmdb_id": "string"})
    check_grain(cast, ["tmdb_id", "credit_id"], "cast")
    return cast


def flatten_directors(credits: dict) -> pd.DataFrame:
    """One row per film per director, taken from the crew list."""
    crew = pd.json_normalize(list(credits.values()), record_path="crew",
                             meta="id", meta_prefix="film_")
    directors = crew[crew["job"].eq("Director")]
    directors = directors.rename(columns={"film_id": "tmdb_id", "id": "person_id",
                                          "name": "person_name"})
    directors = directors[["tmdb_id", "person_id", "person_name"]].astype(
        {"tmdb_id": "string"})
    check_grain(directors, ["tmdb_id", "person_id"], "directors")
    return directors


def flatten_all(details: dict, credits: dict, fetch_log: pd.DataFrame) -> dict:
    """Stage 3: build every table, check each grain, and check no film was lost."""
    tables = {
        "films": flatten_films(details, fetch_log),
        "film_genres": flatten_genres(details),
        "cast": flatten_cast(credits),
        "directors": flatten_directors(credits),
    }
    films = tables["films"]
    assert len(films) == len(details), "a film was lost while flattening"
    assert set(films["tmdb_id"]) == set(credits), "details and credits cover different films"

    for name in ("film_genres", "cast", "directors"):
        missing = set(films["tmdb_id"]) - set(tables[name]["tmdb_id"])
        print(f"  films with no rows in {name}: {len(missing)}"
              + (f" {sorted(missing)}" if missing else ""))
    return tables
