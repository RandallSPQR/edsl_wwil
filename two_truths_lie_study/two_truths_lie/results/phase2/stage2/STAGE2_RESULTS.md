# The Perfect Lie, Phase 2: stage-2 results (unblinded 2026-10-27)

Registered analysis (`PREREG_PHASE2.md` sections 7, 7a, 8, 10; Addenda 1-8). It was run on the owner's go after two
independent blind reviews of the code (the second after Addendum 8), with the screens adjudicated (2 refusal-pattern
matches, both "not a confession") and the blinded permutation check done. Code at commit `482fce9`, every file
matching its addendum hash; full output in `stage2_result.json`.

Steering is unit(v) x alpha x ||v|| at the probe-selected layer (Gemma 3 27B block 35, Llama 3.1 8B block 12),
against the Addendum 5 placebo: covariance-matched, orthogonal to v, the same length. Confirmatory alphas from the
pilot: Gemma H1 2.0, H2 1.0; Llama H1 4.0, H2 4.0. The 32 evaluation categories x 5 targets give 160 cells per arm. s
is the share of the target's scorable cues the primary grader (Claude Sonnet 4.5, direct route) marks present.

## Primary (section 7)

Delta_k = the mean over targets of s(steered) - s(placebo), per category; two-sided t on K - 1 df; Holm across the four
tests in each family (efficacy; TOST +/-0.10).

| model | hypothesis | Delta [95% CI] | K | p (efficacy) | Holm alpha, efficacy | p (TOST) | Holm alpha, TOST | method check | **label** |
|---|---|---|---|---|---|---|---|---|---|
| Llama 3.1 8B | H1: reversed note + alpha v (predicted rise) | +0.093 [+0.044, +0.142] | 32 | 0.00052 | rejected at 0.0167 | 0.38 | not rejected | passed | **steerable** |
| Llama 3.1 8B | H2: full note - alpha v (predicted fall) | -0.124 [-0.182, -0.066] | 32 | 0.00013 | rejected at 0.0125 | 0.80 | not rejected | passed | **steerable** |
| Gemma 3 27B | H1 | +0.020 [-0.034, +0.074] | 32 | 0.46 | not rejected | 0.0025 | rejected at 0.0125 | failed | **inconclusive: method check failed** |
| Gemma 3 27B | H2 | -0.030 [-0.080, +0.020] | 32 | 0.23 | not rejected | 0.0037 | rejected at 0.0167 | failed | **inconclusive: method check failed** |

- **Llama:** steering along the note-valence direction moves cue use the way the note's valence does, in both
  directions.
  - Adding v under the reversed note raises s.
  - Subtracting v under the full note lowers s.
  - Both effects are relative to a same-length placebo orthogonal to v.
- **Gemma:** both contrasts are small. Their 95% intervals lie inside +/-0.08, and the equivalence family rejects both.
  But the positive control did not move s for Gemma (below), and the registration makes a null with a failed method
  check inconclusive. Gemma's result is therefore not "not steerable": the method did not demonstrably work for Gemma
  at all.

## Method check (section 6, as redefined in Addendum 7)

Per target, v_fp,t (target t's full note minus the placebo note it receives) is added at alpha 1 under t's placebo
note, against its own orthogonal placebo, on 16 categories. Prediction: s rises; one-sided t at 0.05.

| model | d [95% CI] | K | p (one-sided) | passed |
|---|---|---|---|---|
| Llama 3.1 8B | +0.076 [+0.030, +0.122] | 16 | 0.0015 | yes |
| Gemma 3 27B | +0.015 [-0.043, +0.072] | 16 | 0.30 | **no** |

## Missing data, balance, tipping point (section 7a)

- **Cells:** 1,280 per model, all generated (0 generation failures).
  - Grading failures, after 3 attempts: Gemma 10, Llama 8. In the stage-2 steered and placebo arms there are 4 per
    model, all under H2 (1 steered, 3 placebo).
  - Non-viable lies: 1 (Llama H1 steered); it stays in, under rule (a).
  - Confessions: 0.
- **Balance check** (grading failures across steered, placebo and the hypothesis's reference):
  - per model x hypothesis, every p >= 0.33;
  - **pooled H1 is flagged (p = 0.038)**: 0 steered, 0 placebo, 4 reference failures (2 per model, all in the
    unsteered reversed-note reference);
  - pooled H2: p = 0.37.
  - The flag concerns the reference arm only. The H1 primary contrast has no missing cell. It is a flag, not a gate.
- **Tipping point:**
  - H1: no missing steered or placebo cell for either model.
  - H2 (4 missing cells each): no imputation shift delta in [0, 1], against or for the hypothesis, changes any label.
    The worst case keeps every label.

## Reported (sections 7, 8)

| | Gemma H1 | Gemma H2 | Llama H1 | Llama H2 |
|---|---|---|---|---|
| placebo's own shift vs the hypothesis's unsteered reference | +0.016 [-0.029, +0.060] | +0.026 [-0.029, +0.080] | **+0.071 [+0.030, +0.112]** | -0.017 [-0.074, +0.040] |
| Delta / (s_full - s_reversed) | 0.05 | -0.07 | **0.45** | **-0.60** |
| per-category SD of Delta (powered for 0.14) | 0.150 | 0.138 | 0.135 | 0.161 |

- **The note's own effect** on the unsteered references (s_full - s_reversed): Gemma +0.424 [+0.368, +0.479], Llama
  +0.206 [+0.155, +0.257].
  - Llama's steering moves s by 45% (H1) and 60% (H2) of the note's own full-vs-reversed effect.
- **Llama's placebo itself raised s under H1, by +0.071.** Section 8 anticipated this: a placebo that moves s in the
  predicted direction shrinks Delta. The H1 rejection holds despite it. Against the unsteered reference, the steered
  lies' shift is about +0.16 (Delta + placebo shift).
- **Naturalness:**
  - cos(v, the full - reversed shift at the last prompt token, evaluation categories, out of sample): Gemma 0.999,
    Llama 0.998.
  - At the first generated token: Gemma 0.39, Llama 0.10.

## Addendum 2: Google grader on the 20% subsample (descriptive)

One cell per category (32 cells per arm). The grader is gemini-2.5-flash, which shares a family with Gemma.

| contrast | Google | primary, same cells | primary, all cells |
|---|---|---|---|
| Llama H1 steered - placebo | +0.146 | +0.120 | +0.093 |
| Llama H2 steered - placebo | -0.078 | -0.104 | -0.124 |
| Llama method check | +0.156 | +0.104 | |
| Gemma H1 steered - placebo | -0.010 | +0.026 | +0.020 |
| Gemma H2 steered - placebo | -0.010 | -0.005 | -0.030 |
| Gemma method check | -0.010 | -0.115 | |
| ref full - ref reversed: Llama / Gemma | +0.198 / +0.396 | +0.204 / +0.452 | |

- The Google grader agrees on the direction of every Llama contrast.
- Per-cue kappa, primary vs Google: Llama 0.85 over all cues and 0.93 over the cues in s; Gemma 0.75 and 0.77.
- No Google grade failed.

## Section 10

- The blinded permutation check (10,000 within-cell swaps) gave efficacy-rejection shares of 1.15-1.35% per test, as
  designed.
- The screens matched 2 lies, adjudicated before unblinding; neither was excluded.

## Scope of the claims

- **Llama 3.1 8B:**
  - A direction read from the model's own activations distinguishes full from reversed notes across held-out
    personas and wordings.
  - Pushing the residual stream along it, with no change to the prompt, moves the liar's use of the target's cues in
    the direction the note's valence would. This holds in both directions and against an orthogonal, same-length
    placebo.
  - The method check passed. This is evidence that the note's valence acts through this representation.
  - Its size is 45-60% of the note's own effect, at alpha 4 (the top of the registered grid, every alpha coherent).
- **Gemma 3 27B:**
  - The direction passed the probe gate but, at the coherent alphas (2.0 and 1.0), steering did not move s.
  - The positive control did not move s either, so the result is uninterpretable as evidence for or against a causal
    role.
  - Gemma became incoherent above alpha 1-2 in the pilot, so a stronger push was not available within the
    registration.
