# Improvement beyond the brief: the cut-off year table

## The problem it solves

The brief fixes one cut-off, 2000, because Yaw in Finance distrusts older figures. But 2000 is a round number, not a reason. In the room, the obvious next challenge is: why 2000 and not 1995, or 2005? If the answer only holds at exactly 2000, Kwame's recommendation falls apart as soon as someone moves the line. Nobody can answer that today without rerunning the analysis.

## What I built

One extra table, produced on every run of the pipeline (`data/output/kpi_by_cutoff_year.csv`). It repeats the franchise-against-standalone comparison for films released from each of six cut-off years, with the number of films behind each figure:

| Films from | Franchise films | Standalone films | Franchise median return | Standalone median return | Franchise to standalone |
|---|---|---|---|---|---|
| 1980 | 91 | 15 | 5.41 | 3.24 | 1.67 |
| 1990 | 79 | 14 | 5.12 | 3.84 | 1.33 |
| 1995 | 71 | 9 | 5.12 | 3.24 | 1.58 |
| 2000 | 63 | 8 | 5.05 | 3.84 | 1.32 |
| 2005 | 39 | 5 | 4.56 | 3.24 | 1.41 |
| 2010 | 21 | 2 | 4.56 | 4.88 | 0.93 |

The cut-off years are a setting in `pipeline/config.py`, so Adjoa can test any year without changing code.

## What it shows

Franchise films have the higher median return for every cut-off from 1980 to 2005, by 1.3 to 1.7 times. The recommendation does not depend on choosing 2000.

It reverses only at 2010, where the standalone side rests on **2 films**. That is too few to mean anything, and the table shows the count so nobody mistakes it for a finding. It is also a warning: the more recent the window, the fewer standalone films the list contains.

## What it is worth

- **To Kwame:** when someone in the room asks why 2000, he can answer that the conclusion holds for any cut-off from 1980 to 2005, with the figures in hand. That defends the recommendation against the most likely attack on it.
- **To Adjoa:** each quarter, she sees immediately whether a new list makes the answer depend on where the line is drawn, without building anything.
- **To the next list:** if next year's list has more recent standalone films, the 2005 and 2010 rows become reliable, and this table is the first place a change in the answer would show.

## What it cost

- **To build:** about 30 minutes; one function that reuses the same calculation as the main comparison.
- **To run:** under a hundredth of a second on each run.
- **Risk:** low. It changes no existing figure; it only adds a table.
