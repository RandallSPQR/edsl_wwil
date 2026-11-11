# Methods

Numbers in this section are design constants quoted from the registrations or counts read from the results files; each is listed in `CLAIMS_MANIFEST.csv` with its source. Labels follow the registrations and their addenda.

## Shared instrument

A liar model writes a story to persuade a judge model. The public prompt is identical in every condition; only a private note given to the liar differs between conditions.
The note describes what one target persona (`P1`, `P2`, `P3`, `P5` or `P6`) finds convincing, as beliefs naming cues from the frozen cue list (rubric v0.6).
The outcome s of a lie is the share of the target's scorable cues that the primary grader (Claude Sonnet 4.5) marks present in the story. Scorable cues exclude heatmap-only cues and cues removed by a per-cue agreement gate between the primary grader and a second grader (gemini-2.5-flash).
Each study was registered on OSF before its data were collected. Changes were made by dated addenda. Analysis code was validated on simulated data, reviewed and hashed before unblinding, and each study ran a blinded permutation check before unblinding.

## Study 1: full versus placebo note

Registration: `PREREG_DRAFT.md` (revision 3; tag `perfect-lie-prereg-v1`).

- Liars and judges: four models (Llama 3.1 8B, Gemma 3 27B, gpt-4o-mini, Gemini 2.5 Flash-Lite); every lie is read by all four as judges.
- Conditions: no note (`none`), a placebo note describing another persona, and the target's full note. Per replicate and liar, 6 prompts, 2 targets and three conditions, 36 cells.
- Unit and outcome: a unit is (liar, prompt, target, replicate); its lift is d = s(full) − s(placebo), scored on the target's note-named cues that the placebo note does not name. A unit with an empty cue set is dropped.
- Looks: an interim after replicate 15 of 35; a model inconclusive at the interim extends.
- **Primary test** (registered primary; registration sections 4-5): Z = mean(d) / SE, two-look group-sequential boundaries (Lan-DeMets O'Brien-Fleming). Efficacy is two-sided, with Holm across the four liars by the graphical approach, each model starting at local alpha 0.0125. Equivalence is a TOST by repeated confidence intervals with margin 0.10, Holm in the same way. Outcomes: belief-tracking, flat, extend, or inconclusive.
- Registered robustness: the mixed model `d ~ 1 + (1 | prompt)` (section 4); flagged cues dropped and a pooled gate (section 6); the gpt-5 grader on a seeded 25% subsample, descriptive (section 8).
- Registered secondary: P4, the public-versus-private conflict condition (section 7). Registered as exploratory: the secondary analyses of section 10.
- Amendments:
  - Addendum 1 (before data; log item 29): the run generates only the registered conditions (the tagged code also generated an unregistered one); the sequential-analysis code, written after the tag and before data, implements registration sections 3-6; non-viable lies (word range, refusal) stay in the primary analysis, and one sensitivity analysis excludes units with a non-viable lie, labelled "added post-registration, before data".
  - Addendum 2 (before the interim analysis; log item 30): transport failures (rate limit, timeout, dropped connection) were retried with backoff and re-run from their last completed stage; other failed cells stayed failed.
  - Addendum 3 (before unblinding; log items 32-34): stagewise median-unbiased estimates with intervals, a tipping point for the failed cells, the breakdown of empty-cue exclusions, and the confession rule's text. A conditional median-unbiased estimate was added before unblinding and is labelled not pre-registered.
  - After unblinding (post hoc (descriptive)): the gpt-5 subsample's units were also scored with the primary grader.
- Data: 2,110 lies at the interim; units per model Llama 3.1 8B 131, Gemma 3 27B 130, gpt-4o-mini 128, Gemini 2.5 Flash-Lite 122. Units excluded: 29 with a missing or failed cell, 60 with an empty cue set, 0 confessed.

## Study 2: reversed note

Registration: `PREREG_REVERSED.md` (tag `perfect-lie-reversed-prereg-v1`).

- Liars, judges and graders as in study 1; the gpt-5 grader on a seeded 25% subsample. Sampling for all liars: temperature 0.6, top_p 0.9.
- Conditions: placebo, full, and reversed. The reversed note flips each belief's valence by the smallest edit (the judge finds the cue suspect), naming the same cues with the same cue words.
- Size: 72 categories, five targets, three conditions and four liars, 4,320 lies, one replicate.
- **Primary test** (registered primary; section 4): Test B = s(full) − s(reversed), per liar, from `s ~ condition + persona + (1 + condition | category)` (REML), with t on K − 1 = 71 df; if the fit fails, a per-category t-test on the persona-averaged paired differences (registered fallback). Holm across the four liars in an efficacy family (two-sided) and an equivalence family (TOST, margin 0.10). Labels: belief-tracking; fewer named cues under full than under reversed; no valence effect beyond the margin; valence effect present within the margin; inconclusive.
- Registered secondary (section 5, registered as exploratory, no label): Test A = s(reversed) − s(placebo).
- Registered secondary (section 11a): a comprehension check asking each liar whether the judge finds each noted quality convincing or suspicious; comprehension holds if the balanced accuracy's lower 95% bound is at least 0.85. It cannot change a label.
- Registered robustness (section 4): a random-intercepts model, the gpt-5 subsample (descriptive), the pooled gate, and non-viable lies excluded. Missing data (section 7): failed cells and grader content-filter blocks counted separately, a balance check of blocks across conditions (flag only), and a tipping point.
- Registered as exploratory (section 11): judge-side analyses including the same-family acceptance difference.
- Amendments: Addendum 1 (before unblinding) recorded the fixes from the final-analysis code reviews and the owner's adjudication of the blind screen matches (lies kept as confessions and excluded: 1).
- After unblinding (post hoc (descriptive); owner's requests): balanced accuracy on parseable comprehension answers only, and Test B from the second grader's annotations.

## Phase 2: activation probe and steering

Registration: `PREREG_PHASE2.md` (revision 4; tag `perfect-lie-phase2-prereg-v1`), with Addenda 1-8 (`PREREG_PHASE2_ADDENDA.md`).

- Models: Gemma 3 27B IT and Llama 3.1 8B Instruct with open weights (bf16), the two open-weight liars of the earlier studies. Their prompt renderings were fixed by a registered identity check comparing the hosted model with the API (section 2).
- Category split: the frozen categories split once into 32 evaluation and 40 training categories.
- **Probe** (section 4; code hashed in Addendum 1): v_L = mean(h_full − h_reversed) at the last prompt token of block L, over training items. Two transfer tests: held-out personas (each target held out in turn, scores pooled) and held-out wordings (three paraphrase sets). A layer passes if every test has AUROC of at least 0.70 and a cluster-bootstrap lower bound above 0.50. The gate requires a passing candidate layer; the layer is the passing candidate with the highest mean held-out-wording AUROC.
- Diagnostics before the pilot (Addendum 3): the registered cue-mention control was recorded as uninformative by design (placebo items equal other targets' full items); a label-permutation null with a stop rule; a within-fold persona AUROC (descriptive).
- **Steering vector** (section 6): unit(v) × alpha × ||v|| added at the selected block's output at every prompt and generated position. Placebo (Addendum 5, replacing the registered covariance-matched placebo): a draw from the condition-centred covariance of the training activations, with its v component projected out, at the same length.
- **Stage 1, dose-finding pilot** (section 6; coherence measures exploratory; alpha rule registered; Addenda 4 and 5): training categories only, alpha in {0.25, 0.5, 1, 2, 4}. Coherence gate for the steered and the placebo lies: viability of at least 95%, median perplexity ratio at most 2.0, repeated-4-gram share at most 0.25. Confirmatory alpha: the largest grid alpha at which both pass.
- **Stage 2** (sections 6-7): the 32 evaluation categories and five targets. H1: the reversed note plus alpha v (predicted rise in s). H2: the full note minus alpha v (predicted fall). Arms: steered, placebo, and unsteered references (placebo, full and reversed notes). The stage-2 coherence gate is re-applied before grading; a failing test is untestable.
- **Primary analysis** (registered primary; section 7): Delta_k = mean over targets of s(steered) − s(placebo) per category; two-sided t on 31 df with Holm across the four tests; TOST at 0.10 with Holm. Labels: steerable; opposite; not steerable within the margin (equivalence rejected, efficacy not, method check passed); inconclusive (including a failed method check); untestable.
- **Method check** (section 6, redefined in Addendum 7): the registered direction v_fp (full minus placebo note) is zero by construction, because the placebo items are the full items relabelled. Per target t, v_fp,t = mean(h(t's full note) − h(the placebo note t receives)) was added at alpha 1 under t's placebo note, against its own orthogonal placebo, on the method check's 16 categories; one-sided t (s rises) at 0.05.
- Grading (section 11): every stage-2 lie by the primary grader through the provider's API directly (strict tool decoding). Addendum 2: the Google grader on a seeded 20% subsample of cells (one target per category), descriptive; it shares a family with Gemma.
- Missing data (section 7a): failed generation and grading counted separately, a balance check of grading failures across arms (flag only), and a tipping point. Addendum 8 (before unblinding) made every planned cell a record, so generation failures enter these counts.
- Addenda:
  - 1: probe-stage code and its fixed details.
  - 2: the Google-grader subsample (descriptive).
  - 3: probe diagnostics; the cue-mention control recorded as uninformative; an approved exception: the Addendum 2 subsample is graded through OpenRouter, while all primary grading stays on the direct route.
  - 4: pilot code and coherence details, with two pre-generation revisions of the hook check.
  - 5: the new placebo and the rerun of the pilot's placebo half; the confirmatory alphas replaced.
  - 6: stage-2 analysis and grading code.
  - 7: stage-2 generation code and the per-target method check.
  - 8: generation failures recorded as cells.

