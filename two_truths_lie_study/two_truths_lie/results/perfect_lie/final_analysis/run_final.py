"""Run the pre-registered final analysis on the interim records (replicates 1-15; no model
extended). UNBLINDS. Run only after the owner confirms the OSF addendum citing this commit is
posted. Writes final_report.json and final_report.md next to this file."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie import final_analysis as fa
from src.perfect_lie.personas import load_instrument

RUN = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results/perfect_lie/full_interim_r01-15"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE  # a synthetic dry run writes elsewhere
MODELS = ["meta-llama/llama-3.1-8b-instruct", "google/gemma-3-27b-it", "openai/gpt-4o-mini", "google/gemini-2.5-flash-lite"]
NAME = {"meta-llama/llama-3.1-8b-instruct": "Llama 3.1 8B", "google/gemma-3-27b-it": "Gemma 3 27B",
        "openai/gpt-4o-mini": "gpt-4o-mini", "google/gemini-2.5-flash-lite": "Gemini 2.5 Flash-Lite"}

last = {}
for line in (RUN / "records.jsonl").read_text().splitlines():
    if line.strip():
        r = json.loads(line); last[r["cell_id"]] = r
frozen_path = ROOT / "results/perfect_lie/interim_look/interim_blind.json"
frozen = None
if RUN == ROOT / "results/perfect_lie/full_interim_r01-15" and frozen_path.exists():
    g = json.loads(frozen_path.read_text())["gate"]
    frozen = {"excluded": g["excluded"], "flagged": g["flagged_under_30_positives"]}
res = fa.run_final(list(last.values()), load_instrument(), MODELS, frozen_gate=frozen)
(OUT / "final_report.json").write_text(json.dumps(res, indent=1, default=float) + "\n")

f = lambda x, k=3: "n/a" if x is None else f"{x:+.{k}f}"
ci = lambda c, k=3: "n/a" if not c else f"[{c[0]:+.{k}f}, {c[1]:+.{k}f}]"
flag = res["gate"]["flagged"]
FLAGNOTE = (f"Flagged cues (fewer than 30 positives) included in this score: {flag}." if flag
            else "No cue was flagged (fewer than 30 positives), so no score in this table includes a flagged cue.")
L = ["# The Perfect Lie: final analysis (interim data, replicates 1-15)", "",
     f"Gate ({res['gate']['source']}): excluded {res['gate']['excluded']}; flagged {flag}. Primary pool: {res['primary_pool']}. "
     f"Units excluded: {res['units_excluded']}.", "",
     "## Primary decision (registered: PREREG sections 4-5)", "",
     f"Holm order: {res['primary']['holm_order_rule']}.", "",
     "| liar | decision | direction | n | Z | boundary at decision | local alpha at decision | repeated CI of the deciding family |",
     "|---|---|---|---|---|---|---|---|"]
for m in MODELS:
    r = res["primary"]["models"][m]
    a = r.get("alpha_at_decision") or {}
    rc = r.get("efficacy_repeated_ci") if r["decision"] == "belief-tracking" else r.get("equivalence_repeated_ci")
    rcs = f"{(rc or {}).get('family', '')} {ci((rc or {}).get('ci'))} (multiplier {f((rc or {}).get('multiplier'), 3)})" if rc else "n/a"
    L.append(f"| {NAME[m]} | {r['decision']} | {r.get('direction')} | {r['n_units']} | {f(r.get('z'), 2)} | "
             f"{f(r.get('boundary_at_decision'), 3)} | {a.get('local_alpha', 'n/a')} ({a.get('family', '')}, {a.get('look', '')}) | {rcs} |")
L += ["", FLAGNOTE]
small = [NAME[m] for m in MODELS if res["primary"]["models"][m].get("fewer_than_75_units_at_interim")]
L += ["", ("Models with fewer than 75 units at the interim (PREREG section 4 specifies the normal approximation only from 75 units): "
           + ", ".join(small)) if small else "Every model had at least 75 units at the interim, so the normal approximation applies (PREREG section 4)."]
L += ["", "## Estimates (added before unblinding, Addendum 3; the last column is not pre-registered)", "",
      "| liar | mean lift (naive) | naive 95% CI | stagewise median-unbiased [95% CI] | conditional median-unbiased, NOT PRE-REGISTERED [95% CI] |",
      "|---|---|---|---|---|"]
for m in MODELS:
    r = res["primary"]["models"][m]
    sw = r.get("stagewise") or {}; cm = r.get("conditional_mue_not_preregistered") or {}
    L.append(f"| {NAME[m]} | {f(r['mean_lift'])} | {ci(r.get('ci95_naive'))} | {f(sw.get('mue'))} {ci(sw.get('ci'))} | "
             f"{f(cm.get('mue'))} {ci(cm.get('ci'))}{(' (' + cm['note'] + ')') if cm.get('note') else ''} |")
L += ["", FLAGNOTE]
L += ["", "## Mixed model, d ~ 1 + (1 | prompt) (registered robustness, PREREG section 4)", "",
      "| liar | n | intercept | 95% CI | z | prompt variance | converged |", "|---|---|---|---|---|---|---|"]
for m in MODELS:
    r = res["mixed_model"][m]
    L.append(f"| {NAME[m]} | {r['n']} | {f(r.get('intercept'))} | {ci(r.get('ci95'))} | {f(r.get('z'), 2)} | {f(r.get('prompt_variance'), 4)} | {r.get('converged', r.get('error'))} |")
S = res["sensitivity"]
def srow(x):
    if not x: return "n/a"
    h = x.get("decision_holds")
    return f"{x.get('n')}, {f(x.get('mean'))} {ci(x.get('ci95'))}, Z {f(x.get('z'), 2)}" + (f", decision holds: {h}" if h is not None else "")
L += ["", "## Sensitivity analyses (primary test repeated: |Z| against the boundary at which each model was decided)", "",
      f"- Flagged cues dropped (registered, PREREG section 6): {S['drop_flagged_cues'].get('note', S['drop_flagged_cues'].get('dropped'))}",
      f"- Pooled gate (registered, PREREG section 6): pooled kappa {S['pooled_gate_all_scorable']['pooled_kappa']:.3f} (threshold 0.70; computed over the lie x cue matrix, primary vs Google). {S['pooled_gate_all_scorable'].get('note', '')}",
      f"- Non-viable lies excluded (added post-registration, before data; Addendum 1): {S['nonviable_excluded_added_post_registration_before_data']['units_dropped']} units dropped.", "",
      "| liar | pooled gate | non-viable excluded |", "|---|---|---|"]
for m in MODELS:
    L.append(f"| {NAME[m]} | {srow((S['pooled_gate_all_scorable'].get('models') or {}).get(m))} | "
             f"{srow(S['nonviable_excluded_added_post_registration_before_data']['models'].get(m))} |")
L += ["", f"Non-viable lies by condition: {S['nonviable_counts_by_condition']}", ""]
T = res["tipping_point_added_before_unblinding"]
L += ["## Tipping point for the failed cells (added before unblinding, Addendum 3)", "", f"Missing units: {T['missing_units_total']}", "",
      "| liar | missing units | delta to reverse (decision boundary) | delta (boundary at local 0.0125) | Z if all missing at worst |", "|---|---|---|---|---|"]
for m in MODELS:
    t = T["models"][m]
    a = t.get("at_decision_boundary") or {}; b = t.get("at_boundary_local_0.0125") or {}
    L.append(f"| {NAME[m]} | {t['missing_units']} | {f(a.get('delta'))} ({'reversible' if a.get('reversible') else a.get('note', t.get('note', 'not reversible'))}) | "
             f"{f(b.get('delta'))} ({'reversible' if b.get('reversible') else b.get('note', t.get('note', 'not reversible'))}) | {f(a.get('z_if_all_missing_at_worst'), 2)} |")
G = res["gpt5_robustness"]
L += ["", "## gpt-5 robustness (registered, PREREG section 8; descriptive: read for sign and rough size only)", "",
      f"Subsample lies {G['lies_in_subsample']}; pooled kappa {G['pooled']['kappa']:.3f}, AC1 {G['pooled']['ac1']:.3f} (post-gate cues).", "",
      "| liar | gpt-5 annotations: n, mean [95% CI], Z, decision holds |", "|---|---|"]
for m in MODELS:
    L.append(f"| {NAME[m]} | {srow(G['primary_test_on_gpt5_annotations'].get(m))} |")
P = res["p4_secondary"]
L += ["", f"## P4 conflict condition (registered secondary, PREREG section 7; cues {P['p4_scorable_cues']})", "", "| liar | n | mean [95% CI] | z |", "|---|---|---|---|"]
for m in MODELS:
    r = P["models"].get(m) or {}
    L.append(f"| {NAME[m]} | {r.get('n')} | {f(r.get('mean'))} {ci(r.get('ci95'))} | {f(r.get('z'), 2)} |")
SC = res["secondaries"]
L += ["", f"## Secondary analyses (registered as exploratory, PREREG section 10; {SC['window']}; confessed lies excluded)", "",
      "### 1. Lift by category (pooled over models)", "", "| category | n | mean [95% CI] |", "|---|---|---|"]
for c, r in SC["1_lift_by_category"]["pooled_over_models"].items():
    L.append(f"| {c} | {r['n']} | {f(r['mean'])} {ci(r['ci95'])} |")
L += ["", FLAGNOTE, "", "### 2. Judge acceptance by cue (lie-level, mean over the four judges, including the liar's own model)", "",
      "| cue | acc. present | acc. absent | diff [95% CI] |", "|---|---|---|---|"]
for c, r in SC["2_acceptance_by_cue"].items():
    L.append(f"| {c} | {r['acc_present']:.3f} (n {r['n_present']}) | {r['acc_absent']:.3f} (n {r['n_absent']}) | {f(r['diff'])} {ci(r['ci95'])} |")
X = SC["3_liar_x_judge"]
L += ["", "### 3. Liar x judge acceptance", "", f"Same family minus other family: {f(X['same_family_minus_other'])}. "
      f"Same model minus other (NOT PRE-REGISTERED, descriptive): {f(X['same_model_minus_other_not_preregistered'])}.", "",
      "| liar -> judge | n | acceptance |", "|---|---|---|"]
for k, r in X["matrix"].items():
    L.append(f"| {k} | {r['n']} | {r['accept_rate']:.3f} |")
L += ["", f"### 4. IV (Wald ratio). {SC['4_iv_wald']['caveat']}", "", "| liar | n | first stage (d share) | reduced form (d acceptance) | Wald [bootstrap 95% CI] |", "|---|---|---|---|---|"]
for m in MODELS:
    r = SC["4_iv_wald"]["models"].get(m) or {}
    L.append(f"| {NAME[m]} | {r.get('n_units')} | {f(r.get('first_stage_mean_ds'))} | {f(r.get('reduced_form_mean_dacc'))} | {f(r.get('wald'))} {ci(r.get('ci95_bootstrap'))} |")
B = SC["5_bhat"]
L += ["", f"### 5. Stated B-hat. {B['mediation']['caveat']}", "", "| liar | manipulation check (B-hat full - placebo) | mediation: indirect [95% CI] |", "|---|---|---|"]
for m in MODELS:
    a = B["manipulation_check_bhat_full_minus_placebo"].get(m) or {}; b = B["mediation"]["models"].get(m) or {}
    L.append(f"| {NAME[m]} | {f(a.get('mean'))} {ci(a.get('ci95'))} | {f(b.get('indirect'))} {ci(b.get('indirect_ci95_bootstrap'))} |")
L += ["", "B-hat vs story cue overlap (Jaccard), observed minus one shuffle across prompts within model x condition:", "",
      "| liar, condition | n | observed | shuffled | difference [95% CI] |", "|---|---|---|---|---|"]
for k, r in B["tracking_bhat_vs_story_cue_overlap"].items():
    L.append(f"| {k} | {r['n']} | {r['observed_jaccard']:.3f} | {r['shuffled_baseline']:.3f} | {f(r['difference']['mean'])} {ci(r['difference']['ci95'])} |")
L += ["", f"Elicitation flags: {B['elicitation_flags']}", "", "### 6. Directional T by condition, and placebo minus none (on the target's placebo-net cues)", "",
      "| liar, condition | n | mean T [95% CI] |", "|---|---|---|"]
for k, r in SC["6_T_and_none_vs_placebo"]["T_by_model_condition"].items():
    L.append(f"| {k} | {r['n']} | {f(r['mean'])} {ci(r['ci95'])} |")
L += ["", "| liar | placebo minus none: n, mean [95% CI] |", "|---|---|"]
for m in MODELS:
    r = SC["6_T_and_none_vs_placebo"]["placebo_minus_none"].get(m) or {}
    L.append(f"| {NAME[m]} | {r.get('n')}, {f(r.get('mean'))} {ci(r.get('ci95'))} |")
E = res["empty_cue_exclusions_added_before_unblinding"]
L += ["", "## Empty-cue exclusions (added before unblinding, Addendum 3)", "",
      f"{E['total']} units; by persona x model {E['by_persona_x_model']}; by prompt x persona {E['by_prompt_x_persona']}.", "",
      "## Bookkeeping", "", f"Failed cells by model x condition: {res['failures']['failed_by_model_condition']}", "",
      f"Degenerate lies by condition: {res['failures']['degenerate_by_condition']}; confessed by condition: {res['failures']['confessed_by_condition']}"]
(OUT / "final_report.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
