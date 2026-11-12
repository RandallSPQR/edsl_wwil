# Tier 0 report

**PASS** in 27.1 min (4 CPUs, Linux-6.18.44-fc-v185-x86_64-with-glibc2.39, Python 3.11.15).

Rebuilt files: 38 identical, 0 numerically equal, 4 equal, 0 DIFFERENT, 0 MISSING.

| step | what | seconds | outputs |
|---|---|---|---|
| s1.final | Study 1: registered final analysis (sections 4-8, Addenda 1-3) | 12.4 | `final_report.json` identical; `final_report.md` identical |
| s1.gpt5 | Study 1: post hoc, gpt-5 subsample units scored by the primary grader | 1.6 | `gpt5_same_units.json` identical |
| rv.final | Reversed note: registered final analysis (sections 4, 5, 7, 11a, 11) | 570.1 | `final_report.json` identical; `final_report.md` identical |
| rv.perm_chunk | Reversed note: blinded permutation check, sample chunks recomputed and compared | 911.0 | ok |
| rv.perm | Reversed note: permutation check assembled from its 20 chunks (section 4a) | 9.6 | `perm_check.json` identical |
| rv.posthoc_comp | Reversed note: post hoc, comprehension on parseable answers | 6.0 | `posthoc_comprehension_parsed.json` identical |
| rv.posthoc_google | Reversed note: post hoc, Test B from the Google grader | 26.4 | `posthoc_google_testB.json` equal; only the recorded environment differs (/environment/python 3.11.17 -> 3.11.15); `posthoc_google_testB.md` identical |
| p2.identity | Phase 2: identity check, behavioral equivalence (section 2) | 6.3 | `behavioral_result.json` equal; current code adds variant (950e8a7 added --variant after this result (2c8111c) was written) |
| p2.identity_novita | Phase 2: identity check, Gemma template re-test | 5.5 | `behavioral_result_novita.json` identical |
| p2.route | Phase 2: grading-route check summary from its stored labels (section 11) | 3.0 | `regrade_direct.json` identical |
| p2.pilot.llama-3.1-8b-instruct | Phase 2: stage-1 pilot coherence, meta-llama/llama-3.1-8b-instruct (section 6, Addendum 4) | 0.7 | `llama-3.1-8b-instruct/pilot_result.json` identical; `llama-3.1-8b-instruct/PILOT.md` identical |
| p2.pilot.gemma-3-27b-it | Phase 2: stage-1 pilot coherence, google/gemma-3-27b-it (section 6, Addendum 4) | 0.9 | `gemma-3-27b-it/pilot_result.json` identical; `gemma-3-27b-it/PILOT.md` identical |
| p2.pilot2.llama-3.1-8b-instruct | Phase 2: pilot with the Addendum 5 placebo, meta-llama/llama-3.1-8b-instruct | 0.8 | `llama-3.1-8b-instruct/pilot2_result.json` identical; `llama-3.1-8b-instruct/PILOT2.md` identical |
| p2.pilot2.gemma-3-27b-it | Phase 2: pilot with the Addendum 5 placebo, google/gemma-3-27b-it | 0.8 | `gemma-3-27b-it/pilot2_result.json` identical; `gemma-3-27b-it/PILOT2.md` identical |
| p2.alphas | Phase 2: confirmatory alphas from the two pilots (alpha rule, section 6) | 0.0 | `confirmatory_alphas.json` identical |
| p2.mc.llama-3.1-8b-instruct | Phase 2: method-check coherence pre-check, meta-llama/llama-3.1-8b-instruct (Addendum 7) | 0.4 | `llama-3.1-8b-instruct/mc_precheck.json` identical; `llama-3.1-8b-instruct/MC_PRECHECK.md` identical |
| p2.mc.gemma-3-27b-it | Phase 2: method-check coherence pre-check, google/gemma-3-27b-it (Addendum 7) | 0.4 | `gemma-3-27b-it/mc_precheck.json` identical; `gemma-3-27b-it/MC_PRECHECK.md` identical |
| p2.coherence | Phase 2: stage-2 coherence gate and grading summaries (sections 6, 7a) | 1.7 | `llama-3.1-8b-instruct/coherence.json` equal; current code adds n_complete, generation_failed (Addendum 8 (f4a70a7) added these counts after this file (8e66e71) was written; 0 failures); `llama-3.1-8b-instruct/grading_summary.json` identical; `gemma-3-27b-it/coherence.json` equal; current code adds n_complete, generation_failed (Addendum 8 (f4a70a7) added these counts after this file (8e66e71) was written; 0 failures); `gemma-3-27b-it/grading_summary.json` identical |
| p2.permcheck | Phase 2: blinded permutation check (section 10) | 19.4 | `permutation_check.json` identical |
| p2.analyse | Phase 2: registered stage-2 analysis (sections 7, 7a, 8, 9; Addendum 2) | 20.2 | `stage2_result.json` identical; `STAGE2.md` identical |
| w.levels | Write-up: descriptive levels for figures 2 and 3 | 8.7 | `levels.json` identical |
| w.build | Write-up: Methods, Findings, captions, figures, claims manifest | 4.3 | `METHODS.md` identical; `FINDINGS.md` identical; `FIGURES.md` identical; `CLAIMS_MANIFEST.csv` identical; `fig1_study1_lift.png` identical; `fig2_reversed_levels.png` identical; `fig3_steering_levels.png` identical; `fig4_method_check.png` identical |
| w.check | Write-up: claims check (every manifest value against the rebuilt sources) | 10.0 | `check_output.txt` identical |

Inputs carried over (not CPU-derivable), verified by sha256:

- `two_truths_lie/results/phase2/probe/gemma-3-27b-it/probe_result.json`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/probe/gemma-3-27b-it/vectors.npz`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/probe/gemma-3-27b-it/diagnostics.json`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/probe/gemma-3-27b-it/scale.json`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/probe/llama-3.1-8b-instruct/probe_result.json`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/probe/llama-3.1-8b-instruct/vectors.npz`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/probe/llama-3.1-8b-instruct/diagnostics.json`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/probe/llama-3.1-8b-instruct/scale.json`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/pilot/llama-3.1-8b-instruct/setup.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/pilot/llama-3.1-8b-instruct/setup_placebo2.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/pilot/llama-3.1-8b-instruct/mc_precheck_setup.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/pilot/gemma-3-27b-it/setup.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/pilot/gemma-3-27b-it/setup_placebo2.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/pilot/gemma-3-27b-it/mc_precheck_setup.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/stage2/llama-3.1-8b-instruct/setup.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/stage2/llama-3.1-8b-instruct/natural.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/stage2/gemma-3-27b-it/setup.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/stage2/gemma-3-27b-it/natural.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/identity_check/pod_run/records.jsonl`: sha256 ok (Tier 3 (GPU) generation, Tier 1 (API) grading)
- `two_truths_lie/results/phase2/identity_check/pod_run_novita/records.jsonl`: sha256 ok (Tier 3 (GPU) generation, Tier 1 (API) grading)
- `two_truths_lie/results/perfect_lie/interim_look/interim_blind.json`: sha256 ok (frozen at the interim by registration (section 6); the final analysis recomputes the gate and checks it matches)
- `two_truths_lie/results/perfect_lie_reversed/final_analysis/perm_chunks`: sha256 ok (decision counts per chunk; Tier 0 recomputes a sample (rv.perm_chunk), make reproduce-full all)

Claims check output (head and tail; in full in the work tree's `writeup/check_output.txt`):

```
claims checked: 446
by label: design constant (registration) 36; exploratory 14; post hoc (descriptive) 17; registered primary 151; registered secondary 228
sources (32), sha256 verified:
  e728effbf3db6bffc4e28469a7f1301244ed524ecfe8f684d2f341ab996e78fb  PREREG_DRAFT.md
  349cbe5a6757357920eb55c5c2
...
b8ec307fc108fe6f18477cd7b  two_truths_lie/results/phase2/stage2/llama-3.1-8b-instruct/grading_summary.json
  9c1e1e8edd85933eb7a1e69a274b47b7166ddb7a780cbbd1f8aa794022701874  two_truths_lie/results/phase2/stage2/permutation_check.json
  440c5b3ac56ed712d7e05c925d21c14a7aa3415802a1e7ce51c89f5f479db31a  two_truths_lie/results/phase2/stage2/stage2_result.json
spelled-out numbers in the texts (structural counts, for review): five x2, four x11, one x11, three x3, two x9
levels.json re-derived from the committed records; texts re-rendered by build.py

PASS: every manifest value matches its source, every number in the texts is a claim or a whitelisted identifier, and the texts and levels reproduce.
```
