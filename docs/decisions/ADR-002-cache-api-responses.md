# ADR-002: Fetch each response once, cache it with its fetch time, and retry only what waiting can fix

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Irene

## Context

The analysis needs two TMDb requests per film (details and credits): 234 requests for the 117 unique TMDb ids in this year's 127-row list (the other 10 rows are duplicates or not ids; data diagnosis F1 to F3), and about 1,000 for next year's list of about 500. TMDb is a free, shared service, and many learners are fetching the same films this week. Development means running the pipeline many times. Adjoa must be able to rerun the analysis on her own laptop, sometimes live in a meeting, possibly without internet (Q1). TMDb is edited by its community every day, so the same request can return different numbers on different days. The first full fetch took about 117 seconds; the same run from the cache took under a second.

## Decision

- **Fetch once, then read from the cache.** Every response is saved to `data/cache/<endpoint>/<id>.json` with its status and the UTC time it was fetched. The cache is checked before every request, so a rerun makes no API calls.
- **Final answers are cached, including 404s.** A 200 or a 404 is stored. A 404 means TMDb has no film with that id, so it is recorded in the id account and not asked again.
- **The cache is refreshed by hand, not automatically.** To take a new snapshot, delete `data/cache/` and run the pipeline once. Adjoa does this each quarter, on purpose. Results are always tied to one dated snapshot.
- **The cache is not committed to Git.** A clean clone runs a first fetch, which needs a TMDb key and internet for about two minutes.
- **Retry only what waiting can fix.** Timeouts, connection errors, 429 (rate limit) and 5xx (server errors) are retried up to three times, waiting 1, 2 and 4 seconds plus a small random jitter, or as long as the server's Retry-After asks. Other errors, including 404, are not retried. A 401 (bad key) stops the run at once with a clear message.
- **Treat the API politely.** One session for all requests, a 0.25-second pause after each request, a connect and read timeout on every request, and a User-Agent that identifies the project.
- **IMDb ids are converted with TMDb's find lookup**, also cached. This is a third endpoint beyond the two the brief names, used only for ids in IMDb format (F2).

## Alternatives considered

**Fetch live on every run.** Always current, but each run takes about two minutes, needs the key and internet, and can give different numbers on different days for reasons nobody chose. A figure challenged at the board could not be traced to what TMDb said at the time.

**Expire cached responses automatically (for example, after 30 days).** Keeps data fresher without anyone acting, but results could change between two runs without anyone deciding it, and the snapshot behind a reported figure would be unclear. It also breaks the spot-check, which compares a fixed snapshot against a live re-fetch.

**Retry 404s on every run.** Would pick up a film restored on TMDb automatically, but costs 10 extra requests per run on this list, makes every run need the key and internet (contradicting Q1), and goes against the rule not to retry a permanent failure. A manual refresh picks up restored films anyway.

**Commit the cache to Git.** A clean clone would reproduce my exact numbers with no key, but it puts data in the repository and stores TMDb's content in a public place without checking their terms.

## Consequences

- After the first fetch, every run is fast, offline and gives the same numbers.
- Every figure can be traced to a dated TMDb response. The memo quotes the fetch date as its as-of date.
- A clean clone needs a TMDb key and one online run. The README must say so, and a grader's numbers may differ slightly from mine if TMDb has changed since my fetch date.
- The cache can go stale. Someone has to decide to refresh it.
- If TMDb restores a deleted film, it is only picked up at the next manual refresh.

## What this survives

- **Next year's list of about 500 ids:** about 1,000 requests in the first run (roughly eight to ten minutes with the pause), then fast offline reruns. Only new ids are fetched if the cache is kept.
- **Adjoa rerunning it alone, in a meeting:** no internet or key needed after the first run.
- **A figure challenged at the board:** the cached response and its fetch time show exactly what TMDb said and when.
- **TMDb being slow or briefly down:** temporary failures are retried; anything still failing is recorded, and the next run tries again because failures other than 404 are not cached.
- **A wrong or expired key:** the run stops at once and says so, instead of recording 117 failures.