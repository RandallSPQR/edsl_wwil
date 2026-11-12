# Findings

Labels: **registered primary**, **registered secondary**, **post hoc (descriptive)**, **exploratory**, as set by each registration and its addenda. Intervals are 95% unless stated.

## Phase 1: full versus placebo note (registered as study 1)

**registered primary** (registration sections 4-5). Lift is s(full) − s(placebo); the decision is taken at the look shown.

| liar | units | look | decision | mean lift [95% CI] | Z | boundary | local alpha at decision |
|---|---|---|---|---|---|---|---|
| Llama 3.1 8B | 131 | interim | belief-tracking | +0.285 [+0.223, +0.347] | +8.95 | 3.641 | 0.025 |
| Gemma 3 27B | 130 | interim | belief-tracking | +0.433 [+0.364, +0.503] | +12.24 | 4.016 | 0.0125 |
| gpt-4o-mini | 128 | interim | belief-tracking | +0.363 [+0.294, +0.432] | +10.31 | 3.864 | 0.0167 |
| Gemini 2.5 Flash-Lite | 122 | interim | belief-tracking | +0.352 [+0.274, +0.431] | +8.80 | 3.231 | 0.05 |

- **registered secondary** (Addendum 3, before unblinding): stagewise median-unbiased estimate [95% CI], Llama 3.1 8B +0.285 [+0.223, +0.347]; Gemma 3 27B +0.433 [+0.364, +0.503]; gpt-4o-mini +0.363 [+0.294, +0.432]; Gemini 2.5 Flash-Lite +0.352 [+0.274, +0.431].
- **registered secondary** (robustness, section 4), mixed model `d ~ 1 + (1 | prompt)`, intercept [95% CI]: Llama 3.1 8B +0.295 [+0.110, +0.479]; Gemma 3 27B +0.442 [+0.290, +0.595]; gpt-4o-mini +0.347 [+0.181, +0.512]; Gemini 2.5 Flash-Lite +0.326 [+0.179, +0.474]. Fits converged: 4 of 4.
- **registered secondary** (sensitivity, section 6): flagged cues dropped, 0 cues flagged, so identical to the primary. Pooled gate (kappa 0.778), mean lift Llama 3.1 8B +0.274; Gemma 3 27B +0.384; gpt-4o-mini +0.337; Gemini 2.5 Flash-Lite +0.294; decision holds for 4 of 4.
- **registered secondary** (sensitivity added by Addendum 1, post-registration, before data): units with a non-viable lie excluded, 1 unit dropped; decision holds for 4 of 4.
- **registered secondary** (tipping point for the failed cells, Addendum 3): missing units Llama 3.1 8B 4, Gemma 3 27B 5, gpt-4o-mini 7, Gemini 2.5 Flash-Lite 13. With every missing unit at its worst value, Z is Llama 3.1 8B +6.82, Gemma 3 27B +9.20, gpt-4o-mini +6.90, Gemini 2.5 Flash-Lite +4.45; decisions reversible: 0 of 4.
- **registered secondary** (gpt-5 subsample, section 8, descriptive): 524 lies; pooled kappa with the primary grader 0.768. Units and mean lift under gpt-5: Llama 3.1 8B 13, +0.276; Gemma 3 27B 8, +0.229; gpt-4o-mini 7, +0.000; Gemini 2.5 Flash-Lite 5, +0.600. On these units the primary test's boundary is crossed for 0 of 4.
- **post hoc (descriptive)** (after unblinding): the same subsample units scored by the primary grader give mean lifts Llama 3.1 8B +0.295; Gemma 3 27B +0.125; gpt-4o-mini +0.214; Gemini 2.5 Flash-Lite +0.400.
- **registered secondary** (P4 conflict condition, section 7; outside the primary pool and the Holm families), lift [95% CI]: Llama 3.1 8B +0.107 [+0.006, +0.208]; Gemma 3 27B +0.753 [+0.664, +0.843]; gpt-4o-mini +0.083 [-0.003, +0.170]; Gemini 2.5 Flash-Lite +0.769 [+0.668, +0.870].
- **exploratory** (section 10, analysis 3): judge acceptance of same-family minus other-family lies, +0.046 (3,158 same-family and 5,282 other-family judgements).
- **post hoc (descriptive)** (added before unblinding, labelled not pre-registered): conditional median-unbiased estimate given the early stop, Llama 3.1 8B +0.285; Gemma 3 27B +0.433; gpt-4o-mini +0.363; Gemini 2.5 Flash-Lite +0.352.

## Phase 2: reversed note (registered as the reversed-note study)

**registered primary** (section 4). Test B = s(full) − s(reversed). Liars estimated by the registered fallback (per-category t-test) because the mixed model did not converge: 4 of 4; categories per liar 72. Lies analysed: 4,296; confessions excluded: 1.

| liar | label | B | SE | t | Holm alpha at the efficacy rejection | p, TOST | Holm alpha at the equivalence rejection |
|---|---|---|---|---|---|---|---|
| Llama 3.1 8B | belief-tracking | +0.246 | 0.013 | 18.3 | 0.0167 | 1.0 | not rejected |
| Gemma 3 27B | belief-tracking | +0.430 | 0.017 | 25.1 | 0.0125 | 1.0 | not rejected |
| gpt-4o-mini | belief-tracking | +0.391 | 0.024 | 16.5 | 0.025 | 1.0 | not rejected |
| Gemini 2.5 Flash-Lite | belief-tracking | +0.348 | 0.021 | 16.3 | 0.05 | 1.0 | not rejected |

- **registered secondary** (Test A = s(reversed) − s(placebo), section 5; registered as exploratory, no label) [95% CI], and the share of placebo lies with s = 0: Llama 3.1 8B +0.116 [+0.090, +0.141], 60%; Gemma 3 27B +0.102 [+0.064, +0.140], 53%; gpt-4o-mini -0.056 [-0.079, -0.032], 70%; Gemini 2.5 Flash-Lite +0.117 [+0.082, +0.153], 64%.
- **registered secondary** (comprehension check, section 11a; cannot change a label): balanced accuracy [95% CI], comprehension holds: Llama 3.1 8B 0.417 [0.345, 0.490], no; Gemma 3 27B 0.915 [0.887, 0.943], yes; gpt-4o-mini 0.865 [0.825, 0.902], no; Gemini 2.5 Flash-Lite 0.995 [0.988, 1.000], yes.
- **registered secondary** (missing data, section 7): grader content-filter blocks for Gemma 3 27B by condition, placebo 6, full 2, reversed 0; balance check p = 0.034, flagged: yes. Liars flagged: 1 of 4.
- **registered secondary** (tipping point, section 7): missing cells Llama 3.1 8B 2, Gemma 3 27B 4, gpt-4o-mini 1, Gemini 2.5 Flash-Lite 2. Reversals found by the scan on a grid of step 0.01: 0 (a scan, not a proof); worst case holds: 4 of 4.
- **registered secondary** (robustness, section 4), random-intercepts model B and whether it converged: Llama 3.1 8B +0.247, no; Gemma 3 27B +0.431, yes; gpt-4o-mini +0.390, yes; Gemini 2.5 Flash-Lite +0.350, no. Where it did not converge the analysis makes no preservation claim; primary rejections preserved: 2 of 4.
- **registered secondary** (robustness, section 4), pooled gate (kappa 0.789), B Llama 3.1 8B +0.276; Gemma 3 27B +0.441; gpt-4o-mini +0.375; Gemini 2.5 Flash-Lite +0.364; primary rejections preserved: 4 of 4. Non-viable lies excluded: preserved 4 of 4.
- **registered secondary** (gpt-5 subsample, section 4, descriptive): B Llama 3.1 8B +0.169 (20 categories); Gemma 3 27B +0.568 (16 categories); gpt-4o-mini +0.361 (21 categories); Gemini 2.5 Flash-Lite +0.462 (22 categories).
- **registered secondary** (blinded permutation check, section 4a; 10,000 permutations): efficacy decisions in 1.3% to 1.4% of permutations per liar.
- **exploratory** (section 11): same-family minus other-family judge acceptance +0.014.
- **post hoc (descriptive)** (after unblinding, owner's request): Llama 3.1 8B balanced accuracy on parseable answers only, 0.536 [0.469, 0.603].
- **post hoc (descriptive)** (after unblinding, owner's request): Test B from the second grader's annotations, Llama 3.1 8B +0.269; Gemma 3 27B +0.394; gpt-4o-mini +0.401; Gemini 2.5 Flash-Lite +0.368; primary rejections preserved: 4 of 4. The second grader shares a family with the Gemma and Gemini liars.

## Phase 3: activation probe and steering (registered as "Phase 2")

### Before the probe

- **registered secondary** (identity check, section 2; completed and disclosed in the registration): hosted-minus-API difference in Test B on 36 categories [90% CI], equivalent within the margin: Llama 3.1 8B -0.004 [-0.060, +0.052], yes; Gemma 3 27B with the official template +0.073 [+0.015, +0.131], no; Gemma 3 27B with the provider's rendering +0.008 [-0.051, +0.068], yes. Phase 3 uses the renderings that were equivalent.
- **registered secondary** (grading route, section 11): grades through the provider's API directly agreed with the earlier route with kappa 0.915 over 784 cue labels.

### Probe gate

**registered primary** (section 4, gate and stop rule; Addendum 1).

| model | gate | selected block | held-out personas AUROC | held-out wordings A / B / C |
|---|---|---|---|---|
| Llama 3.1 8B | PASS | 12 | 0.828 | 1.000 / 1.000 / 1.000 |
| Gemma 3 27B | PASS | 35 | 0.768 | 1.000 / 1.000 / 1.000 |

- **registered secondary** (Addendum 3, before the pilot; stop rule): mean label-permutation null AUROC for held-out personas at the selected block, Llama 3.1 8B 0.498, Gemma 3 27B 0.499. Null means inside the stop band at the selected blocks (four tests per model): 4 of 4 (Llama 3.1 8B) and 4 of 4 (Gemma 3 27B).
- **registered secondary** (Addendum 3, descriptive): AUROC within each held-out persona at the selected block, minimum over the personas, Llama 3.1 8B 1.000, Gemma 3 27B 1.000.

### Stage 1: dose-finding pilot

- **registered secondary** (alpha rule, section 6; Addendum 5): confirmatory alphas with the Addendum 5 placebo, Llama 3.1 8B H1 4.0, H2 4.0; Gemma 3 27B H1 2.0, H2 1.0. Under the retired placebo they had been Llama 3.1 8B H1 4.0, H2 4.0; Gemma 3 27B H1 1.0, H2 1.0.
- **registered secondary** (Addendum 5): cosine of the placebo with v, retired placebo Gemma 3 27B 0.64, Llama 3.1 8B 0.24; new placebo Gemma 3 27B -5.9e-17, Llama 3.1 8B 1.7e-18.
- **exploratory** (pilot coherence measures, section 6): median perplexity ratio of steered lies under H1 by alpha (0.25, 0.5, 1, 2, 4, in order): Llama 3.1 8B 1.00 / 1.00 / 1.00 / 1.00 / 1.09; Gemma 3 27B 1.00 / 1.02 / 1.09 / 1.63 / 11.36.
- **registered secondary** (method-check coherence before stage 2, Addendum 7; coherence only, nothing graded): median perplexity ratio of the method-check steered lies and coherence gate passed: Llama 3.1 8B 1.00, yes; Gemma 3 27B 1.38, yes.

### Stage 2: steering

**registered primary** (section 7). Delta = mean over categories of s(steered) − s(placebo); Holm across the four tests in each family. Stage-2 coherence checks passed (steered and placebo arms, H1 and H2): 4 of 4 (Llama 3.1 8B) and 4 of 4 (Gemma 3 27B).

| model | hypothesis | alpha | Delta [95% CI] | categories | p, efficacy | Holm alpha, efficacy | p, TOST | Holm alpha, TOST | method check passed | label |
|---|---|---|---|---|---|---|---|---|---|---|
| Llama 3.1 8B | H1 | 4.0 | +0.093 [+0.044, +0.142] | 32 | < 0.001 | 0.0167 | 0.38 | not rejected | yes | **steerable** |
| Llama 3.1 8B | H2 | 4.0 | -0.124 [-0.182, -0.066] | 32 | < 0.001 | 0.0125 | 0.80 | not rejected | yes | **steerable** |
| Gemma 3 27B | H1 | 2.0 | +0.020 [-0.034, +0.074] | 32 | 0.46 | not rejected | 0.0025 | 0.0125 | no | **inconclusive: method check failed** |
| Gemma 3 27B | H2 | 1.0 | -0.030 [-0.080, +0.020] | 32 | 0.23 | not rejected | 0.0037 | 0.0167 | no | **inconclusive: method check failed** |

- **registered primary** (method check, section 6 as redefined in Addendum 7; one-sided t at 0.05), d [95% CI] on the categories shown, one-sided p, passed: Llama 3.1 8B +0.076 [+0.030, +0.122] (16 categories), p = 0.0015, yes; Gemma 3 27B +0.015 [-0.043, +0.072] (16 categories), p = 0.30, no.
- **registered secondary** (section 7a, as amended by Addendum 8): cells generated and graded per model, Llama 3.1 8B 1,280, grading failures after 3 attempts 8; Gemma 3 27B 1,280, grading failures after 3 attempts 10; generation failures, all models and arms: 0.
- **registered secondary** (section 7a, balance check; a flag, not a gate): pooled over models under H1, p = 0.038, flagged: yes (grading failures: reference 4, steered 0, placebo 0). Other balance checks flagged: 0 of 5.
- **registered secondary** (section 7a, tipping point): missing steered or placebo cells Llama 3.1 8B H1 0; Llama 3.1 8B H2 4; Gemma 3 27B H1 0; Gemma 3 27B H2 4. Imputation values in the scan that change a label: 0. Worst-case labels: Llama 3.1 8B H2 steerable; Gemma 3 27B H2 inconclusive: method check failed.
- **registered secondary** (section 8): the placebo arm's own shift against the hypothesis's unsteered reference [95% CI], Llama 3.1 8B H1 +0.071 [+0.030, +0.112]; Llama 3.1 8B H2 -0.017 [-0.074, +0.040]; Gemma 3 27B H1 +0.016 [-0.029, +0.060]; Gemma 3 27B H2 +0.026 [-0.029, +0.080].
- **registered secondary** (section 8): per-category SD of Delta, Llama 3.1 8B H1 0.135; Llama 3.1 8B H2 0.161; Gemma 3 27B H1 0.150; Gemma 3 27B H2 0.138.
- **registered secondary** (section 7, effect relative to the note): the note's own effect on the unsteered references, s(full) − s(reversed) [95% CI], Llama 3.1 8B +0.206 [+0.155, +0.257]; Gemma 3 27B +0.424 [+0.368, +0.479]; Delta as a share of it, Llama 3.1 8B H1 45%; Llama 3.1 8B H2 -60%; Gemma 3 27B H1 5%; Gemma 3 27B H2 -7%.
- **registered secondary** (section 7, naturalness): cosine of v with the full − reversed shift at the last prompt token on the evaluation categories (out of sample), Llama 3.1 8B 0.998; Gemma 3 27B 0.999; at the first generated token, Llama 3.1 8B 0.10; Gemma 3 27B 0.39.
- **registered secondary** (section 10, blinded permutation check; 10,000 permutations): efficacy decisions in 1.1% to 1.4% of permutations per test.
- **registered secondary** (Addendum 2, descriptive; the second grader shares a family with Gemma): steered − placebo on the subsample cells, second grader versus primary grader on the same cells, Llama 3.1 8B H1 +0.146 versus +0.120; Llama 3.1 8B H2 -0.078 versus -0.104; Gemma 3 27B H1 -0.010 versus +0.026; Gemma 3 27B H2 -0.010 versus -0.005. Per-cue kappa over all cues, Llama 3.1 8B 0.85; Gemma 3 27B 0.75. Lies graded by the second grader: Llama 3.1 8B 256; Gemma 3 27B 256.
- **registered secondary** (section 9, Llama dissociation, descriptive; Gemma alongside): held-out-persona probe AUROC at the selected block beside the registered comprehension balanced accuracy of Phase 2, Llama 3.1 8B 0.828 and 0.417; Gemma 3 27B 0.768 and 0.915; Llama 3.1 8B on parseable answers only (post hoc (descriptive)), 0.536.
- **exploratory** (section 9): the SAE-feature and MLP-neuron alignment analyses have not been run.

