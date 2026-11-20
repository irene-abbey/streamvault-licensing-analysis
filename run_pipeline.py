"""Run the StreamVault pipeline from start to finish with one command:

    python run_pipeline.py

The stages run in a fixed order, defined once in run_stages(), which
measure.py also uses. Each stage's tables are saved to data/output/ as soon as
that stage finishes, so if a later stage fails, the earlier results can still
be inspected. Results from the previous run are removed first, so data/output/
never mixes two runs. If a stage fails, the run names the stage and stops.
"""
import time

from pipeline import config
from pipeline.analyse import analyse
from pipeline.fetch import fetch_all
from pipeline.flatten import flatten_all
from pipeline.join import join_all
from pipeline.load_ids import load_ids
from pipeline.profile import profile_films

timings = {}


def timed(name, stage, *args):
    """Run one stage, print its name, record how long it took, and return its result."""
    print(f"\n== {name} ==")
    start = time.perf_counter()
    try:
        result = stage(*args)
    except Exception:
        print(f"\nFAILED in stage '{name}'. Results of the stages before it are in data/output/.")
        raise
    timings[name] = round(time.perf_counter() - start, 3)
    return result


def clear_outputs() -> None:
    """Remove the previous run's tables, so outputs never mix two runs."""
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for old_file in config.OUTPUT_DIR.glob("*.csv"):
        old_file.unlink()


def save_tables(tables: dict) -> None:
    """Save each table as a CSV file in data/output/."""
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(config.OUTPUT_DIR / f"{name}.csv", index=False)


def run_stages(timer, save: bool = True) -> tuple:
    """Every stage, in order. timer runs and times one stage; save writes its tables."""
    keep = save_tables if save else (lambda tables: None)

    account = timer("load ids", load_ids)
    keep({"id_account": account})

    details, credits, fetch_log, account = timer("fetch", fetch_all, account)
    keep({"id_account": account})

    tables = timer("flatten", flatten_all, details, credits, fetch_log)
    keep(tables)

    tables = timer("join", join_all, account, tables)
    keep({"film_talent": tables["film_talent"]})

    profile = timer("profile", profile_films, tables["films"])
    keep(profile)

    results = timer("analyse", analyse, tables)
    keep(results)
    return account, tables, profile, results


def main():
    clear_outputs()
    account, tables, profile, results = run_stages(timed)
    print("\n== id account ==")
    print(account["outcome"].value_counts().to_string())
    print(f"Total: {len(account)} rows, saved to data/output/id_account.csv")
    print("\nSeconds per stage:", timings)


if __name__ == "__main__":
    main()