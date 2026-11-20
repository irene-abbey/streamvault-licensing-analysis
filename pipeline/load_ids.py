import pandas as pd

from pipeline import config


def read_id_list(path=config.ID_LIST) -> pd.Series:
    """Read the id list as text, so no value is converted or dropped on the way in."""
    if not path.exists():
        raise FileNotFoundError(f"Id list not found: {path}")

    table = pd.read_csv(path, dtype="string", keep_default_na=False,
                        skip_blank_lines=False)
    if table.shape[1] != 1:
        raise ValueError(
            f"Expected one column, found {table.shape[1]}: {list(table.columns)}"
        )
    header = table.columns[0]
    print(f"Column name in file: {header!r}")
    if header.strip().isdigit():
        print("  WARNING: the header looks like an id; the file may have no header row")
    return table.iloc[:, 0].rename("raw_id")


def check_ids(raw: pd.Series) -> dict:
    """Count each kind of problem in the raw ids. Nothing is changed."""
    stripped = raw.str.strip()
    is_digits = stripped.str.fullmatch(r"\d+")

    # Hidden duplicates: different raw text that becomes the same id once
    digits = pd.DataFrame({"raw_id": raw[is_digits],
                           "normalised": stripped[is_digits].str.lstrip("0")})
    forms_per_id = digits.groupby("normalised")["raw_id"].nunique()
    hidden_ids = forms_per_id[forms_per_id > 1].index

    return {
        "rows": len(raw),
        "empty": raw[stripped.eq("")].tolist(),
        "spaces around value": raw[raw.ne(stripped) & stripped.ne("")].tolist(),
        "not digits only": raw[~is_digits & stripped.ne("")].tolist(),
        "leading zero": raw[stripped.str.startswith("0")].tolist(),
        "exact repeats": raw[raw.duplicated(keep=False)].value_counts().to_dict(),
        "same id written differently": digits[digits["normalised"].isin(hidden_ids)]
            .groupby("normalised")["raw_id"].apply(list).to_dict(),
        "unique ids after normalising": int(digits["normalised"].nunique()),
    }


def print_report(report: dict) -> None:
    """Print the checks so every problem is visible on every run."""
    print(f"Rows read: {report['rows']}")
    for name, found in report.items():
        if name in ("rows", "unique ids after normalising"):
            continue
        print(f"  {name}: {len(found)}")
        if found:
            print(f"    {found}")
    print(f"Unique ids after normalising: {report['unique ids after normalising']}")


def classify_ids(raw: pd.Series) -> pd.DataFrame:
    """Give every row of the file an outcome and a reason. One row per file row."""
    stripped = raw.str.strip()
    is_tmdb = stripped.str.fullmatch(r"\d+")
    is_imdb = stripped.str.fullmatch(r"tt\d+")

    account = pd.DataFrame({
        "file_row": range(1, len(raw) + 1),   # 1 = first id under the header
        "raw_id": raw.to_numpy(),
        "tmdb_id": stripped.str.lstrip("0").where(is_tmdb).to_numpy(),
    })
    account["outcome"] = "excluded"
    account["reason"] = "not an id (placeholder for a missing value)"
    account["stage"] = "load ids"

    account.loc[is_imdb.to_numpy(), ["outcome", "reason"]] = [
        "imdb id", "IMDb id; converted to a TMDb id in the fetch stage"]

    tmdb_rows = is_tmdb.to_numpy()
    repeat = account["tmdb_id"].duplicated(keep="first") & tmdb_rows
    account.loc[tmdb_rows, ["outcome", "reason"]] = ["to fetch", ""]
    account.loc[repeat, ["outcome", "reason"]] = [
        "duplicate", "same TMDb id as an earlier row; kept once"]
    return account


def load_ids(path=config.ID_LIST) -> pd.DataFrame:
    """Stage 1: read the id list, report the checks, and return the id account."""
    raw = read_id_list(path)
    print_report(check_ids(raw))
    account = classify_ids(raw)
    print("Outcomes after loading:")
    print(account["outcome"].value_counts().to_string())
    assert len(account) == len(raw), "a row was lost while classifying"
    return account