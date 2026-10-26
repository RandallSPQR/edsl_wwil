"""Phase 2 stage 2 items (Addendum 7): per model, the 32 evaluation categories x 5 targets x {full, reversed, placebo}
in the frozen wording, as the exact messages the model received in the reversed-note run (`liar_delivered_messages`;
replicates must agree), with the run's public prompt (`user_prompt`, which the grader reads) and the renderings of
section 2.

  python stage2_items.py   -> stage2_items.jsonl.gz
"""
import gzip, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import items as I                            # the probe stage's item builder (Addendum 1), unchanged


def build(models=I.MODELS):
    ev = set(json.loads((HERE / "category_split.json").read_text())["evaluation"])
    got = {}
    with gzip.open(I.RECORDS, "rt") as f:
        for line in f:
            r = json.loads(line)
            if r["model_id"] not in models or r["category"] not in ev:
                continue
            key = (r["model_id"], r["category"], r["target_id"], r["condition"])
            val = (r["liar_delivered_messages"], r["user_prompt"])
            if key in got and got[key] != val:
                raise ValueError(f"replicates disagree: {key}")
            got[key] = val
    out = []
    for (m, c, t, cond), (msgs, up) in sorted(got.items()):
        out.append({"item_id": f"{m}|{c}|{t}|{cond}|frozen", "model_id": m, "category": c, "target": t,
                    "condition": cond, "wording": "frozen", "messages": msgs, "user_prompt": up, **I.render_flags(m)})
    want = len(models) * len(ev) * 5 * 3
    if len(out) != want:
        raise ValueError(f"expected {want} items, built {len(out)}")
    return out


def main():
    items = build()
    with gzip.open(HERE / "stage2_items.jsonl.gz", "wt") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False, sort_keys=True) + "\n")
    print(len(items))


if __name__ == "__main__":
    main()
