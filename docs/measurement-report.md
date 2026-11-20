# Measurement report: pipeline run time

## Target

A full rerun of the pipeline from the cached TMDb responses finishes in **under 10 seconds**, for this year's list and for next year's list of about 500 titles. Adjoa may rerun the analysis live in a meeting, so it has to be quick enough to run while people wait.

The brief does not give a number, so this target is my own assumption (questions log, Q1; ADR-002). The first fetch from TMDb is not part of the target: it depends on TMDb and the internet, not on our code, and it happens once per snapshot.

## Method

- **Hardware and software:** Windows 11 (10.0.26300), Intel 64 processor (family 6, model 140), Python 3.15.2, pandas 3.1.1, numpy 2.5.5. This is the laptop the analysis will be presented from.
- **What was timed:** each stage of `run_pipeline.py`, from the start of the stage to the end, using `time.perf_counter()`: load ids, fetch (answered from the cache), flatten, join, profile and analyse. Printing to the screen is excluded.
- **What was not timed:** fetching from TMDb. The first full fetch of 235 requests took 117 seconds on 2026-11-20, most of it the deliberate 0.25-second pause between requests (ADR-002).
- **Runs:** 6 full runs in a row. The first is reported separately as the **cold run** (files not yet in the computer's memory). The figure reported is the **median of runs 2 to 6** (warm runs), with the slowest warm run beside it.
- **Scaling:** the analysis stage was run 6 times each on synthetic lists of 127, 500 and 5,000 films, built by sampling the real films with replacement (fixed seed, so the lists are the same on every run) and giving each copy a new id. The median is reported.
- **How to reproduce:** after one full `python run_pipeline.py`, run `python measure.py`. Results are saved to `data/output/checks/timings.csv` and `data/output/checks/scaling.csv`.

## Results

**Full pipeline from the cache (127 ids, 112 films):**

| Stage | Cold run (s) | Warm runs, median (s) | Slowest warm run (s) |
|---|---|---|---|
| Load ids | 0.031 | 0.006 | 0.012 |
| Fetch, from the cache | 6.950 | 0.118 | 0.166 |
| Flatten | 0.194 | 0.199 | 0.204 |
| Join | 0.012 | 0.009 | 0.013 |
| Profile | 0.015 | 0.010 | 0.014 |
| Analyse | 0.061 | 0.061 | 0.064 |
| **Total** | **7.263** | **0.411** | **0.447** |

Both the warm rerun (0.41 seconds) and the cold rerun (7.26 seconds) meet the 10-second target for this year's list.

**Analysis stage on larger lists:**

| Films | Analyse (s) | Seconds per 1,000 films |
|---|---|---|
| 127 | 0.063 | 0.496 |
| 500 | 0.065 | 0.130 |
| 5,000 | 0.095 | 0.019 |

Forty times as many films took about 1.5 times as long. Most of the analysis time is fixed set-up, not work per film, because every calculation runs on whole columns at once (no loops over rows).

## Before and after

The one design change that decides the run time is the cache (ADR-002). Without it, every run would fetch from TMDb.

| Run | Before: fetch from TMDb on every run | After: read from the cache |
|---|---|---|
| Fetch stage, 127 ids | 116.8 s (first run, 235 requests) | 0.118 s (warm median) |
| Whole pipeline | about 117.5 s | 0.411 s (warm median); 7.263 s (cold) |
| Needs internet and a key | Yes, every run | Only for the first run |

## Projection to 500 titles

| Stage | How it grows | Projected at 500 titles (s) |
|---|---|---|
| Fetch from the cache, warm | With the number of cached files (about 1,000) | about 0.5 |
| Flatten | With the number of credit rows | about 0.9 |
| Analyse | Barely, as measured above | about 0.07 |
| Other stages | Small at any size | under 0.1 |
| **Warm rerun total** | | **about 1.5** |

The warm rerun stays well inside the target. The **cold rerun may not**: reading 234 cached files took 6.95 seconds cold, about 0.03 seconds per file, so about 1,000 files could take around 30 seconds the first time after the laptop starts. See the caveats.

The first fetch from TMDb at 500 titles is about 1,000 requests, roughly 8 to 10 minutes with the pause. That happens once per snapshot, before the meeting.

## Caveats

- **The cold read is the risk to the target.** The cold run spent 6.95 of its 7.26 seconds opening the 234 small cache files for the first time. On Windows this is usually the disk and the antivirus scanning each file; once read, the same files take 0.12 seconds. At 500 titles a cold rerun could exceed 10 seconds. Two simple mitigations: run the pipeline once before the meeting so the files are warm, or store the cache as one file per endpoint instead of one file per film (a change for next year, not made here).
- **Synthetic lists repeat real films many times:** 500 films drawn from 112 means each real film appears about 4 times, and 5,000 means about 45 times. The timings show how the code grows with the number of rows, but the per-1,000-films figure may look better than it would for 5,000 genuinely different films, for example because a few collections grow very large. Next year's real list of about 500 titles should be timed with `measure.py` when it arrives.
- **Timings vary between runs** by a few hundredths of a second; the slowest warm run is shown so the spread is visible.
- **Only one machine was measured.** Adjoa's laptop may be slower or faster; `measure.py` lets her check on her own machine in under a minute.