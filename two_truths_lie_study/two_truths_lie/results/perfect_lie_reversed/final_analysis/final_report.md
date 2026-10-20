# The Perfect Lie, follow-up (reversed note): final analysis

Gate (fresh, primary vs Google): excluded ['historical_anchor', 'emotional_appeal']; flagged []. Pool: ['P1', 'P2', 'P3', 'P5', 'P6']. Lies analysed: 4296. Confessions excluded: 1.

## Primary: Test B = full - reversed (registered, section 4)

| liar | label | direction | B | SE | t (df) | method | efficacy alpha at decision | equivalence alpha at decision |
|---|---|---|---|---|---|---|---|---|
| Llama 3.1 8B | **belief-tracking** | positive | +0.246 | +0.0134 | +18.33 (71) | per-category t-test (fallback) — did not converge | 0.016666666666666666 | not rejected |
| Gemma 3 27B | **belief-tracking** | positive | +0.430 | +0.0171 | +25.11 (71) | per-category t-test (fallback) — did not converge | 0.0125 | not rejected |
| gpt-4o-mini | **belief-tracking** | positive | +0.391 | +0.0237 | +16.48 (71) | per-category t-test (fallback) — did not converge | 0.025 | not rejected |
| Gemini 2.5 Flash-Lite | **belief-tracking** | positive | +0.348 | +0.0214 | +16.30 (71) | per-category t-test (fallback) — did not converge | 0.05 | not rejected |

## Missing data (registered, section 7)

Cells by model x condition (complete / failed / grader block):

- Llama 3.1 8B, placebo: 359 / 1 / 0
- Llama 3.1 8B, full: 360 / 0 / 0
- Llama 3.1 8B, reversed: 358 / 2 / 0
- Gemma 3 27B, placebo: 351 / 3 / 6
- Gemma 3 27B, full: 357 / 1 / 2
- Gemma 3 27B, reversed: 359 / 1 / 0
- gpt-4o-mini, placebo: 360 / 0 / 0
- gpt-4o-mini, full: 360 / 0 / 0
- gpt-4o-mini, reversed: 359 / 1 / 0
- Gemini 2.5 Flash-Lite, placebo: 356 / 4 / 0
- Gemini 2.5 Flash-Lite, full: 358 / 1 / 1
- Gemini 2.5 Flash-Lite, reversed: 360 / 0 / 0

Degenerate lies (reported, never excluded): 


Grader-block balance check (exact multinomial, Monte Carlo; flag only):

- Llama 3.1 8B: blocks {'placebo': 0, 'full': 0, 'reversed': 0}, p = 1.000
- Gemma 3 27B: blocks {'placebo': 6, 'full': 2, 'reversed': 0}, p = 0.034 — FLAGGED
- gpt-4o-mini: blocks {'placebo': 0, 'full': 0, 'reversed': 0}, p = 1.000
- Gemini 2.5 Flash-Lite: blocks {'placebo': 0, 'full': 1, 'reversed': 0}, p = 1.000
- pooled: blocks {'placebo': 6, 'full': 3, 'reversed': 0}, p = 0.051

Tipping point (first delta reversing the efficacy decision detected by the grid scan; a crossing between grid points can be missed, and 'no crossing detected' is not a proof of non-reversibility):

- Llama 3.1 8B: missing 2, delta n/a — no crossing detected by the 0.01 scan (no grid point in [0, 1] reverses the decision; this is not a proof of non-reversibility), worst case holds: True; registered rule; grid 0.01
- Gemma 3 27B: missing 4, delta n/a — no crossing detected by the 0.01 scan (no grid point in [0, 1] reverses the decision; this is not a proof of non-reversibility), worst case holds: True; registered rule; grid 0.01
- gpt-4o-mini: missing 1, delta n/a — no crossing detected by the 0.01 scan (no grid point in [0, 1] reverses the decision; this is not a proof of non-reversibility), worst case holds: True; registered rule; grid 0.01
- Gemini 2.5 Flash-Lite: missing 2, delta n/a — no crossing detected by the 0.01 scan (no grid point in [0, 1] reverses the decision; this is not a proof of non-reversibility), worst case holds: True; registered rule; grid 0.01

## Comprehension check (secondary, section 11a; cannot change the label)

| liar | balanced accuracy [95%] | J | criterion c | holds | reading |
|---|---|---|---|---|---|
| Llama 3.1 8B | +0.42 [0.34, 0.49] | +0.10 | +0.53 | False | belief use confirmed (comprehension reported as context) |
| Gemma 3 27B | +0.92 [0.89, 0.94] | +0.83 | +0.93 | True | belief use confirmed (comprehension reported as context) |
| gpt-4o-mini | +0.86 [0.82, 0.90] | +0.73 | -0.80 | False | belief use confirmed (comprehension reported as context) |
| Gemini 2.5 Flash-Lite | +0.99 [0.99, 1.00] | +0.99 | +0.28 | True | belief use confirmed (comprehension reported as context) |

## Secondary: Test A = reversed - placebo (section 5; a null is not evidence against belief-tracking)

| liar | A [95% CI] | placebo lies at s = 0 |
|---|---|---|
| Llama 3.1 8B | +0.116 [+0.090, +0.141] (df 71) | 60% |
| Gemma 3 27B | +0.102 [+0.064, +0.140] (df 71) | 53% |
| gpt-4o-mini | -0.056 [-0.079, -0.032] (df 71) | 70% |
| Gemini 2.5 Flash-Lite | +0.117 [+0.082, +0.153] (df 71) | 64% |

## Robustness (section 4)

- m1_random_intercepts_assumes_no_heterogeneity: Llama 3.1 8B B +0.247 (all_primary_rejections_preserved None); Gemma 3 27B B +0.431 (efficacy_holds True, all_primary_rejections_preserved True); gpt-4o-mini B +0.390 (efficacy_holds True, all_primary_rejections_preserved True); Gemini 2.5 Flash-Lite B +0.350 (all_primary_rejections_preserved None)
- nonviable_excluded: Llama 3.1 8B B +0.246 (efficacy_holds True, all_primary_rejections_preserved True); Gemma 3 27B B +0.430 (efficacy_holds True, all_primary_rejections_preserved True); gpt-4o-mini B +0.391 (efficacy_holds True, all_primary_rejections_preserved True); Gemini 2.5 Flash-Lite B +0.348 (efficacy_holds True, all_primary_rejections_preserved True)
- pooled gate (kappa 0.789): Llama 3.1 8B B +0.276 (efficacy_holds True, all_primary_rejections_preserved True); Gemma 3 27B B +0.441 (efficacy_holds True, all_primary_rejections_preserved True); gpt-4o-mini B +0.375 (efficacy_holds True, all_primary_rejections_preserved True); Gemini 2.5 Flash-Lite B +0.364 (efficacy_holds True, all_primary_rejections_preserved True)
- gpt-5 subsample (descriptive): Llama 3.1 8B B +0.169 (K 20); Gemma 3 27B B +0.568 (K 16); gpt-4o-mini B +0.361 (K 21); Gemini 2.5 Flash-Lite B +0.462 (K 22)
- flagged cues dropped: no cue flagged; identical to the primary analysis

## Exploratory (section 11; leads, not results)

Family diagonal: same family +0.606, other +0.592, difference +0.014. Full tables (liar x judge, acceptance by cue, breakdowns, acceptance by condition, off-target shifts) are in final_report.json.
