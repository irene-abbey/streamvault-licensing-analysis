"""Stage 4: join the tables and prove that no film was dropped or duplicated.

Two joins, each validated:
1. The id account against the films table, one to one. Every id marked
   "fetched" must have exactly one film row, and every film row must come from
   a fetched id. This links the 127 input rows to the films analysed.
2. Talent (lead actors and directors) against the films table, many to one.
   Each talent row must find exactly one film, and the join must not change the
   number of talent rows. A row-count change would mean a film was duplicated.

The films table stays one row per film; it is what the franchise comparison
uses. The talent table (one row per film per person per role) is for the
talent read only, so a film with three leads never counts three times in the
franchise averages.
"""
import pandas as pd

from pipeline import config
from pipeline.flatten import check_grain

FILM_COLUMNS_FOR_TALENT = ["tmdb_id", "title", "release_date", "budget", "revenue",
                           "collection_id", "collection_name"]


def check_account_against_films(account: pd.DataFrame, films: pd.DataFrame) -> None:
    """Every fetched id has exactly one film, and every film came from a fetched id."""
    fetched = account.loc[account["outcome"].eq("fetched"), ["tmdb_id"]]
    linked = fetched.merge(films[["tmdb_id"]], on="tmdb_id", how="outer",
                           validate="one_to_one", indicator=True)
    counts = linked["_merge"].value_counts()
    print(f"  id account to films: {counts.get('both', 0)} matched, "
          f"{counts.get('left_only', 0)} fetched ids with no film, "
          f"{counts.get('right_only', 0)} films with no fetched id")
    if counts.get("left_only", 0) or counts.get("right_only", 0):
        raise ValueError("The id account and the films table do not match")


def build_talent(cast: pd.DataFrame, directors: pd.DataFrame) -> pd.DataFrame:
    """One row per film per person per role: lead actors and directors."""
    leads = cast[cast["billing_order"] < config.LEAD_ACTOR_COUNT]
    leads = leads.sort_values("billing_order")
    # An actor can hold two credits in one film (two characters). Count them once.
    repeated = leads.duplicated(["tmdb_id", "person_id"])
    if repeated.any():
        print(f"  lead actors listed twice in the same film, counted once: {int(repeated.sum())}")
    leads = leads[~repeated].assign(role="lead actor")

    talent = pd.concat([
        leads[["tmdb_id", "person_id", "person_name", "role", "billing_order"]],
        directors.assign(role="director", billing_order=pd.NA)[
            ["tmdb_id", "person_id", "person_name", "role", "billing_order"]],
    ], ignore_index=True)
    check_grain(talent, ["tmdb_id", "person_id", "role"], "talent")
    return talent


def join_talent_to_films(talent: pd.DataFrame, films: pd.DataFrame) -> pd.DataFrame:
    """Attach each film's details to its talent rows, proving the join is clean."""
    rows_before = len(talent)
    film_talent = talent.merge(films[FILM_COLUMNS_FOR_TALENT], on="tmdb_id",
                               how="left", validate="many_to_one", indicator=True)
    unmatched = int(film_talent["_merge"].eq("left_only").sum())
    print(f"  talent to films: {rows_before} rows before, {len(film_talent)} after, "
          f"{unmatched} with no film")
    if len(film_talent) != rows_before:
        raise ValueError("The talent join changed the number of rows")
    if unmatched:
        raise ValueError(f"{unmatched} talent rows have no matching film")

    for role in ("lead actor", "director"):
        covered = film_talent.loc[film_talent["role"].eq(role), "tmdb_id"].nunique()
        print(f"  films with at least one {role}: {covered} of {len(films)}")
    return film_talent.drop(columns="_merge")


def join_all(account: pd.DataFrame, tables: dict) -> dict:
    """Stage 4: validate the id account against the films, then build film_talent."""
    films = tables["films"]
    check_account_against_films(account, films)
    talent = build_talent(tables["cast"], tables["directors"])
    tables["film_talent"] = join_talent_to_films(talent, films)
    return tables
