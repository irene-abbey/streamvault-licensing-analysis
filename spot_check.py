"""Spot-check the pipeline's output against TMDb as it is today.

Run separately, after the pipeline, with internet and a TMDb key:

    python spot_check.py

Films are chosen deliberately, in four groups, because errors are not spread
evenly:
- random: drawn with a fixed seed, so the check repeats and cannot be accused
  of being chosen to pass
- extremes: the highest and lowest return multiple, which pull hardest on the answer
- most transformed: films that went through the most handling (the id that was
  listed twice and also arrived as an IMDb id, the co-directed films, the
  largest cast)
- boundary and decision drivers: films either side of the 2000 cut-off, a
  single-film collection, and the films behind the deal-note number

Eight fields are compared per film: title, release date, budget, revenue,
collection, IMDb id, the lead actors (one field: their ids in billing order)
and the directors (one field: their ids). Each field is compared three ways:
the pipeline's table, the cached response it
was built from, and a fresh live response (never from the cache). That makes
every difference classifiable:
- table differs from the cached response: our bug
- table matches the cache but not the live response: source changed since the snapshot
- live response is a 404: genuinely missing
Tolerances were set before looking: exact for ids, titles, dates and people;
budget and revenue within MONEY_TOLERANCE (1%).
"""
import contextlib
import io
import json

import pandas as pd

from pipeline import config
from pipeline.analyse import prepare
from pipeline.fetch import ApiClient, _cache_file
from run_pipeline import run_stages

MONEY_FIELDS = {"budget", "revenue"}


def build_snapshot_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Rebuild the pipeline's tables from the cache, with the same stages as a normal run."""
    def quiet_timer(name, stage, *args):
        return stage(*args)

    with contextlib.redirect_stdout(io.StringIO()):
        _, tables, _, _ = run_stages(quiet_timer, save=False)
    return prepare(tables["films"]), tables["film_talent"]


def choose_films(films: pd.DataFrame, film_talent: pd.DataFrame) -> pd.DataFrame:
    """Pick the sample in four deliberate groups, and say why each film is in it."""
    picks = []

    def add(rows: pd.DataFrame, group: str, reason: str) -> None:
        for tmdb_id in rows["tmdb_id"]:
            picks.append({"tmdb_id": tmdb_id, "group": group, "reason": reason})

    add(films.sample(config.SPOT_CHECK_RANDOM, random_state=config.SPOT_CHECK_SEED),
        "random", f"fixed seed {config.SPOT_CHECK_SEED}")
    add(films.nlargest(1, "return_multiple"), "extreme", "highest return multiple")
    add(films.nsmallest(1, "return_multiple"), "extreme", "lowest return multiple")

    add(films[films["tmdb_id"].eq("155")], "most transformed",
        "listed twice and also as an IMDb id")
    directors = film_talent[film_talent["role"].eq("director")].groupby("tmdb_id").size()
    add(films[films["tmdb_id"].isin(directors[directors > 1].index)].head(2),
        "most transformed", "co-directed: several director rows")

    recent = films["release_year"].ge(config.WINDOW_START_YEAR)
    add(films[~recent].sort_values("release_date").tail(1), "boundary", "last film before the cut-off")
    add(films[recent].sort_values("release_date").head(1), "boundary", "first film from the cut-off")
    add(films[films["collection_films_on_list"].eq(1)].head(1), "boundary",
        "single-film collection")

    recent_franchise = films[recent & films["is_franchise"]]
    top = (recent_franchise.groupby("collection_name")["return_multiple"]
           .agg(["median", "size"]).query(f"size >= {config.MIN_FILMS_PER_FRANCHISE}")
           .sort_values("median", ascending=False).index[0])
    add(recent_franchise[recent_franchise["collection_name"].eq(top)], "decision driver",
        f"behind the deal-note number ({top})")

    sample = pd.DataFrame(picks)
    # A film picked twice keeps all its reasons in one row.
    return (sample.groupby("tmdb_id", sort=False)
            .agg(group=("group", " / ".join), reason=("reason", "; ".join))
            .reset_index())


def fields_from_details(body: dict) -> dict:
    collection = body.get("belongs_to_collection") or {}
    return {"title": body.get("title"), "release_date": body.get("release_date") or None,
            "budget": body.get("budget"), "revenue": body.get("revenue"),
            "collection_id": str(collection["id"]) if collection else None,
            "imdb_id": body.get("imdb_id")}


def fields_from_credits(body: dict) -> dict:
    leads = sorted((c for c in body.get("cast", []) if c["order"] < config.LEAD_ACTOR_COUNT),
                   key=lambda c: c["order"])
    directors = sorted({c["id"] for c in body.get("crew", []) if c["job"] == "Director"})
    return {"lead_actor_ids": ",".join(str(c["id"]) for c in leads),
            "director_ids": ",".join(map(str, directors))}


def fields_from_tables(tmdb_id: str, films: pd.DataFrame, film_talent: pd.DataFrame) -> dict:
    film = films[films["tmdb_id"].eq(tmdb_id)].iloc[0]
    people = film_talent[film_talent["tmdb_id"].eq(tmdb_id)]
    leads = people[people["role"].eq("lead actor")].sort_values("billing_order")
    directors = sorted(people.loc[people["role"].eq("director"), "person_id"])
    return {"title": film["title"], "release_date": film["release_date"],
            "budget": film["budget"], "revenue": film["revenue"],
            "collection_id": film["collection_id"] if pd.notna(film["collection_id"]) else None,
            "imdb_id": film["imdb_id"],
            "lead_actor_ids": ",".join(map(str, leads["person_id"])),
            "director_ids": ",".join(map(str, directors))}


def same(field: str, a, b) -> bool:
    """Exact for everything except money, which allows MONEY_TOLERANCE."""
    if field in MONEY_FIELDS and a is not None and b is not None:
        larger = max(abs(float(a)), abs(float(b)), 1.0)
        return abs(float(a) - float(b)) / larger <= config.MONEY_TOLERANCE
    return str(a) == str(b)


def classify(field: str, table, cached, live, live_found: bool) -> str:
    if not live_found:
        return "genuinely missing"
    if not same(field, table, cached):
        return "our bug"
    if not same(field, cached, live):
        return "source changed"
    return "match"


def main() -> None:
    films, film_talent = build_snapshot_tables()
    sample = choose_films(films, film_talent)
    print(f"\n== spot-check: {len(sample)} films, fetched live ==")

    client = ApiClient()
    rows = []
    for pick in sample.itertuples(index=False):   # one live request per film: not a row loop over data
        tmdb_id = pick.tmdb_id
        cached = (fields_from_details(json.loads(_cache_file("movie", tmdb_id).read_text())["body"])
                  | fields_from_credits(json.loads(_cache_file("credits", tmdb_id).read_text())["body"]))
        live_details = client.get(f"/movie/{tmdb_id}")
        live_credits = client.get(f"/movie/{tmdb_id}/credits")
        live_found = live_details[0] == 200 and live_credits[0] == 200
        live = (fields_from_details(live_details[1]) | fields_from_credits(live_credits[1])
                if live_found else {})
        table = fields_from_tables(tmdb_id, films, film_talent)
        for field in table:
            rows.append({
                "tmdb_id": tmdb_id, "title": table["title"], "group": pick.group,
                "reason": pick.reason, "field": field,
                "pipeline_table": table[field], "cached_response": cached[field],
                "live_now": live.get(field),
                "result": classify(field, table[field], cached[field], live.get(field), live_found),
            })

    results = pd.DataFrame(rows)
    config.CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    results.to_csv(config.CHECKS_DIR / "spot_check.csv", index=False)

    print(f"Fields compared: {len(results)} ({results['tmdb_id'].nunique()} films)")
    print(results["result"].value_counts().to_string())
    differences = results[results["result"].ne("match")]
    if differences.empty:
        print("Every field matches within tolerance.")
    else:
        print("\nDifferences to explain:")
        print(differences[["title", "field", "pipeline_table", "cached_response",
                           "live_now", "result"]].to_string(index=False))
    print("\nSample:")
    print(sample.merge(films[["tmdb_id", "title"]], on="tmdb_id")[
        ["title", "group", "reason"]].to_string(index=False))
    print("Saved to data/output/checks/spot_check.csv")


if __name__ == "__main__":
    main()