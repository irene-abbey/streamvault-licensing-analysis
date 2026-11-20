# ADR-003: Measure success as the median return multiple, with no inflation adjustment

- **Status:** Accepted
- **Date:** 2026-11-20
- **Decision owner:** Irene

## Context

Kwame's team is arguing about whether franchise bundles or standalone films are the better buy. The standalone side's case is that bundles make StreamVault overpay, so any measure of success has to include cost. TMDb gives two money figures per film: budget (what the film cost to make) and revenue (worldwide box office). Neither is what StreamVault will pay or earn from streaming, so both are proxies.

The data is lopsided. Across 112 films, the median return multiple is 5.37x but the mean is 8.50x, because a few old blockbusters returned 30 to 70 times their budget (data diagnosis, F5). Franchise films also cost more: in 2000 onward, the median franchise budget is 150 million against 65 million for standalones. The films span 1966 to 2019, and Yaw in Finance distrusts figures from before 2000.

## Decision

- **Success is the return multiple:** revenue divided by budget, per film.
- **The headline is the median per group,** reported with the number of films behind it. The mean and the median revenue are shown beside it as checks.
- **A budget or revenue of 0 or missing is treated as missing:** the film keeps its place in counts and in the id account, but has no return multiple. None occur in the 2026-11-20 snapshot.
- **No inflation adjustment.** Budget and revenue for a film are in the same era's money, so their ratio largely cancels inflation. The remaining distortion for old films (revenue that includes decades of re-releases) is handled by leading with the 2000-onward window (ADR-004).

## Alternatives considered

**Median revenue.** Simple and easy to explain, but it ignores cost, which is the standalone side's whole argument. In 2000 onward it shows franchises at 787 million against 283 million for standalones, a gap of about 2.8 times, compared with 1.3 times on return. Most of that gap is bigger budgets, not better buys.

**Median profit (revenue minus budget).** Includes cost, but in money terms, so big films still dominate regardless of what they cost.

**Mean return multiple.** Uses every value, but a handful of extreme films decide it. In all years, the mean puts franchise and standalone almost level (8.54x against 8.28x), while the median shows 5.62x against 3.84x. The difference comes from a few old standalone hits such as The Good, the Bad and the Ugly (32x) and Pulp Fiction (27x).

**Adjusting to today's money.** Changes money totals but barely changes a ratio, and needs a sourced index and base year that the brief does not provide.

## Consequences

- The measure speaks directly to the overpaying argument, and one or two extreme films cannot decide it.
- A median says nothing about the spread. The weakest film in each franchise and the group sizes are shown so the risk is visible.
- Box office is not streaming value. The memo says so; if StreamVault has its own viewing data, that would be a better measure.
- A film with a tiny budget can have a huge multiple. The extremes are listed in the data diagnosis, and the comparison is also shown without them.

## What this survives

- **Next year's list of about 500 titles:** the measure, the zero rule and the median are set in code and apply to any list size. Zeros, if they appear, are counted and reported automatically.
- **Yaw's objection to old figures:** the ratio removes most of the inflation effect, and the 2000-onward window removes the old blockbusters.
- **A challenge that the median hides something:** the mean, the weakest film and the group size are all in the output tables, so anyone can see the full picture.
