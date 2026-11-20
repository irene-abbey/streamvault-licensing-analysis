# Data diagnosis

Every problem found in the data, how it was found, what it does to Kwame's
recommendation, and how it is handled, ranked by how much it could move the
answer. Evidence comes from the checks the pipeline prints on every run:
`pipeline/load_ids.py` (the id list), `pipeline/fetch.py` (the fetch log) and
`pipeline/profile.py` (the films table). Snapshot: TMDb responses fetched on
2026-11-20.

## Findings, ranked by risk to the recommendation

| Rank | ID | What I saw | How I found it | Rows | What it does to the recommendation | Handling |
|---|---|---|---|---|---|---|
| 1 | F8 | All 11 extreme returns are films from 1966 to 1994: Star Wars 70x, Jaws 67x, The Godfather 41x, The Good, the Bad and the Ugly 32x, and seven more. Nine of the 11 are in a collection. | IQR rule on revenue divided by budget (`profile.py`) | 11 of 112 | The all-years comparison can be decided by a handful of old blockbusters. Their revenue is lifetime box office, including decades of re-releases, so old films look stronger than a film bought today could be. This is exactly Yaw's objection, and the main reason the result could differ between the two windows. | Kept: they are real values, not errors. Median is the headline; results are also shown without them, and for 2000 onward. |
| 2 | F9 | Every film made money: the lowest return is 1.13x (The Shawshank Redemption). No flops. The list is almost entirely famous, successful films. | Numeric summary: minimum return; revenue below budget = 0 | 112 | The standalone side's argument is that bundles include weak middle entries. A list with no flops cannot fully test that. Both groups look strong, and the gap between them says more about which hits were chosen than about bundles in general. | Kept; stated as a limit in the memo. |
| 3 | F10 | Only 16 films are not in a collection, against 96 in one. | Collection counts (`profile.py`) | 16 of 112 | The standalone figures rest on 16 films, so one or two films can move their median a lot. The 2000-onward standalone group is smaller still. | Group size shown beside every figure; the minimum group size is decided in Phase 7. |
| 4 | F11 | Revenue on TMDb is worldwide box office, not streaming value. | Field definition | 112 | Kwame is buying streaming rights. Box office is the best available signal of audience demand, but it is not what StreamVault will earn. | Used as a proxy; stated in the memo. |
| 5 | F12 | 9 collections have only one of their films on the list (for example Jaws, The Lion King, Blade Runner). | Collection sizes (`profile.py`) | 9 | Whether these count as franchise or standalone moves 9 films between the groups, and the standalone group has only 16. | Decided in Phase 7 (Q2). |
| 6 | F13 | 7 films were released in 1999 or 2000, on the edge of the 2000-onward window. | Boundary check (`profile.py`) | 7 | A wrong date would move a film between windows. The dates come from one TMDb field and all are readable. | `release_date` decides the window (Q5). |
| 7 | F4 | 5 ids return 404 on both TMDb endpoints: 8471293, 9412887, 8471294, 9412888, 7733901 | Fetch log | 5 | Five candidates cannot be evaluated. Their ids are far outside the range of the others, so they may never have been real films. | Recorded, not retried; listed below and in the memo's limits. |
| 8 | F3 | Three values that are not ids: an empty value, `-1` and `N/A` | Empty and not-digits checks (`load_ids.py`) | 3 | Three candidates cannot be evaluated. | Excluded; each listed below. |
| 9 | F1 | Six TMDb ids listed twice: 155, 680, 278, 603, 1891, 550 | Repeat check (`load_ids.py`) | 6 extra rows | Before handling: the highest risk. These include The Dark Knight, The Matrix and The Empire Strikes Back, all strong franchise films, so counting them twice would have pushed the franchise figures up. After handling: none. | Each film kept once; the copies logged. |
| 10 | F2 | An IMDb id, `tt0468569`, in a list of TMDb ids | Not-digits check; TMDb find lookup returned 155 (The Dark Knight) | 1 | Converted naively, it would add a third copy of film 155. | Converted, then logged as a duplicate of 155. |

## Checked and not a problem (false alarms)

The brief warns that the list has problems it does not name, and that not
everything that looks wrong is wrong. These were checked and found clean in this
snapshot. The code still handles them, because next year's list may have them.

| Check | Result | Rule kept in the code |
|---|---|---|
| Budget or revenue of 0 or missing | 0 of 112 | Treated as missing: excluded from return figures only, and counted (Q4) |
| Release date missing or unreadable | 0 of 112 | A film with no date stays in all years and is left out of 2000 onward (Q5) |
| Films not yet released | 0 of 112 | Reported on every run |
| Two ids for the same film (same IMDb id, or same title and year) | 0 | Reported on every run |
| Same title in different years (remakes) | 0 | Kept as different films if found |
| Revenue below budget | 0 of 112 | Kept; a loss is a real result |

## Where every id went

| Stage | Outcome | Rows |
|---|---|---|
| Load ids | Excluded: not an id | 3 |
| Load ids | Duplicate of an earlier row | 6 |
| Fetch | Duplicate: IMDb id `tt0468569` is TMDb 155 | 1 |
| Fetch | Not found on TMDb (404) | 5 |
| Fetch | Fetched: details and credits both returned | 112 |
| **Total** | | **127** |

Every row that did not become a film in the analysis:

| File row | Value | Outcome | Reason | Stage |
|---|---|---|---|---|
| 17 | 8471293 | Not found | 404 on details and credits | Fetch |
| 29 | `-1` | Excluded | Not an id | Load ids |
| 34 | 9412887 | Not found | 404 on details and credits | Fetch |
| 42 | 603 | Duplicate | Same id as an earlier row | Load ids |
| 59 | 278 | Duplicate | Same id as an earlier row | Load ids |
| 68 | (empty) | Excluded | Not an id | Load ids |
| 72 | 8471294 | Not found | 404 on details and credits | Fetch |
| 89 | 1891 | Duplicate | Same id as an earlier row | Load ids |
| 90 | 155 | Duplicate | Same id as an earlier row | Load ids |
| 92 | 9412888 | Not found | 404 on details and credits | Fetch |
| 93 | 550 | Duplicate | Same id as an earlier row | Load ids |
| 94 | `tt0468569` | Duplicate | IMDb id for TMDb 155, already listed | Fetch |
| 98 | 7733901 | Not found | 404 on details and credits | Fetch |
| 101 | 680 | Duplicate | Same id as an earlier row | Load ids |
| 110 | `N/A` | Excluded | Not an id | Load ids |

The full account, one row per input row, is written to `data/output/id_account.csv` on every run.
