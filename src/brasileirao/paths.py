from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
RAW = DATA / "raw"
REFERENCE = DATA / "reference"
PROCESSED = DATA / "processed"
FIGURES = ROOT / "reports" / "figures"

for _p in (RAW, REFERENCE, PROCESSED, FIGURES):
    _p.mkdir(parents=True, exist_ok=True)
