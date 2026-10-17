"""Build the self-contained review package for the reversed follow-up's final analysis (third review:
the ZIP must run from a clean extract, without a repository checkout).

    python two_truths_lie_study/two_truths_lie/results/perfect_lie_reversed/final_analysis/build_review_package.py OUT.zip [EXTRA_FILE ...]

Run from the repository root. Packs, from the committed tree (git ls-files, so nothing untracked):
the EDSL source and its pyproject.toml, the study's src/, tests/, data/, top-level scripts and
configuration, the study brief and both registrations, and the reversed follow-up's design and
final-analysis folders. No run records (results/*/full_run, records.jsonl*) are included.
"""

import subprocess
import sys
import zipfile
from pathlib import Path

S = "two_truths_lie_study"
T = f"{S}/two_truths_lie"
INCLUDE = ["edsl", "pyproject.toml", f"{S}/PERFECT_LIE.md", f"{S}/PREREG.md", f"{S}/PREREG_REVERSED.md",
           f"{T}/src", f"{T}/tests", f"{T}/data", f"{T}/pytest.ini",
           f"{T}/results/perfect_lie_reversed/design", f"{T}/results/perfect_lie_reversed/final_analysis"]
TOP_LEVEL = (".py", ".ini", ".toml", ".cfg", ".txt", ".md")


def files() -> list:
    out = subprocess.run(["git", "ls-files", "--", *INCLUDE], capture_output=True, text=True, check=True).stdout.split()
    top = subprocess.run(["git", "ls-files", "--", T], capture_output=True, text=True, check=True).stdout.split()
    out += [f for f in top if f.count("/") == 2 and f.endswith(TOP_LEVEL)]   # top-level scripts and config
    bad = [f for f in out if "full_run" in f or "records.jsonl" in f]
    if bad:
        raise SystemExit(f"run records would be packed: {bad[:3]}")
    return sorted(set(out))


def main(dest: str, *extra: str) -> None:
    fs = files()
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for f in fs:
            z.write(f, f)
        for e in extra:
            z.write(e, Path(e).name)
        z.writestr("PACKAGE_COMMIT.txt", head + "\n")
    print(f"{dest}: {len(fs)} files from commit {head}")


if __name__ == "__main__":
    main(*sys.argv[1:])
