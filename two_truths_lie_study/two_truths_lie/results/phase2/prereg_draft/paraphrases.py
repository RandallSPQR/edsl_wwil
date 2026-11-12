"""Phase 2 (draft): three paraphrase sets of the reversed-note study's valence words, for the probe's
held-out-wording test. Each set replaces ONLY the words that differ between a frozen full line and its
frozen reversed line (the valence spans, found with the frozen lint); everything else, including every
cue word, is unchanged. Lint, per line and set: with the valence spans masked, the frozen full, frozen reversed, paraphrased
full and paraphrased reversed token sequences are identical (so every cue word and every other word
is unchanged); each replaced span is one of the set's listed pairs; no new valence word shares a stem
with a cue's name; and the paraphrase actually differs from the frozen wording.
Writes paraphrase_sets.json and paraphrase_lint.md.
"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from src.perfect_lie import reversed as rv
from src.perfect_lie.personas import load_instrument

# (frozen full span, frozen reversed span) -> (paraphrase full, paraphrase reversed), per set
SETS = {
    "A": {("credible", "suspect"): ("convincing", "doubtful"), ("more", "less"): ("much more", "much less"),
          ("most", "least"): ("above all", "least of all"), ("Trusts", "Distrusts"): ("Has faith in", "Has no faith in"),
          ("Believes", "Doubts"): ("Accepts", "Questions"), ("convinced", "unconvinced"): ("persuaded", "unpersuaded"),
          ("reassured", "suspicious"): ("put at ease", "put on guard"), ("Warms to", "Distrusts"): ("Is drawn to", "Is put off by"),
          ("nothing", "something"): ("nothing whatsoever", "something"), ("invented", "genuine"): ("made up", "authentic")},
    "B": {("credible", "suspect"): ("believable", "dubious"), ("more", "less"): ("all the more", "all the less"),
          ("most", "least"): ("especially", "hardly at all"), ("Trusts", "Distrusts"): ("Relies on", "Is wary of"),
          ("Believes", "Doubts"): ("Gives credit to", "Discounts"), ("convinced", "unconvinced"): ("won over", "left cold"),
          ("reassured", "suspicious"): ("comforted", "alarmed"), ("Warms to", "Distrusts"): ("Likes", "Dislikes"),
          ("nothing", "something"): ("nothing", "a great deal"), ("invented", "genuine"): ("fabricated", "true")},
    "C": {("credible", "suspect"): ("plausible", "questionable"), ("more", "less"): ("far more", "far less"),
          ("most", "least"): ("most of all", "not at all"), ("Trusts", "Distrusts"): ("Credits", "Discredits"),
          ("Believes", "Doubts"): ("Is persuaded by", "Has misgivings about"), ("convinced", "unconvinced"): ("impressed", "unimpressed"),
          ("reassured", "suspicious"): ("relieved", "wary"), ("Warms to", "Distrusts"): ("Takes to", "Is cold toward"),
          ("nothing", "something"): ("no secret", "a secret"), ("invented", "genuine"): ("contrived", "honest")},
}


def segments(full, rev):
    """Frozen full vs frozen reversed: [("eq", tokens) | ("span", full_span, rev_span)], left to right."""
    import difflib
    a, b = rv._tok(full), rv._tok(rev)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        out.append(("eq", a[i1:i2]) if op == "equal" else ("span", " ".join(a[i1:i2]), " ".join(b[j1:j2])))
    return out


def detok(t):
    return "".join((" " if i and (w[0].isalnum() or w[0] == "'") else "") + w for i, w in enumerate(t))


def paraphrase(full, rev, mapping):
    """Replace each valence span with the set's wording; every other token is copied unchanged."""
    fa, fb, used = [], [], []
    for seg in segments(full, rev):
        if seg[0] == "eq":
            fa += seg[1]; fb += seg[1]
        else:
            nf, nr = mapping[(seg[1], seg[2])]
            fa += rv._tok(nf); fb += rv._tok(nr); used.append((seg[1], seg[2]))
    return detok(fa), detok(fb), used


def masked(text, spans):
    """Token sequence with each listed span (in order) replaced by a placeholder."""
    t, out, k = rv._tok(text), [], 0
    i = 0
    while i < len(t):
        if k < len(spans):
            sp = rv._tok(spans[k])
            if t[i:i + len(sp)] == sp:
                out.append("<V>"); i += len(sp); k += 1; continue
        out.append(t[i]); i += 1
    return out, k == len(spans)


CUE_STEMS = None


def cue_overlap(words, inst):
    """Words of a new valence span that share a stem (first 5 letters, length >= 5) with a word of any cue's name
    (e.g. document, citation, witness, humor, expert, quotation): a new valence word must not name a cue."""
    global CUE_STEMS
    if CUE_STEMS is None:
        import re
        CUE_STEMS = {w.lower()[:5] for c in inst.cues for w in re.split(r"_", c.id) if len(w) >= 5}
    return [w for w in rv._tok(words) if len(w) >= 5 and w.lower()[:5] in CUE_STEMS]


def main():
    inst = load_instrument(); rn = rv.load_reversed(); design = rv.load_design()
    lines = [("header", None, rn["header"]["full"].strip("\n").split("\n")[-1], rn["header"]["reversed"].strip("\n").split("\n")[-1])]
    for pid in design["targets"]:
        for b in inst.personas[pid].beliefs:
            lines.append((pid, b.cue, b.text, rn["reversed"][pid][b.cue]))
    out, report, ok_all = {"frozen_commit_note": "frozen wording: reversed_notes.json and personas.json (PREREG_REVERSED.md)", "sets": {}}, [], True
    for name, mapping in SETS.items():
        rows = []
        for pid, cue, full, rev in lines:
            pf, pr, used = paraphrase(full, rev, mapping)
            new_f, new_r = [mapping[u][0] for u in used], [mapping[u][1] for u in used]
            m_full, ok1 = masked(full, [u[0] for u in used]); m_pf, ok2 = masked(pf, new_f)
            m_rev, ok3 = masked(rev, [u[1] for u in used]); m_pr, ok4 = masked(pr, new_r)
            same = ok1 and ok2 and ok3 and ok4 and m_full == m_pf == m_rev == m_pr
            overlap = sorted({w for x in new_f + new_r for w in cue_overlap(x, inst)})
            ok = same and not overlap and pf != full and pr != rev
            ok_all &= ok
            rows.append({"persona": pid, "cue": cue, "full": pf, "reversed": pr, "lint_ok": ok})
            if not ok:
                report.append(f"- set {name}, {pid} {cue}: masked-identical={same} cue-overlap={overlap}")
        out["sets"][name] = {"pairs": [[*k, *v] for k, v in mapping.items()], "lines": rows}
    out["lint_all_ok"] = ok_all
    (HERE / "paraphrase_sets.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    md = ["# Paraphrase sets: lint", "", f"All lines pass: **{ok_all}**", ""] + (report or ["No violations."])
    for name, s in out["sets"].items():
        md += ["", f"## Set {name}", "", "| persona | cue | full | reversed |", "|---|---|---|---|"]
        md += [f"| {r['persona']} | {r['cue'] or '(header)'} | {r['full']} | {r['reversed']} |" for r in s["lines"]]
    (HERE / "paraphrase_lint.md").write_text("\n".join(md) + "\n")
    print("lint all ok:", ok_all); print("\n".join(report[:10]))


if __name__ == "__main__":
    main()
