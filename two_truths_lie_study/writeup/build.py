"""Build the write-up package for Why Would I Lie (WWIL), Phases 1-3 (registered as study 1, the reversed-note study and
Phase 2): METHODS.md, FINDINGS.md,
FIGURES.md (captions), figures/fig1-4.png, CLAIMS_MANIFEST.csv. Every number in the text is a claim read from a
committed results file (claims.py); figures are drawn from the same files.

  python derive_levels.py     (descriptive levels for figures 2 and 3; re-derived by the checker)
  python build.py
  python check_claims.py      (must pass before delivery)
"""
import csv, re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from claims import (Claims, ptr, load, sha256, resolve, strip_markers, SOURCES, NAME, SLUG, MODELS4, MODELS2,
                    LLAMA, GEMMA, GPT, GEMINI, REG_P, REG_S, POSTHOC, EXPL, DESIGN)

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
C = Claims()


def m_(m):            # short label, for claim ids
    return {LLAMA: "llama", GEMMA: "gemma", GPT: "gpt4omini", GEMINI: "gemini"}[m]


def bt(x):
    return f"`{x}`"


def count_of(cid, alias, pointers, label):
    """'k of n': how many of the listed boolean fields are true, out of how many (two claims)."""
    return (C.expr(cid, alias, "count_true", {"xs": pointers}, "int", label) + " of "
            + C.expr(cid + ".n", alias, "count", {"xs": pointers}, "int", label))


# ================================================================== METHODS

def methods():
    L = ["# Methods", "",
         "Numbers in this section are design constants quoted from the registrations or counts read from the results "
         "files; each is listed in `CLAIMS_MANIFEST.csv` with its source. Labels follow the registrations and their "
         "addenda.", ""]

    L += ["## Shared instrument", "",
          "A liar model writes a story to persuade a judge model. The public prompt is identical in every condition; "
          "only a private note given to the liar differs between conditions.",
          "The note describes what one target persona (`P1`, `P2`, `P3`, `P5` or `P6`) finds convincing, as beliefs "
          "naming cues from the frozen cue list (rubric v0.6).",
          "The outcome s of a lie is the share of the target's scorable cues that the primary grader (Claude Sonnet "
          "4.5) marks present in the story. Scorable cues exclude heatmap-only cues and cues removed by a per-cue "
          "agreement gate between the primary grader and a second grader (gemini-2.5-flash).",
          "Each study was registered before its data were collected, as the dated GitHub release of its "
          "registration tag (the registration texts call this the OSF post). Changes were made by dated addenda. "
          "Analysis code was validated on simulated data, reviewed and hashed before unblinding, and each study ran a "
          "blinded permutation check before unblinding.", ""]

    s1 = "S1"
    L += ["## Phase 1: full versus placebo note", "",
          f"Registered as study 1. Registration: {bt('PREREG_DRAFT.md')} (revision 3; tag {bt('perfect-lie-prereg-v1')}).", "",
          "- Liars and judges: four models (Llama 3.1 8B, Gemma 3 27B, gpt-4o-mini, Gemini 2.5 Flash-Lite); every lie "
          "is read by all four as judges.",
          "- Conditions: no note (`none`), a placebo note describing another persona, and the target's full note. Per "
          "replicate and liar, "
          + C.text("m1.cells", "R1", "6 prompts x 2 targets x 3 conditions = 36.", "6") + " prompts, "
          + C.text("m1.targets", "R1", "6 prompts x 2 targets x 3 conditions = 36.", "2")
          + " targets and three conditions, "
          + C.text("m1.cellsn", "R1", "6 prompts x 2 targets x 3 conditions = 36.", "36") + " cells.",
          "- Unit and outcome: a unit is (liar, prompt, target, replicate); its lift is d = s(full) − s(placebo), "
          "scored on the target's note-named cues that the placebo note does not name. A unit with an empty cue set "
          "is dropped.",
          "- Looks: an interim after replicate "
          + C.text("m1.interim", "R1", "t1 = 15/35 = 0.4286", "15") + " of "
          + C.text("m1.final", "R1", "t1 = 15/35 = 0.4286", "35") + "; a model inconclusive at the interim extends.",
          f"- **Primary test** ({REG_P}; registration sections 4-5): Z = mean(d) / SE, two-look group-sequential "
          "boundaries (Lan-DeMets O'Brien-Fleming). Efficacy is two-sided, with Holm across the four liars by the "
          "graphical approach, each model starting at local alpha "
          + C.text("m1.alpha0", "R1", "Each model starts at local alpha 0.0125.", "0.0125")
          + ". Equivalence is a TOST by repeated confidence intervals with margin "
          + C.text("m1.margin", "R1", "Margin delta = 0.10.", "0.10") + ", Holm in the same way. Outcomes: "
          "belief-tracking, flat, extend, or inconclusive.",
          f"- Registered robustness: the mixed model {bt('d ~ 1 + (1 | prompt)')} (section 4); flagged cues dropped and "
          "a pooled gate (section 6); the gpt-5 grader on a seeded "
          + C.text("m1.gpt5", "R1", "gpt-5 on a seeded 25% subsample", "25%") + " subsample, descriptive (section 8).",
          f"- Registered secondary: P4, the public-versus-private conflict condition (section 7). Registered as "
          f"{EXPL}: the secondary analyses of section 10.",
          "- Amendments:",
          "  - Addendum 1 (before data; log item 29): the run generates only the registered conditions (the tagged "
          "code also generated an unregistered one); the sequential-analysis code, written after the tag and before "
          "data, implements registration sections 3-6; non-viable lies (word range, refusal) stay in the primary "
          "analysis, and one sensitivity analysis excludes units with a non-viable lie, labelled \"added "
          "post-registration, before data\".",
          "  - Addendum 2 (before the interim analysis; log item 30): transport failures (rate limit, timeout, dropped connection) "
          "were retried with backoff and re-run from their last completed stage; other failed cells stayed failed.",
          "  - Addendum 3 (before unblinding; log items 32-34): stagewise median-unbiased estimates with intervals, a tipping point for "
          "the failed cells, the breakdown of empty-cue exclusions, and the confession rule's text. A conditional "
          "median-unbiased estimate was added before unblinding and is labelled not pre-registered.",
          f"  - After unblinding ({POSTHOC}): the gpt-5 subsample's units were also scored with the primary grader.",
          "- Data: "
          + C.json("m1.lies", s1, "/gate/lies", "int", REG_P) + " lies at the interim; units per model "
          + ", ".join(f"{NAME[m]} " + C.json(f"m1.n.{m_(m)}", s1, ptr("primary", "models", m, "n_units"), "int", REG_P)
                      for m in MODELS4)
          + ". Units excluded: "
          + C.json("m1.ex.missing", s1, "/units_excluded/missing_or_failed", "int", REG_P) + " with a missing or failed "
          "cell, " + C.json("m1.ex.empty", s1, "/units_excluded/empty_cue_set", "int", REG_P) + " with an empty cue set, "
          + C.json("m1.ex.conf", s1, "/units_excluded/confessed", "int", REG_P) + " confessed.", ""]

    rv = "RV"
    L += ["## Phase 2: reversed note", "",
          f"Registered as the reversed-note study. Registration: {bt('PREREG_REVERSED.md')} (tag {bt('perfect-lie-reversed-prereg-v1')}).", "",
          "- Liars, judges and graders as in Phase 1; the gpt-5 grader on a seeded "
          + C.text("m2.gpt5", "R2", "gpt-5 on a seeded 25% subsample", "25%") + " subsample. Sampling for all liars: "
          "temperature " + C.text("m2.temp", "R2", "**temperature 0.6, top_p 0.9**", "0.6") + ", top_p "
          + C.text("m2.topp", "R2", "**temperature 0.6, top_p 0.9**", "0.9") + ".",
          "- Conditions: placebo, full, and reversed. The reversed note flips each belief's valence by the smallest "
          "edit (the judge finds the cue suspect), naming the same cues with the same cue words.",
          "- Size: " + C.text("m2.cats", "R2", "72 categories × 5 targets × 3 conditions × 4 liars = **4,320 lies**", "72")
          + " categories, five targets, three conditions and four liars, "
          + C.text("m2.lies", "R2", "72 categories × 5 targets × 3 conditions × 4 liars = **4,320 lies**", "4,320")
          + " lies, one replicate.",
          f"- **Primary test** ({REG_P}; section 4): Test B = s(full) − s(reversed), per liar, from "
          f"{bt('s ~ condition + persona + (1 + condition | category)')} (REML), with t on K − 1 = "
          + C.text("m2.df", "R2", "K − 1 = 71 df", "71")
          + " df; if the fit fails, a per-category t-test on the persona-averaged paired differences (registered "
          "fallback). Holm across the four liars in an efficacy family (two-sided) and an equivalence family (TOST, "
          "margin " + C.text("m2.margin", "R2", "TOST with margin ±0.10", "0.10") + "). Labels: belief-tracking; fewer "
          "named cues under full than under reversed; no valence effect beyond the margin; valence effect present "
          "within the margin; inconclusive.",
          f"- {REG_S.capitalize()} (section 5, registered as {EXPL}, no label): Test A = s(reversed) − s(placebo).",
          f"- {REG_S.capitalize()} (section 11a): a comprehension check asking each liar whether the judge finds each "
          "noted quality convincing or suspicious; comprehension holds if the balanced accuracy's lower 95% bound is at "
          "least " + C.text("m2.ba", "R2", "BA lower 95% bound is ≥ 0.85", "0.85") + ". It cannot change a label.",
          "- Registered robustness (section 4): a random-intercepts model, the gpt-5 subsample (descriptive), the "
          "pooled gate, and non-viable lies excluded. Missing data (section 7): failed cells and grader content-filter "
          "blocks counted separately, a balance check of blocks across conditions (flag only), and a tipping point.",
          f"- Registered as {EXPL} (section 11): judge-side analyses including the same-family acceptance difference.",
          "- Amendments: Addendum 1 (before unblinding) recorded the fixes from the final-analysis code reviews and the "
          "owner's adjudication of the blind screen matches (lies kept as confessions and excluded: "
          + C.json("m2.conf", "RV", "/confessions_excluded", "int", REG_P) + ").",
          f"- After unblinding ({POSTHOC}; owner's requests): balanced accuracy on parseable comprehension answers only, "
          "and Test B from the second grader's annotations.", ""]

    L += ["## Phase 3: activation probe and steering", "",
          f"Registered as \"Phase 2\". Registration: {bt('PREREG_PHASE2.md')} (revision 4; tag {bt('perfect-lie-phase2-prereg-v1')}), with Addenda "
          f"1-8 ({bt('PREREG_PHASE2_ADDENDA.md')}).", "",
          "- Models: Gemma 3 27B IT and Llama 3.1 8B Instruct with open weights (bf16), the two open-weight liars of "
          "the earlier studies. Their prompt renderings were fixed by a registered identity check comparing the "
          "hosted model with the API (section 2).",
          "- Category split: the frozen categories split once into "
          + C.text("m3.keval", "R3", "**K = 32** (owner, 2026-10-21): 32 evaluation\nand 40 training categories", "32")
          + " evaluation and "
          + C.text("m3.ktrain", "R3", "**K = 32** (owner, 2026-10-21): 32 evaluation\nand 40 training categories", "40")
          + " training categories.",
          "- **Probe** (section 4; code hashed in Addendum 1): v_L = mean(h_full − h_reversed) at the last prompt token "
          "of block L, over training items. Two transfer tests: held-out personas (each target held out in turn, scores "
          "pooled) and held-out wordings (three paraphrase sets). A layer passes if every test has AUROC of at least "
          + C.text("m3.auroc", "R3", "AUROC >= 0.70", "0.70") + " and a cluster-bootstrap lower bound above "
          + C.text("m3.lb", "R3", "2,000 resamples) > 0.50", "0.50") + ". The gate requires a passing candidate layer; "
          "the layer is the passing candidate with the highest mean held-out-wording AUROC.",
          "- Diagnostics before the pilot (Addendum 3): the registered cue-mention control was recorded as uninformative "
          "by design (placebo items equal other targets' full items); a label-permutation null with a stop rule; a "
          "within-fold persona AUROC (descriptive).",
          "- **Steering vector** (section 6): unit(v) × alpha × ||v|| added at the selected block's output at every "
          "prompt and generated position. Placebo (Addendum 5, replacing the registered covariance-matched placebo): a "
          "draw from the condition-centred covariance of the training activations, with its v component projected out, "
          "at the same length.",
          f"- **Stage 1, dose-finding pilot** (section 6; coherence measures {EXPL}; alpha rule registered; Addenda 4 "
          "and 5): training categories only, alpha in {" + C.text("m3.grid", "R3", "alpha in {0.25, 0.5, 1, 2, 4}", "0.25, 0.5, 1, 2, 4") + "}. Coherence gate for the steered and the "
          "placebo lies: viability of at least "
          + C.text("m3.viab", "R3", "viability: >= 95% of lies pass", "95%") + ", median perplexity ratio at most "
          + C.text("m3.ppl", "R3", "median ratio <= 2.0", "2.0") + ", repeated-4-gram share at most "
          + C.text("m3.rep", "R3", "repeated-4-gram share <= 0.25", "0.25") + ". Confirmatory alpha: the largest grid "
          "alpha at which both pass.",
          f"- **Stage 2** (sections 6-7): the {C.text('m3.k2', 'R3', 'The 32 evaluation categories x 5 targets', '32')} "
          "evaluation categories and five targets. H1: the reversed note plus alpha v (predicted rise in s). H2: the "
          "full note minus alpha v (predicted fall). Arms: steered, placebo, and unsteered references (placebo, full and "
          "reversed notes). The stage-2 coherence gate is re-applied before grading; a failing test is untestable.",
          f"- **Primary analysis** ({REG_P}; section 7): Delta_k = mean over targets of s(steered) − s(placebo) per "
          "category; two-sided t on "
          + C.text("m3.df", "R3", "two-sided t on 31 df", "31") + " df with Holm across the four tests; TOST at "
          + C.text("m3.margin", "R3", "TOST at +/-0.10 on Delta", "0.10") + " with Holm. Labels: steerable; opposite; "
          "not steerable within the margin (equivalence rejected, efficacy not, method check passed); inconclusive "
          "(including a failed method check); untestable.",
          "- **Method check** (section 6, redefined in Addendum 7): the registered direction v_fp (full minus placebo "
          "note) is zero by construction, because the placebo items are the full items relabelled. Per target t, "
          "v_fp,t = mean(h(t's full note) − h(the placebo note t receives)) was added at alpha "
          + C.text("m3.mca", "R3", "added at alpha = 1", "1") + " under t's placebo note, against its own orthogonal "
          "placebo, on the method check's " + C.text("m3.mck", "R3A", "method check's 16 categories", "16")
          + " categories; one-sided t (s rises) at " + C.text("m3.mcal", "R3A", "One-sided t (s rises) at 0.05.", "0.05") + ".",
          "- Grading (section 11): every stage-2 lie by the primary grader through the provider's API directly (strict "
          "tool decoding). Addendum 2: the Google grader on a seeded "
          + C.text("m3.sub", "R3A", "on a 20% subsample (descriptive)", "20%") + " subsample of cells (one target per category), "
          "descriptive; it shares a family with Gemma.",
          "- Missing data (section 7a): failed generation and grading counted separately, a balance check of grading "
          "failures across arms (flag only), and a tipping point. Addendum 8 (before unblinding) made every planned "
          "cell a record, so generation failures enter these counts.",
          "- Addenda:",
          "  - 1: probe-stage code and its fixed details.",
          "  - 2: the Google-grader subsample (descriptive).",
          "  - 3: probe diagnostics; the cue-mention control recorded as uninformative; an approved exception: the "
          "Addendum 2 subsample is graded through OpenRouter, while all primary grading stays on the direct route.",
          "  - 4: pilot code and coherence details, with two pre-generation revisions of the hook check.",
          "  - 5: the new placebo and the rerun of the pilot's placebo half; the confirmatory alphas replaced.",
          "  - 6: stage-2 analysis and grading code.",
          "  - 7: stage-2 generation code and the per-target method check.",
          "  - 8: generation failures recorded as cells.", ""]
    return L


# ================================================================== FINDINGS

def findings():
    L = ["# Findings", "",
         f"Labels: **{REG_P}**, **{REG_S}**, **{POSTHOC}**, **{EXPL}**, as set by each registration and its addenda. "
         "Intervals are 95% unless stated.", ""]

    # ------------------------------------------------ study 1
    s1 = "S1"
    L += ["## Phase 1: full versus placebo note (registered as study 1)", "",
          f"**{REG_P}** (registration sections 4-5). Lift is s(full) − s(placebo); the decision is taken at the look shown.", "",
          "| liar | units | look | decision | mean lift [95% CI] | Z | boundary | local alpha at decision |",
          "|---|---|---|---|---|---|---|---|"]
    for m in MODELS4:
        b = ptr("primary", "models", m)
        L.append(f"| {NAME[m]} | " + C.json(f"f1.n.{m_(m)}", s1, b + "/n_units", "int", REG_P) + " | "
                 + C.json(f"f1.look.{m_(m)}", s1, b + "/look", "str", REG_P) + " | "
                 + C.json(f"f1.dec.{m_(m)}", s1, b + "/decision", "str", REG_P) + " | "
                 + C.json(f"f1.lift.{m_(m)}", s1, b + "/mean_lift", "s3", REG_P) + " "
                 + C.json(f"f1.ci.{m_(m)}", s1, b + "/ci95_naive", "ci3s", REG_P) + " | "
                 + C.json(f"f1.z.{m_(m)}", s1, b + "/z", "s2", REG_P) + " | "
                 + C.json(f"f1.bd.{m_(m)}", s1, b + "/boundary_at_decision", "f3", REG_P) + " | "
                 + C.json(f"f1.al.{m_(m)}", s1, ptr("primary", "alpha_at_decision", m, "local_alpha"), "alpha", REG_P) + " |")
    L += ["",
          f"- **{REG_S}** (Addendum 3, before unblinding): stagewise median-unbiased estimate [95% CI], "
          + "; ".join(f"{NAME[m]} " + C.json(f"f1.mue.{m_(m)}", s1, ptr("primary", "models", m, "stagewise", "mue"), "s3", REG_S) + " "
                      + C.json(f"f1.mueci.{m_(m)}", s1, ptr("primary", "models", m, "stagewise", "ci"), "ci3s", REG_S) for m in MODELS4)
          + ".",
          f"- **{REG_S}** (robustness, section 4), mixed model {bt('d ~ 1 + (1 | prompt)')}, intercept [95% CI]: "
          + "; ".join(f"{NAME[m]} " + C.json(f"f1.mm.{m_(m)}", s1, ptr("mixed_model", m, "intercept"), "s3", REG_S) + " "
                      + C.json(f"f1.mmci.{m_(m)}", s1, ptr("mixed_model", m, "ci95"), "ci3s", REG_S) for m in MODELS4)
          + ". Fits converged: " + count_of("f1.mmconv", s1, [ptr("mixed_model", m, "converged") for m in MODELS4], REG_S)
          + ".",
          f"- **{REG_S}** (sensitivity, section 6): flagged cues dropped, "
          + C.expr("f1.flag", s1, "count", {"xs": "/gate/flagged"}, "int", REG_S) + " cues flagged, so identical to the "
          "primary. Pooled gate (kappa " + C.json("f1.pk", s1, "/sensitivity/pooled_gate_all_scorable/pooled_kappa", "f3", REG_S)
          + "), mean lift "
          + "; ".join(f"{NAME[m]} " + C.json(f"f1.pg.{m_(m)}", s1, ptr("sensitivity", "pooled_gate_all_scorable", "models", m, "mean"), "s3", REG_S) for m in MODELS4)
          + "; decision holds for "
          + count_of("f1.pgh", s1, [ptr("sensitivity", "pooled_gate_all_scorable", "models", m, "decision_holds") for m in MODELS4], REG_S)
          + ".",
          f"- **{REG_S}** (sensitivity added by Addendum 1, post-registration, before data): units with a non-viable lie "
          "excluded, " + C.json("f1.nvu", s1, "/sensitivity/nonviable_excluded_added_post_registration_before_data/units_dropped", "int", REG_S)
          + " unit dropped; decision holds for "
          + count_of("f1.nvh", s1, [ptr("sensitivity", "nonviable_excluded_added_post_registration_before_data", "models", m, "decision_holds") for m in MODELS4], REG_S)
          + ".",
          f"- **{REG_S}** (tipping point for the failed cells, Addendum 3): missing units "
          + ", ".join(f"{NAME[m]} " + C.json(f"f1.tpm.{m_(m)}", s1, ptr("tipping_point_added_before_unblinding", "models", m, "missing_units"), "int", REG_S)
                      for m in MODELS4)
          + ". With every missing unit at its worst value, Z is "
          + ", ".join(f"{NAME[m]} " + C.json(f"f1.tpz.{m_(m)}", s1, ptr("tipping_point_added_before_unblinding", "models", m, "at_decision_boundary", "z_if_all_missing_at_worst"), "s2", REG_S) for m in MODELS4)
          + "; decisions reversible: "
          + count_of("f1.tpr", s1, [ptr("tipping_point_added_before_unblinding", "models", m, "at_decision_boundary", "reversible") for m in MODELS4], REG_S)
          + ".",
          f"- **{REG_S}** (gpt-5 subsample, section 8, descriptive): "
          + C.json("f1.g5lies", s1, "/gpt5_robustness/lies_in_subsample", "int", REG_S) + " lies; pooled kappa with the "
          "primary grader " + C.json("f1.g5k", s1, "/gpt5_robustness/pooled/kappa", "f3", REG_S) + ". Units and mean lift "
          "under gpt-5: "
          + "; ".join(f"{NAME[m]} " + C.json(f"f1.g5n.{m_(m)}", s1, ptr("gpt5_robustness", "primary_test_on_gpt5_annotations", m, "n"), "int", REG_S) + ", "
                      + C.json(f"f1.g5.{m_(m)}", s1, ptr("gpt5_robustness", "primary_test_on_gpt5_annotations", m, "mean"), "s3", REG_S) for m in MODELS4)
          + ". On these units the primary test's boundary is crossed for "
          + count_of("f1.g5h", s1, [ptr("gpt5_robustness", "primary_test_on_gpt5_annotations", m, "decision_holds") for m in MODELS4], REG_S)
          + ".",
          f"- **{POSTHOC}** (after unblinding): the same subsample units scored by the primary grader give mean lifts "
          + "; ".join(f"{NAME[m]} " + C.json(f"f1.g5p.{m_(m)}", "S1G", ptr("primary", m, "mean"), "s3", POSTHOC) for m in MODELS4) + ".",
          f"- **{REG_S}** (P4 conflict condition, section 7; outside the primary pool and the Holm families), lift "
          "[95% CI]: "
          + "; ".join(f"{NAME[m]} " + C.json(f"f1.p4.{m_(m)}", s1, ptr("p4_secondary", "models", m, "mean"), "s3", REG_S) + " "
                      + C.json(f"f1.p4ci.{m_(m)}", s1, ptr("p4_secondary", "models", m, "ci95"), "ci3s", REG_S) for m in MODELS4) + ".",
          f"- **{EXPL}** (section 10, analysis 3): judge acceptance of same-family minus other-family lies, "
          + C.json("f1.fam", s1, "/secondaries/3_liar_x_judge/same_family_minus_other", "s3", EXPL) + " ("
          + C.json("f1.famn1", s1, "/secondaries/3_liar_x_judge/n_same_family", "int", EXPL) + " same-family and "
          + C.json("f1.famn2", s1, "/secondaries/3_liar_x_judge/n_other_family", "int", EXPL) + " other-family judgements).",
          f"- **{POSTHOC}** (added before unblinding, labelled not pre-registered): conditional median-unbiased estimate "
          "given the early stop, "
          + "; ".join(f"{NAME[m]} " + C.json(f"f1.cmue.{m_(m)}", s1, ptr("primary", "models", m, "conditional_mue_not_preregistered", "mue"), "s3", POSTHOC) for m in MODELS4)
          + ".", ""]

    # ------------------------------------------------ reversed note
    rv = "RV"
    rob = "m1_random_intercepts_assumes_no_heterogeneity"
    L += ["## Phase 2: reversed note (registered as the reversed-note study)", "",
          f"**{REG_P}** (section 4). Test B = s(full) − s(reversed). Liars estimated by the registered fallback "
          "(per-category t-test) because the mixed model did not converge: "
          + C.expr("f2.fb", rv, "count_fallback", {"xs": [ptr("primary", m, "method") for m in MODELS4]}, "int", REG_P)
          + " of " + C.expr("f2.fbn", rv, "count", {"xs": [ptr("primary", m, "method") for m in MODELS4]}, "int", REG_P)
          + "; categories per liar " + C.json("f2.K", rv, ptr("primary", LLAMA, "K"), "int", REG_P) + ". Lies analysed: "
          + C.json("f2.n", rv, "/n_lies_analysed", "int", REG_P) + "; confessions excluded: "
          + C.json("f2.conf", rv, "/confessions_excluded", "int", REG_P) + ".", "",
          "| liar | label | B | SE | t | Holm alpha at the efficacy rejection | p, TOST | Holm alpha at the equivalence "
          "rejection |", "|---|---|---|---|---|---|---|---|"]
    for m in MODELS4:
        b = ptr("primary", m)
        qa = resolve(load(rv), b + "/equivalence_alpha_at_decision")
        ea = resolve(load(rv), b + "/efficacy_alpha_at_decision")
        L.append(f"| {NAME[m]} | " + C.json(f"f2.lab.{m_(m)}", rv, b + "/label", "str", REG_P) + " | "
                 + C.json(f"f2.B.{m_(m)}", rv, b + "/B", "s3", REG_P) + " | "
                 + C.json(f"f2.se.{m_(m)}", rv, b + "/B_se", "f3", REG_P) + " | "
                 + C.json(f"f2.t.{m_(m)}", rv, b + "/t", "f1", REG_P) + " | "
                 + (C.json(f"f2.al.{m_(m)}", rv, b + "/efficacy_alpha_at_decision", "alpha", REG_P) if ea is not None else "not rejected") + " | "
                 + C.json(f"f2.pt.{m_(m)}", rv, b + "/p_tost", "p", REG_P) + " | "
                 + (C.json(f"f2.qa.{m_(m)}", rv, b + "/equivalence_alpha_at_decision", "alpha", REG_P) if qa is not None else "not rejected")
                 + " |")
    L += ["",
          f"- **{REG_S}** (Test A = s(reversed) − s(placebo), section 5; registered as exploratory, no label) [95% CI], "
          "and the share of placebo lies with s = 0: "
          + "; ".join(f"{NAME[m]} " + C.json(f"f2.A.{m_(m)}", rv, ptr("test_A", m, "A"), "s3", REG_S) + " "
                      + C.json(f"f2.Aci.{m_(m)}", rv, ptr("test_A", m, "ci95"), "ci3s", REG_S) + ", "
                      + C.json(f"f2.Az.{m_(m)}", rv, ptr("test_A", m, "placebo_share_at_zero"), "pct", REG_S, scale=100)
                      for m in MODELS4) + ".",
          f"- **{REG_S}** (comprehension check, section 11a; cannot change a label): balanced accuracy [95% CI], "
          "comprehension holds: "
          + "; ".join(f"{NAME[m]} " + C.json(f"f2.ba.{m_(m)}", rv, ptr("comprehension", m, "balanced_accuracy"), "f3", REG_S) + " "
                      + C.json(f"f2.baci.{m_(m)}", rv, ptr("comprehension", m, "ci95", "balanced_accuracy"), "ci3", REG_S)
                      + ", " + C.json(f"f2.bah.{m_(m)}", rv, ptr("comprehension", m, "comprehension_holds"), "yn", REG_S)
                      for m in MODELS4) + ".",
          f"- **{REG_S}** (missing data, section 7): grader content-filter blocks for Gemma 3 27B by condition, placebo "
          + C.json("f2.blk.p", rv, ptr("balance_check", GEMMA, "blocks", "placebo"), "int", REG_S) + ", full "
          + C.json("f2.blk.f", rv, ptr("balance_check", GEMMA, "blocks", "full"), "int", REG_S) + ", reversed "
          + C.json("f2.blk.r", rv, ptr("balance_check", GEMMA, "blocks", "reversed"), "int", REG_S)
          + "; balance check p = " + C.json("f2.blkp", rv, ptr("balance_check", GEMMA, "p"), "p", REG_S)
          + ", flagged: " + C.json("f2.blkf", rv, ptr("balance_check", GEMMA, "flag"), "yn", REG_S)
          + ". Liars flagged: " + count_of("f2.blkn", rv, [ptr("balance_check", m, "flag") for m in MODELS4], REG_S) + ".",
          f"- **{REG_S}** (tipping point, section 7): missing cells "
          + ", ".join(f"{NAME[m]} " + C.json(f"f2.tpm.{m_(m)}", rv, ptr("tipping_point", m, "missing"), "int", REG_S) for m in MODELS4)
          + ". Reversals found by the scan on a grid of step "
          + C.json("f2.tpg", rv, ptr("tipping_point", LLAMA, "grid_step"), "f2", REG_S) + ": "
          + C.expr("f2.tpr", rv, "count_not_none", {"xs": [ptr("tipping_point", m, "delta") for m in MODELS4]}, "int", REG_S)
          + " (a scan, not a proof); worst case holds: "
          + count_of("f2.tpw", rv, [ptr("tipping_point", m, "worst_case_holds") for m in MODELS4], REG_S) + ".",
          f"- **{REG_S}** (robustness, section 4), random-intercepts model B and whether it converged: "
          + "; ".join(f"{NAME[m]} " + C.json(f"f2.m1.{m_(m)}", rv, ptr("robustness", rob, m, "B"), "s3", REG_S) + ", "
                      + C.json(f"f2.m1c.{m_(m)}", rv, ptr("robustness", rob, m, "converged"), "yn", REG_S) for m in MODELS4)
          + ". Where it did not converge the analysis makes no preservation claim; primary rejections preserved: "
          + count_of("f2.m1p", rv, [ptr("robustness", rob, m, "preserved", "all_primary_rejections_preserved") for m in MODELS4], REG_S)
          + ".",
          f"- **{REG_S}** (robustness, section 4), pooled gate (kappa "
          + C.json("f2.pk", rv, "/robustness/pooled_gate/kappa", "f3", REG_S) + "), B "
          + "; ".join(f"{NAME[m]} " + C.json(f"f2.pg.{m_(m)}", rv, ptr("robustness", "pooled_gate", "models", m, "B"), "s3", REG_S) for m in MODELS4)
          + "; primary rejections preserved: "
          + count_of("f2.pgp", rv, [ptr("robustness", "pooled_gate", "models", m, "preserved", "all_primary_rejections_preserved") for m in MODELS4], REG_S)
          + ". Non-viable lies excluded: preserved "
          + count_of("f2.nvp", rv, [ptr("robustness", "nonviable_excluded", m, "preserved", "all_primary_rejections_preserved") for m in MODELS4], REG_S)
          + ".",
          f"- **{REG_S}** (gpt-5 subsample, section 4, descriptive): B "
          + "; ".join(f"{NAME[m]} " + C.json(f"f2.g5.{m_(m)}", rv, ptr("robustness", "gpt5_subsample_descriptive", m, "est"), "s3", REG_S)
                      + " (" + C.json(f"f2.g5k.{m_(m)}", rv, ptr("robustness", "gpt5_subsample_descriptive", m, "K"), "int", REG_S) + " categories)"
                      for m in MODELS4) + ".",
          f"- **{REG_S}** (blinded permutation check, section 4a; " + C.json("f2.permn", "RVPERM", "/n", "int", REG_S)
          + " permutations): efficacy decisions in "
          + C.expr("f2.permlo", "RVPERM", "minimum_pct", {"xs": [ptr("efficacy_share", m) for m in MODELS4]}, "pct1", REG_S)
          + " to " + C.expr("f2.permhi", "RVPERM", "maximum_pct", {"xs": [ptr("efficacy_share", m) for m in MODELS4]}, "pct1", REG_S)
          + " of permutations per liar.",
          f"- **{EXPL}** (section 11): same-family minus other-family judge acceptance "
          + C.json("f2.fam", rv, "/exploratory/family_diagonal/same_minus_other", "s3", EXPL) + ".",
          f"- **{POSTHOC}** (after unblinding, owner's request): Llama 3.1 8B balanced accuracy on parseable answers "
          "only, " + C.json("f2.pc", "RVPC", ptr("models", LLAMA, "parsed_only", "balanced_accuracy"), "f3", POSTHOC) + " "
          + C.json("f2.pcci", "RVPC", ptr("models", LLAMA, "parsed_only", "ci95"), "ci3", POSTHOC) + ".",
          f"- **{POSTHOC}** (after unblinding, owner's request): Test B from the second grader's annotations, "
          + "; ".join(f"{NAME[m]} " + C.json(f"f2.gB.{m_(m)}", "RVG", ptr("models", m, "google", "B"), "s3", POSTHOC) for m in MODELS4)
          + "; primary rejections preserved: "
          + count_of("f2.gBp", "RVG", [ptr("models", m, "primary_rejections_preserved", "all_primary_rejections_preserved") for m in MODELS4], POSTHOC)
          + ". The second grader shares a family with the Gemma and Gemini liars.", ""]

    # ------------------------------------------------ phase 2
    st = "ST"
    sel = {LLAMA: str(resolve(load("PRL"), "/selected_layer")), GEMMA: str(resolve(load("PRG"), "/selected_layer"))}
    PR = {LLAMA: "PRL", GEMMA: "PRG"}; DG = {LLAMA: "DGL", GEMMA: "DGG"}; P2 = {LLAMA: "P2L", GEMMA: "P2G"}
    MC = {LLAMA: "MCL", GEMMA: "MCG"}; CO = {LLAMA: "COL", GEMMA: "COG"}; GS = {LLAMA: "GSL", GEMMA: "GSG"}
    L += ["## Phase 3: activation probe and steering (registered as \"Phase 2\")", "",
          "### Before the probe", "",
          f"- **{REG_S}** (identity check, section 2; completed and disclosed in the registration): hosted-minus-API "
          "difference in Test B on " + C.json("p.idk", "IDC", "/k", "int", REG_S) + " categories [90% CI], equivalent "
          "within the margin: Llama 3.1 8B "
          + C.json("p.idl", "IDC", ptr("models", LLAMA, "tests", "B", "diff"), "s3", REG_S) + " "
          + C.json("p.idlci", "IDC", ptr("models", LLAMA, "tests", "B", "ci90"), "ci3s", REG_S) + ", "
          + C.json("p.idle", "IDC", ptr("models", LLAMA, "tests", "B", "equivalent"), "yn", REG_S)
          + "; Gemma 3 27B with the official template "
          + C.json("p.idg", "IDC", ptr("models", GEMMA, "tests", "B", "diff"), "s3", REG_S) + " "
          + C.json("p.idgci", "IDC", ptr("models", GEMMA, "tests", "B", "ci90"), "ci3s", REG_S) + ", "
          + C.json("p.idge", "IDC", ptr("models", GEMMA, "tests", "B", "equivalent"), "yn", REG_S)
          + "; Gemma 3 27B with the provider's rendering "
          + C.json("p.idn", "IDN", ptr("models", GEMMA, "tests", "B", "diff"), "s3", REG_S) + " "
          + C.json("p.idnci", "IDN", ptr("models", GEMMA, "tests", "B", "ci90"), "ci3s", REG_S) + ", "
          + C.json("p.idne", "IDN", ptr("models", GEMMA, "tests", "B", "equivalent"), "yn", REG_S)
          + ". Phase 3 uses the renderings that were equivalent.",
          f"- **{REG_S}** (grading route, section 11): grades through the provider's API directly agreed with the earlier "
          "route with kappa " + C.json("p.grk", "GR", "/pooled_all_cues/kappa", "f3", REG_S) + " over "
          + C.json("p.grn", "GR", "/pooled_all_cues/labels", "int", REG_S) + " cue labels.", "",
          "### Probe gate", "",
          f"**{REG_P}** (section 4, gate and stop rule; Addendum 1).", "",
          "| model | gate | selected block | held-out personas AUROC | held-out wordings A / B / C |", "|---|---|---|---|---|"]
    for m in MODELS2:
        a = PR[m]; b = ptr("per_layer", sel[m])
        L.append(f"| {NAME[m]} | " + C.json(f"p.gate.{m_(m)}", a, "/gate", "str", REG_P) + " | "
                 + C.json(f"p.layer.{m_(m)}", a, "/selected_layer", "int", REG_P) + " | "
                 + C.json(f"p.hp.{m_(m)}", a, b + "/held_out_personas/auroc", "f3", REG_P) + " | "
                 + " / ".join(C.json(f"p.hw{s}.{m_(m)}", a, b + f"/held_out_wordings/{s}/auroc", "f3", REG_P) for s in "ABC") + " |")
    band = [ptr("permutation", sel[m], t, "inside_band") for m in MODELS2 for t in ("held_out_personas", "A", "B", "C")]
    L += ["",
          f"- **{REG_S}** (Addendum 3, before the pilot; stop rule): mean label-permutation null AUROC for held-out "
          "personas at the selected block, "
          + ", ".join(f"{NAME[m]} " + C.json(f"p.null.{m_(m)}", DG[m], ptr("permutation", sel[m], "held_out_personas", "null", "mean"), "f3", REG_S)
                      for m in MODELS2)
          + ". Null means inside the stop band at the selected blocks (four tests per model): "
          + " and ".join(count_of(f"p.band.{m_(m)}", DG[m], [ptr("permutation", sel[m], t, "inside_band") for t in ("held_out_personas", "A", "B", "C")], REG_S)
                         + f" ({NAME[m]})" for m in MODELS2) + ".",
          f"- **{REG_S}** (Addendum 3, descriptive): AUROC within each held-out persona at the selected block, minimum "
          "over the personas, "
          + ", ".join(f"{NAME[m]} " + C.json(f"p.wf.{m_(m)}", DG[m], ptr("within_fold", sel[m], "min_auroc"), "f3", REG_S)
                      for m in MODELS2) + ".", "",
          "### Stage 1: dose-finding pilot", "",
          f"- **{REG_S}** (alpha rule, section 6; Addendum 5): confirmatory alphas with the Addendum 5 placebo, Llama 3.1 "
          "8B H1 " + C.json("p.al.l1", "CA", "/confirmatory_alpha/llama-3.1-8b-instruct/H1", "f1", REG_S) + ", H2 "
          + C.json("p.al.l2", "CA", "/confirmatory_alpha/llama-3.1-8b-instruct/H2", "f1", REG_S) + "; Gemma 3 27B H1 "
          + C.json("p.al.g1", "CA", "/confirmatory_alpha/gemma-3-27b-it/H1", "f1", REG_S) + ", H2 "
          + C.json("p.al.g2", "CA", "/confirmatory_alpha/gemma-3-27b-it/H2", "f1", REG_S) + ". Under the retired placebo "
          "they had been Llama 3.1 8B H1 "
          + C.json("p.alr.l1", "CA", "/supersedes/confirmatory_alpha/llama-3.1-8b-instruct/H1", "f1", REG_S) + ", H2 "
          + C.json("p.alr.l2", "CA", "/supersedes/confirmatory_alpha/llama-3.1-8b-instruct/H2", "f1", REG_S) + "; Gemma 3 27B H1 "
          + C.json("p.alr.g1", "CA", "/supersedes/confirmatory_alpha/gemma-3-27b-it/H1", "f1", REG_S) + ", H2 "
          + C.json("p.alr.g2", "CA", "/supersedes/confirmatory_alpha/gemma-3-27b-it/H2", "f1", REG_S) + ".",
          f"- **{REG_S}** (Addendum 5): cosine of the placebo with v, retired placebo Gemma 3 27B "
          + C.json("p.cosold.g", "SU1G", "/prepare/cos_v_placebo", "f2", REG_S) + ", Llama 3.1 8B "
          + C.json("p.cosold.l", "SU1L", "/prepare/cos_v_placebo", "f2", REG_S) + "; new placebo Gemma 3 27B "
          + C.json("p.cosnew.g", "SPG", "/prepare/cos_v_placebo", "e1", REG_S) + ", Llama 3.1 8B "
          + C.json("p.cosnew.l", "SPL", "/prepare/cos_v_placebo", "e1", REG_S) + ".",
          f"- **{EXPL}** (pilot coherence measures, section 6): median perplexity ratio of steered lies under H1 by alpha "
          "(" + C.text("p.grid", "R3", "alpha in {0.25, 0.5, 1, 2, 4}", "0.25, 0.5, 1, 2, 4") + ", in order): "
          + "; ".join(f"{NAME[m]} " + " / ".join(C.json(f"p.pp.{m_(m)}.{g}", P2[m], f"/hypotheses/H1/grid/{g}/steered/ppl_ratio_median", "f2", EXPL)
                                               for g in ("0.25", "0.5", "1.0", "2.0", "4.0")) for m in MODELS2) + ".",
          f"- **{REG_S}** (method-check coherence before stage 2, Addendum 7; coherence only, nothing graded): median "
          "perplexity ratio of the method-check steered lies and coherence gate passed: "
          + "; ".join(f"{NAME[m]} " + C.json(f"p.mc.{m_(m)}", MC[m], "/mc_steered/ppl_ratio_median", "f2", REG_S) + ", "
                      + C.json(f"p.mcc.{m_(m)}", MC[m], "/coherent", "yn", REG_S) for m in MODELS2) + ".", "",
          "### Stage 2: steering", "",
          f"**{REG_P}** (section 7). Delta = mean over categories of s(steered) − s(placebo); Holm across the four tests "
          "in each family. Stage-2 coherence checks passed (steered and placebo arms, H1 and H2): "
          + " and ".join(count_of(f"s.coh.{m_(m)}", CO[m], [ptr(h, a, "passes") for h in ("H1", "H2") for a in ("steered", "placebo")], REG_P)
                         + f" ({NAME[m]})" for m in MODELS2) + ".", "",
          "| model | hypothesis | alpha | Delta [95% CI] | categories | p, efficacy | Holm alpha, efficacy | p, TOST | "
          "Holm alpha, TOST | method check passed | label |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in MODELS2:
        for h in ("H1", "H2"):
            b = ptr("primary", f"{m}|{h}")
            k = f"{m_(m)}.{h}"
            ea = resolve(load(st), b + "/efficacy_alpha_at_decision")
            qa = resolve(load(st), b + "/equivalence_alpha_at_decision")
            L.append(f"| {NAME[m]} | {h} | " + C.json(f"s.al.{k}", "CA", ptr("confirmatory_alpha", SLUG[m], h), "f1", REG_P) + " | "
                     + C.json(f"s.d.{k}", st, b + "/est", "s3", REG_P) + " "
                     + C.json(f"s.ci.{k}", st, b + "/ci95", "ci3s", REG_P) + " | "
                     + C.json(f"s.K.{k}", st, b + "/K", "int", REG_P) + " | "
                     + C.json(f"s.p.{k}", st, b + "/p_efficacy", "p", REG_P) + " | "
                     + (C.json(f"s.ea.{k}", st, b + "/efficacy_alpha_at_decision", "alpha", REG_P) if ea is not None else "not rejected") + " | "
                     + C.json(f"s.pt.{k}", st, b + "/p_tost", "p", REG_P) + " | "
                     + (C.json(f"s.qa.{k}", st, b + "/equivalence_alpha_at_decision", "alpha", REG_P) if qa is not None else "not rejected") + " | "
                     + C.json(f"s.mcp2.{k}", st, b + "/method_check_passed", "yn", REG_P) + " | "
                     + "**" + C.json(f"s.lab.{k}", st, b + "/label", "str", REG_P) + "** |")
    gen = [ptr("counts", k, "generation_failed") for k in load(st)["counts"]]
    sp = lambda m, h: ptr("google_subsample", "contrasts", f"{m}|{h}|steered-placebo")
    L += ["",
          f"- **{REG_P}** (method check, section 6 as redefined in Addendum 7; one-sided t at "
          + C.text("s.mcal", "R3A", "One-sided t (s rises) at 0.05.", "0.05") + "), d [95% CI] on "
          "the categories shown, one-sided p, passed: "
          + "; ".join(f"{NAME[m]} " + C.json(f"s.mc.{m_(m)}", st, ptr("method_check", m, "est"), "s3", REG_P) + " "
                      + C.json(f"s.mcci.{m_(m)}", st, ptr("method_check", m, "ci95"), "ci3s", REG_P) + " ("
                      + C.json(f"s.mck.{m_(m)}", st, ptr("method_check", m, "K"), "int", REG_P) + " categories), p = "
                      + C.json(f"s.mcp.{m_(m)}", st, ptr("method_check", m, "p_one_sided"), "p", REG_P) + ", "
                      + C.json(f"s.mcpass.{m_(m)}", st, ptr("method_check", m, "passed"), "yn", REG_P)
                      for m in MODELS2) + ".",
          f"- **{REG_S}** (section 7a, as amended by Addendum 8): cells generated and graded per model, "
          + "; ".join(f"{NAME[m]} " + C.json(f"s.gr.{m_(m)}", GS[m], "/graded", "int", REG_S) + ", grading failures after "
                      "" + C.text(f"s.att.{m_(m)}", "R3", "**after 3 attempts the cell is failed.**", "3") + " attempts " + C.json(f"s.grf.{m_(m)}", GS[m], "/primary_failed", "int", REG_S) for m in MODELS2)
          + "; generation failures, all models and arms: "
          + C.expr("s.genf", st, "total", {"xs": gen}, "int", REG_S) + ".",
          f"- **{REG_S}** (section 7a, balance check; a flag, not a gate): pooled over models under H1, p = "
          + C.json("s.bal.p", st, ptr("balance", "pooled|H1", "p"), "p", REG_S) + ", flagged: "
          + C.json("s.bal.f", st, ptr("balance", "pooled|H1", "flag"), "yn", REG_S) + " (grading failures: reference "
          + C.json("s.bal.r", st, ptr("balance", "pooled|H1", "failures", "reference"), "int", REG_S) + ", steered "
          + C.json("s.bal.s", st, ptr("balance", "pooled|H1", "failures", "steered"), "int", REG_S) + ", placebo "
          + C.json("s.bal.pl", st, ptr("balance", "pooled|H1", "failures", "placebo"), "int", REG_S) + "). Other balance "
          "checks flagged: "
          + count_of("s.bal.n", st, [ptr("balance", k, "flag") for k in (f"{m}|{h}" for m in MODELS2 for h in ("H1", "H2"))]
                     + [ptr("balance", "pooled|H2", "flag")], REG_S) + ".",
          f"- **{REG_S}** (section 7a, tipping point): missing steered or placebo cells "
          + "; ".join(f"{NAME[m]} {h} " + C.json(f"s.tpm.{m_(m)}.{h}", st, ptr("tipping_point", f"{m}|{h}", "missing"), "int", REG_S)
                      for m in MODELS2 for h in ("H1", "H2"))
          + ". Imputation values in the scan that change a label: "
          + C.expr("s.tpc", st, "count_not_none", {"xs": [ptr("tipping_point", f"{m}|H2", d) for m in MODELS2 for d in ("delta_against", "delta_for")]}, "int", REG_S)
          + ". Worst-case labels: "
          + "; ".join(f"{NAME[m]} H2 " + C.json(f"s.tpw.{m_(m)}", st, ptr("tipping_point", f"{m}|H2", "worst_case_label"), "str", REG_S) for m in MODELS2)
          + ".",
          f"- **{REG_S}** (section 8): the placebo arm's own shift against the hypothesis's unsteered reference [95% CI], "
          + "; ".join(f"{NAME[m]} {h} " + C.json(f"s.ps.{m_(m)}.{h}", st, ptr("placebo_shift", f"{m}|{h}", "est"), "s3", REG_S) + " "
                      + C.json(f"s.psci.{m_(m)}.{h}", st, ptr("placebo_shift", f"{m}|{h}", "ci95"), "ci3s", REG_S)
                      for m in MODELS2 for h in ("H1", "H2")) + ".",
          f"- **{REG_S}** (section 8): per-category SD of Delta, "
          + "; ".join(f"{NAME[m]} {h} " + C.json(f"s.sd.{m_(m)}.{h}", st, ptr("per_category_sd", f"{m}|{h}"), "f3", REG_S)
                      for m in MODELS2 for h in ("H1", "H2")) + ".",
          f"- **{REG_S}** (section 7, effect relative to the note): the note's own effect on the unsteered references, "
          "s(full) − s(reversed) [95% CI], "
          + "; ".join(f"{NAME[m]} " + C.json(f"s.ne.{m_(m)}", st, ptr("note_effect", m, "est"), "s3", REG_S) + " "
                      + C.json(f"s.neci.{m_(m)}", st, ptr("note_effect", m, "ci95"), "ci3s", REG_S) for m in MODELS2)
          + "; Delta as a share of it, "
          + "; ".join(f"{NAME[m]} {h} " + C.json(f"s.rel.{m_(m)}.{h}", st, ptr("effect_relative_to_note", f"{m}|{h}"), "pct", REG_S, scale=100)
                      for m in MODELS2 for h in ("H1", "H2")) + ".",
          f"- **{REG_S}** (section 7, naturalness): cosine of v with the full − reversed shift at the last prompt token "
          "on the evaluation categories (out of sample), "
          + "; ".join(f"{NAME[m]} " + C.json(f"s.nl.{m_(m)}", st, ptr("naturalness", m, "cos_last_token_evaluation"), "f3", REG_S) for m in MODELS2)
          + "; at the first generated token, "
          + "; ".join(f"{NAME[m]} " + C.json(f"s.nf.{m_(m)}", st, ptr("naturalness", m, "cos_first_generated_token"), "f2", REG_S) for m in MODELS2) + ".",
          f"- **{REG_S}** (section 10, blinded permutation check; " + C.json("s.permn", "PC2", "/n", "int", REG_S)
          + " permutations): efficacy decisions in "
          + C.expr("s.perm.lo", "PC2", "minimum_pct", {"xs": [ptr("shares", f"{m}|{h}", "efficacy") for m in MODELS2 for h in ("H1", "H2")]}, "pct1", REG_S)
          + " to "
          + C.expr("s.perm.hi", "PC2", "maximum_pct", {"xs": [ptr("shares", f"{m}|{h}", "efficacy") for m in MODELS2 for h in ("H1", "H2")]}, "pct1", REG_S)
          + " of permutations per test.",
          f"- **{REG_S}** (Addendum 2, descriptive; the second grader shares a family with Gemma): steered − placebo on "
          "the subsample cells, second grader versus primary grader on the same cells, "
          + "; ".join(f"{NAME[m]} {h} " + C.json(f"s.gg.{m_(m)}.{h}", st, sp(m, h) + "/google/est", "s3", REG_S)
                      + " versus " + C.json(f"s.gp.{m_(m)}.{h}", st, sp(m, h) + "/primary_same_cells/est", "s3", REG_S)
                      for m in MODELS2 for h in ("H1", "H2"))
          + ". Per-cue kappa over all cues, "
          + "; ".join(f"{NAME[m]} " + C.json(f"s.gk.{m_(m)}", st, ptr("google_subsample", "agreement", m, "kappa_all_cues"), "f2", REG_S) for m in MODELS2)
          + ". Lies graded by the second grader: "
          + "; ".join(f"{NAME[m]} " + C.json(f"s.gn.{m_(m)}", GS[m], "/google_graded", "int", REG_S) for m in MODELS2) + ".",
          f"- **{REG_S}** (section 9, Llama dissociation, descriptive; Gemma alongside): held-out-persona probe AUROC at "
          "the selected block beside the registered comprehension balanced accuracy of Phase 2, "
          + "; ".join(f"{NAME[m]} " + C.json(f"s.s9.au.{m_(m)}", PR[m], ptr("per_layer", sel[m], "held_out_personas", "auroc"), "f3", REG_S)
                      + " and " + C.json(f"s.s9.ba.{m_(m)}", "RV", ptr("comprehension", m, "balanced_accuracy"), "f3", REG_S) for m in MODELS2)
          + "; Llama 3.1 8B on parseable answers only (" + POSTHOC + "), "
          + C.json("s.s9.pc", "RVPC", ptr("models", LLAMA, "parsed_only", "balanced_accuracy"), "f3", POSTHOC) + ".",
          f"- **{EXPL}** (section 9): the SAE-feature and MLP-neuron alignment analyses have not been run.", ""]
    return L


# ================================================================== FIGURES

COL = {LLAMA: "#4e79a7", GEMMA: "#f28e2b", GPT: "#e15759", GEMINI: "#76b7b2"}
RC = {"font.family": "serif", "font.serif": ["ET Book", "Palatino", "Palatino Linotype", "Georgia", "DejaVu Serif"],
      "font.size": 12, "figure.facecolor": "#fffff8", "axes.facecolor": "#fffff8", "savefig.facecolor": "#fffff8",
      "figure.dpi": 150, "axes.edgecolor": "#cccccc", "axes.linewidth": 0.5, "axes.labelcolor": "#666666",
      "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False, "xtick.color": "#999999",
      "ytick.color": "#999999", "xtick.labelsize": 11, "ytick.labelsize": 11, "xtick.direction": "in",
      "ytick.direction": "in", "xtick.major.size": 3, "ytick.major.size": 3, "xtick.major.width": 0.5,
      "ytick.major.width": 0.5, "lines.linewidth": 1.5, "savefig.bbox": "tight", "savefig.pad_inches": 0.25}
matplotlib.rcdefaults()     # ignore any machine's matplotlibrc (one here set text.hinting); the style is all in RC
plt.rcParams.update(RC)
# Draw with matplotlib's bundled fonts only (DejaVu Serif and Sans; the preferred serifs above are rarely installed):
# system fonts differ between machines and change text metrics, so the PNGs would not be byte-identical elsewhere.
from matplotlib import font_manager as _fm
_fm.fontManager.ttflist = [f for f in _fm.fontManager.ttflist if "mpl-data" in f.fname.replace("\\", "/")]


def short(alias):
    return sha256(alias)[:12]


def titles(fig, title, sub, y=1.0):
    fig.text(0.01, y + 0.075, title, fontsize=17, color="#111111", ha="left", va="bottom")
    fig.text(0.01, y + 0.065, sub, fontsize=11.5, color="#666666", ha="left", va="top")


def note(fig, text, y=-0.03):
    fig.text(0.01, y, text, fontsize=8.5, color="#999999", ha="left", va="top", fontfamily="sans-serif")


def s_axis_limits():
    lv = load("LV")
    vals = [x for m in lv["reversed_note"]["levels"].values() for c in m.values() for x in c["ci95"]]
    vals += [x for m in lv["phase2_stage2"]["levels"].values() for c in m.values() for x in c["ci95"]]
    return (np.floor(min(vals) * 10) / 10, np.ceil(max(vals) * 10) / 10)


def const(alias, quote, value):
    """A registration constant used in figure text: the quote must be in the registration (as in Claims.text)."""
    assert quote in load(alias) and value in quote, (alias, quote)
    return value


S_TICKS = np.arange(0, 1.01, 0.2)


def fmt_p(x):
    return "< 0.001" if x < 0.001 else f"{x:#.2g}"


def fig1():
    rep = load("S1")
    P = rep["primary"]["models"]
    fig, ax = plt.subplots(figsize=(9, 5.6))
    ys = {m: len(MODELS4) - i for i, m in enumerate(MODELS4)}
    for m in MODELS4:
        p = P[m]; mm = rep["mixed_model"][m]; y = ys[m]
        ax.plot(p["ci95_naive"], [y + 0.14] * 2, color=COL[m], lw=2.2, solid_capstyle="butt")
        ax.plot([p["mean_lift"]], [y + 0.14], "o", color=COL[m], ms=5.5)
        ax.plot(mm["ci95"], [y - 0.14] * 2, color=COL[m], lw=1.4, alpha=0.6, ls=(0, (4, 2)))
        ax.plot([mm["intercept"]], [y - 0.14], "o", mfc="#fffff8", mec=COL[m], ms=5.5)
        ax.text(p["ci95_naive"][1] + 0.012, y + 0.14, f"naive  {p['mean_lift']:+.3f}", va="center", fontsize=10.5, color="#333333")
        ax.text(mm["ci95"][1] + 0.012, y - 0.14, f"mixed model  {mm['intercept']:+.3f}", va="center", fontsize=10.5, color="#666666")
        ax.text(-0.02, y, f"{NAME[m]}\nn = {p['n_units']} units", ha="right", va="center", fontsize=12, color=COL[m])
    ax.axvline(0, color="#cccccc", lw=0.8)
    ax.text(0.004, 0.47, "no lift", fontsize=9.5, color="#999999", style="italic")
    ax.set_yticks([]); ax.spines["left"].set_visible(False)
    hi = max(max(rep["mixed_model"][m]["ci95"][1], P[m]["ci95_naive"][1]) for m in MODELS4)
    top = np.ceil(hi * 10) / 10
    ax.set_xlim(-0.005, top + 0.22); ax.set_ylim(0.45, len(MODELS4) + 0.55)
    ax.spines["bottom"].set_bounds(0, top); ax.set_xticks(np.arange(0, top + 0.001, 0.1))
    ax.set_xlabel("lift: s(full) − s(placebo), share of the target's note-named cues")
    looks = sorted({P[m]["look"] for m in MODELS4}); decs = sorted({P[m]["decision"] for m in MODELS4})
    allpos = all(P[m]["ci95_naive"][0] > 0 for m in MODELS4)
    titles(fig, "Lift above zero for every liar: more of the target's named cues under the full note than under the placebo"
           if allpos else "Lift of the full over the placebo note, per liar",
           f"Phase 1, {' / '.join(looks)} look. Point and 95% CI per liar: naive mean (registered estimate, solid) and\n"
           "mixed model d ~ 1 + (1 | prompt) (registered robustness, dashed)", y=1.02)
    note(fig, f"Source: results/perfect_lie/final_analysis/final_report.json (sha256 {short('S1')}…).\nRegistered primary "
              f"test: group-sequential Z with Holm across liars. Decisions: {', '.join(decs)} "
              f"({sum(P[m]['decision'] == decs[0] for m in MODELS4)} of {len(MODELS4)}), at the {' / '.join(looks)} look.")
    fig.savefig(FIG / "fig1_study1_lift.png"); plt.close(fig)


def fig2():
    lv = load("LV")["reversed_note"]["levels"]; rep = load("RV")
    ylo, yhi = s_axis_limits()
    fig, axes = plt.subplots(1, 4, figsize=(13, 5.4), sharey=True, gridspec_kw={"wspace": 0.12})
    conds = ["placebo", "reversed", "full"]
    for ax, m in zip(axes, MODELS4):
        y = [lv[m][c]["mean"] for c in conds]
        lo = [lv[m][c]["ci95"][0] for c in conds]; hi = [lv[m][c]["ci95"][1] for c in conds]
        x = np.arange(3)
        ax.plot(x, y, color=COL[m], lw=1.6)
        ax.vlines(x, lo, hi, color=COL[m], lw=2.2)
        ax.plot(x, y, "o", color=COL[m], ms=5)
        A = rep["test_A"][m]; B = rep["primary"][m]
        ax.text(0.4, max(hi[0], hi[1]) + 0.05, f"A {A['A']:+.3f}\n[{A['ci95'][0]:+.3f}, {A['ci95'][1]:+.3f}]",
                ha="center", va="bottom", fontsize=9, color="#555555", style="italic")
        ax.text(1.55, (y[1] + y[2]) / 2 - 0.03, f"B {B['B']:+.3f}\n(SE {B['B_se']:.3f})\n{B['label']}",
                ha="left", va="top", fontsize=9, color="#333333", style="italic")
        ax.set_xticks(x); ax.set_xticklabels(conds, fontsize=10)
        ax.set_title(NAME[m], loc="left", fontsize=13, color=COL[m])
        ax.set_ylim(ylo, yhi); ax.set_yticks(S_TICKS[S_TICKS <= yhi + 1e-9])
        ax.spines["bottom"].set_bounds(0, 2); ax.set_xlim(-0.35, 2.75)
    axes[0].set_ylabel("s, share of the target's scorable cues present")
    labs = sorted({rep["primary"][m]["label"] for m in MODELS4})
    K = sorted({lv[m][c]["K"] for m in MODELS4 for c in conds})
    allB = all(rep["primary"][m]["B"] > 0 for m in MODELS4)
    titles(fig, (f"Test B, full − reversed, was positive for every liar (labels: {', '.join(labs)})" if allB
                 else f"Test B, full − reversed, per liar (labels: {', '.join(labs)})"),
           f"Phase 2 (reversed note): s by note, mean over {'/'.join(map(str, K))} categories with a 95% t interval. "
           "A = reversed − placebo (registered secondary); B = full − reversed (registered primary)", y=0.98)
    note(fig, f"Sources: results/perfect_lie_reversed/final_analysis/final_report.json (sha256 {short('RV')}…) for A and B; "
              f"levels (post hoc, descriptive) from writeup/derived/levels.json (sha256 {short('LV')}…),\nderived from the "
              "committed records with the registered scoring code. Same s axis as figure 3.")
    fig.savefig(FIG / "fig2_reversed_levels.png"); plt.close(fig)


def fig3():
    lv = load("LV")["phase2_stage2"]["levels"]; st = load("ST"); ca = load("CA")["confirmatory_alpha"]
    ylo, yhi = s_axis_limits()
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.4), sharey=True, gridspec_kw={"hspace": 0.55, "wspace": 0.12})
    spec = {"H1": ("ref_reversed|None", "reversed", "ref_full|None", "full", "+"),
            "H2": ("ref_full|None", "full", "ref_reversed|None", "reversed", "−")}
    for i, m in enumerate(MODELS2):
        for j, h in enumerate(("H1", "H2")):
            ax = axes[i, j]
            ref, nt, opp, opp_nt, sign = spec[h]
            pts = [lv[m][ref], lv[m][f"placebo|{h}"], lv[m][f"steered|{h}"]]
            x = np.arange(3)
            ax.axhline(lv[m][opp]["mean"], xmin=0, xmax=1, color=COL[m], lw=1.2, alpha=0.3)
            ax.text(2.25, lv[m][opp]["mean"], f"unsteered,\n{opp_nt} note", fontsize=8.5, color="#999999", va="center")
            for xi, p, mk in zip(x, pts, ("o", "s", "D")):
                a = 1 if xi == 2 else 0.55
                ax.vlines(xi, p["ci95"][0], p["ci95"][1], color=COL[m], lw=2.2, alpha=a)
                ax.plot(xi, p["mean"], mk, color=COL[m], ms=5.5, alpha=a)
            d = st["primary"][f"{m}|{h}"]
            txt = f"Δ {d['est']:+.3f} [{d['ci95'][0]:+.3f}, {d['ci95'][1]:+.3f}]\n{d['label']}"
            data_hi = max(max(p["ci95"][1] for p in pts), lv[m][opp]["mean"])
            top = data_hi < ylo + 0.62 * (yhi - ylo)
            ax.text(0.02, 0.97 if top else 0.03, txt, transform=ax.transAxes, va="top" if top else "bottom",
                    fontsize=9.5, style="italic", color="#333333" if d["label"] == "steerable" else "#777777")
            ax.set_xticks(x); ax.set_xticklabels([f"unsteered\n({nt} note)", "placebo", "steered"], fontsize=10)
            ax.set_title(f"{NAME[m]}   {h}: {nt} note {sign} α·v, α {ca[SLUG[m]][h]:g}", loc="left", fontsize=11.5,
                         color=COL[m])
            ax.set_ylim(ylo, yhi); ax.set_yticks(S_TICKS[S_TICKS <= yhi + 1e-9])
            ax.spines["bottom"].set_bounds(0, 2); ax.set_xlim(-0.35, 3.0)
    fig.supylabel("s, share of the target's scorable cues present", x=0.06, fontsize=12, color="#666666")
    K = sorted({lv[m][k]["K"] for m in MODELS2 for k in lv[m] if not k.startswith("mc_")})
    titles(fig, "Phase 3 steering: s by arm under each hypothesis",
           f"Stage 2: mean over {'/'.join(map(str, K))} evaluation categories with a 95% t interval. Faint line: the "
           "opposite note's unsteered level.\nΔ = steered − placebo and the registered label (registered primary).",
           y=0.93)
    note(fig, f"Sources: results/phase2/stage2/stage2_result.json (sha256 {short('ST')}…) for Δ and labels; levels "
              f"(post hoc, descriptive) from writeup/derived/levels.json\n(sha256 {short('LV')}…). Same s axis as figure 2.",
         y=0.04)
    fig.savefig(FIG / "fig3_steering_levels.png"); plt.close(fig)


def fig4():
    st = load("ST")
    a_mc = const("R3", "added at alpha = 1", "1")
    a_t = const("R3A", "One-sided t (s rises) at 0.05.", "0.05")
    fig, ax = plt.subplots(figsize=(9, 4.4))
    hi = 0
    for i, m in enumerate(MODELS2):
        mc = st["method_check"][m]
        lb = mc["est"] - stats.t.ppf(0.95, mc["df"]) * mc["se"]
        hi = max(hi, mc["ci95"][1])
    right = np.ceil(hi * 20) / 20 + 0.1
    for i, m in enumerate(MODELS2):
        mc = st["method_check"][m]
        lb = mc["est"] - stats.t.ppf(0.95, mc["df"]) * mc["se"]
        y = len(MODELS2) - i
        ax.annotate("", xy=(right, y), xytext=(lb, y), arrowprops=dict(arrowstyle="-|>", color=COL[m], lw=2, alpha=0.8))
        ax.plot([lb, lb], [y - 0.06, y + 0.06], color=COL[m], lw=2)
        ax.plot(mc["est"], y, "o", color=COL[m], ms=7)
        verdict = "passed" if mc["passed"] else "failed"
        ax.text(lb, y + 0.2, f"d {mc['est']:+.3f}; one-sided 95% lower bound {lb:+.3f}; p = {fmt_p(mc['p_one_sided'])}: "
                f"{verdict}", fontsize=10, color="#333333" if mc["passed"] else "#777777", style="italic")
        ax.text(-0.075, y, f"{NAME[m]}\n{mc['K']} categories", ha="right", va="center", fontsize=12, color=COL[m])
    ax.axvline(0, color="#999999", lw=0.8)
    ax.text(0.002, 0.55, "no change in s", fontsize=9.5, color="#999999", style="italic")
    ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.set_xlim(-0.07, right + 0.01); ax.set_ylim(0.4, len(MODELS2) + 0.6)
    ax.set_xlabel("d = s(steered along v_fp,t) − s(its placebo), mean over categories")
    res = "; ".join(f"{NAME[m]} {'passed' if st['method_check'][m]['passed'] else 'failed'}" for m in MODELS2)
    titles(fig, f"Method check (registered primary): {res}",
           f"Phase 3, Addendum 7: per-target v_fp,t at alpha {a_mc} under the placebo note. Point and one-sided 95% "
           f"interval (arrow: no upper bound);\nregistered test: one-sided t at {a_t}, against 0", y=1.0)
    note(fig, f"Source: results/phase2/stage2/stage2_result.json (sha256 {short('ST')}…). Under the registration "
              "(section 7), a failed method check makes a model's null labels inconclusive.")
    fig.savefig(FIG / "fig4_method_check.png"); plt.close(fig)


def captions():
    L = ["# Figures", ""]
    GS2 = {LLAMA: "GSL", GEMMA: "GSG"}
    s1 = "S1"
    L += ["**Figure 1** (`figures/fig1_study1_lift.png`). Phase 1: lift s(full) − s(placebo) per liar with two 95% "
          "intervals, the naive mean (the registered estimate; " + REG_P + ") and the mixed model "
          "`d ~ 1 + (1 | prompt)` (" + REG_S + ", robustness). Units: "
          + ", ".join(f"{NAME[m]} " + C.json(f"c1.n.{m_(m)}", s1, ptr("primary", "models", m, "n_units"), "int", REG_P) for m in MODELS4)
          + ". Test: group-sequential Z with Holm across the four liars; decision and look, "
          + "; ".join(f"{NAME[m]} " + C.json(f"c1.dec.{m_(m)}", s1, ptr("primary", "models", m, "decision"), "str", REG_P) + ", "
                      + C.json(f"c1.look.{m_(m)}", s1, ptr("primary", "models", m, "look"), "str", REG_P) for m in MODELS4)
          + ". "
          f"Source: `{SOURCES['S1']}`, sha256 `{sha256('S1')}`.", ""]
    L += ["**Figure 2** (`figures/fig2_reversed_levels.png`). Phase 2 (reversed note): s by note per liar, as the mean over "
          "categories of per-category means with a 95% t interval (" + POSTHOC + ", derived from the committed records "
          "with the registered scoring code). Annotated: Test A = reversed − placebo (" + REG_S + ") and Test B = full − "
          "reversed (" + REG_P + "; per-category t-test, the registered fallback, Holm across four). Lies analysed: "
          + C.json("c2.n", "RV", "/n_lies_analysed", "int", REG_P) + ". Sources: `" + SOURCES["RV"] + "`, sha256 `"
          + sha256("RV") + "`; `" + SOURCES["LV"] + "`, sha256 `" + sha256("LV") + "`.", ""]
    L += ["**Figure 3** (`figures/fig3_steering_levels.png`). Phase 3 stage 2: s by arm per model and hypothesis, mean "
          "over the evaluation categories with a 95% t interval (" + POSTHOC + "); the faint line is the opposite note's "
          "unsteered level. Annotated: Delta = steered − placebo with its 95% CI and the registered label (" + REG_P
          + "; two-sided t on the categories with Holm across four, TOST with Holm). Lies per model: "
          + "; ".join(f"{NAME[m]} " + C.json(f"c3.n.{m_(m)}", GS2[m], "/graded", "int", REG_S) for m in MODELS2)
          + ". Sources: `" + SOURCES["ST"] + "`, sha256 `" + sha256("ST")
          + "`; `" + SOURCES["LV"] + "`, sha256 `" + sha256("LV") + "`.", ""]
    L += ["**Figure 4** (`figures/fig4_method_check.png`). Phase 3 method check (Addendum 7): d = s(steered along "
          "v_fp,t) − s(its placebo), mean over categories, with the one-sided 95% interval (" + REG_P + "; one-sided t "
          "at " + C.text("c4.al", "R3A", "One-sided t (s rises) at 0.05.", "0.05") + "). One-sided lower bounds: "
          + "; ".join(f"{NAME[m]} " + C.expr(f"c4.lb.{m_(m)}", "ST", "lb95_onesided",
                                            {"est": ptr("method_check", m, "est"), "se": ptr("method_check", m, "se"),
                                             "df": ptr("method_check", m, "df")}, "s3", REG_P)
                      + " on " + C.json(f"c4.K.{m_(m)}", "ST", ptr("method_check", m, "K"), "int", REG_P) + " categories"
                      + ", passed: " + C.json(f"c4.pass.{m_(m)}", "ST", ptr("method_check", m, "passed"), "yn", REG_P)
                      for m in MODELS2)
          + ". Source: `" + SOURCES["ST"] + "`, sha256 `" + sha256("ST") + "`.", ""]
    return L


# ================================================================== assemble

def write_section(name, lines, rows, spans_all):
    raw = "\n".join(lines) + "\n"
    clean, spans = strip_markers(raw)
    (HERE / name).write_text(clean)
    spans_all[name] = spans
    by_id = {c["id"]: c for c in C.items}
    for start, end, cid in spans:
        ls = clean.rfind("\n", 0, start) + 1
        le = clean.find("\n", end)
        by_id[cid]["sentence"] = clean[ls:le if le >= 0 else None]
        by_id[cid]["file"] = name
        by_id[cid]["offset"] = start - ls
        rows.append(cid)


PHASES = [  # WWIL phase, question, registered name, tag, release date (the GitHub release of the tag)
    ("Phase 1", "finds the effect: full vs placebo note", "study 1", "perfect-lie-prereg-v1", "2026-10-06"),
    ("Phase 2", "why one path rather than another: full vs reversed note", "the reversed-note study",
     "perfect-lie-reversed-prereg-v1", "2026-10-15"),
    ("Phase 3", "probes causality: activation probe and steering", "\"Phase 2\"", "perfect-lie-phase2-prereg-v1",
     "2026-10-22"),
]
SECTIONS = HERE / "sections"


def _split(text):
    """A generated section file -> (preamble lines, {heading: body lines}) at its '## ' headings."""
    pre, parts, cur = [], {}, None
    for line in text.rstrip("\n").split("\n")[1:]:              # drop the file's '# Title'
        if line.startswith("## "):
            cur = line[3:]; parts[cur] = []
        elif cur is None:
            pre.append(line)
        else:
            parts[cur].append(line)
    return pre, parts


def paper(methods_text, findings_text, figures_text):
    """PAPER.md: the owner's sections (sections/*.md, verbatim) around the generated Methods, Findings and figure
    captions, which appear verbatim (headings one level down) in the WWIL phase order. No number is added here."""
    owner = {p.stem: p.read_text().rstrip("\n") for p in sorted(SECTIONS.glob("*.md"))}
    m_pre, m = _split(methods_text)
    f_pre, f = _split(findings_text)
    caps = {ln.split("**")[1]: ln for ln in figures_text.split("\n") if ln.startswith("**Figure ")}
    figs = {"Phase 1": ["Figure 1"], "Phase 2": ["Figure 2"], "Phase 3": ["Figure 3", "Figure 4"]}
    files = {"Figure 1": "fig1_study1_lift.png", "Figure 2": "fig2_reversed_levels.png",
             "Figure 3": "fig3_steering_levels.png", "Figure 4": "fig4_method_check.png"}
    demote = lambda ls: [("#" + x) if x.startswith("###") else x for x in ls]
    L = [owner["00_title"], "", owner["01_motivation_perfect_lie"], "", owner["02_wwil_introduction"], "",
         "## The three phases", "",
         "| phase | question | registered as | registration (dated GitHub release) |", "|---|---|---|---|"]
    L += [f"| {ph} | {q} | {reg} | [`{tag}`](https://github.com/RandallSPQR/edsl_wwil/releases/tag/{tag}), {d} |"
          for ph, q, reg, tag, d in PHASES]
    L += ["", "## Methods common to all phases", ""] + [x for x in m_pre if x.strip()] + [""]
    L += m["Shared instrument"] + [""]
    L += [x for x in f_pre if x.strip()] + [""]
    for ph in ("Phase 1", "Phase 2", "Phase 3"):
        mk = next(k for k in m if k.startswith(ph + ":"))
        fk = next(k for k in f if k.startswith(ph + ":"))
        L += [f"## {mk}", "", "### Methods", ""] + demote(m[mk]) + ["", "### Findings", ""] + demote(f[fk]) + [""]
        for fg in figs[ph]:
            L += [f"![{fg}](figures/{files[fg]})", "", caps[fg], ""]
    L += [owner["03_discussion"], "",
          "---", "",
          "Every number in the Methods, Findings and figure captions above is generated from the committed results files "
          "and listed with its source in `CLAIMS_MANIFEST.csv`; `check_claims.py` verifies them. The author's sections "
          "(`sections/`) are not checked."]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(L)) + "\n"


def main():
    FIG.mkdir(exist_ok=True)
    rows, spans = [], {}
    write_section("METHODS.md", methods(), rows, spans)
    write_section("FINDINGS.md", findings(), rows, spans)
    write_section("FIGURES.md", captions(), rows, spans)
    (HERE / "PAPER.md").write_text(paper(*((HERE / n).read_text() for n in ("METHODS.md", "FINDINGS.md", "FIGURES.md"))))
    fig1(); fig2(); fig3(); fig4()
    by_id = {c["id"]: c for c in C.items}
    with open(HERE / "CLAIMS_MANIFEST.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["claim_id", "sentence", "value", "source_file", "file_sha256", "json_path", "label", "text_file",
                    "offset_in_sentence"])
        for cid in rows:
            c = by_id[cid]
            w.writerow([cid, c["sentence"], c["value"], SOURCES[c["alias"]], sha256(c["alias"]), c["path"], c["label"], c["file"],
                        c["offset"]])
    print(f"{len(rows)} claims; figures in {FIG}")


if __name__ == "__main__":
    main()
