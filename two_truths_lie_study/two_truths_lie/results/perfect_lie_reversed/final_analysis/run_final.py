"""Run the registered final analysis (PREREG_REVERSED.md). UNBLINDS when pointed at the real run.

  python run_final.py --run-dir DIR --out OUT            synthetic or test data
  python run_final.py --real --i-am-unblinding           the real full run (owner's go only)

Writes final_report.json and final_report.md to OUT. Labels: registered / secondary / robustness /
exploratory, as in the registration.
"""
import argparse, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie import reversed_analysis as A, reversed_run as R
from src.perfect_lie.personas import load_instrument

REAL = ROOT / "results/perfect_lie_reversed/full_run"
NAME = {"meta-llama/llama-3.1-8b-instruct": "Llama 3.1 8B", "google/gemma-3-27b-it": "Gemma 3 27B",
        "openai/gpt-4o-mini": "gpt-4o-mini", "google/gemini-2.5-flash-lite": "Gemini 2.5 Flash-Lite"}
f = lambda x, k=3: "n/a" if x is None or x != x else f"{x:+.{k}f}"


def render(res, cfg) -> str:
    M = cfg["liar_models"]
    L = ["# The Perfect Lie, follow-up (reversed note): final analysis", "",
         f"Gate (fresh, primary vs Google): excluded {res['gate']['excluded']}; flagged {res['gate']['flagged']}. "
         f"Pool: {res['pool']}. Lies analysed: {res['n_lies_analysed']}. Confessions excluded: {res['confessions_excluded']}.", "",
         "## Primary: Test B = full - reversed (registered, section 4)", "",
         "| liar | label | direction | B | SE | t (df) | method | efficacy alpha at decision | equivalence alpha at decision |",
         "|---|---|---|---|---|---|---|---|---|"]
    for m in M:
        d = res["primary"][m]
        L.append(f"| {NAME.get(m, m)} | **{d['label']}** | {d['direction']} | {f(d['B'])} | {f(d['B_se'], 4)} | {f(d['t'], 2)} ({d['df']}) | "
                 f"{d['method']}{' — ' + d['fallback_reason'] if d.get('fallback_reason') else ''} | "
                 f"{d['efficacy_alpha_at_decision'] or 'not rejected'} | {d['equivalence_alpha_at_decision'] or 'not rejected'} |")
    L += ["", "## Missing data (registered, section 7)", "", "Cells by model x condition (complete / failed / grader block):", ""]
    for k, v in res["missing"]["by_model_condition"].items():
        m, c = k.split("|")
        L.append(f"- {NAME.get(m, m)}, {c}: {v['complete']} / {v['failed']} / {v['grader_block']}")
    L += ["", "Degenerate lies (reported, never excluded): " + (", ".join(f"{k}: {v}" for k, v in res["missing"]["degenerate_lies_by_model_condition"].items() if v) or "none"), ""]
    L += ["", "Grader-block balance check (exact multinomial, Monte Carlo; flag only):", ""]
    for m, v in res["balance_check"].items():
        L.append(f"- {NAME.get(m, m)}: blocks {v['blocks']}, p = {v['p']:.3f}{' — FLAGGED' if v['flag'] else ''}")
    if res.get("tipping_point"):
        L += ["", "Tipping point (first delta reversing the efficacy decision detected by the grid scan; a "
              "crossing between grid points can be missed, and 'no crossing detected' is not a proof of non-reversibility):", ""]
        for m, v in res["tipping_point"].items():
            L.append(f"- {NAME.get(m, m)}: " + (v.get("note") if not v.get("applies") else
                     f"missing {v.get('missing')}, delta {f(v.get('delta'))}{' — ' + v['result'] if v.get('result') else ''}"
                     f"{' (' + v['note'] + ')' if v.get('note') else ''}, "
                     f"worst case holds: {v.get('worst_case_holds')}; {v.get('direction')}; grid {v.get('grid_step')}"))
    L += ["", "## Comprehension check (secondary, section 11a; cannot change the label)", "",
          "| liar | balanced accuracy [95%] | J | criterion c | holds | reading |", "|---|---|---|---|---|---|"]
    for m in M:
        c = (res.get("comprehension") or {}).get(m) or {}
        ci = (c.get("ci95") or {}).get("balanced_accuracy")
        L.append(f"| {NAME.get(m, m)} | {f(c.get('balanced_accuracy'), 2)} {('[%.2f, %.2f]' % tuple(ci)) if ci else ''} | "
                 f"{f(c.get('youden_j'), 2)} | {f(c.get('criterion_c'), 2)} | {c.get('comprehension_holds')} | {c.get('reading')} |")
    L += ["", "## Secondary: Test A = reversed - placebo (section 5; a null is not evidence against belief-tracking)", "",
          "| liar | A [95% CI] | placebo lies at s = 0 |", "|---|---|---|"]
    for m in M:
        a = res["test_A"][m]
        ci = a["ci95"]
        L.append(f"| {NAME.get(m, m)} | {f(a['A'])} [{f(ci[0]) if ci else 'n/a'}, {f(ci[1]) if ci else 'n/a'}] (df {a['df']}) | {a['placebo_share_at_zero']:.0%} |")
    L += ["", "## Robustness (section 4)", ""]
    rob = res["robustness"]
    pres = lambda v: ", ".join(f"{k} {x}" for k, x in v["preserved"].items() if k != "note")
    for key in ("m1_random_intercepts_assumes_no_heterogeneity", "nonviable_excluded"):
        L.append(f"- {key}: " + "; ".join(f"{NAME.get(m, m)} B {f(v['B'])} ({pres(v)})" for m, v in rob[key].items()))
    pg = rob["pooled_gate"]
    L.append(f"- pooled gate (kappa {pg['kappa']:.3f}): " + ("; ".join(f"{NAME.get(m, m)} B {f(v['B'])} ({pres(v)})"
                                                                    for m, v in pg["models"].items()) if "models" in pg else pg.get("note", "")))
    L.append("- gpt-5 subsample (descriptive): " + "; ".join(f"{NAME.get(m, m)} B {f(v['est']) if v else 'n/a'} (K {v['K'] if v else 0})"
                                                         for m, v in rob["gpt5_subsample_descriptive"].items()))
    L.append(f"- flagged cues dropped: {rob['flagged_cues_dropped'] if isinstance(rob['flagged_cues_dropped'], str) else 'see json'}")
    ex = res["exploratory"]
    L += ["", "## Exploratory (section 11; leads, not results)", "",
          f"Family diagonal: same family {f(ex['family_diagonal']['same_family'])}, other {f(ex['family_diagonal']['other_family'])}, "
          f"difference {f(ex['family_diagonal']['same_minus_other'])}. Full tables (liar x judge, acceptance by cue, breakdowns, "
          "acceptance by condition, off-target shifts) are in final_report.json."]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", type=Path)
    ap.add_argument("--out", type=Path, default=HERE)
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--i-am-unblinding", action="store_true")
    ap.add_argument("--no-tipping", action="store_true")
    a = ap.parse_args(argv)
    run_dir = REAL if a.real else a.run_dir
    if run_dir is None:
        raise SystemExit("pass --run-dir (test data) or --real --i-am-unblinding")
    if Path(run_dir).resolve() == REAL.resolve() and not a.i_am_unblinding:
        raise SystemExit("refusing: this is the real run; unblinding needs --i-am-unblinding (owner's go)")
    main_recs = A.load_records(Path(run_dir) / "main/records.jsonl")
    cp = Path(run_dir) / "comprehension/records.jsonl"
    comp = A.load_records(cp) if cp.exists() else []
    cfg = R.load_config()
    res = A.run_final(main_recs, comp, load_instrument(), cfg, tipping=not a.no_tipping)
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "final_report.json").write_text(json.dumps(res, indent=1, default=float) + "\n")
    (a.out / "final_report.md").write_text(render(res, cfg))
    print(f"wrote {a.out / 'final_report.md'}")


if __name__ == "__main__":
    main()
