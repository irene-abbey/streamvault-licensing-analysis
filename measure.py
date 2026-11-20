import contextlib
import io
import platform
import statistics
import time

import numpy as np
import pandas as pd

from pipeline import config
from pipeline.analyse import analyse
from pipeline.fetch import fetch_all
from pipeline.flatten import flatten_all
from pipeline.join import join_all
from pipeline.load_ids import load_ids
from pipeline.profile import profile_films

RUNS = 6
SCALE_SIZES = [127, 500, 5000]


def run_once() -> tuple[dict, dict]:
    """One full run from the cache, with output hidden; returns timings and tables."""
    timings = {}
    with contextlib.redirect_stdout(io.StringIO()):
        start = time.perf_counter()
        account = load_ids()
        timings["load ids"] = time.perf_counter() - start

        start = time.perf_counter()
        details, credits, fetch_log, account = fetch_all(account)
        timings["fetch (from cache)"] = time.perf_counter() - start

        start = time.perf_counter()
        tables = flatten_all(details, credits, fetch_log)
        timings["flatten"] = time.perf_counter() - start

        start = time.perf_counter()
        tables = join_all(account, tables)
        timings["join"] = time.perf_counter() - start

        start = time.perf_counter()
        profile_films(tables["films"])
        timings["profile"] = time.perf_counter() - start

        start = time.perf_counter()
        analyse(tables)
        timings["analyse"] = time.perf_counter() - start
    timings["total"] = sum(timings.values())
    return timings, tables


def synthetic(tables: dict, n_films: int, seed: int = 0) -> dict:
    """A list of n_films built by sampling the real films, each copy with a new id."""
    films = tables["films"].sample(n_films, replace=True, random_state=seed)
    new_ids = pd.Series(np.arange(1, n_films + 1).astype(str), index=films.index)
    mapping = pd.DataFrame({"tmdb_id": films["tmdb_id"].to_numpy(),
                            "new_id": new_ids.to_numpy()})
    talent = tables["film_talent"].merge(mapping, on="tmdb_id")
    return {"films": films.assign(tmdb_id=new_ids.to_numpy()),
            "film_talent": talent.assign(tmdb_id=talent["new_id"]).drop(columns="new_id")}


def time_analysis(data: dict) -> float:
    """Median seconds for the analysis stage over RUNS runs."""
    times = []
    for _ in range(RUNS):
        with contextlib.redirect_stdout(io.StringIO()):
            start = time.perf_counter()
            analyse(dict(data))
            times.append(time.perf_counter() - start)
    return statistics.median(times)


def main() -> None:
    print(f"Machine: {platform.platform()}, {platform.processor() or platform.machine()}")
    print(f"Python {platform.python_version()}, pandas {pd.__version__}, numpy {np.__version__}")

    runs = [run_once() for _ in range(RUNS)]
    tables = runs[-1][1]
    timings = pd.DataFrame([timing for timing, _ in runs])
    report = pd.DataFrame({
        "cold run (s)": timings.iloc[0],
        f"median of warm runs {2}-{RUNS} (s)": timings.iloc[1:].median(),
        "slowest warm run (s)": timings.iloc[1:].max(),
    }).round(3)
    print(f"\nFull pipeline from the cache, {RUNS} runs:")
    print(report.to_string())

    print("\nAnalysis stage on larger synthetic lists:")
    rows = []
    for size in SCALE_SIZES:
        seconds = time_analysis(synthetic(tables, size))
        rows.append({"films": size, "analyse (s)": round(seconds, 3)})
    scaling = pd.DataFrame(rows)
    scaling["seconds per 1,000 films"] = (scaling["analyse (s)"] / scaling["films"] * 1000).round(3)
    print(scaling.to_string(index=False))

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report.to_csv(config.OUTPUT_DIR / "timings.csv")
    scaling.to_csv(config.OUTPUT_DIR / "scaling.csv", index=False)
    print("\nSaved to data/output/timings.csv and data/output/scaling.csv")


if __name__ == "__main__":
    main()
