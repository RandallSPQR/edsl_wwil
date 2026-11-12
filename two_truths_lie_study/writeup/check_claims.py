"""Check the write-up package against its sources. Must pass before delivery.

  python check_claims.py            (prints a report; exit code 0 only if every check passes)

Checks, re-reading every source from disk (value lookup is re-implemented here, not imported from claims.py):
  1. Manifest: each row's source file exists and its sha256 matches; the JSON pointer / expression / registration
     quote is resolved again and the displayed value agrees with it within its display rounding.
  2. Sentences: each row's sentence is a line of its text file, with the claim value at its recorded offset.
  3. Coverage: every number in METHODS.md, FINDINGS.md and FIGURES.md is a claim value or an identifier on the
     whitelist below (names, section/addendum numbers, CI descriptors, code in backticks). Spelled-out numbers are
     listed for review.
  4. Reproducibility: the texts are byte-identical to a fresh render by build.py, and derived/levels.json is
     identical (within 1e-12) to a fresh derivation from the committed records by derive_levels.py.
  5. Figures: every figure file named in FIGURES.md exists.
"""
import csv, hashlib, json, math, re, sys
from pathlib import Path

from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TEXTS = ["METHODS.md", "FINDINGS.md", "FIGURES.md"]
FAIL = []


def fail(msg):
    FAIL.append(msg)


# ------------------------------------------------------------------ independent lookup

def resolve(obj, pointer):
    for raw in pointer.lstrip("/").split("/"):
        k = raw.replace("~1", "/").replace("~0", "~")
        obj = obj[int(k)] if isinstance(obj, list) else obj[k]
    return obj


F = {"lb95_onesided": lambda est, se, df: est - stats.t.ppf(0.95, df) * se,
     "diff": lambda a, b: a - b, "ratio_pct": lambda a, b: 100 * a / b,
     "count_true": lambda xs: sum(1 for x in xs if x), "count": lambda xs: len(xs),
     "count_not_none": lambda xs: sum(1 for x in xs if x is not None),
     "count_fallback": lambda xs: sum(1 for x in xs if "fallback" in str(x)),
     "minimum": lambda xs: min(xs), "maximum": lambda xs: max(xs), "minimum_pct": lambda xs: 100 * min(xs),
     "maximum_pct": lambda xs: 100 * max(xs), "total": lambda xs: sum(xs)}


def evaluate(path, src_text, src_json):
    """Return (kind, value) for a manifest path."""
    if path.startswith("text: "):
        return "text", path[len('text: "'):-1]
    if path.startswith("expr: "):
        m = re.fullmatch(r"expr: (\w+)\((.*)\)", path)
        args = {}
        for part in re.findall(r"(\w+)=(\[[^\]]*\]|[^,]+)", m.group(2)):
            k, v = part
            v = v.strip()
            args[k] = [resolve(src_json, q.strip()) for q in v[1:-1].split(", ")] if v.startswith("[") else resolve(src_json, v)
        return "num", F[m.group(1)](**args)
    m = re.fullmatch(r"(/.*?)( x(\d+))?", path)
    v = resolve(src_json, m.group(1))
    if m.group(3):
        sc = float(m.group(3))
        v = [x * sc for x in v] if isinstance(v, list) else v * sc
    return "num", v


NUM = re.compile(r"[-+−]?\d[\d,]*(?:\.\d+)?(?:e[-+]\d+)?")


def agrees(display, raw):
    """Does the displayed text represent raw within display rounding?"""
    if isinstance(raw, bool) or raw is None:
        return display == {True: "yes", False: "no", None: "none"}[raw] or display == str(raw)
    if isinstance(raw, str):
        return display == raw
    if display.startswith("< "):
        return raw < float(display[2:])
    nums = [t.replace(",", "").replace("−", "-") for t in NUM.findall(display)]
    raws = raw if isinstance(raw, list) else [raw]
    if len(nums) != len(raws):
        return False
    for t, r in zip(nums, raws):
        x = float(t)
        if "e" in t:
            if not math.isclose(x, r, rel_tol=0.06):
                return False
            continue
        dec = len(t.split(".")[1]) if "." in t else 0
        tol = 0.5 * 10 ** -dec + 1e-12
        if abs(x - r) > tol:
            return False
    return True


# ------------------------------------------------------------------ 1-2: manifest

def check_manifest():
    rows = list(csv.DictReader(open(HERE / "CLAIMS_MANIFEST.csv", newline="")))
    texts = {t: (HERE / t).read_text() for t in TEXTS}
    cache = {}
    for r in rows:
        p = ROOT / r["source_file"]
        if not p.exists():
            fail(f"{r['claim_id']}: source missing {r['source_file']}"); continue
        if r["source_file"] not in cache:
            b = p.read_bytes()
            cache[r["source_file"]] = (hashlib.sha256(b).hexdigest(), b.decode(),
                                       json.loads(b) if p.suffix == ".json" else None)
        sha, txt, js = cache[r["source_file"]]
        if sha != r["file_sha256"]:
            fail(f"{r['claim_id']}: sha256 mismatch for {r['source_file']}")
        try:
            kind, v = evaluate(r["json_path"], txt, js)
        except Exception as e:
            fail(f"{r['claim_id']}: cannot resolve {r['json_path']}: {e!r}"); continue
        if kind == "text":
            if v not in txt:
                fail(f"{r['claim_id']}: quote not in {r['source_file']}")
            elif r["value"] not in v:
                fail(f"{r['claim_id']}: value {r['value']!r} not in its quote")
        elif not agrees(r["value"], v):
            fail(f"{r['claim_id']}: displayed {r['value']!r} disagrees with source value {v!r}")
        if r["label"] not in ("registered primary", "registered secondary", "post hoc (descriptive)", "exploratory",
                              "design constant (registration)"):
            fail(f"{r['claim_id']}: unknown label {r['label']!r}")
        if r["sentence"] not in texts[r["text_file"]].split("\n"):
            fail(f"{r['claim_id']}: sentence is not a line of {r['text_file']}")
        o = int(r["offset_in_sentence"])
        if r["sentence"][o:o + len(r["value"])] != r["value"]:
            fail(f"{r['claim_id']}: value is not at its recorded offset in the sentence")
    return rows, texts


# ------------------------------------------------------------------ 3: coverage

MODEL_NAMES = ["Llama 3.1 8B Instruct", "Gemma 3 27B IT", "Llama 3.1 8B", "Gemma 3 27B", "gpt-4o-mini",
               "Gemini 2.5 Flash-Lite", "gemini-2.5-flash", "Claude Sonnet 4.5", "gpt-5"]
WHITELIST = [
    r"`[^`]*`",                                                         # code, paths, hashes, formulas
    r"\bAddend(?:um|a) \d+(?:-\d+)?(?: and \d+)?", r"\blog items? \d+(?:-\d+)?",
    r"\bsections? \d+[a-z]?(?:-\d+[a-z]?)?(?:, \d+[a-z]?)*", r"\b[Ff]igure \d\b",
    r"\b[Ss]tudy [12]\b", r"\bPhase 2\b", r"\b[Ss]tage[ -][12]\b", r"\brevision \d\b", r"\banalysis \d+\b",
    r"\bsha256\b", r"\bH[12]\b", r"\bP[1-6]\b",
    r"\bv0\.6\b", r"\bbf16\b", r"\b4-gram\b", r"\b(?:95|90)%", r"\bK − 1\b", r"\bs = 0\b",
    r"^\s*- [1-8]: ",                                                   # the Addenda list
    r"^\*\*Figure \d\*\*",
]


def check_coverage(rows, texts):
    spelled = {}
    by_line = {}
    for r in rows:
        by_line.setdefault((r["text_file"], r["sentence"]), []).append((int(r["offset_in_sentence"]), r["value"]))
    for name, txt in texts.items():
        for line in txt.split("\n"):
            covered = [False] * len(line)
            for i, v in by_line.get((name, line), []):
                for k in range(i, i + len(v)):
                    covered[k] = True
            masked = line
            for mname in MODEL_NAMES:
                for mm in re.finditer(re.escape(mname), masked):
                    for k in range(mm.start(), mm.end()):
                        covered[k] = True
            for pat in WHITELIST:
                for mm in re.finditer(pat, line):
                    for k in range(mm.start(), mm.end()):
                        covered[k] = True
            for mm in re.finditer(r"\d+(?:[.,]\d+)*", line):
                if not all(covered[mm.start():mm.end()]):
                    fail(f"{name}: number {mm.group()!r} is neither a claim nor whitelisted: …{line[max(0, mm.start() - 50):mm.end() + 30]}…")
            for mm in re.finditer(r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\b", line, re.I):
                k = mm.group(1).lower()
                spelled[k] = spelled.get(k, 0) + 1
    return spelled


# ------------------------------------------------------------------ 4-5: reproducibility, figures

def close(a, b):
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(close(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))
    if isinstance(a, float):
        return isinstance(b, (int, float)) and abs(a - b) <= 1e-12
    return a == b


def check_rebuild():
    sys.path.insert(0, str(HERE))
    import derive_levels
    fresh = json.loads(json.dumps(derive_levels.derive(), sort_keys=True))
    if not close(json.loads((HERE / "derived/levels.json").read_text()), fresh):
        fail("derived/levels.json differs from a fresh derivation")
    import build
    from claims import strip_markers
    for name, fn in (("METHODS.md", build.methods), ("FINDINGS.md", build.findings), ("FIGURES.md", build.captions)):
        build.C.__init__()
        clean, _ = strip_markers("\n".join(fn()) + "\n")
        if clean != (HERE / name).read_text():
            fail(f"{name} differs from a fresh render by build.py")
    for f in re.findall(r"`(figures/[^`]+\.png)`", (HERE / "FIGURES.md").read_text()):
        if not (HERE / f).exists():
            fail(f"figure missing: {f}")


def main():
    rows, texts = check_manifest()
    spelled = check_coverage(rows, texts)
    check_rebuild()
    srcs = sorted({(r["source_file"], r["file_sha256"]) for r in rows})
    labels = {}
    for r in rows:
        labels[r["label"]] = labels.get(r["label"], 0) + 1
    print(f"claims checked: {len(rows)}")
    print("by label: " + "; ".join(f"{k} {v}" for k, v in sorted(labels.items())))
    print(f"sources ({len(srcs)}), sha256 verified:")
    for s, h in srcs:
        print(f"  {h}  {s}")
    print("spelled-out numbers in the texts (structural counts, for review): "
          + ", ".join(f"{k} x{v}" for k, v in sorted(spelled.items())))
    print("levels.json re-derived from the committed records; texts re-rendered by build.py")
    if FAIL:
        print(f"\nFAIL: {len(FAIL)} problem(s)")
        for f in FAIL:
            print("  - " + f)
        sys.exit(1)
    print("\nPASS: every manifest value matches its source, every number in the texts is a claim or a whitelisted "
          "identifier, and the texts and levels reproduce.")


if __name__ == "__main__":
    main()
