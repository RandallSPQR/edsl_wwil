"""Write release/tier0/EXPECTED.json: the pinned environment and the sha256 of every released file Tier 0 reads or
rebuilds. Run by the maintainer when the release is cut (after the write-up is built in the pinned environment).

  python release/tier0/make_expected.py
"""
import hashlib, json
from pathlib import Path

REL = Path(__file__).resolve().parents[1]
STUDY = REL.parent
DIRS = ["two_truths_lie/results/perfect_lie/final_analysis", "two_truths_lie/results/perfect_lie/full_interim_r01-15",
        "two_truths_lie/results/perfect_lie/interim_look", "two_truths_lie/results/perfect_lie_reversed/final_analysis",
        "two_truths_lie/results/perfect_lie_reversed/full_run", "two_truths_lie/results/phase2",
        "two_truths_lie/src/perfect_lie", "two_truths_lie/data", "writeup", "release/tier0/inputs"]
TOP = ["PREREG_DRAFT.md", "PREREG_REVERSED.md", "PREREG_PHASE2.md", "PREREG_PHASE2_ADDENDA.md", "PERFECT_LIE.md"]
PINS = {"python": "3.11", "packages": {"numpy": "2.4.6", "pandas": "2.3.3", "patsy": "1.0.3", "scipy": "1.17.1",
                                       "statsmodels": "0.15.0", "matplotlib": "3.11.2"}}


def keep(p):
    if "__pycache__" in p.parts or p.name.startswith("."):
        return False
    if p.suffix == ".jsonl" and p.with_name(p.name + ".gz").exists():
        return False                     # the .gz is the released file; Tier 0 decompresses it
    return p.is_file()


files = {}
for d in DIRS:
    for p in sorted((STUDY / d).rglob("*")):
        if keep(p):
            files[str(p.relative_to(STUDY))] = hashlib.sha256(p.read_bytes()).hexdigest()
for t in TOP:
    files[t] = hashlib.sha256((STUDY / t).read_bytes()).hexdigest()
(REL / "tier0" / "EXPECTED.json").write_text(json.dumps({"environment": PINS, "files": files}, indent=1) + "\n")
print(f"{len(files)} files hashed")
