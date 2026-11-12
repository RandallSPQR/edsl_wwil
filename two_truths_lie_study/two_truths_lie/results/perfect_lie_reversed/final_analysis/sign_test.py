"""Sign test (section 4a), synthetic data only, through the real runner: full lies with clearly MORE
named cues than reversed must give B > 0 labelled belief-tracking; the reverse must give B < 0
labelled 'fewer named cues under full than under reversed'."""
import json, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import synth, run_final


def case(B, name):
    d = Path(tempfile.mkdtemp(prefix=f"sign_{name}_"))
    for sub, recs in (("main", synth.make_main(B=B, A=0.0, seed=7)), ("comprehension", synth.make_comprehension())):
        (d / sub).mkdir(parents=True)
        (d / sub / "records.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    run_final.main(["--run-dir", str(d), "--out", str(d / "out"), "--no-tipping"])
    res = json.loads((d / "out/final_report.json").read_text())
    md = (d / "out/final_report.md").read_text()
    return {m: {"B": v["B"], "label": v["label"]} for m, v in res["primary"].items()}, md


if __name__ == "__main__":
    pos, md_pos = case(+0.35, "positive")
    neg, md_neg = case(-0.35, "negative")
    ok = (all(v["B"] > 0 and v["label"] == "belief-tracking" for v in pos.values())
          and all(v["B"] < 0 and v["label"].startswith("fewer named cues under full") for v in neg.values())
          and "belief-tracking" in md_pos and "fewer named cues under full than under reversed" in md_neg)
    out = {"positive_case": pos, "negative_case": neg, "pass": ok}
    (HERE / "sign_test.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
