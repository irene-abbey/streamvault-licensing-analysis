# ADR-001: Commit the input id list to the repository

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Irene

## Context

The pipeline has one input: `id_list.csv`, 127 TMDb ids in one column. The brief requires the analysis to run from a clean clone with no manual edits, and Adjoa must re-run it on her own laptop without me. The usual rule is not to commit data, but this file is small (128 lines) and the pipeline cannot start without it.

## Decision

`id_list.csv` is committed in `data/input/`. Everything the pipeline generates (the API cache in `data/cache/` and the results in `data/output/`) is ignored by Git and rebuilt on each run. The path to the file is set once in `pipeline/config.py`.

There are two reasons, of equal weight. First, a clean clone runs with no manual step. Second, everyone who reruns the analysis starts from exactly the same 127 ids, so any figure can be checked against the same input.

## Alternatives considered

**Download the list inside the pipeline from a shared location.** This keeps data out of the repository and would always fetch the latest list. I rejected it because it adds a dependency on a location and access rights that the brief does not give me, it fails if that location moves or Adjoa has no access in a meeting, and the input could change between runs without anyone noticing, so two runs could give different answers with no record of why.

## Consequences

- The repository runs end to end straight after cloning.
- The input is versioned: if the list changes, Git shows exactly which ids changed and when.
- The file is visible to anyone who can see the repository. It holds only public TMDb ids, so this is acceptable here, but a list containing client or personal data should not be committed this way.
- Each quarter, Adjoa replaces the file and commits the new version.

## What this survives

- **Next year's list of about 500 ids:** Adjoa replaces one file. No code changes, because the path comes from `config.py` and nothing assumes 127 rows.
- **Adjoa running it alone:** there is no file to find or place by hand.
- **A disputed figure later:** the exact input behind any result is recorded in the Git history.