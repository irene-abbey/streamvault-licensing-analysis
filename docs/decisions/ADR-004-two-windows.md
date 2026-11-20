# ADR-004: Lead with the 2000-onward window, decided before seeing the results

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Irene

## Context

The brief requires the franchise-against-standalone comparison for all years and for 2000 onward, and says that if the recommendation changes between them, it must be said loudly. Yaw in Finance distrusts anything released before 2000 because of inflation, currency and how box office used to be reported, and he will say so in the room.

Profiling showed his concern is real in this list: all 11 extreme returns are films from 1966 to 1994, nine of them in a collection (data diagnosis, F5). Their revenue is lifetime box office, including re-releases, so old films look stronger than a film licensed today can be. 41 of the 112 films were released before 2000. The 2000-onward standalone group has only 8 films.

## Decision

- **2000 onward leads** the memo and the shortlists. All years is shown beside it in every table.
- **This was decided before any results were computed,** so the choice of window cannot have been made to suit the answer.
- **A film's window is set by TMDb's release_date.** A film with no date stays in all years and is left out of 2000 onward, with the count reported. None are missing in the 2026-11-20 snapshot; 7 films fall in 1999 or 2000.
- **The shortlists rank on 2000 onward.** A franchise needs at least 2 films from 2000 onward to be ranked. Franchises and standalones that are strong only on older figures are listed separately, not dropped.
- **Every comparison is run in both windows and under each cleaning choice** (extremes kept or removed, single-film collections either way), and the output shows whether the answer flips.

## Alternatives considered

**Lead with all years.** More films (16 standalones instead of 8), but the answer and the shortlists would rest on old blockbusters Yaw will challenge. Ranked on all years, Star Wars tops the franchises at 13.4x; on its 2000-onward films it returns 6.5x and ranks fourth. Four of the top five standalones would be from 1966 to 1994.

**Report only 2000 onward.** Avoids the argument, but the brief requires both windows, and Kwame would lose sight of older titles he could still license.

**Choose the window after seeing which gives a clearer answer.** Rejected because it is exactly what the brief warns against: picking the window that suits the conclusion.

## Consequences

- The memo opens on figures Yaw cannot dismiss as old.
- The standalone side of the comparison is small (8 films), so its median can move a lot with one or two films. Group sizes are shown beside every figure.
- In the 2026-11-20 snapshot the answer does not flip: franchises have the higher median return in all 8 variants checked (2000 onward 5.05x against 3.84x; all years 5.62x against 3.84x). The size of the gap is less stable, from 1.11 to 1.74 times, so the memo states the direction with more confidence than the size.
- Older franchises such as Back to the Future and Alien cannot be ranked, because they have no films from 2000 onward. They are listed as strong on older figures only.

## What this survives

- **Yaw saying it out loud:** the lead figures are 2000 onward, and the all-years figures sit beside them.
- **Next year's list of about 500 titles:** the window year is one setting in `config.py`, and the flip check runs automatically, so Adjoa sees immediately if the answer changes.
- **A recommendation that flips next year:** the sensitivity table shows it in the same run, and the memo must then say so first.
- **A different cut-off year:** changing `WINDOW_START_YEAR` reruns every table for the new window.
