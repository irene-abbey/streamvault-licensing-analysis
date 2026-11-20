import time

from pipeline import config
from pipeline.fetch import fetch_all
from pipeline.load_ids import load_ids

timings = {}


def timed(name, stage, *args):
    """Run one stage, record how long it took, and return its result."""
    print(f"\n== {name} ==")
    start = time.perf_counter()
    result = stage(*args)
    timings[name] = round(time.perf_counter() - start, 3)
    return result


def not_built(name):
    print(f"{name}: not built yet")


def report_id_account(account) -> None:
    """Save the id account and show that every row of the input is accounted for."""
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    account.to_csv(config.OUTPUT_DIR / "id_account.csv", index=False)
    print("\n== id account ==")
    print(account["outcome"].value_counts().to_string())
    print(f"Total: {len(account)} rows, saved to data/output/id_account.csv")


def main():
    account = timed("load ids", load_ids)
    details, credits, fetch_log, account = timed("fetch", fetch_all, account)
    for name in ["flatten", "join", "analyse"]:
        timed(name, not_built, name)
    report_id_account(account)
    print("\nSeconds per stage:", timings)


if __name__ == "__main__":
    main()