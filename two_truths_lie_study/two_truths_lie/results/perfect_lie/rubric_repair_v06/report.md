# Rubric repair v0.6: regrade report

Date 2026-10-06. Brief §8 item 24. This is the owner-approved regrade, run before pre-registration
approval and blind to condition. No lift, score or condition contrast was computed. The analysis
code reads grades and cue ids only.

## What changed (cues.json v0.5 to v0.6)

| cue | change |
|---|---|
| hedged_claim | Tightened: the narrator's own uncertainty about memory, source or a specific fact. Hedges voiced by characters, scientific uncertainty that is part of the story's content, and naming an open question do not count. 5 boundary examples. |
| direct_quotation | Tightened: verbatim words of three or more inside quotation marks. Paraphrase, reported speech, quoted names, titles, single terms and scare quotes do not count. 5 boundary examples. |
| mundane_aftermath | Tightened: the reported consequence is small, bureaucratic or anticlimactic. Recognition, fame, disasters, legacies and closing reflections do not count. 5 boundary examples. |
| historical_anchor | Not rewritten. Per the owner's instruction it is judged on v3 data only (the pilot's 0.19 kappa came from the original prompt). |

The boundary examples were written from the definitions, without reading Stage 1 disagreements.
Old definitions are kept in `cues.json` as `definition_v05`. Hashes at regrade (sha256):
`cues.json` v0.6 `aee8391e509a22c083a72ef1e04971772bab64d52da414521e300bb1d722def4`
(commit 35d059d, recorded before the regrade). The rendered grader rubric text is
`36d97192487edd17677bcff5137cf76e3bda87085f3d297b5ea62dff069ec494`.

## Run

| | |
|---|---|
| source | `results/perfect_lie/stage1_v3_controls` (95 lies, prompt v3, conditions `none` and `placebo`) |
| graders | primary Claude Sonnet 4.5; Google gemini-2.5-flash (thinking off); both at temperature 0 with the strict schema |
| gradings | 190 of 190 written; 0 parse failures; 0 retries failed |
| spend | $1.35 counted at list price ($1.12 billed delta on the OpenRouter account); cap $5, kill on breach, not breached |
| grader input | public prompt and story only (invariant 3 and 5); condition labels never sent |

gpt-5 was not regraded (the owner named the primary and Google graders only), so the
primary-versus-gpt-5 figures below are still on v0.5.

## Agreement, primary vs Google, old rubric vs new

The same 95 lies were used for both columns. Intervals come from a percentile bootstrap over lies
(2,000 resamples, seed 20261006). "pos" counts lies marked positive by either grader under v0.6.
A cue is **at risk** when both lower bounds fall below 0.70 (the pre-registered exclusion rule).
Revised cues are marked with *.

| cue | v0.5 kappa [95% CI] | v0.5 AC1 [95% CI] | v0.6 kappa [95% CI] | v0.6 AC1 [95% CI] | pos | at risk v0.5 → v0.6 |
|---|---|---|---|---|---|---|
| document_citation | 0.79 [0.56, 0.95] | 0.93 [0.86, 0.99] | 0.81 [0.60, 0.96] | 0.95 [0.89, 0.99] | 14 | no → no |
| institutional_authority | 0.82 [0.70, 0.93] | 0.84 [0.73, 0.94] | 0.70 [0.55, 0.85] | 0.75 [0.61, 0.87] | 40 | no → **yes** |
| historical_anchor | 0.77 [0.63, 0.89] | 0.77 [0.64, 0.89] | 0.73 [0.59, 0.85] | 0.73 [0.58, 0.86] | 51 | yes → **yes** |
| official_failure | 0.63 [0.30, 0.88] | 0.92 [0.85, 0.98] | 0.59 [0.23, 0.85] | 0.93 [0.86, 0.98] | 11 | no → no |
| first_person_witness | 0.89 [0.76, 0.98] | 0.93 [0.86, 0.99] | 0.89 [0.76, 0.97] | 0.93 [0.86, 0.98] | 25 | no → no |
| family_provenance | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.93 [0.81, 1.00] | 0.97 [0.92, 1.00] | 18 | no → no |
| direct_quotation* | 0.68 [0.51, 0.83] | 0.73 [0.59, 0.86] | **0.84 [0.71, 0.93]** | **0.86 [0.75, 0.95]** | 37 | yes → **no** |
| mundane_aftermath* | 0.50 [0.25, 0.72] | 0.79 [0.67, 0.90] | 0.51 [0.25, 0.72] | **0.83 [0.73, 0.92]** | 20 | yes → **no** |
| emotional_appeal | 0.77 [0.63, 0.89] | 0.77 [0.64, 0.89] | 0.65 [0.49, 0.80] | 0.67 [0.52, 0.82] | 47 | yes → **yes** |
| hedged_claim* | 0.41 [0.25, 0.57] | 0.44 [0.25, 0.62] | 0.34 [0.11, 0.57] | 0.71 [0.56, 0.84] | 27 | yes → **yes** |
| self_deprecation | 0.58 [-0.02, 0.90] | 0.95 [0.90, 0.99] | 0.56 [-0.02, 1.00] | 0.97 [0.93, 1.00] | 5 | no → no |
| skeptic_acknowledgment | 0.72 [0.47, 0.90] | 0.92 [0.85, 0.97] | 0.78 [0.51, 0.95] | 0.95 [0.89, 0.99] | 12 | no → no |
| humor | 0.73 [0.49, 0.90] | 0.92 [0.83, 0.97] | 0.81 [0.52, 1.00] | 0.96 [0.91, 1.00] | 10 | no → no |

**At risk under v0.6:** institutional_authority, historical_anchor, emotional_appeal, hedged_claim.
**Repaired:** direct_quotation (clearly) and mundane_aftermath (through AC1; its kappa did not move).

### Prevalence (share of lies marked positive, primary / Google)

| cue | v0.5 | v0.6 |
|---|---|---|
| hedged_claim* | 0.51 / 0.27 | 0.23 / 0.14 |
| direct_quotation* | 0.37 / 0.35 | 0.35 / 0.36 |
| mundane_aftermath* | 0.22 / 0.14 | 0.09 / 0.20 |
| historical_anchor | 0.55 / 0.47 | 0.51 / 0.43 |

hedged_claim shows the kappa paradox. The new definition halved its prevalence and closed most
of the gap between graders (AC1 rose from 0.44 to 0.71), but at a prevalence near 0.2 kappa falls.
mundane_aftermath reversed direction: under v0.6 the Google grader marks it twice as often as the
primary.

### Within-grader change, same lies, old rubric vs new

This is the share of a grader's labels that flipped. Only the starred cues' definitions changed.

| cue | primary | Google |
|---|---|---|
| document_citation | 0.01 | 0.02 |
| institutional_authority | 0.03 | **0.11** |
| historical_anchor | 0.04 | 0.08 |
| official_failure | 0.01 | 0.05 |
| first_person_witness | 0.02 | 0.02 |
| family_provenance | 0.02 | 0.00 |
| direct_quotation* | 0.04 | 0.07 |
| mundane_aftermath* | 0.17 | 0.11 |
| emotional_appeal | 0.09 | **0.21** |
| hedged_claim* | 0.27 | 0.18 |
| self_deprecation | 0.01 | 0.04 |
| skeptic_acknowledgment | 0.05 | 0.05 |
| humor | 0.04 | 0.05 |

**This is the main caution in this report.** Two cues whose definitions did not change got
worse: institutional_authority entered the at-risk set (kappa 0.82 to 0.70) and emotional_appeal,
already at risk, fell further (0.77 to 0.65). The shift came mostly
from the Google grader (11% and 21% of its labels flipped), so a longer rubric changes how that
grader reads its neighbouring cues. Some of the flips may be ordinary provider non-determinism at
temperature 0. No same-rubric repeat was run, so the two cannot be separated here. Either way,
Stage 1 agreement on 95 lies is a rough guide, not a forecast of the interim gate.

## Which personas name the at-risk cues

From `personas.json` (full notes; partial notes in brackets):

| cue | named by |
|---|---|
| **hedged_claim** | **P4 only** (no partial note) |
| institutional_authority | P1 (partial: P1) |
| historical_anchor | P1, P5 |
| emotional_appeal | P4, P6 (partial: P6) |
| direct_quotation (repaired) | P3, P5 (partial: P3, P5) |
| mundane_aftermath (repaired) | P3 |

P4 is outside the primary pool (secondary conflict condition), so hedged_claim cannot affect the
primary test whether it passes the gate or not. It matters for the P4 secondary analysis only.

## Worst case for the primary pool (all four v0.6 at-risk cues excluded)

| persona | scorable cues left | pool |
|---|---|---|
| P1 | document_citation, official_failure (2) | primary |
| P2 | first_person_witness, family_provenance, humor (3) | primary |
| P3 | direct_quotation, mundane_aftermath (2) | primary |
| P4 | self_deprecation, skeptic_acknowledgment (2) | secondary (P4) |
| P5 | family_provenance, direct_quotation (2) | primary |
| P6 | first_person_witness, humor (2) | primary |

One unit drops out: technology / P6, which has no placebo-free cue left. That leaves **9 units per
replicate per liar**. The figure is 10 with no exclusions, and the v0.5 worst case was 5. No
persona falls below the two-cue floor. The repair of direct_quotation and mundane_aftermath is
what keeps P3 and P5 in the pool.

## Minimum positives (decision 1)

At 95 lies, 9 of 13 scorable cues have fewer than 30 positives. Projected to the 2,160 interim
lies at Stage 1 prevalence, the rarest cue (self_deprecation, 5 of 95) reaches about 110
positives. No cue is projected to fall under 30 at the interim. The `full` condition and the P4
targets may shift these numbers.

## Cost implication

The boundary examples lengthen the grader system prompt by about 30% (about 2,490 to 3,240 input
tokens per cue grading). The re-estimated design cost (`none`, `placebo` and `full`; all graders;
B-hat coding; current prices) is:

| | 15 replicates | 35 replicates |
|---|---|---|
| v0.5 rubric | $46.70 | $108.96 |
| v0.6 rubric | **$52.70** | **$122.98** |

As a check, the regrade billed $0.0118 per lie for the primary and Google story gradings, against
an estimate of $0.0112.

## Files

- `regrades.jsonl`: 190 gradings (cell id, grader, cues, counts, confidence).
- `manifest.json`: run parameters, spend, rubric hash.
- Code: `src/perfect_lie/regrade.py` (blind input, kill on breach).
- `analysis/`: agreement and flip tables (`regrade_agreement.*`), the v0.6 cost re-estimate
  (`costs_v06.txt`), and the boundary and power computation for PREREG revision 3
  (`gsd3.py`, `gsd3.txt`; offline, no model calls).
