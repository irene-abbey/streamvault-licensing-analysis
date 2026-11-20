"""Stage 2: fetch each film's details and credits from TMDb, with a cache.

Every response is cached with its fetch time, so a rerun makes no API calls.
Only failures that waiting can fix (timeouts, 429, 5xx) are retried; a 404 is
recorded and never retried; a 401 stops the run. The loop is over API calls,
not rows of data: each id needs its own request.
"""
import json
import random
import time
from datetime import datetime, timezone

import pandas as pd
import requests

from pipeline import config

RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
CACHEABLE_STATUSES = {200, 404}   # final answers; anything else is tried again next run


class ApiClient:
    """Makes TMDb requests through one session, created only if a call is needed."""

    def __init__(self):
        self._session = None
        self.calls_made = 0

    def _get_session(self) -> requests.Session:
        if self._session is None:
            session = requests.Session()
            session.headers["User-Agent"] = config.USER_AGENT
            session.params = {"api_key": config.get_api_key()}
            self._session = session
        return self._session

    def get(self, path: str, params: dict | None = None) -> tuple[int | str, dict | None]:
        """Return (status, body). Retries only failures that waiting can fix."""
        url = f"{config.API_BASE_URL}{path}"
        status: int | str = "not attempted"
        for attempt in range(config.MAX_RETRIES + 1):
            wait = config.BACKOFF_SECONDS * 2 ** attempt + random.uniform(0, 0.5)
            try:
                self.calls_made += 1
                response = self._get_session().get(
                    url, params=params, timeout=config.REQUEST_TIMEOUT)
            except (requests.Timeout, requests.ConnectionError) as exc:
                status = f"network error: {type(exc).__name__}"
            else:
                status = response.status_code
                if status == 200:
                    return status, response.json()
                if status == 404:
                    return status, None
                if status == 401:
                    raise RuntimeError("TMDb rejected the API key (401). Check TMDB_API_KEY.")
                if status not in RETRYABLE_STATUSES:
                    return status, None          # other 4xx: retrying will not help
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    wait = int(retry_after)
            if attempt < config.MAX_RETRIES:
                print(f"  {path}: {status}, retrying in {wait:.1f}s")
                time.sleep(wait)
        return status, None


def _cache_file(endpoint: str, key: str):
    return config.CACHE_DIR / endpoint / f"{key}.json"


def cached_get(client: ApiClient, endpoint: str, key: str, path: str,
               params: dict | None = None) -> dict:
    """Return the cached record for one request, calling the API only on a cache miss."""
    cache_file = _cache_file(endpoint, key)
    if cache_file.exists():
        record = json.loads(cache_file.read_text(encoding="utf-8"))
        record["from_cache"] = True
        return record

    status, body = client.get(path, params)
    record = {
        "endpoint": endpoint,
        "key": key,
        "status": status,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "body": body,
    }
    if status in CACHEABLE_STATUSES:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(record), encoding="utf-8")
    time.sleep(config.PAUSE_BETWEEN_CALLS)
    record["from_cache"] = False
    return record


def resolve_imdb_ids(client: ApiClient, account: pd.DataFrame) -> pd.DataFrame:
    """Convert IMDb ids to TMDb ids with TMDb's find lookup, then mark repeats."""
    account = account.copy()
    for index in account.index[account["outcome"].eq("imdb id")]:
        imdb_id = account.at[index, "raw_id"].strip()
        record = cached_get(client, "find", imdb_id, f"/find/{imdb_id}",
                            {"external_source": "imdb_id"})
        matches = (record["body"] or {}).get("movie_results", [])
        if record["status"] != 200 or not matches:
            account.loc[index, ["outcome", "reason", "stage"]] = [
                "excluded", f"IMDb id not found on TMDb (status {record['status']})", "fetch"]
            continue
        tmdb_id = str(matches[0]["id"])
        already_listed = account["tmdb_id"].eq(tmdb_id).any()
        account.at[index, "tmdb_id"] = tmdb_id
        if already_listed:
            account.loc[index, ["outcome", "reason", "stage"]] = [
                "duplicate", f"IMDb id {imdb_id} is TMDb {tmdb_id}, already listed", "fetch"]
        else:
            account.loc[index, ["outcome", "reason", "stage"]] = [
                "to fetch", f"converted from IMDb id {imdb_id}", "fetch"]
    return account


def fetch_all(account: pd.DataFrame):
    """Stage 2: fetch details and credits for every id marked "to fetch".

    Returns the details and credits bodies by TMDb id, a log with one row per
    request, and the id account updated with each id's fetch result.
    """
    client = ApiClient()
    account = resolve_imdb_ids(client, account)
    ids = account.loc[account["outcome"].eq("to fetch"), "tmdb_id"].tolist()
    print(f"Ids to fetch: {len(ids)} (two requests each)")

    details, credits, log_rows = {}, {}, []
    for tmdb_id in ids:
        for endpoint, path, store in (
            ("movie", f"/movie/{tmdb_id}", details),
            ("credits", f"/movie/{tmdb_id}/credits", credits),
        ):
            record = cached_get(client, endpoint, tmdb_id, path)
            log_rows.append({key: record[key] for key in
                             ("endpoint", "key", "status", "fetched_at", "from_cache")})
            if record["status"] == 200:
                store[tmdb_id] = record["body"]

    log = pd.DataFrame(log_rows).rename(columns={"key": "tmdb_id"})

    # Record each id's result in the account: fetched only if both requests worked.
    ok = log.assign(ok=log["status"].eq(200)).groupby("tmdb_id")["ok"].all()
    statuses = log.groupby("tmdb_id")["status"].agg(lambda s: ", ".join(map(str, s)))
    to_fetch = account["outcome"].eq("to fetch")
    fetched = to_fetch & account["tmdb_id"].map(ok).fillna(False).astype(bool)
    failed = to_fetch & ~fetched
    account.loc[fetched, "outcome"] = "fetched"
    account.loc[failed, "outcome"] = "fetch failed"
    account.loc[failed, "reason"] = ("details, credits status: "
                                     + account.loc[failed, "tmdb_id"].map(statuses))
    account.loc[failed, "stage"] = "fetch"

    assert len(log) == 2 * len(ids), "a request is missing from the fetch log"
    print(f"API calls made this run: {client.calls_made}")
    print(f"Requests answered from cache: {int(log['from_cache'].sum())} of {len(log)}")
    print("Request results:")
    print(log.groupby(["endpoint", "status"]).size().to_string())
    return details, credits, log, account