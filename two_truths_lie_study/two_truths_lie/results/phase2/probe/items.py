"""Phase 2 probe stage, step 1 (PREREG_PHASE2 sections 3-5; Addendum 1): the category split and the probe items.

  python items.py   -> category_split.json, probe_items.jsonl.gz

Split (section 3): random.Random(20261023).sample(sorted(final_72), 32) are the evaluation categories; the other
40 are the training categories. The probe stage uses the training categories only.

Items, per model, on the training categories x the 5 targets:
  - frozen wording: full, reversed and placebo notes, as the exact messages the model received in the reversed-note
    run (records.jsonl.gz, `liar_delivered_messages`; identical across replicates, checked);
  - paraphrase sets A, B, C (section 5): the same full and reversed messages with the header line and the target's
    four belief lines replaced by the set's lines (each frozen line occurs exactly once, checked). Activations only.
Repair (Addendum 1): the frozen paraphrase lines carry a detokenizer artifact, "well- known" for "well-known" (the
two historical_anchor lines of P1 and P5, all three sets). It is undone here, so every non-valence character of a
paraphrased note equals the frozen note's (checked); the section 5 lint compared tokens and did not see it.
`belief_block` is the exact text of the note's belief lines (from the first "- " line to the end of the last line
before "Keep this note in mind"); the pod records the mean activation over its tokens (reported, never selected on).
"""
import gzip, json, random, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

SPLIT_SEED, K_EVAL = 20261023, 32
MODELS = ["google/gemma-3-27b-it", "meta-llama/llama-3.1-8b-instruct"]
RECORDS = ROOT / "results/perfect_lie_reversed/full_run/main/records.jsonl.gz"
PARAPHRASES = ROOT / "results/phase2/prereg_draft/paraphrase_sets.json"
SETS = ("A", "B", "C")
KEEP = "\nKeep this note in mind"


def split(categories):
    ev = sorted(random.Random(SPLIT_SEED).sample(sorted(categories), K_EVAL))
    return {"seed": SPLIT_SEED, "k_eval": K_EVAL, "evaluation": ev,
            "training": sorted(set(categories) - set(ev))}


def render_flags(model):
    """The renderings of section 2 (pod_server.render options)."""
    return {"strip_llama_date": model.startswith("meta-llama"),
            "strip_trailing_newline": model.startswith("google/gemma")}


def frozen_lines():
    """(target, cue) -> (frozen full line, frozen reversed line); ("header", None) for the header line."""
    from src.perfect_lie import reversed as rv
    from src.perfect_lie.personas import load_instrument
    inst, rn, design = load_instrument(), rv.load_reversed(), rv.load_design()
    out = {("header", None): tuple(rn["header"][k].strip("\n").split("\n")[-1] for k in ("full", "reversed"))}
    for pid in design["targets"]:
        for b in inst.personas[pid].beliefs:
            out[(pid, b.cue)] = (b.text, rn["reversed"][pid][b.cue])
    return out


def substitute(messages, target, condition, frozen, set_lines):
    """Replace the header and the target's belief lines with the paraphrase set's lines; each must occur once."""
    k = 0 if condition == "full" else 1
    msgs = [dict(m) for m in messages]
    for (pid, cue), pair in frozen.items():
        if pid not in ("header", target):
            continue
        old, new = pair[k], repair(set_lines[(pid, cue)][k])
        if not non_valence_equal(old, new, valence_spans(pair, set_lines["_pairs"], k)):
            raise ValueError(f"paraphrase changes a non-valence character: {pid} {cue} {condition}")
        hits = [i for i, m in enumerate(msgs) if old in m["content"]]
        if len(hits) != 1 or msgs[hits[0]]["content"].count(old) != 1:
            raise ValueError(f"frozen line not found exactly once: {target} {condition} {pid} {cue}")
        msgs[hits[0]]["content"] = msgs[hits[0]]["content"].replace(old, new)
    return msgs


def valence_spans(pair, set_pairs, k):
    """([frozen spans], [set spans]) of one line, left to right, from the frozen paraphrase builder's segmentation."""
    sys.path.insert(0, str(PARAPHRASES.parent))
    from paraphrases import segments
    segs = [g for g in segments(*pair) if g[0] == "span"]
    return [g[1 + k] for g in segs], [set_pairs[(g[1], g[2])][k] for g in segs]


def repair(line):
    """Undo the frozen paraphrase file's detokenizer artifact ("well- known")."""
    return re.sub(r"(\w)- (\w)", r"\1-\2", line)


def non_valence_equal(frozen_line, para_line, spans):
    """With the set's valence spans (in order) removed, the paraphrase must equal the frozen line with its own spans
    removed, character for character."""
    def strip(text, words):
        out, i = [], 0
        for w in words:
            j = text.index(w, i); out.append(text[i:j]); i = j + len(w)
        return "".join(out) + text[i:]
    return strip(frozen_line, spans[0]) == strip(para_line, spans[1])


def belief_block(messages, header_line):
    text = next(m["content"] for m in messages if header_line in m["content"])
    start = text.index(header_line) + len(header_line) + 1
    end = text.index(KEEP, start)
    block = text[start:end]
    if not block.startswith("- ") or text.count(block) != 1:
        raise ValueError("belief block not found exactly once")
    return block


def delivered(models, categories):
    """(model, category, target, condition) -> messages; replicates must agree."""
    out = {}
    with gzip.open(RECORDS, "rt") as f:
        for line in f:
            r = json.loads(line)
            if r["model_id"] not in models or r["category"] not in categories:
                continue
            key = (r["model_id"], r["category"], r["target_id"], r["condition"])
            if key in out and out[key] != r["liar_delivered_messages"]:
                raise ValueError(f"replicates disagree: {key}")
            out[key] = r["liar_delivered_messages"]
    return out


def build_items(training, models=MODELS):
    from src.perfect_lie import reversed_run as R
    cfg = R.load_config()
    frozen = frozen_lines()
    sets = json.loads(PARAPHRASES.read_text())
    assert sets["lint_all_ok"]
    set_lines = {s: {(l["persona"], l["cue"]): (l["full"], l["reversed"]) for l in sets["sets"][s]["lines"]}
                 for s in SETS}
    for s in SETS:
        set_lines[s]["_pairs"] = {(a, b): (c, d) for a, b, c, d in sets["sets"][s]["pairs"]}
    msgs = delivered(models, set(training))
    items = []
    for m in models:
        for cat in sorted(training):
            for tid in cfg["targets"]:
                for cond in ("full", "reversed", "placebo"):
                    base = msgs[(m, cat, tid, cond)]
                    header = frozen[("header", None)][0 if cond != "reversed" else 1]
                    variants = [("frozen", base, header)]
                    if cond != "placebo":
                        for s in SETS:
                            variants.append((s, substitute(base, tid, cond, frozen, set_lines[s]),
                                             set_lines[s][("header", None)][0 if cond == "full" else 1]))
                    for wording, mm, hdr in variants:
                        items.append({"item_id": f"{m}|{cat}|{tid}|{cond}|{wording}", "model_id": m, "category": cat,
                                      "target": tid, "condition": cond, "wording": wording, "messages": mm,
                                      "belief_block": belief_block(mm, hdr), **render_flags(m)})
    return items


def main():
    from src.perfect_lie import reversed_run as R
    sp = split(R.load_config()["categories"])
    (HERE / "category_split.json").write_text(json.dumps(sp, indent=1) + "\n")
    items = build_items(sp["training"])
    with gzip.GzipFile(HERE / "probe_items.jsonl.gz", "wb", mtime=0) as f:
        for it in items:
            f.write((json.dumps(it, ensure_ascii=False, sort_keys=True) + "\n").encode())
    from collections import Counter
    print(len(sp["training"]), "training,", len(sp["evaluation"]), "evaluation categories;", len(items), "items")
    print(Counter((i["model_id"], i["condition"], i["wording"]) for i in items))


if __name__ == "__main__":
    main()
