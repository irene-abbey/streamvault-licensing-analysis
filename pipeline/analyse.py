"""Stage 6: compute Kwame's numbers, for both windows, without looping over rows.

Decisions applied (see docs/questions.md and the ADRs):
- Success is the return multiple: revenue divided by budget, median per group
  (Q3). A budget or revenue of 0 or missing makes the multiple missing (Q4).
- A film is a franchise film if TMDb puts it in a collection (Q2).
- The 2000-onward window leads; all years is shown beside it (Q6). The window
  is decided by release_date; a film with no date is in all years only (Q5).
- No inflation adjustment: budget and revenue are in the same era's money, so
  the ratio largely cancels it (Q9).

Every comparison is computed by one function, kpi_table(), with each cleaning
choice as a parameter, so the same code produces both windows and every
sensitivity check, and the flip check is a table rather than a claim.
"""
import pandas as pd

from pipeline import config
from pipeline.profile import add_profile_columns, flag_extremes

WINDOWS = {"2000 onward": True, "all years": False}


def prepare(films: pd.DataFrame) -> pd.DataFrame:
    """Add the columns every KPI needs: year, return multiple, group, series key."""
    films = add_profile_columns(films)
    films["is_franchise"] = films["collection_id"].notna()
    on_list = films.groupby("collection_id")["tmdb_id"].transform("size")
    films["collection_films_on_list"] = on_list
    # A "series" is a collection, or the film itself if it is standalone.
    films["series_id"] = films["collection_id"].fillna("film-" + films["tmdb_id"])
    films["is_extreme"] = flag_extremes(films["return_multiple"])
    return films


def select(films: pd.DataFrame, from_2000: bool, drop_extremes: bool = False) -> pd.DataFrame:
    """Rows for one window, optionally without the extreme returns."""
    keep = pd.Series(True, index=films.index)
    if from_2000:
        keep &= films["release_year"].ge(config.WINDOW_START_YEAR)
    if drop_extremes:
        keep &= ~films["is_extreme"]
    return films[keep]


def kpi_table(films: pd.DataFrame, group_column: str = "is_franchise") -> pd.DataFrame:
    """One row per group: how many films, how many usable, and the key statistics."""
    table = films.groupby(group_column).agg(
        titles=("tmdb_id", "size"),
        usable=("return_multiple", "count"),
        median_return=("return_multiple", "median"),
        mean_return=("return_multiple", "mean"),
        median_revenue_m=("revenue", "median"),
        median_budget_m=("budget", "median"),
    )
    table[["median_revenue_m", "median_budget_m"]] /= 1e6
    table.index = table.index.map({True: "franchise", False: "standalone"})
    return table.round(2)


def headline(films: pd.DataFrame) -> pd.DataFrame:
    """Franchise against standalone in each window, lead window first."""
    tables = {name: kpi_table(select(films, from_2000)) for name, from_2000 in WINDOWS.items()}
    return pd.concat(tables, names=["window", "group"]).reset_index()


def sensitivity(films: pd.DataFrame) -> pd.DataFrame:
    """Does the answer flip under any window or cleaning choice?"""
    singles_as_standalone = films.assign(
        is_franchise=films["is_franchise"] & films["collection_films_on_list"].ge(2))
    variants = {
        "as decided": films,
        "single-film collections as standalone": singles_as_standalone,
    }
    rows = []
    for variant, data in variants.items():
        for window, from_2000 in WINDOWS.items():
            for drop in (False, True):
                table = kpi_table(select(data, from_2000, drop))
                franchise, standalone = table.loc["franchise"], table.loc["standalone"]
                rows.append({
                    "variant": variant,
                    "window": window,
                    "extremes": "removed" if drop else "kept",
                    "franchise_n": franchise["usable"],
                    "standalone_n": standalone["usable"],
                    "franchise_median": franchise["median_return"],
                    "standalone_median": standalone["median_return"],
                    "franchise_to_standalone": round(
                        franchise["median_return"] / standalone["median_return"], 2),
                    "higher_median": "franchise" if franchise["median_return"]
                        > standalone["median_return"] else "standalone",
                })
    return mark_reliability(pd.DataFrame(rows))


def cutoff_sensitivity(films: pd.DataFrame) -> pd.DataFrame:
    """The franchise-against-standalone comparison for each cut-off year in config.

    Answers the question Yaw will ask: would the answer change if the line were
    drawn somewhere other than 2000? Each row uses only films released in or
    after that year, with the number of films behind each median.
    """
    rows = []
    for year in config.CUTOFF_YEARS_TO_TEST:
        table = kpi_table(films[films["release_year"].ge(year)])
        franchise, standalone = table.loc["franchise"], table.loc["standalone"]
        rows.append({
            "films_from": year,
            "franchise_n": int(franchise["usable"]),
            "standalone_n": int(standalone["usable"]),
            "franchise_median": franchise["median_return"],
            "standalone_median": standalone["median_return"],
            "franchise_to_standalone": round(
                franchise["median_return"] / standalone["median_return"], 2),
        })
    return mark_reliability(pd.DataFrame(rows))


def mark_reliability(table: pd.DataFrame) -> pd.DataFrame:
    """Mark rows where either group has fewer films than MIN_GROUP_SIZE."""
    enough = (table["franchise_n"].ge(config.MIN_GROUP_SIZE)
              & table["standalone_n"].ge(config.MIN_GROUP_SIZE))
    return table.assign(reliable=enough.map({True: "yes", False: "no: too few films"}))


def franchise_shortlist(films: pd.DataFrame) -> pd.DataFrame:
    """Collections scored by the median return of their films from 2000 onward (Q6, Q7).

    A collection needs MIN_FILMS_PER_FRANCHISE films from 2000 onward to be
    ranked. All-years figures and the weakest film are shown beside it, because
    a bundle includes every film, old and new.
    """
    franchises = films[films["is_franchise"]]
    recent = franchises["release_year"].ge(config.WINDOW_START_YEAR)
    table = franchises.assign(
        recent_return=franchises["return_multiple"].where(recent),
        recent=recent,
    ).groupby("collection_name").agg(
        films_on_list=("tmdb_id", "size"),
        films_2000_onward=("recent", "sum"),
        median_return_2000_onward=("recent_return", "median"),
        weakest_return_2000_onward=("recent_return", "min"),
        median_return_all_years=("return_multiple", "median"),
        weakest_return_all_years=("return_multiple", "min"),
        total_budget_m=("budget", "sum"),
    )
    table["total_budget_m"] /= 1e6
    table["ranked"] = table["films_2000_onward"].ge(config.MIN_FILMS_PER_FRANCHISE)
    return table.sort_values(["ranked", "median_return_2000_onward"],
                             ascending=False).round(2)


def standalone_shortlist(films: pd.DataFrame) -> pd.DataFrame:
    """Standalone films, ranked within the 2000-onward window first."""
    standalone = films[~films["is_franchise"]].assign(
        ranked=lambda d: d["release_year"].ge(config.WINDOW_START_YEAR))
    table = standalone[["title", "release_year", "budget", "revenue",
                        "return_multiple", "ranked"]]
    return table.sort_values(["ranked", "return_multiple"], ascending=False).round(2)


def talent_read(film_talent: pd.DataFrame, films: pd.DataFrame) -> pd.DataFrame:
    """Directors and lead actors with enough films, across enough series, to judge.

    Ranked on all their films on the list, because a person's record spans
    both windows; the 2000-onward median is shown beside it so a name whose
    record rests on older films can be seen.
    """
    talent = film_talent[["tmdb_id", "person_id", "person_name", "role"]].merge(
        films[["tmdb_id", "return_multiple", "series_id", "release_year"]],
        on="tmdb_id", how="left", validate="many_to_one")
    recent = talent["release_year"].ge(config.WINDOW_START_YEAR)
    talent = talent.assign(recent_return=talent["return_multiple"].where(recent),
                           recent=recent)
    table = talent.groupby(["role", "person_id", "person_name"]).agg(
        films=("tmdb_id", "nunique"),
        films_2000_onward=("recent", "sum"),
        series=("series_id", "nunique"),
        median_return=("return_multiple", "median"),
        weakest_return=("return_multiple", "min"),
        median_return_2000_onward=("recent_return", "median"),
        first_year=("release_year", "min"),
        last_year=("release_year", "max"),
    ).reset_index()
    reliable = (table["films"].ge(config.MIN_FILMS_PER_PERSON)
                & table["series"].ge(config.MIN_SERIES_PER_PERSON))
    return (table[reliable].drop(columns="person_id")
            .sort_values(["role", "median_return"], ascending=[True, False]).round(2))


def analyse(tables: dict) -> dict:
    """Stage 6: every number the memo needs, saved as tables and printed."""
    films = prepare(tables["films"])
    results = {
        "kpi_headline": headline(films),
        "kpi_sensitivity": sensitivity(films),
        "kpi_by_cutoff_year": cutoff_sensitivity(films),
        "shortlist_franchises": franchise_shortlist(films).reset_index(),
        "shortlist_standalones": standalone_shortlist(films),
        "talent_read": talent_read(tables["film_talent"], films),
    }
    show = {
        "kpi_headline": None,
        "kpi_sensitivity": None,
        "kpi_by_cutoff_year": None,
        "shortlist_franchises": None,
        "shortlist_standalones": None,
        "talent_read": None,
    }
    for name, rows in show.items():
        print(f"\n{name}:")
        table = results[name]
        print((table if rows is None else table.head(rows)).to_string(index=False))

    top = results["shortlist_franchises"].iloc[0]
    lead = kpi_table(select(films, from_2000=True)).loc["standalone"]
    print(f"\nDeal note (2000 onward): {top['collection_name']} median return "
          f"{top['median_return_2000_onward']}x over {top['films_2000_onward']} films is "
          f"{top['median_return_2000_onward'] / lead['median_return']:.2f} times the "
          f"standalone median of {lead['median_return']}x over {int(lead['usable'])} films")
    return results