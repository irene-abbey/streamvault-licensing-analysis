"""Time the pipeline from the cache, and test how the analysis grows with the list.

Run after one full pipeline run, so the cache is filled: python measure.py
Each stage is timed over 6 runs; the first (cold) run is reported separately
and the median of the rest is the reported figure. Fetching from TMDb is not
timed, because it measures the network, not our code.
"""
import contextlib
import io
import platform
import statistics
import time

import numpy as np
import pandas as pd

from pipeline import config
from pipeline.analyse import analyse
from run_pipeline import run_stages

RUNS = 6
SCALE_SIZES = [127, 500, 5000]


def run_once() -> tuple[dict, dict]:
    """One full run from the cache, with output hidden; returns timings and tables.

    Uses run_stages() from run_pipeline.py, so the stages and their order are
    exactly those of a normal run. Writing CSV files is left out, because it is
    not part of any stage's work.
    """
    timings = {}

    def silent_timer(name, stage, *args):
        start = time.perf_counter()
        result = stage(*args)
        timings[name] = time.perf_counter() - start
        return result

    with contextlib.redirect_stdout(io.StringIO()):
        _, tables, _, _ = run_stages(silent_timer, save=False)
    timings["total"] = sum(timings.values())
    return timings, tables


def synthetic(tables: dict, n_films: int, seed: int = 0) -> dict:
    """A list of n_films built by sampling the real films, each copy with a new id.

    The seed is fixed, so the same synthetic lists are built on every run and
    timings can be compared. Sampling 500 or 5,000 films from 112 repeats each
    real film many times; the timings measure how the code grows with the
    number of rows, not how it would handle 5,000 different films.
    """
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

    config.CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    report.to_csv(config.CHECKS_DIR / "timings.csv")
    scaling.to_csv(config.CHECKS_DIR / "scaling.csv", index=False)
    print("\nSaved to data/output/checks/timings.csv and data/output/checks/scaling.csv")


if __name__ == "__main__":
    main()