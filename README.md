# Data Football — Brasileirão Study

A data-science anthology on Brazil's Campeonato Brasileiro Série A (the
"Brasileirão"), built to demonstrate ML rigor and honest storytelling: each
chapter reports what the data actually shows — including its nulls — rather than
what makes a tidy headline. Every chapter is a standalone article with embedded
figures, backed by a reusable package (`src/brasileirao/`) and reproducible
notebooks.

## The chapters

- **[Chapter A — Anatomy of the World's Strongest Home Advantage](docs/chapter-a-home-advantage.md)**
  How big is the Brasileirão's home advantage (points share **0.652**, above La
  Liga and the Premier League), and what actually causes it? Decomposes crowd,
  travel, and heat using a COVID natural experiment and a SHAP-explained outcome
  model. *Verdict: the effects are real in aggregate points share, not in
  per-match prediction — Elo already captures nearly everything forecastable
  about a single match.*

- **[Chapter B — Anyone Beats Anyone? Cross-League Unpredictability](docs/chapter-b-unpredictability.md)**
  How competitively balanced is the Brasileirão against Europe's big five —
  outcome entropy, underdog points share, model and market calibration,
  Noll–Scully standings spread, and title-race volatility? *Verdict: the most
  unpredictable of the six leagues at both the match and the season level.*

- **[Chapter C — The Mid-Season Exodus](docs/chapter-c-exodus.md)**
  Brazil's transfer windows don't align with Europe's, so stars are sold
  mid-campaign. Does losing them cost the clubs left behind? A threshold-free
  dose–response plus a major-sale event study swept across fee thresholds.
  *Verdict: no detectable effect, well-powered — a clean null.*

## Reproduce

Python 3.13 on Windows / PowerShell:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest -q
```

The notebooks in `notebooks/` regenerate every figure in `reports/figures/` from
scratch; see each chapter article for its full narrative and results.
