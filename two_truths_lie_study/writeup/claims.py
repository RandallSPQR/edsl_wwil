"""Claim machinery for the write-up: every number in the text enters through a claim.

A claim reads a value from a source file and formats it:
  json   value at an RFC 6901 JSON Pointer in a JSON source, optionally scaled (x100 for a percentage);
  expr   a value computed from JSON Pointer inputs (a pointer, or a list of pointers) by a named formula (FORMULAS);
  text   a design constant quoted from a registration text (the exact substring is recorded).
The rendered value is wrapped in markers during rendering, so each claim's sentence can be recorded and every number in
the delivered text can be traced to a claim (check_claims.py).
"""
import hashlib, json, math, re
from pathlib import Path

from scipy import stats

ROOT = Path(__file__).resolve().parents[1]           # two_truths_lie_study/

SOURCES = {
    # study 1
    "S1": "two_truths_lie/results/perfect_lie/final_analysis/final_report.json",
    "S1G": "two_truths_lie/results/perfect_lie/final_analysis/gpt5_same_units.json",
    # reversed note
    "RV": "two_truths_lie/results/perfect_lie_reversed/final_analysis/final_report.json",
    "RVPERM": "two_truths_lie/results/perfect_lie_reversed/final_analysis/perm_check.json",
    "RVPC": "two_truths_lie/results/perfect_lie_reversed/final_analysis/posthoc_comprehension_parsed.json",
    "RVG": "two_truths_lie/results/perfect_lie_reversed/final_analysis/posthoc_google_testB.json",
    # phase 2
    "IDC": "two_truths_lie/results/phase2/identity_check/behavioral_result.json",
    "IDN": "two_truths_lie/results/phase2/identity_check/behavioral_result_novita.json",
    "GR": "two_truths_lie/results/phase2/grading_route/regrade_direct.json",
    "PRG": "two_truths_lie/results/phase2/probe/gemma-3-27b-it/probe_result.json",
    "PRL": "two_truths_lie/results/phase2/probe/llama-3.1-8b-instruct/probe_result.json",
    "DGG": "two_truths_lie/results/phase2/probe/gemma-3-27b-it/diagnostics.json",
    "DGL": "two_truths_lie/results/phase2/probe/llama-3.1-8b-instruct/diagnostics.json",
    "PLG": "two_truths_lie/results/phase2/pilot/gemma-3-27b-it/pilot_result.json",
    "PLL": "two_truths_lie/results/phase2/pilot/llama-3.1-8b-instruct/pilot_result.json",
    "P2G": "two_truths_lie/results/phase2/pilot/gemma-3-27b-it/pilot2_result.json",
    "P2L": "two_truths_lie/results/phase2/pilot/llama-3.1-8b-instruct/pilot2_result.json",
    "CA": "two_truths_lie/results/phase2/pilot/confirmatory_alphas.json",
    "SPG": "two_truths_lie/results/phase2/pilot/gemma-3-27b-it/setup_placebo2.json",
    "SPL": "two_truths_lie/results/phase2/pilot/llama-3.1-8b-instruct/setup_placebo2.json",
    "SU1G": "two_truths_lie/results/phase2/pilot/gemma-3-27b-it/setup.json",
    "SU1L": "two_truths_lie/results/phase2/pilot/llama-3.1-8b-instruct/setup.json",
    "MCG": "two_truths_lie/results/phase2/pilot/gemma-3-27b-it/mc_precheck.json",
    "MCL": "two_truths_lie/results/phase2/pilot/llama-3.1-8b-instruct/mc_precheck.json",
    "ST": "two_truths_lie/results/phase2/stage2/stage2_result.json",
    "COG": "two_truths_lie/results/phase2/stage2/gemma-3-27b-it/coherence.json",
    "COL": "two_truths_lie/results/phase2/stage2/llama-3.1-8b-instruct/coherence.json",
    "GSG": "two_truths_lie/results/phase2/stage2/gemma-3-27b-it/grading_summary.json",
    "GSL": "two_truths_lie/results/phase2/stage2/llama-3.1-8b-instruct/grading_summary.json",
    "PC2": "two_truths_lie/results/phase2/stage2/permutation_check.json",
    # descriptive levels for figures 2 and 3 (derive_levels.py)
    "LV": "writeup/derived/levels.json",
    # registration texts (design constants only)
    "R1": "PREREG_DRAFT.md",
    "R2": "PREREG_REVERSED.md",
    "R3": "PREREG_PHASE2.md",
    "R3A": "PREREG_PHASE2_ADDENDA.md",
}

GEMMA, LLAMA = "google/gemma-3-27b-it", "meta-llama/llama-3.1-8b-instruct"
GPT, GEMINI = "openai/gpt-4o-mini", "google/gemini-2.5-flash-lite"
MODELS4 = [LLAMA, GEMMA, GPT, GEMINI]                  # one order everywhere
MODELS2 = [LLAMA, GEMMA]
NAME = {LLAMA: "Llama 3.1 8B", GEMMA: "Gemma 3 27B", GPT: "gpt-4o-mini", GEMINI: "Gemini 2.5 Flash-Lite"}
SLUG = {GEMMA: "gemma-3-27b-it", LLAMA: "llama-3.1-8b-instruct"}

# labels (match the registrations and addenda)
REG_P = "registered primary"
REG_S = "registered secondary"
POSTHOC = "post hoc (descriptive)"
EXPL = "exploratory"
DESIGN = "design constant (registration)"


def sha256(alias):
    return hashlib.sha256((ROOT / SOURCES[alias]).read_bytes()).hexdigest()


_cache = {}


def load(alias):
    if alias not in _cache:
        p = ROOT / SOURCES[alias]
        _cache[alias] = p.read_text() if p.suffix == ".md" else json.loads(p.read_text())
    return _cache[alias]


def esc(key):
    return str(key).replace("~", "~0").replace("/", "~1")


def ptr(*parts):
    return "/" + "/".join(esc(p) for p in parts)


def resolve(obj, pointer):
    if pointer in ("", "/"):
        return obj
    for raw in pointer.lstrip("/").split("/"):
        k = raw.replace("~1", "/").replace("~0", "~")
        obj = obj[int(k)] if isinstance(obj, list) else obj[k]
    return obj


# formulas usable in expr claims (the checker has the same table)
FORMULAS = {
    "lb95_onesided": lambda est, se, df: est - stats.t.ppf(0.95, df) * se,
    "diff": lambda a, b: a - b,
    "ratio_pct": lambda a, b: 100 * a / b,
    "count_true": lambda xs: sum(1 for x in xs if x),
    "count": lambda xs: len(xs),
    "count_not_none": lambda xs: sum(1 for x in xs if x is not None),
    "count_fallback": lambda xs: sum(1 for x in xs if "fallback" in str(x)),
    "minimum": lambda xs: min(xs),
    "minimum_pct": lambda xs: 100 * min(xs),
    "maximum_pct": lambda xs: 100 * max(xs),
    "maximum": lambda xs: max(xs),
    "total": lambda xs: sum(xs),
}


# ---------------------------------------------------------------- formatting

def f_signed(x, d=3):
    return f"{x:+.{d}f}"


def f_plain(x, d=3):
    return f"{x:.{d}f}"


def f_ci(xs, d=3, signed=True):
    g = f_signed if signed else f_plain
    return f"[{g(xs[0], d)}, {g(xs[1], d)}]"


def f_int(x):
    return f"{int(round(x)):,}"


def f_p(x):
    if x < 0.001:
        return "< 0.001"
    s = f"{x:#.2g}"
    return s if "e" not in s else f"{x:.4f}"


def f_alpha(x):
    return f"{x:.3g}"


def f_pct(x, d=0):
    return f"{x:.{d}f}%"


FMT = {
    "s3": lambda x: f_signed(x, 3), "s2": lambda x: f_signed(x, 2), "s4": lambda x: f_signed(x, 4),
    "f4": lambda x: f_plain(x, 4), "f3": lambda x: f_plain(x, 3), "f2": lambda x: f_plain(x, 2), "f1": lambda x: f_plain(x, 1),
    "f0": lambda x: f_plain(x, 0),
    "ci3s": lambda x: f_ci(x, 3, True), "ci2s": lambda x: f_ci(x, 2, True), "ci3": lambda x: f_ci(x, 3, False),
    "ci2": lambda x: f_ci(x, 2, False),
    "int": f_int, "p": f_p, "alpha": f_alpha, "pct": lambda x: f_pct(x, 0), "pct1": lambda x: f_pct(x, 1),
    "str": lambda x: str(x), "e1": lambda x: f"{x:.1e}",
    "yn": lambda x: {True: "yes", False: "no", None: "none"}[x],
}


class Claims:
    def __init__(self):
        self.items = []
        self.ids = set()

    def _add(self, cid, alias, path, value, text, label):
        if cid in self.ids:
            raise ValueError(f"duplicate claim id {cid}")
        self.ids.add(cid)
        self.items.append({"id": cid, "alias": alias, "path": path, "raw": value, "value": text, "label": label})
        return f"⟦{cid}⟧{text}⟦/⟧"

    def json(self, cid, alias, pointer, fmt, label, scale=None):
        v = resolve(load(alias), pointer)
        x = [y * scale for y in v] if (scale and isinstance(v, list)) else (v * scale if scale else v)
        path = pointer + (f" x{scale:g}" if scale else "")
        return self._add(cid, alias, path, v, FMT[fmt](x), label)

    def expr(self, cid, alias, formula, inputs, fmt, label):
        vals = {k: [resolve(load(alias), q) for q in p] if isinstance(p, list) else resolve(load(alias), p)
                for k, p in inputs.items()}
        x = FORMULAS[formula](**vals)
        path = f"expr: {formula}(" + ", ".join(f"{k}={'[' + ', '.join(p) + ']' if isinstance(p, list) else p}"
                                               for k, p in inputs.items()) + ")"
        return self._add(cid, alias, path, x, FMT[fmt](x), label)

    def text(self, cid, alias, quote, value, label=DESIGN):
        body = load(alias)
        if quote not in body:
            raise ValueError(f"{cid}: quote not in {SOURCES[alias]}: {quote!r}")
        if value not in quote:
            raise ValueError(f"{cid}: value {value!r} not in quote")
        return self._add(cid, alias, f'text: "{quote}"', value, value, label)


MARK = re.compile("⟦([^⟧]+)⟧(.*?)⟦/⟧")


def strip_markers(text):
    """Remove markers; return clean text and the spans (start, end, claim id) of each claim value."""
    out, spans, pos = [], [], 0
    clean_len = 0
    for m in MARK.finditer(text):
        before = text[pos:m.start()]
        out.append(before); clean_len += len(before)
        spans.append((clean_len, clean_len + len(m.group(2)), m.group(1)))
        out.append(m.group(2)); clean_len += len(m.group(2))
        pos = m.end()
    out.append(text[pos:])
    return "".join(out), spans
