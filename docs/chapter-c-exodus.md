# Chapter C — The Mid-Season Exodus: Does Losing a Star Mid-Campaign Cost You?

In August 2021, with the Brasileirão not yet at its halfway point, Red Bull
Bragantino sold Claudinho — the reigning league MVP, the man who had dragged a
small São Paulo-state club into title contention — to Zenit St. Petersburg for
around €11 million. The Russian season was just starting. The Brazilian season
had another twenty rounds to run. Bragantino, in other words, lost their best
player *in the middle of their own campaign*, and then had to keep playing it.

This is not a freak event; it is structural. Brazil's Série A runs on the
calendar year, roughly April to December. Europe's summer transfer window opens
in July and closes in early September — squarely in the middle of the Brazilian
season. So every year, a handful of Brazilian clubs watch a key player board a
plane to Europe with half a league campaign still to play. This chapter asks the
obvious question, and tries to answer it honestly: **does the club left behind
actually suffer a measurable dip in form over the rest of the season?**

It is a harder question than it sounds, because the clubs that sell are not a
random sample. A club that cashes in mid-season is often one that needs the money,
or one whose player was playing well *because the team was* — and teams that are
overperforming tend to regress with or without a sale. Selling and declining can
travel together without one causing the other. So the whole design below is built
around one discipline, carried straight over from Chapters A and B: **measure the
apparent dip, then check it against a no-effect baseline before believing it.**

## The data, and what it can and cannot tell us

Match results and pre-match [causal Elo](README.md) come from the same clean
Brasileirão history used throughout this project (2003–2024). The **departures**
come from the open [dcaribou Transfermarkt dataset](https://github.com/dcaribou/transfermarkt-datasets),
a weekly-refreshed public dump — no fragile live scraping. Every departure is
matched to a club by Transfermarkt's numeric `club_id`, never by name (club-name
matching silently confuses foreign and youth sides, and was verified to inflate
the sample badly).

Restricting to July–August departures by clubs that were actually in Série A that
season, over 2012–2024, gives **64 departures across 53 club-seasons** — the
"treated" group — against **187 non-selling club-seasons** as controls, out of 240
in total. Three honest limitations shape everything that follows:

- **Market value is the only size signal available.** Transfer *fees* are recorded
  for only ~11% of these moves, so they are unusable; **market value** is present
  for **92%** and is what we use. But the values are small — median €0.7m, 90th
  percentile €4.4m, a single €11m maximum (Claudinho) — and market value is a proxy
  for how important a player was to his team, not a direct measure. The dataset only
  carries Brazilian minutes played from 2024 onward, so a "share of the club's
  minutes" measure isn't available historically.
- **The sample is modest and recency-weighted**, which is why the window is
  2012–2024 rather than the full history, and why some estimates below are
  imprecise. We say so rather than dress it up.
- **2020 is excluded.** Its COVID-shifted calendar (played August 2020 – February
  2021) put the European summer window *before* the season even started, so there
  was no mid-campaign to disrupt — the same "drop the season the design can't
  measure" discipline Chapter B applied to Ligue 1's cancelled 2019/20.

![Mid-season departures from Série A clubs by season, 2012–2024](reports/figures/exodus_departures_by_season.png)

![Departure market values: most are small, with a thin high-dose tail](reports/figures/exodus_value_distribution.png)

The genuine "star leaves mid-campaign" cases — the ones the whole chapter is
motivated by — are the thin right-hand tail of that value distribution: Claudinho
(Bragantino → Zenit, 2021, €11m), Marcos Paulo (Fluminense → Atlético Madrid,
2021, €9m), Mário Fernandes (Grêmio → CSKA Moscow, 2012, €9m), Kaiky (Santos →
Almería, 2022, €8m), Souza (São Paulo → Fenerbahçe, 2015, €8m), Felipe
(Corinthians → Porto, 2016, €6m). Only **7** of the 53 treated club-seasons lost
a player worth €5m or more; **25** lost one worth at least €1m. Portugal is the
single most common destination — the classic stepping stone — but a third of moves
go to clubs the dataset can't identify, so we treat the departure itself, not its
destination, as the event.

## How to measure a "dip" without fooling yourself

The outcome is not raw points. A club's second-half fixtures are not its
first-half fixtures — the opponents differ in strength — so a naive "points before
vs points after" would confuse *who you played* with *how a sale affected you*. So
we measure **Elo-residual points**: for every match, the club's actual points minus
the points its pre-match Elo rating says a team of its strength should expect
against that specific opponent. Averaged over a stretch of matches, this residual
is a schedule-adjusted read of whether a club is over- or under-performing its own
established level.

We split each club-season's fixtures at the transfer window: **pre-window** matches
(before July 1), the **window itself** (July–August, excluded as a washout because
a player leaving at an unknown point inside it makes those matches ambiguous), and
**post-window** matches (from September 1). The statistic for a club-season is the
change in mean Elo-residual points, **post minus pre**. A negative value means the
club underperformed its own level more (or overperformed less) after the window
than before it — the "dip" we're hunting for. The same split is applied identically
to selling and non-selling clubs, so anything common to all clubs in the second
half of a season differences out.

Three estimators, layered from most direct to most defended — exactly the
"primary metric + naive floor + honest confound check" structure of Chapters A
and B:

## ① The apparent dip — and ③ whether it clears a no-effect floor

Across the 53 treated club-seasons, the average post-minus-pre change in
Elo-residual points is **−0.079 points per match** (raw points-per-game tells the
same story: −0.073). Taken at face value, that is a dip: clubs that sold a player
mid-season did do a little worse over the rest of the campaign than before it.

But "a little worse than before" is exactly what regression to the mean and
ordinary second-half drift produce *without any sale at all*. To see how much of
the −0.079 is real signal, we build a **placebo no-effect floor**: assign a fake
July–August "departure" to the 187 non-selling club-seasons at random, compute the
identical statistic, and repeat 2,000 times. The spread of those placebo results is
what "no effect" looks like given this data's noise — the direct analog of the
class-prior floor that every model in Chapters A and B had to clear.

![Rest-of-season form change after a mid-season sale versus the placebo no-effect floor](reports/figures/exodus_effect_vs_placebo.png)

The real treated effect (**−0.079**) sits **inside** the placebo distribution's 95%
band of **[−0.088, +0.160]**. It does not clear the floor. The event-study
confidence interval says the same thing from the other direction: **[−0.238,
+0.063]**, comfortably straddling zero. In plain terms: the dip we measured is
smaller than the swings you get by drawing random non-selling clubs and pretending
they sold someone. We cannot distinguish it from nothing.

## ② Difference-in-differences, and the trend that has to be parallel

The placebo floor handles noise, but not selection: maybe selling clubs really are
different from non-selling ones. The last layer is a **difference-in-differences** —
compare each treated club-season's post-minus-pre change against a non-selling
control club-season matched to it on pre-window Elo (nearest strength), and take the
difference. That removes any second-half drift common to comparable clubs and the
mechanical regression they share.

![Difference-in-differences and the pre-window parallel-trends check](reports/figures/exodus_did.png)

The DiD estimate is **−0.109 points per match** (treated clubs change by −0.079,
their matched controls by +0.030). It leans a touch more negative than the raw
event study — but it rests on a matching assumption that must be checked, and the
left panel above is that check. Difference-in-differences is only credible if
treated and control clubs were on **parallel trends before** the intervention;
if selling clubs were already sliding faster, the "effect" is just that slide
continuing. The pre-window residual slopes are **−0.012 for treated clubs and
−0.041 for controls** — both mildly negative, treated if anything slightly *flatter*
than control. The parallel-trends assumption is not violated, which is what makes
the DiD worth reporting at all; but −0.109 is still well within the range the
placebo floor calls noise.

Finally, if mid-season sales genuinely hurt, *bigger* sales should hurt more. They
don't, detectably: across the 48 treated club-seasons with a recorded market value,
the correlation between how much value walked out the door and the size of the
rest-of-season dip is **−0.185** — the right sign, but weak, and driven by a
handful of points.

![Dose–response: bigger sales are only weakly associated with bigger dips](reports/figures/exodus_dose_response.png)

## The verdict

Every estimator points the same direction — a small negative — and not one of them
clears its own no-effect baseline. The honest verdict is **(c): no detectable
effect**. The point estimates are consistent with a *modest* rest-of-season dip for
clubs that lose a player mid-campaign (somewhere around a tenth of a point per match,
which over twenty remaining rounds would be roughly two points — a place or two in
the table). But "consistent with a modest dip" is not the same as "shows a dip,"
and the placebo floor is explicit that this data cannot tell the two apart. If the
misalignment of Brazil's calendar with Europe's transfer windows exacts a
competitive price on the clubs left behind, it is small enough that 53 mid-season
sales over thirteen seasons cannot prove it exists.

That is a genuine finding, not a failed one. The intuitive story — sell your star
mid-season and your campaign falls apart — is the kind of narrative that feels
obviously true and mostly isn't measurable, because the clubs are deep enough, the
replacements quick enough, and the noise large enough that one player's July exit
doesn't reliably move a season. It joins Chapter A's "the quirks don't beat Elo"
and Chapter B's "the entropy metric lies" as a result whose value is in *not*
overclaiming.

## Limitations

- **Modest, recency-weighted sample.** 53 treated club-seasons is enough to rule
  out a *large* effect but not a small one; the wide confidence interval
  ([−0.238, +0.063]) is the honest expression of that. A larger or longer sample
  might resolve the small negative point estimate into a real, if minor, effect.
- **Market value is a proxy for importance, not a measure of it.** A €0.7m median
  means many "departures" were squad players whose exit shouldn't move a season; we
  cannot weight by the share of minutes or goals a player actually contributed,
  because Brazilian minutes data in this source begins only in 2024. The true "star
  leaves" effect, if any, lives in the thin high-value tail, where the sample is
  smallest.
- **Selection on unobservables remains.** The DiD and parallel-trends check
  address *observable* strength (pre-window Elo) and common drift, but a club that
  sells because of a cash crisis or a dressing-room rift carries problems Elo can't
  see. This is observational data; the placebo floor bounds the noise, not the
  hidden confounds.
- **Departures are counted gross, not net of arrivals.** A club that sold a star
  and immediately bought a replacement had its true loss muted; we don't model
  incoming signings, which biases the estimate *toward zero* — so a real effect
  would be conservatively understated here, not inflated.
- **Coarse dates.** About a fifth of the transfer dates are month-boundary
  placeholders, so we place departures in the July–August *window* rather than on an
  exact day; the excluded-washout split is designed to be robust to this, but it is
  a coarsening.
- **Season-ending collapses are dropped, not counted.** A club-season with no
  post-window matches (e.g. a schedule quirk) is excluded for lack of an outcome —
  a mild bias toward the null if a departure ever coincided with such a case.

## Reproduce

Transfer events are downloaded on first run from the public dcaribou Transfermarkt
R2 bucket and cached under `data/raw/` (gitignored); match results and Elo come
from `data/processed/matches.parquet`, built by Chapter A's pipeline. All logic
lives in `brasileirao.transfers` (acquire departures) and `brasileirao.exodus`
(Elo-expected par points, the window split, and the three estimators); the
notebooks hold only narrative and figures.

```powershell
# 1. Environment (Python 3.13) and tests
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest -q

# 2. Assemble the departures table and run the event study
.venv\Scripts\python -m jupyter nbconvert --to notebook --execute --inplace notebooks/06_transfer_data.ipynb --ExecutePreprocessor.timeout=600
.venv\Scripts\python -m jupyter nbconvert --to notebook --execute --inplace notebooks/07_exodus_event_study.ipynb --ExecutePreprocessor.timeout=900
```

Notebook 06 builds and validates the departures table; Notebook 07 computes the
three estimators, renders every figure above, and prints the (a)/(b)/(c) verdict.
Each number in this article traces to a value printed by Notebook 07.
