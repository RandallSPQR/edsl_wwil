# The Perfect Lie: release package

Reproduction package for three pre-registered studies of whether language models write lies to a judge's private
beliefs: **study 1** (full versus placebo note), the **reversed-note study** (full versus reversed note) and
**Phase 2** (an activation probe and steering on two open-weight liars). The Methods and Findings sections, figures
and claims manifest are in `two_truths_lie_study/writeup/`.

**Cite:** [doi:10.5281/zenodo.24122306](https://doi.org/10.5281/zenodo.24122306). **Dataset:** [Hugging Face](https://huggingface.co/datasets/RandallSPQR/perfect-lie) (gated: acknowledge the fabricated-content notice) and the release asset `perfect-lie-dataset-v1.tar.gz`.

## Tier 0: reproduce everything on a CPU (no network, no GPU, no API key)

Requirements: Linux or macOS, `git`, `make`, and either [uv](https://docs.astral.sh/uv/) or Docker; about 2 GB of free
disk (the environment about 400 MB, Tier 0's work tree about 450 MB, uv's own cache and Python about 450 MB). Setting up
the environment needs the network once (`make env` downloads about 150 MB: Python 3.11 and 22 packages; about 2 min);
Tier 0 itself never does.

```
git clone https://github.com/RandallSPQR/edsl_wwil.git && cd edsl_wwil
git checkout perfect-lie-release-v1          # the release tag
cd two_truths_lie_study
make env                                      # Python 3.11 + the pinned packages in release/.venv (uv)
make reproduce                                # Tier 0
```

Or with Docker instead of uv: `make docker-image` (once), then `make docker-reproduce` (runs with `--network none`).

Offline on either route: on the uv route every Tier 0 step runs with a socket guard (`release/tier0/netguard/`) that
refuses network connections and with the proxy variables removed, so a step that tried to reach the network would fail; the Docker route
removes the network altogether. Any Python 3.11 patch release works (tested: 3.11.15 from uv, 3.11.17, 3.11.18 in the
image); uv 0.11 or later.

`make reproduce` ends with `PASS` or `FAIL` and writes `build/tier0/two_truths_lie_study/release/TIER0_REPORT.md`
(and `tier0_report.json`); the claims checker's full output (the number of claims checked, every source hash) is in
`build/tier0/two_truths_lie_study/writeup/check_output.txt`. It takes about **27 minutes** on 4 CPUs (measured: 1,596 s; most of it two steps: the reversed-note
final analysis, about 10 min single-threaded, and one recomputed permutation chunk, about 15 min).

### What Tier 0 does

1. Copies this study tree into `build/tier0/`, deletes every result it is about to rebuild, and decompresses the raw
   records (`*.jsonl.gz`).
2. Runs each registered analysis script, unchanged, on the raw records: study 1's final analysis and its post hoc
   companion; the reversed note's final analysis, permutation check (one of its 20 chunks recomputed; all 20 with
   `make reproduce-full`, about 4.8 h) and post hoc scripts; Phase 2's identity check, grading-route check, pilot
   coherence, confirmatory alphas, method-check pre-check, stage-2 coherence, permutation check and the registered
   stage-2 analysis.
3. Compares every rebuilt file with the released one: **identical** (byte for byte), numerically equal (within 1e-9),
   or DIFFERENT.
4. Rebuilds the write-up there (`writeup/derive_levels.py`, `writeup/build.py`: Methods, Findings, captions, four
   figures, `CLAIMS_MANIFEST.csv`) and runs `writeup/check_claims.py`, which re-hashes every source the manifest cites
   and checks every number in the texts against them.

`PASS` means: every rebuilt file matches, and every claim in the manifest matches the rebuilt sources. Three
released files predate fields the current code adds, and one records the Python patch version that wrote it; Tier 0
reports these as "equal; ..." after checking every released value (`release/REPRODUCTION_NOTES.md`, items 3 and 8).

Files only a GPU or an API call can produce (the probe's activations and vectors, steering setups, the identity
check's pod lies) are inputs to Tier 0: it verifies their sha256 against `release/tier0/EXPECTED.json` and names the
tier that regenerates each.

### The environment is pinned for a reason

Python 3.11 with numpy 2.4.6, pandas 2.3.3, scipy 1.17.1, statsmodels 0.15.0, matplotlib 3.11.2 (`release/uv.lock`),
and **one BLAS thread** (Tier 0 sets it). Under newer numpy/pandas/scipy, Gemma 3 27B's registered mixed model in the
reversed-note study converges instead of falling back, and its Test B prints +0.431 instead of the registered +0.430;
with a multi-threaded BLAS, a robustness model's convergence flag flips. `reproduce.py` refuses an unpinned
environment. Details and evidence: `release/ENVIRONMENT.md`.

## Tiers 1-3 (optional; new model calls)

| tier | re-does | kind | cost (logged or estimated) |
|---|---|---|---|
| 1 | grading of the released lies (Anthropic API) | re-measurement | ≈ $27 / $55 / $36 for all lies of study 1 / reversed / Phase 2 |
| 2 | new lies, grading, analysis (OpenRouter) | **replication, not reproduction** | logged $63.73 (study 1) and $69.44 (reversed) |
| 3 | Phase 2 on the open weights (one 96 GB GPU) | re-computation | logged ≈ $16.5 of pod time + Tier 1 grading |

Scripts, commands and caveats (API model drift, retired models, hardware): `release/tiers/README.md`.

## Layout

```
two_truths_lie_study/
  Makefile                      env, reproduce, reproduce-full, docker-image, docker-reproduce, dataset, clean
  PREREG_DRAFT.md               study 1 registration (rev. 3)      } with PREREG_PHASE2_ADDENDA.md (Addenda 1-8) and
  PREREG_REVERSED.md            reversed-note registration         } PERFECT_LIE.md (the study log: study 1 Addenda
  PREREG_PHASE2.md              Phase 2 registration (rev. 4)      }  1-3, reversed Addendum 1, every decision)
  writeup/                      Methods, Findings, figures, CLAIMS_MANIFEST.csv, check_claims.py
  two_truths_lie/               code (src/perfect_lie), instrument (data/), raw records and results (results/)
  release/
    README.md                   this file
    ENVIRONMENT.md              the pinned environment and why
    REPRODUCTION_NOTES.md       what building Tier 0 found (versions, threads, file vintages, the permutation check)
    pyproject.toml, uv.lock     the environment (uv); requirements.lock.txt (pip, with hashes); Dockerfile
    tier0/                      reproduce.py, its helpers, EXPECTED.json (pins and sha256 of every released file)
    tiers/                      Tiers 1-3: scripts and README
    dataset/                    build_dataset.py, DATASET_CARD.md, hf_revisions.json
    environment_evidence/       the version and thread probes behind ENVIRONMENT.md
    fresh_run/                  independent Tier 0 runs on fresh clones by a README-only agent (logs, reports)
    ARCHIVE.md                  GitHub release, Hugging Face dataset, Zenodo DOI, registration record
    CITATION.cff
```

## Dataset

The dataset is published at https://huggingface.co/datasets/RandallSPQR/perfect-lie and as the release asset. `make dataset` rebuilds it (every lie, note, prompt, raw judge verdict and grader output,
comprehension answer, screen and adjudication; Phase 2 probe directions, per-layer AUROC tables and steering setups;
pinned Hugging Face revisions) into `build/dataset/`, with its card (`release/dataset/DATASET_CARD.md`). **The lies are
fabricated stories, many about real, named organizations; read the card's notice before using them.**
