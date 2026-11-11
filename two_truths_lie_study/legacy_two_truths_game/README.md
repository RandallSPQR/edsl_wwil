# Legacy: the original Two Truths and a Lie game

Files from the project that came before The Perfect Lie: a three-storyteller "Two Truths and a Lie" game played by
language models (baseline, championship, frame-break and phase 1-3 experiments), with its web interface and status
notes. They are kept here, unchanged, with their git history (moved on 2026-11-11 with `git mv`).

None of The Perfect Lie's code, registrations, analyses, write-up or reproduction package refers to them.

| here | was at |
|---|---|
| `two_truths_lie/` (run, analyze, monitor and test scripts, status notes, `edsl_data/`, the game's original `README.md`) | `two_truths_lie_study/two_truths_lie/` |
| `backend/`, `web/` (the game's web interface) | `two_truths_lie_study/` |
| `results/`, `experiment_results/` (the game's results) | `two_truths_lie_study/` |
| design and status notes (`API_TEST_RESULTS.md`, `MVP_STATUS.md`, ...) | `two_truths_lie_study/` |

Not moved, because the study cites them: the game's engine and tests (`two_truths_lie_study/two_truths_lie/src/`,
`tests/`), `two_truths_lie/PHASE2_SUMMARY.md` (cited by the frozen instrument) and `STUDY_DESIGN.md` and
`FEATURE_ROADMAP.md` (cited by the study log).

The scripts expect to run from `two_truths_lie_study/two_truths_lie/` (they import `src` relative to it); copy one
back there to run it.
