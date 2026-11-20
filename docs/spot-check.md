# Spot-check against the live API

**Run:** 2026-11-20, against the snapshot fetched the same day.
**Command:** `python spot_check.py` (needs internet and a TMDb key). Full results: `data/output/checks/spot_check.csv`.

## What was checked

13 films, chosen in four groups because errors are not spread evenly:

| Group | Films | Why |
|---|---|---|
| Random (fixed seed 2026) | Terminator Salvation, Mission: Impossible II, Schindler's List, Ocean's Eleven | Repeatable, and cannot be said to be chosen to pass |
| Extremes | Star Wars (highest return, 70.5x), The Shawshank Redemption (lowest, 1.13x) | They pull hardest on the medians and the shortlists |
| Most transformed | The Dark Knight (listed twice and also as an IMDb id), The Lion King and Avengers: Endgame (co-directed) | The most handling, so the most chances for an error |
| Boundary and decision drivers | Toy Story 2 (last film before 2000), Mission: Impossible II (first from 2000), The Lion King (single-film collection), the three Lord of the Rings films (behind the deal-note number) | They decide which window and group a film is in, and the one number in the deal note |

For each film, 8 fields were compared: title, release date, budget, revenue, collection, IMDb id, the lead actors (one field: the ids of the three top-billed actors, in billing order) and the directors (one field: the ids of all directors). 13 films times 8 fields is 104 fields.

Each field was compared three ways: the pipeline's table, the cached response it was built from, and a fresh request to TMDb (not from the cache). A difference would be classed as:

- **our bug:** the table differs from the cached response;
- **source changed:** the table matches the cache, but TMDb now says something else;
- **genuinely missing:** TMDb now returns 404 for the film.

**Tolerances, set before the check was run:** exact for ids, titles, dates, collections and people; within 1% for budget and revenue.

## Result

| Result | Fields |
|---|---|
| Match | 104 |
| Our bug | 0 |
| Source changed | 0 |
| Genuinely missing | 0 |

Every field matches within tolerance, so no discrepancy moves the recommendation.

## Limits

- **The snapshot was a few hours old when checked.** The match shows the pipeline carries TMDb's values through without error; it does not show they will stay the same. TMDb is edited every day, so a rerun later may find source changes, which should be recorded with both values and both dates.
- **This compares the output with TMDb, not with an independent source.** It proves the pipeline did not corrupt the data, not that TMDb's box office figures are right. TMDb revenue is worldwide box office including re-releases (data diagnosis, F8).