"""Stage 5: profile the films table and flag anything that could mislead the analysis.

This stage changes nothing. It prints and saves checks that each answer one
question about the data, so every finding in docs/data-diagnosis.md can point
to the check that found it:
- numeric summary: missing values, zeros, min, median, mean, max, and the
  mean-to-median ratio (a ratio well above 1 means a few large values pull
  the mean up)
- disguised missing values: zero or missing budget or revenue, missing or
  unreadable release dates, films not yet released
- look-alike films: two ids with the same IMDb id or the same title and year
- extremes: return multiples far from the rest (IQR rule), listed for a
  decision, never removed automatically
- the 2000 boundary and collection sizes, which decide the two windows and
  the franchise groups
"""
import pandas as pd

from pipeline import config


def numeric_summary(films: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """One row per numeric column: how complete it is and how lopsided."""
    data = films[columns]
    summary = pd.DataFrame({
        "count": data.count(),
        "missing": data.isna().sum(),
        "zeros": data.eq(0).sum(),
        "min": data.min(),
        "median": data.median(),
        "mean": data.mean(),
        "max": data.max(),
    })
    summary["mean_to_median"] = (summary["mean"] / summary["median"]).round(2)
    return summary


def add_profile_columns(films: pd.DataFrame) -> pd.DataFrame:
    """Release year, and revenue as a multiple of budget where both are usable."""
    films = films.copy()
    films["release_year"] = pd.to_datetime(films["release_date"], errors="coerce").dt.year
    usable = films["budget"].gt(0) & films["revenue"].gt(0)
    films["return_multiple"] = (films["revenue"] / films["budget"]).where(usable)
    return films


def flag_extremes(values: pd.Series) -> pd.Series:
    """True where a value is outside 1.5 times the interquartile range."""
    q1, q3 = values.quantile([0.25, 0.75])
    spread = q3 - q1
    return values.lt(q1 - 1.5 * spread) | values.gt(q3 + 1.5 * spread)


def profile_films(films: pd.DataFrame) -> dict:
    """Stage 5: run every check, print the results, and return them as tables."""
    films = add_profile_columns(films)
    numeric = numeric_summary(
        films, ["budget", "revenue", "return_multiple", "runtime", "release_year"])
    print("Numeric summary:")
    print(numeric.to_string(float_format=lambda v: f"{v:,.2f}"))

    print("\nDisguised missing values:")
    checks = {
        "budget missing or 0": films["budget"].isna() | films["budget"].eq(0),
        "revenue missing or 0": films["revenue"].isna() | films["revenue"].eq(0),
        "release date missing or unreadable": films["release_year"].isna(),
        "status not Released": films["status"].ne("Released"),
        "revenue below budget": films["revenue"].lt(films["budget"]),
    }
    for name, mask in checks.items():
        print(f"  {name}: {int(mask.sum())}")

    print("\nLook-alike films (different ids):")
    same_imdb = films["imdb_id"].notna() & films.duplicated("imdb_id", keep=False)
    same_title_year = films.assign(t=films["title"].str.casefold()).duplicated(
        ["t", "release_year"], keep=False)
    same_title = films.assign(t=films["title"].str.casefold()).duplicated("t", keep=False)
    print(f"  same IMDb id: {int(same_imdb.sum())}")
    print(f"  same title and year: {int(same_title_year.sum())}")
    print(f"  same title, different year (likely remakes, kept): {int((same_title & ~same_title_year).sum())}")

    extremes = films[flag_extremes(films["return_multiple"])].sort_values(
        "return_multiple", ascending=False)
    print(f"\nReturn multiples outside the IQR range: {len(extremes)} (listed, not removed)")
    print(extremes[["title", "release_year", "budget", "revenue", "return_multiple",
                    "collection_name"]].to_string(index=False))

    year = films["release_year"]
    print(f"\nReleased before {config.WINDOW_START_YEAR}: {int(year.lt(config.WINDOW_START_YEAR).sum())}"
          f" of {len(films)}")
    boundary = films[year.between(config.WINDOW_START_YEAR - 1, config.WINDOW_START_YEAR)]
    print(f"Released in {config.WINDOW_START_YEAR - 1} or {config.WINDOW_START_YEAR} "
          f"(boundary of the windows): {len(boundary)}")
    print(boundary[["title", "release_date"]].to_string(index=False))

    in_collection = films["collection_id"].notna()
    sizes = films[in_collection].groupby("collection_name").size()
    print(f"\nFilms in a collection: {int(in_collection.sum())}; not in one: {int((~in_collection).sum())}")
    print(f"Collections on the list: {len(sizes)}; with only one of their films on the list: "
          f"{int(sizes.eq(1).sum())}")
    print(sizes[sizes.eq(1)].index.tolist())

    flags = pd.concat(
        {name: films.loc[mask, ["tmdb_id", "title"]] for name, mask in checks.items()}
        | {"extreme return multiple": extremes[["tmdb_id", "title"]],
           "release year on the window boundary": boundary[["tmdb_id", "title"]]},
        names=["check"]).reset_index(level="check")
    return {"profile_summary": numeric.reset_index(names="column"),
            "profile_flags": flags}
