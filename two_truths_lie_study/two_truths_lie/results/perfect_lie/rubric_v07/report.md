# Rubric v0.7 check and the freeze decision

Date 2026-10-06. The rule was fixed before any grading (brief §8 item 26, commit a4abf79), and
v0.7 was committed before grading (987893c). Blind to condition, with no lift computed. The
analysis reads cue labels by cell id and grader only (`analysis/freeze_rule.py`).

## Outcome: freeze v0.6

| condition | result | met |
|---|---|---|
| A. emotional_appeal, primary vs Google: v0.7 kappa and AC1 both above v0.6 | kappa 0.652 → 0.672; AC1 0.674 → 0.734 | yes |
| B. Every other cue (all 15), primary and Google: v0.6 → v0.7 label change at most 0.08 | primary max 0.063 (mechanism_explanation); **Google: hedged_claim 0.126, mechanism_explanation 0.095, institutional_authority 0.084** | **no** |
| cap not breached; at least 90 lies valid for both primary and Google | $3.37 of $5; 95 lies | yes |

The rule is not met, so **v0.6 is frozen**.
- `cues.json` is restored byte-for-byte (sha256 `aee8391e509a22c083a72ef1e04971772bab64d52da414521e300bb1d722def4`).
- The rendered grader rubric hash is `36d97192…`.
- Both match section 2 of the pre-registration. The other instrument hashes are unchanged.
- There will be no further rubric iterations. The v0.7 file is kept for the record as
  `cues_v07_not_frozen.json`.

## Runs

| run | grader | gradings | spend counted / billed | namespace (fresh cache) |
|---|---|---|---|---|
| v0.7 | primary + Google | 190 / 190 | $1.41 / $1.05 | `rubric_v07_20261006` |
| v0.7 retest | primary | 95 / 95 | $1.26 / $0.89 | `rubric_v07_retest_20261006` |
| v0.7 | gpt-5 | 95 / 95 | $0.70 / $0.70 | `rubric_v07_gpt5_20261006` |
| | | **475, no failures** | **$3.37 combined**, cap $5 not breached | |

## Label change rates (share of the 95 lies whose label differs)

The 0.08 noise band is Google's run-to-run change under a fixed rubric (item 25). `!` marks a cue
outside the band that counts against rule B. emotional_appeal is the changed cue and is exempt.
`h` marks heatmap-only cues.

| cue | primary v0.6 → v0.7 | Google v0.6 → v0.7 | primary retest (v0.7 vs v0.7) | gpt-5 v0.6 → v0.7 (info) |
|---|---|---|---|---|
| document_citation | 0.000 | 0.021 | 0.011 | 0.011 |
| institutional_authority | 0.000 | **0.084 !** | 0.011 | 0.021 |
| named_expert h | 0.000 | 0.063 | 0.000 | 0.000 |
| historical_anchor | 0.011 | 0.032 | 0.011 | 0.043 |
| official_failure | 0.000 | 0.032 | 0.000 | 0.021 |
| first_person_witness | 0.011 | 0.021 | 0.011 | 0.000 |
| family_provenance | 0.000 | 0.000 | 0.000 | 0.000 |
| sensory_detail h | 0.021 | 0.053 | 0.021 | 0.032 |
| direct_quotation | 0.011 | 0.032 | 0.011 | 0.032 |
| mundane_aftermath | 0.011 | 0.074 | 0.021 | 0.021 |
| mechanism_explanation h | 0.063 | **0.095 !** | 0.021 | 0.043 |
| emotional_appeal (changed) | 0.126 | 0.105 | 0.021 | 0.117 |
| hedged_claim | 0.032 | **0.126 !** | 0.032 | 0.053 |
| self_deprecation | 0.000 | 0.011 | 0.000 | 0.011 |
| skeptic_acknowledgment | 0.011 | 0.042 | 0.000 | 0.053 |
| humor | 0.021 | 0.032 | 0.011 | 0.011 |

What the table shows:
- **The primary grader is steady.** Its retest under v0.7 changes at most 3.2% of labels on any
  cue, and on most cues 0 to 1%. That is about a third of Google's noise.
- **The rubric change stayed within noise for the primary grader** on every other cue (at most
  6.3%).
- **Google moved beyond its noise band on three cues.** institutional_authority (8 of 95 lies) is
  only one lie past the line and is consistent with noise. hedged_claim (0.126) is well past it.
  The new emotional_appeal text mentions hedges explicitly ("a line that does not count as a
  hedge… still counts here"), and that sentence seems to have reached the hedged_claim
  judgments. This is the same kind of spillover that v0.7 was meant to remove. The rule counts
  all three cues as written.

## Agreement under v0.7 (for the record; v0.7 is not frozen)

The bootstrap is over lies (2,000 resamples, seed 20261006). A cue is at risk when both lower
bounds are below 0.70.

| cue | primary vs Google: kappa [95% CI] / AC1 [95% CI] | primary vs gpt-5: kappa / AC1 |
|---|---|---|
| document_citation | 0.73 [0.49, 0.92] / 0.92 [0.84, 0.97] | 0.75 / 0.95 |
| institutional_authority | 0.79 [0.65, 0.91] / 0.83 [0.72, 0.93] | 0.90 / 0.93 |
| historical_anchor | 0.73 [0.58, 0.85] / 0.73 [0.59, 0.86], at risk | 0.68 / 0.69, at risk |
| official_failure | 0.64 [0.27, 0.90] / 0.94 [0.87, 0.99] | 0.54 / 0.93 |
| first_person_witness | 0.91 [0.80, 1.00] / 0.95 [0.89, 1.00] | 0.94 / 0.97 |
| family_provenance | 0.93 [0.80, 1.00] / 0.97 [0.92, 1.00] | 0.89 / 0.96 |
| direct_quotation | 0.84 [0.72, 0.95] / 0.86 [0.76, 0.96] | 0.80 / 0.82, at risk (lower bounds 0.65 / 0.70) |
| mundane_aftermath | 0.48 [0.21, 0.72] / 0.83 [0.72, 0.92] | 0.49 / 0.87 |
| **emotional_appeal** | **0.67 [0.50, 0.82] / 0.73 [0.58, 0.86], still at risk** | 0.41 / 0.35, at risk |
| hedged_claim | 0.45 [0.21, 0.67] / 0.76 [0.62, 0.86], at risk | 0.33 / 0.74, at risk |
| self_deprecation | 0.66 [0.00, 1.00] / 0.98 [0.94, 1.00] | 0.74 / 0.98 |
| skeptic_acknowledgment | 0.81 [0.52, 1.00] / 0.96 [0.91, 1.00] | 0.68 / 0.90 |
| humor | 0.73 [0.39, 0.94] / 0.95 [0.89, 0.99] | 0.73 / 0.92 |

Even under v0.7, emotional_appeal stayed at risk on the gating pair. gpt-5 marks it about twice as
often as the primary grader (0.63 against 0.31). So the definition split the graders further
rather than bringing them together.

## What freezing v0.6 means for the study

- **At risk on Stage 1 under v0.6:** institutional_authority, historical_anchor, emotional_appeal
  and hedged_claim (item 24). The worst case already assumes all four are excluded, which leaves
  9 units per replicate per liar. Nothing in sections 6 or 9 of the pre-registration changes.
- **The interim gate decides.** It runs on about 2,160 lies, without condition labels.

## Files

- `primary_google/`, `primary_retest/`, `gpt5/`: `regrades.jsonl` and `manifest.json`.
- `analysis/freeze_rule.py`, `.json`, `.log.md`: the rule and the tables above (offline).
- `cues_v07_not_frozen.json`: the v0.7 rubric that was tested and not adopted.
