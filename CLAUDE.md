# Data Football — Brasileirão Study

Portfolio data science project on the Brazilian Série A (Brasileirão). English-language,
aimed at international freelance clients and employers. Demonstrates ML rigor and honest
storytelling. Planned as a three-chapter anthology; **Chapter A is complete and merged to
`main`.**

## Status

- **Phase 0 (shared foundation)** — DONE. Reusable package, clean match dataset, curated
  stadium reference data.
- **Phase 1 / Chapter A — "Anatomy of the World's Strongest Home Advantage"** — DONE.
  Home-advantage decomposition + outcome model + SHAP. README.md is the finished article.
- **Chapter B / Chapter C** — not started. Scoped in the spec; each needs its own
  spec → plan → implementation cycle.

Spec: `docs/superpowers/specs/2026-07-19-brasileirao-home-advantage-design.md`
Plan: `docs/superpowers/plans/2026-07-19-brasileirao-home-advantage.md`

## Architecture

All logic lives in the installable package `src/brasileirao/`; notebooks hold narrative
and figures only; README.md is the article.

| Module | Responsibility |
|---|---|
| `paths.py` | Single source of truth for filesystem locations; creates data dirs on import |
| `ingest.py` | Download + clean match results → canonical `matches.parquet` |
| `geo.py` | Stadium coordinates, haversine travel distance, team-name alias resolution |
| `ratings.py` | Causal Elo (pre-match ratings from strictly prior matches) |
| `features.py` | Model-ready feature table (Elo + travel, temp, rest, crowd, same-state) |
| `analysis.py` | Home/away points share, bootstrap confidence intervals |
| `model.py` | LightGBM, expanding-window season CV, class-prior floor, SHAP inputs |
| `plotting.py` | Shared figure style + save helper |

Notebooks: `01_data_overview` (hook + anchor chart), `02_home_advantage_story` (crowd /
travel / heat decomposition), `03_model_and_shap` (model vs baselines, calibration, SHAP).
Figures export to `reports/figures/` (committed; the README embeds them).

## How to run

Python **3.13** (LightGBM/SHAP wheels confirmed there; 3.14 is the machine default but was
not used). Windows / PowerShell.

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest -q                                  # 31 tests
.venv\Scripts\python -c "from brasileirao import ingest; ingest.build()"
.venv\Scripts\python -m jupyter nbconvert --to notebook --execute --inplace notebooks/01_data_overview.ipynb --ExecutePreprocessor.timeout=600
# ...same for notebooks 02 and 03
```

The whole project regenerates from scratch: delete `data/processed/`, and tests + all three
notebooks run clean.

## Key results (Chapter A)

- Brasileirão home points share **0.652** (2015–2018) vs La Liga 0.600, Premier League 0.585.
- Overall home points share 2003–2024: **0.6407** (8,785 matches).
- Crowd effect (closed-door window vs 2017–19 controls): 0.634 → 0.582, drop **0.051**,
  95% CI [0.009, 0.095] — real but imprecise.
- Travel: no smooth gradient; penalty only beyond ~2,200 km.
- Heat: null result (but the feature is a crude annual-mean proxy).
- Model: Elo-only log loss 1.0303 and full model 1.0318 both beat the class-prior floor
  (1.0514); the quirk features add **no** per-match predictive skill over Elo (lift −0.0015).
- **Headline framing:** effects are real in *aggregate* points share, not in *per-match*
  prediction. Elo already captures nearly everything forecastable about one match.

## Data sources & known adaptation points

- Match results: `adaoduque/Brasileirao_Dataset` GitHub CSV (auto-downloaded → `data/raw/`).
- European results + Brazilian bookmaker odds: football-data.co.uk (auto-downloaded).
- Curated: `data/reference/stadiums.csv` — 48 clubs, city-level coords + annual mean temp
  (committed).
- If a raw schema drifts, fix the mapping in code, **never** edit downloaded data:
  - Column renames → `COLUMN_MAP` in `ingest.py`.
  - Team-name spelling mismatches → `TEAM_ALIASES` in `geo.py` (a test enumerates any
    unmapped name).

## Future steps

Each chapter is independent and gets its own spec → plan → implementation cycle. Start a new
session, brainstorm the chapter into a spec, then execute.

- **Chapter B — cross-league unpredictability.** How competitively balanced is the
  Brasileirão vs the Premier League / La Liga: outcome entropy, model calibration,
  title/relegation-race volatility. Reuses `analysis.py`, `model.py`, and the football-data.co.uk
  loader already written for the Chapter A teaser.
- **Chapter C — the mid-season exodus.** Brazil's transfer windows don't align with Europe's;
  stars are sold mid-season. Does the misalignment cause a measurable dip for clubs left
  behind? Riskiest data problem (needs Transfermarkt scraping) — deliberately last.

A ready-to-paste kickoff prompt lives in
`docs/superpowers/next-session-chapter-bc-prompt.md`.

## Lessons Learned (newest first)

Hard-won during Chapter A. Append new entries at the top before ending any turn with a
substantive correction.

- **Always compare a model against a no-feature naive baseline before reporting any result,
  null or positive.** The first model chapter reported an honest "quirks don't beat Elo" null —
  but neither model had been checked against predicting the historical H/D/A base rates.
  Measured properly, the broken models were *worse* than that class-prior floor: Elo-only log
  loss 1.1046 and full model 1.1214 both above the floor of 1.0514, and the Elo-only model was
  even worse than uniform 1/3 guessing (1.0986). They were badly overfit (300 trees, 3–8
  features, ~380 matches/season). The fix — class-prior reference line + early stopping +
  reduced capacity, chosen once and applied identically to both models — brought Elo-only to
  1.0303 and the full model to 1.0318, both now clearing the 1.0514 floor. A null from a model
  that can't beat base rates is a defect, not a finding.
- **Never `p`-tune toward a desired result on a test set.** When fixing the overfit model,
  the discipline was: fix the *specification* (a model that loses to base rates is
  mis-specified), pick regularization on principled grounds, apply it to baseline and full
  model identically, then report whatever the quirk comparison gives and stop. "Correctly
  specified and clears the naive floor" is the success condition, not "the quirks win."
- **Check join keys for uniqueness before merging.** `rest_days` originally joined on
  `(date, team)`, which is *not* unique in the data (a few dates list a team in two matches).
  The many-to-many merge inflated 8,785 rows to 8,870 and silently misaligned 48% of values —
  and it slipped past both the row-count and null checks, because assigning an oversized
  Series back to a DataFrame column aligns by index label and quietly truncates. Fix: a
  single causal forward pass (one row in, one row out by construction), verified against an
  independent reference. Row-count/null checks are necessary but not sufficient; verify values
  against an independent computation.
- **League seasons that cross the calendar year need explicit boundary handling.** The season
  rule "Jan–Mar belongs to the previous season" (correct for the COVID-delayed 2020 season
  ending Feb 2021) mis-assigned the 2003 opening round (played 29–30 March) to a nonexistent
  "2002" season, and the `season >= 2003` filter then silently dropped 12 real matches. Fix:
  clamp the season floor to the first real season, with a regression test using a
  March-opening fixture.
- **Season-level aggregates are too noisy to prove a mechanism; use a targeted window.** The
  tempting "empty COVID stadiums killed home advantage" story fails at the season level —
  2020 is only the 3rd-lowest season (2017 and 2022, both full-crowd, are lower). The crowd
  effect only holds up when you compare the closed-door *window* (Aug 2020–Sep 2021) against
  control seasons, not whole calendar seasons. Match the comparison window to the intervention
  window.
- **Report null and non-monotonic results honestly, and retitle figures to match.** Travel is
  not a smooth dose-response (penalty only beyond 2,200 km) and heat shows no effect — both
  contrary to the pre-registered hypothesis. Figure titles that assert a trend ("the farther
  you fly, the fewer points you take") were changed to describe what the data shows. A chart
  whose title contradicts its own error bars is the worst outcome; an honest null is a
  strength in a portfolio piece.
- **Name the proxy's limitation when a feature is a proxy.** `temp_gap` uses each city's
  *annual mean* temperature, not match-day weather, so the heat null rules out a large effect
  but can't rule out a small one. State this explicitly rather than concluding "heat doesn't
  matter."
- **Windows console mojibake (`Maracan�`, `400�1200`) is almost always a cp1252 display
  artifact, not real data corruption.** This raised false alarms repeatedly. Verify by reading
  the actual file bytes / Python string codepoints (`\xc3\xa3` = valid UTF-8 "ã") before
  spending any effort "fixing" it. The parquet/notebook files were always correct UTF-8.
- **Verify claims against the data rather than trusting the plan's own code.** Several of the
  above were latent bugs in the written implementation plan, caught only by running independent
  checks on the real 8,785-match dataset after each task, not by reading the code.
