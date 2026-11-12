"""Lint every reversed note against its full twin and write the pairs for owner review.
No model calls. Run: python results/perfect_lie_reversed/lint/lint_reversed.py"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie.personas import load_instrument
from src.perfect_lie import reversed as rv

inst = load_instrument()
res = rv.lint_all(inst.personas)
(HERE / "lint_reversed.json").write_text(json.dumps(res, indent=1) + "\n")
scorable_heat = {c.id for c in inst.cues if c.heatmap_only}
L = ["# Reversed-note pairs and lint (follow-up study, draft)", "",
     f"**Lint: {'PASS' if res['ok'] else 'FAIL'}.** A pair passes when every word that differs is one of the listed "
     "valence substitutions and nothing else differs (word-level diff). Full beliefs are the frozen "
     "`data/perfect_lie/personas.json`, unchanged.", "",
     "Allowed substitutions (full -> reversed): " + "; ".join(f"`{a}` -> `{b}`" for a, b in rv.load_reversed()["valence_pairs"]) + ".", "",
     "## Header", "", f"- full: `{res['header'] and rv.load_reversed()['header']['full'].strip().splitlines()[-1]}`",
     f"- reversed: `{rv.load_reversed()['header']['reversed'].strip().splitlines()[-1]}`",
     f"- edits: {res['header']['edits']}; lint {'pass' if res['header']['ok'] else 'FAIL'}", "",
     "## Beliefs (20 pairs)", "",
     "| persona | cue | full | reversed | words (full / rev) | edits | lint |", "|---|---|---|---|---|---|---|"]
for b in res["beliefs"]:
    cue = b["cue"] + (" (heatmap only)" if b["cue"] in scorable_heat else "")
    L.append(f"| {b['persona']} | {cue} | {b['full']} | {b['reversed']} | {b['words_full']} / {b['words_reversed']} | "
             + "; ".join(f"{x} -> {y}" for x, y in b["edits"]) + f" | {'pass' if b['ok'] else 'FAIL ' + str(b['violations'])} |")
L += ["", "## The three notes per target, exactly as the liar receives them (after the frozen scaffold)", "",
      "Each target's three notes carry the same filler sentences, so they differ only in the header word and the belief lines.", ""]
for pid, n in res["notes"].items():
    L += [f"### Target {pid} (placebo persona {n['placebo_persona']}); words: " +
          ", ".join(f"{k} {v}" for k, v in n["words"].items()), ""]
    for cond in ("full", "reversed", "placebo"):
        L += [f"**{cond}**", "", "```", n["text"][cond].strip(), "```", ""]
(HERE / "reversed_pairs.md").write_text("\n".join(L) + "\n")
print("lint", "PASS" if res["ok"] else "FAIL")
