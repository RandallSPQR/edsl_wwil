# The pinned environment

Tier 0 runs in one environment: **Python 3.11, the exact package versions of `uv.lock`, and one BLAS thread.**

| package | version | source of the pin |
|---|---|---|
| Python | 3.11 (tested 3.11.15, 3.11.17, 3.11.18) | `requirements_review.txt` (3.11.17) |
| numpy | 2.4.6 | `requirements_review.txt` |
| pandas | 2.3.3 | `requirements_review.txt` |
| patsy | 1.0.3 | `requirements_review.txt` |
| scipy | 1.17.1 | `requirements_review.txt` |
| statsmodels | 0.15.0 | `requirements_review.txt` |
| matplotlib | 3.11.2 | the version the figures were drawn with |
| everything else | as locked | `uv.lock` / `requirements.lock.txt` (hashes) |

`requirements_review.txt` (in `two_truths_lie/results/perfect_lie_reversed/final_analysis/`) is the environment the
reversed-note final analysis was reviewed and unblinded in. Study 1 and Phase 2 analyses rebuild identically in it
(Tier 0 checks every file). No analysis needs EDSL, torch or a GPU.

## Why the versions are exact

The reversed-note registration fits a mixed model per liar (random condition slopes by category) and, if it does not
converge, falls back to a per-category t-test (PREREG_REVERSED section 4). Whether Gemma 3 27B's fit converges depends
on the numerical stack:

| stack | Gemma 3 27B, Test B | method |
|---|---|---|
| Python 3.11, numpy 2.4.6, pandas 2.3.3, scipy 1.17.1, statsmodels 0.15.0 (pinned) | **+0.430** (SE 0.0171) | per-category t-test (registered fallback: did not converge) |
| Python 3.13, numpy 2.5.3, pandas 3.0.5, scipy 1.18.1, statsmodels 0.15.0 | +0.431 (SE 0.0201) | mixed model (converges) |

The label (belief-tracking) is the same either way, but the registered estimate is the fallback's +0.430, and under
the newer stack 25 values in `final_report.json` change (Gemma's B, SE, t, df, Test A, its interval and the
tipping-point t). The other three liars fall back under both stacks with bit-identical estimates. Evidence:
`environment_evidence/` (`probe_primary.py`, output in `probe_output.txt`). The same note is in
`posthoc_google_testB.py` and `PERFECT_LIE.md` item 37.

## Why one BLAS thread

The registered robustness model m1 (`(1|category) + (1|persona)` variance components, PREREG_REVERSED section 4)
fits all of a liar's lies as one group. Its convergence flag sits at the optimizer's tolerance: with numpy's OpenBLAS
using 4 threads, the summation order changes the 16th significant digit of B and flips the flag for three liars
(Gemma 3 27B and gpt-4o-mini converged → not; Gemini 2.5 Flash-Lite not → converged). With one thread every value is
bit-identical to the release. The flag matters: a fit that did not converge makes no preservation claim, so the
write-up's "primary rejections preserved: 2 of 4" depends on it. Tier 0 sets `OPENBLAS_NUM_THREADS`, `OMP_NUM_THREADS`,
`MKL_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS` and `NUMEXPR_NUM_THREADS` to 1 for every step. (The primary fits do not
depend on the thread count; `probe_m1.py` shows the m1 flags under 1 and 4 threads.)

## Installing it

Either (both need the network once; Tier 0 itself never does):

- **uv** (recommended): `uv sync --frozen` in `release/` (creates `release/.venv` with Python 3.11; uv downloads Python
  3.11 if it is not installed). `make env` does this.
- **Docker**: `docker build -t perfect-lie-tier0 -f release/Dockerfile release`, then run Tier 0 with
  `--network none` (`make docker-reproduce`). The base image is pinned by digest and the packages are installed from
  `requirements.lock.txt` with hashes.
- **pip**: `python3.11 -m venv .venv && .venv/bin/pip install --require-hashes -r release/requirements.lock.txt`.

`reproduce.py` refuses to run if the installed versions differ from the pins (`--allow-unpinned` runs anyway and
reports what changes).

## What was run where (for the record)

| analysis | where it was originally run |
|---|---|
| Study 1 final analysis (2026-10-09) | not recorded; rebuilds byte-identically in the pinned environment |
| Reversed note final analysis, post hoc scripts (2026-10-20, 2026-10-22) | the pinned environment (`requirements_review.txt`) |
| Phase 2 analyses (2026-10-22 to 2026-10-27) | Python 3.13, `requirements_phase2.txt`; rebuild in the pinned environment as Tier 0 reports |
| Phase 2 activations, steering, NLL (pods) | torch 2.8, transformers 4.53.2, bf16, one RTX PRO 6000 Blackwell (Tier 3) |
