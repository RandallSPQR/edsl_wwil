# Pre-freeze checks: gpt-5 under rubric v0.6, and Google test-retest under the old rubric

Date 2026-10-06. Owner-approved before the freeze. Both checks were blind to condition, with no
lift computed and a combined kill cap of $5. The analysis reads cue labels by cell id and grader
only (`analysis/prefreeze_agreement.py`).

## Runs

| check | grader | rubric | gradings | spend (counted / billed) | namespace (fresh cache) |
|---|---|---|---|---|---|
| 1 | gpt-5 (reasoning minimal) | v0.6 | 95 written, 94 valid | $0.47 / $0.21 | `regrade_gpt5_v06_20261006` |
| 2 | Google gemini-2.5-flash, temperature 0 | v0.5 (old) | 95 of 95 | $0.13 / $0.10 | `retest_google_v05_20261006` |
| | | | **total** | **$0.61 / $0.31** | cap $5, not breached |

Notes on the runs:
- **One gpt-5 grading failed closed.** On one lie, gpt-5 returned self_deprecation = false with
  a count of 1 on all three attempts, so the parser rejected it. That lie is left out of check 1
  (n = 94).
- **The old rubric is exact.** It was rebuilt from `definition_v05` with no boundary examples, and
  its cue list is byte-identical to the one Stage 1 rendered (checked against `cues.json` at
  a0077b7). The preamble and output section are unchanged since Stage 1 (hash c638fea1…).
- **Grader settings are unchanged since Stage 1.** The Google and gpt-5 configurations (model,
  temperature, reasoning, token limit, strict schema) match `models.json` as of the Stage 1 run.

## Check 1: gpt-5 vs primary, both on v0.6

The bootstrap is over lies (2,000 resamples, seed 20261006). A cue is at risk when both lower
bounds are below 0.70. Revised cues are marked with *.

| cue | v0.5 kappa / AC1 (Stage 1) | v0.6 kappa [95% CI] | v0.6 AC1 [95% CI] | pos | at risk v0.5 → v0.6 |
|---|---|---|---|---|---|
| document_citation | 0.71 / 0.94 | 0.81 [0.52, 1.00] | 0.96 [0.91, 1.00] | 10 | no → no |
| institutional_authority | 0.88 / 0.91 | 0.85 [0.73, 0.95] | 0.89 [0.79, 0.96] | 32 | no → no |
| historical_anchor | 0.73 / 0.73 | 0.66 [0.51, 0.80] | 0.67 [0.51, 0.81] | 49 | yes → **yes** |
| official_failure | 0.59 / 0.94 | 0.47 [-0.03, 0.82] | 0.93 [0.86, 0.98] | 9 | no → no |
| first_person_witness | 0.91 / 0.95 | 0.97 [0.89, 1.00] | 0.98 [0.95, 1.00] | 21 | no → no |
| family_provenance | 1.00 / 1.00 | 0.89 [0.75, 1.00] | 0.96 [0.90, 1.00] | 18 | no → no |
| direct_quotation* | 0.67 / 0.70 | **0.84 [0.71, 0.94]** | **0.86 [0.75, 0.95]** | 38 | yes → **no** |
| mundane_aftermath* | 0.59 / 0.84 | 0.46 [0.16, 0.71] | 0.85 [0.74, 0.93] | 17 | no → no |
| emotional_appeal | 0.58 / 0.59 | 0.48 [0.32, 0.62] | 0.45 [0.27, 0.62] | 64 | yes → **yes** |
| hedged_claim* | 0.56 / 0.58 | 0.52 [0.29, 0.71] | 0.76 [0.62, 0.87] | 27 | yes → **yes** |
| self_deprecation | 0.65 / 0.97 | 0.74 [0.00, 1.00] | 0.98 [0.94, 1.00] | 5 | no → no |
| skeptic_acknowledgment | 0.63 / 0.83 | 0.71 [0.47, 0.90] | 0.92 [0.84, 0.97] | 15 | no → no |
| humor | 0.76 / 0.91 | 0.77 [0.54, 0.95] | 0.93 [0.86, 0.99] | 15 | no → no |

Reading:
- **direct_quotation:** gpt-5 confirms the repair. It goes from at risk to 0.84 / 0.86, the same
  as the Google pair.
- **institutional_authority:** clear on this pair, at 0.85 / 0.89.
- **historical_anchor, emotional_appeal and hedged_claim:** at risk here too.
- **emotional_appeal:** worse than under v0.5, at 0.48 / 0.45 against 0.58 / 0.59.

The gpt-5 pair does not gate (section 6 of the draft). It is reported for robustness.

## Check 2: Google test-retest under the old rubric

Three Google runs on the same 95 lies:
- **old run 1:** the Stage 1 grades (v0.5);
- **old run 2:** the retest (v0.5, fresh cache);
- **new:** the v0.6 regrade.

The table gives the share of lies whose label differs between two runs. The old1 → old2 column
measures noise alone.

| cue | old1 → old2 (noise) | old1 → new (rubric + noise) | old2 → new | prevalence old1 / old2 / new |
|---|---|---|---|---|
| document_citation | 0.00 | 0.02 | 0.02 | 0.17 / 0.17 / 0.15 |
| **institutional_authority** | **0.08** | **0.11** | **0.08** | **0.42 / 0.42 / 0.40** |
| historical_anchor | 0.06 | 0.08 | 0.06 | 0.47 / 0.43 / 0.43 |
| official_failure | 0.02 | 0.05 | 0.05 | 0.12 / 0.14 / 0.11 |
| first_person_witness | 0.02 | 0.02 | 0.02 | 0.26 / 0.26 / 0.26 |
| family_provenance | 0.00 | 0.00 | 0.00 | 0.19 / 0.19 / 0.19 |
| direct_quotation* | 0.02 | 0.07 | 0.07 | 0.35 / 0.33 / 0.36 |
| mundane_aftermath* | 0.01 | 0.11 | 0.09 | 0.14 / 0.15 / 0.20 |
| **emotional_appeal** | **0.08** | **0.21** | **0.15** | **0.49 / 0.47 / 0.41** |
| hedged_claim* | 0.08 | 0.18 | 0.16 | 0.27 / 0.27 / 0.14 |
| self_deprecation | 0.02 | 0.04 | 0.04 | 0.05 / 0.05 / 0.03 |
| skeptic_acknowledgment | 0.03 | 0.05 | 0.04 | 0.09 / 0.11 / 0.11 |
| humor | 0.03 | 0.05 | 0.04 | 0.13 / 0.12 / 0.07 |

As a check, Google's agreement with itself (old run 1 vs old run 2) is lowest on hedged_claim
(kappa 0.79) and is 0.83 on both institutional_authority and emotional_appeal. Every cue clears
the gate rule against itself.

### Verdict on the two drops

**institutional_authority: noise, not the rubric.**
- Under the same old rubric, Google changes 8% of its labels from one run to the next. The change
  to v0.6 (8–11%) is no larger.
- Prevalence does not move (0.42, 0.42, 0.40).
- The primary grader against the Google *retest*, both on the old rubric, gives kappa 0.73
  [0.59, 0.87] and AC1 0.76 [0.63, 0.88]. That is already at risk with no rubric change at all.
- So the 0.82 in Stage 1 was a favourable draw. The cue sits near the gate line because the Google
  grader is not deterministic at temperature 0.
- On the gpt-5 pair it is clear (0.85 / 0.89).
- **No fix proposed.**

**emotional_appeal: the rubric caused most of the drop.**
- Google's change from old to new (15–21%) is about twice its retest noise (8%).
- The shift has a direction. Both the primary and Google graders mark the cue less often under
  v0.6:

  | grader | v0.5 prevalence | v0.6 prevalence |
  |---|---|---|
  | primary | 0.51 | 0.41 |
  | Google | 0.49 | 0.41 |
  | gpt-5 | 0.67 | 0.67 |

- The two graders became stricter on different lies, so their agreement fell from 0.77 to 0.65.
  Against gpt-5, which did not move, primary agreement fell from 0.58 to 0.48.
- **Likely mechanism** (inferred from the rubric text, not from reading disagreements): two of
  the new boundary examples teach "does not count" for exactly the material that emotional appeals
  are made of.
  - The hedged_claim example "The farmer worried the bridge might not hold" teaches that a
    character's feeling is not a hedge.
  - The mundane_aftermath example "It reminds us that nature still holds surprises" teaches that
    a reflective closing is not a mundane aftermath.
  - Graders appear to carry those exclusions over to emotional_appeal, whose definition does not
    say how either case is treated.

## Proposed fix (not applied; needs owner approval)

**Rubric v0.7: change only emotional_appeal.** Give it a definition that settles both cases
explicitly and states that it is judged independently of the other cues. Add five boundary
examples, written from the definition and the persona notes, without reading any story or grader
disagreement.

The construct stays narrator-voiced, as in v0.5 and as the notes promise ("conveys how it felt",
P4; "the teller conveys what it felt like to be there", P6).

> **emotional_appeal:** The narrator, in their own voice, names or evokes a feeling about the
> events (wonder, awe, sadness, fear, nostalgia), conveys what it felt like to be there, or asks
> the listener to imagine how it felt. Judge this cue on its own: a line that does not count as a
> hedge or as a mundane aftermath still counts here if the narrator voices or invites a feeling.
> A character's feeling reported as plain fact, and a dramatic or sad event stated without any
> feeling named or evoked, do not count.

| example | counts |
|---|---|
| "I still get chills remembering the silence when the lid came off." | yes |
| "Imagine standing on that ice, hearing it crack beneath you." | yes |
| "It reminds me, every time, of the wonder I felt that morning." | yes (a reflective closing that voices a feeling) |
| "The farmer worried the bridge might not hold." | no (a character's feeling as plain fact) |
| "The flood destroyed forty homes in a single night." | no (dramatic fact, no feeling named or evoked) |

**Verification, if approved:**
- Regrade the same 95 lies with the primary and Google graders under v0.7. That is about $1.40,
  based on the v0.6 regrade cost.
- Optionally add gpt-5 for about $0.50. Kill cap $5.
- Report emotional_appeal against the noise floor above. Also report the within-grader change on
  every other cue, to confirm that v0.7 does not shift its neighbours, which is the failure this
  check found.

Caveats:
- This is the second rubric change tested on the same 95 lies, so it is a check of the repair,
  not an independent validation. The binding test is still the interim gate.
- If the owner prefers not to touch the rubric again, the alternative is to freeze v0.6 as it is.
  emotional_appeal would most likely be excluded at the interim. The worst case already assumes
  that, and P6 keeps 2 cues, for 9 units per replicate. That option costs nothing now. Its price
  is losing P6's second-ranked belief from the primary score.

## Other findings for the record

- **The Google grader is not deterministic at temperature 0.** Its run-to-run label change
  reaches 8% on institutional_authority, emotional_appeal and hedged_claim. Agreement between two
  graders cannot exceed what each has with itself, so the gate (primary vs Google, both lower
  bounds below 0.70 to exclude) has limited headroom on these cues. The primary grader's own
  test-retest was not measured.
- **historical_anchor** is at risk on both pairs (Google 0.73 / 0.73; gpt-5 0.66 / 0.67). The
  test-retest shows no rubric effect: noise 0.06, change to v0.6 0.08. It is a chronically hard
  cue rather than a v0.6 regression. No fix is proposed, as none was asked for.

## Files

- `retest_google_v05/`, `gpt5_v06/`: `regrades.jsonl` and `manifest.json` (spend, cap, rubric
  hash). The gpt-5 manifest also carries the combined spend.
- `analysis/prefreeze_agreement.py`, `.json`, `.log.md`: the tables above (offline).
