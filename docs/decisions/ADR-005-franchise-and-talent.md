# ADR-005: Define franchises by TMDb collection, and judge talent only on enough films across different series

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Irene

## Context

The analysis needs a rule for which films are franchise films, a way to score a whole franchise for the shortlist, and a rule for when a director or lead actor counts as a reliable signal for Kwame's negotiators.

TMDb marks series with a collection: 96 of the 112 films are in one of 32 collections, and 16 are in none. Nine collections have only one of their films on the list (for example Jaws and The Lion King), so whether those films count as franchise or standalone moves 9 films between the groups. Credits list every actor in billing order (0 is top-billed) and every crew member with a job. Some films have two or three directors. Three actors appear in 8 films each, all Harry Potter.

## Decision

- **A film is a franchise film if TMDb puts it in a collection,** even if only one of its films is on the list. The comparison is also run with the 9 single-film collections counted as standalone.
- **A franchise is scored by the median return of its films from 2000 onward,** and needs at least 2 such films to be ranked (ADR-004). Its weakest film is shown beside the median, because a bundle includes every film.
- **Lead actors are the top three billed** (billing order 0, 1 and 2). An actor with two roles in one film is counted once.
- **Directors come from the crew list, and co-directors each count fully** for the film.
- **A director or lead actor counts as a signal only with at least 3 films on the list, across at least 2 different series** (a collection, or a standalone film). Their 2000-onward median is shown beside their overall median.
- **All thresholds are settings in `config.py`.**

## Alternatives considered

**Count only collections with 2 or more films on the list as franchises.** Fits the idea of a bundle on this list, but a film in a series is a franchise entry whether or not its sequels are on the list. Run as a check, it narrows the gap: in 2000 onward, 5.05x against 4.49x instead of 5.05x against 3.84x. The direction does not change.

**Score a franchise by its weakest film, or by total revenue.** The weakest film is the standalone side's worst case and is shown, but on its own it lets one film decide the whole bundle. Total revenue favours long, expensive series regardless of cost.

**Top-billed actor only.** The strictest meaning of lead, but co-leads are missed, and very few actors would have more than one film, so the talent read would say little.

**3 films, with no rule about series.** The Harry Potter cast would top the list on one franchise's results. The series rule stops one franchise's success being credited to its cast.

**2 films.** More names, but one lucky pair of films would make a name look reliable.

## Consequences

- The talent read names 6 directors and 12 lead actors. Several of the strongest records rest on older films: Steven Spielberg's median is 13.3x overall but 4.3x on his one film from 2000 onward, and Harrison Ford's is 14.8x overall. The 2000-onward column makes this visible.
- A person's record is the films of theirs on this list, not their whole career, so a strong name may simply have few films here.
- Small samples remain: a franchise with 2 or 3 films, or a person with 3, can move a lot with one film. Counts are shown beside every figure.

## What this survives

- **Next year's list of about 500 titles:** more people and franchises will pass the thresholds, which are settings Adjoa can change without editing code.
- **A negotiator leaning on a name:** each name comes with its number of films, number of series, weakest film and 2000-onward median, so the lever's strength is visible.
- **A challenge to the franchise definition:** the alternative definition is already run in the sensitivity table, and the direction of the answer holds under both.
