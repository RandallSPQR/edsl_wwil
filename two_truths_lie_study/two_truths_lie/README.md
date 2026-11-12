# The Perfect Lie

Do language models write a lie to fit what a particular judge finds convincing? A liar model writes a story to
persuade a judge model. The public prompt is the same in every condition; only a private note about the judge
changes: no note, a placebo note (another persona's beliefs), the target's own beliefs (full note), or the same
beliefs with their valence flipped (reversed note). The outcome is the share of the target's named cues the story
uses, scored by a blind grader. Three pre-registered phases (Why Would I Lie, WWIL), each registered separately:

| phase (registered as) | question | registration |
|---|---|---|
| **Phase 1** (study 1) | finds the effect: full vs placebo note, four liars, two-look sequential design | [`perfect-lie-prereg-v1`](https://github.com/RandallSPQR/edsl_wwil/releases/tag/perfect-lie-prereg-v1) (2026-10-06) |
| **Phase 2** (reversed-note study) | why one path rather than another: full vs reversed note, belief-tracking or cue priming? | [`perfect-lie-reversed-prereg-v1`](https://github.com/RandallSPQR/edsl_wwil/releases/tag/perfect-lie-reversed-prereg-v1) (2026-10-15) |
| **Phase 3** ("Phase 2") | probes causality: an activation probe for note valence in two open-weight liars, and steering along it | [`perfect-lie-phase2-prereg-v1`](https://github.com/RandallSPQR/edsl_wwil/releases/tag/perfect-lie-phase2-prereg-v1) (2026-10-22) |

## Results at a glance (registered primary tests)

- **Phase 1:** all four liars were belief-tracking at the interim look. The full note raised use of the target's
  named cues by +0.285 (Llama 3.1 8B), +0.433 (Gemma 3 27B), +0.363 (gpt-4o-mini) and +0.352 (Gemini 2.5 Flash-Lite).
- **Phase 2 (Test B, full − reversed):** all four were belief-tracking: +0.246, +0.430, +0.391, +0.348.
- **Phase 3:** Llama 3.1 8B was steerable in both directions (H1 +0.093 [+0.044, +0.142]; H2 −0.124 [−0.182, −0.066];
  method check passed). Gemma 3 27B: inconclusive, method check failed.

Every number, with its registration label (registered primary or secondary, post hoc, exploratory) and its source
file: [`../writeup/FINDINGS.md`](../writeup/FINDINGS.md); design and amendments: [`../writeup/METHODS.md`](../writeup/METHODS.md);
the paper draft in phase order: [`../writeup/PAPER.md`](../writeup/PAPER.md).

## Reproduce it

From the repository root:

```
cd two_truths_lie_study
make env          # Python 3.11 and the pinned packages (uv), once
make reproduce    # Tier 0: about 27 min on 4 CPUs; no network, GPU or API key
```

Tier 0 rebuilds every CPU-derivable result from the raw records in `results/`, then the write-up and figures, and
checks all 446 claims against their sources. An independent run on a fresh clone passed
([`../release/fresh_run/`](../release/fresh_run/)). Details, Docker, Tiers 1-3: [`../release/README.md`](../release/README.md).

## Where things are

| | |
|---|---|
| registrations (frozen texts) | [`../PREREG_DRAFT.md`](../PREREG_DRAFT.md) (Phase 1), [`../PREREG_REVERSED.md`](../PREREG_REVERSED.md) (Phase 2), [`../PREREG_PHASE2.md`](../PREREG_PHASE2.md) (Phase 3) |
| amendments | Phase 3 Addenda 1-8 (the registration's "Phase 2 Addenda"): [`../PREREG_PHASE2_ADDENDA.md`](../PREREG_PHASE2_ADDENDA.md); Phase 1 Addenda 1-3 and Phase 2's Addendum 1: the study log |
| study log (every decision, dated) | [`../PERFECT_LIE.md`](../PERFECT_LIE.md) |
| write-up (Methods, Findings, figures, claims manifest) | [`../writeup/`](../writeup/) |
| reproduction package, environment, dataset card, archive | [`../release/`](../release/) |
| instrument: personas, cues (rubric v0.6), prompts, notes, categories | [`data/perfect_lie/`](data/perfect_lie/), [`data/perfect_lie_reversed/`](data/perfect_lie_reversed/) |
| code | [`src/perfect_lie/`](src/perfect_lie/): prompts and conditions, runner and graders, the registered analyses (`sequential.py`, `final_analysis.py`, `reversed_analysis.py`, `phase2_*.py`) |
| run drivers | [`run_perfect_lie.py`](run_perfect_lie.py) (Phase 1), [`run_perfect_lie_reversed.py`](run_perfect_lie_reversed.py) (Phase 2); Phase 3 drivers in [`results/phase2/probe/`](results/phase2/probe/) |
| raw records and results | [`results/perfect_lie/`](results/perfect_lie/), [`results/perfect_lie_reversed/`](results/perfect_lie_reversed/), [`results/phase2/`](results/phase2/) |
| tests | [`tests/`](tests/) (`test_perfect_lie_*`, `test_phase2_*`) |

**Where the registrations live.** Each registration was published as the GitHub release of its tag (linked above), which
dates it. The registration texts and the study log say "posted on OSF"; in every case that post is the GitHub release.
Phase 3's Addenda 1-3 also appear in its release notes; every addendum is a dated commit of
`PREREG_PHASE2_ADDENDA.md`.

## Data and citation

- Dataset (every lie, note, prompt, judge verdict and grader output; Phase 3 probe directions and steering setups):
  [huggingface.co/datasets/RandallSPQR/perfect-lie](https://huggingface.co/datasets/RandallSPQR/perfect-lie) (gated),
  and the asset of release [`perfect-lie-release-v1`](https://github.com/RandallSPQR/edsl_wwil/releases/tag/perfect-lie-release-v1).
- Cite: [doi:10.5281/zenodo.24122306](https://doi.org/10.5281/zenodo.24122306) ([`../release/CITATION.cff`](../release/CITATION.cff)).

> Every story in the data is a deliberate lie, and many attribute invented events or harms to real, named
> organizations. None of it is true. See the dataset card before using them.

The game this study grew out of (Two Truths and a Lie with three storytellers) is in
[`../legacy_two_truths_game/`](../legacy_two_truths_game/); its engine still lives in `src/`.
