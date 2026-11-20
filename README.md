# StreamVault licensing analysis

Should StreamVault license franchise bundles or standalone films? This pipeline takes a list of TMDb film ids, fetches each film's details and credits from the TMDb API, checks and cleans the data, and compares franchise films with standalone films by return on budget, for all years and for 2000 onward.

The findings are in `docs/client-memo.md`. Everything below is for running it.

## What you need

- Windows (tested on Windows 11). macOS and Linux work with the commands adjusted.
- Python 3.11 or later. The reported figures were produced with Python 3.15.2; the setup was also installed and run on Python 3.14.
- A free TMDb API key: create an account at themoviedb.org, then Settings, API, and request a developer key. Use the **API Key**, not the Read Access Token.
- Internet for the first run only.

## Set up (once per laptop)

In PowerShell, in the folder where you keep projects:

```powershell
git clone https://github.com/irene-abbey/streamvault-licensing-analysis.git
cd streamvault-licensing-analysis
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
setx TMDB_API_KEY "your-api-key"
```

Close the terminal (and VS Code, if you use it) and open it again, so the key is picked up. Activate the environment again with `.venv\Scripts\Activate.ps1`.

If activation says running scripts is disabled, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.

Never put the key in a file in this folder or in a commit.

## Run

```powershell
python run_pipeline.py
```

- **The first run** fetches every film from TMDb and saves the responses in `data/cache/`. It takes about 2 minutes for 127 ids (about 8 to 10 minutes for 500), because it pauses between requests to respect TMDb's limits.
- **Every later run** reads from the cache, needs no internet or key, and takes under a second. Figures stay fixed to the date of the first fetch.

The run prints each stage's checks and timings. Results are written to `data/output/`, each stage's tables as soon as that stage finishes. The previous run's results are removed first. If a stage fails, the run names the stage and stops, and the tables from the stages before it are still there.

| File | What it holds |
|---|---|
| `id_account.csv` | Every row of the input list, what happened to it, and why |
| `films.csv`, `film_genres.csv`, `cast.csv`, `directors.csv`, `film_talent.csv` | The flattened tables, one grain each |
| `profile_summary.csv`, `profile_flags.csv` | Data checks and the films they flag |
| `kpi_headline.csv` | Franchise against standalone, both windows |
| `kpi_sensitivity.csv` | The same comparison under each cleaning choice: does the answer flip? |
| `kpi_by_cutoff_year.csv` | The comparison for other cut-off years (1980 to 2010), with rows on too few films marked not reliable |
| `shortlist_franchises.csv`, `shortlist_standalones.csv`, `talent_read.csv` | Shortlists and the director and lead actor read |

## Other commands

```powershell
python spot_check.py   # compares a sample of results with TMDb today (needs internet and the key)
python measure.py      # times the pipeline and tests it on larger lists
# both save their results in data/output/checks/
```

## Each quarter

- **New list:** replace `data/input/id_list.csv` (one column, `tmdb_id`). IMDb ids (`tt...`) are converted automatically. Then run the pipeline.
- **Fresh figures from TMDb:** delete the `data/cache` folder, then run the pipeline. Without this, results stay on the previous snapshot.
- **Before a meeting:** run the pipeline once beforehand, so the cached files are already loaded and the rerun in the meeting is quick.

## Settings

All rules live in `pipeline/config.py`, so they can be changed without editing code:

| Setting | Default | Meaning |
|---|---|---|
| `WINDOW_START_YEAR` | 2000 | Start of the recent comparison window |
| `LEAD_ACTOR_COUNT` | 3 | Top-billed actors counted as leads |
| `MIN_FILMS_PER_FRANCHISE` | 2 | Films from the window a franchise needs to be ranked |
| `MIN_FILMS_PER_PERSON`, `MIN_SERIES_PER_PERSON` | 3, 2 | When a director or actor counts as a signal |
| `CUTOFF_YEARS_TO_TEST` | 1980 to 2010 | Years in the cut-off table |
| `PAUSE_BETWEEN_CALLS`, `MAX_RETRIES` | 0.25 s, 3 | How politely the API is used |

## Project layout

```text
run_pipeline.py      one command that runs every stage in order
spot_check.py        live comparison with TMDb
measure.py           timing and scaling test
pipeline/            one file per stage: load_ids, fetch, flatten, join, profile, analyse; config
data/input/          the id list (committed)
data/cache/          raw TMDb responses (not committed; rebuilt by the first run)
data/output/         results (not committed; rebuilt by every run)
data/output/checks/  spot-check and timing results (not committed; kept between runs)
docs/                diagnosis, decisions (ADRs), questions, spot-check, measurement, memo, improvement
```

## If something goes wrong

- **TMDB_API_KEY is not set:** set it with `setx` as above, then open a new terminal.
- **TMDb rejected the API key (401):** the key is wrong or expired; check it on the TMDb API settings page.
- **Install fails on a newer Python:** `requirements.txt` pins exact versions of only three packages (pandas, numpy, requests), so this should be rare. If one has no installer for your Python version, install that package without the version pin and note the version you got.

## Tested versions

Python 3.15.2 with pandas 3.1.1, numpy 2.5.5 and requests 2.34.2 on Windows 11; Python 3.14 on a second laptop.
