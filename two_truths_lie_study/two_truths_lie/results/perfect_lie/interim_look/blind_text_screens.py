"""Condition-blind inspection of the confession and refusal screens (review findings F3, F4).

For every complete interim lie, lists each sentence in which the confession screen or the refusal
pattern matches. Output carries no cell id, model, condition, persona, prompt or replicate, and the
order is shuffled. Counts are totals only. Nothing about scores or lift is read.
"""
import json, random, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie import scoring as sc

RUN = ROOT / "results/perfect_lie/full_interim_r01-15"
last = {}
for line in (RUN / "records.jsonl").read_text().splitlines():
    if line.strip():
        r = json.loads(line); last[r["cell_id"]] = r
lies = [r["lie"] for r in last.values() if r.get("status") == "complete" and r.get("lie")]

def sentence_at(text, i, j):
    a = max(text.rfind(". ", 0, i), text.rfind("! ", 0, i), text.rfind("? ", 0, i), text.rfind("\n", 0, i))
    b = min([k for k in (text.find(". ", j), text.find("! ", j), text.find("? ", j), text.find("\n", j)) if k != -1] or [len(text)])
    return " ".join(text[a + 1:b + 1].split())

conf, refu = [], []
n_conf_lies = n_ref_lies = 0
for t in lies:
    hit = sc.confession(t)
    if hit:
        n_conf_lies += 1
        m = re.search(re.escape(hit), t, flags=re.IGNORECASE)
        conf.append({"matched": hit, "sentence": sentence_at(t, m.start(), m.end()) if m else ""})
    ms = list(sc.REFUSAL_PATTERNS.finditer(t))
    if ms:
        n_ref_lies += 1
        for m in ms:
            refu.append({"matched": m.group(0), "sentence": sentence_at(t, m.start(), m.end())})
rng = random.Random(20261008)
rng.shuffle(conf); rng.shuffle(refu)
out = {"complete_lies": len(lies), "lies_flagged_as_confession": n_conf_lies, "lies_matching_refusal_pattern": n_ref_lies,
       "confession_matches": conf, "refusal_matches": refu,
       "note": "no ids, models, conditions or other labels; order shuffled"}
(HERE / "blind_text_screens.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
L = ["# Confession and refusal screen matches (condition-blind, shuffled)", "",
     f"Complete interim lies: {len(lies)}. Flagged as confession: {n_conf_lies}. Matching the refusal pattern: {n_ref_lies}.", "",
     "## Confession screen", ""] + [f"{i+1}. **{x['matched']}**: {x['sentence']}" for i, x in enumerate(conf)] + \
    ["", "## Refusal pattern", ""] + [f"{i+1}. **{x['matched']}**: {x['sentence']}" for i, x in enumerate(refu)]
(HERE / "blind_text_screens.md").write_text("\n".join(L) + "\n")
print(f"complete lies {len(lies)}; confession {n_conf_lies}; refusal-pattern lies {n_ref_lies}; refusal matches {len(refu)}")
