# Fresh Tier 0 run: independent reproduction log

## When and where

- Log written: 2026-10-29 (UTC). Run window: 2026-10-29T18:20:58Z (first command) to 2026-10-29T18:50:05Z (last check).
- Machine:
  - `nproc`: 4
  - `uname -a`: `Linux vm 6.18.44-fc-v185 #1 SMP PREEMPT_DYNAMIC @0 x86_64 x86_64 x86_64 GNU/Linux`
  - `uv --version`: `uv 0.11.32 (x86_64-unknown-linux-gnu)`
  - Memory 15 GB, no swap; 22 GB free disk at start.
- Clone: `/tmp/claude-0/-home-user-edsl-wwil/4699dee8-10e0-5f40-a807-efe82da6461d/scratchpad/fresh_run/edsl_wwil`
- Clone commit (`git -C <clone> rev-parse HEAD`): `9dc154ecf8a4ed5a8b9516f8faea407949488933`
- `git clone` and `git checkout perfect-lie-release-v1` were skipped as instructed (the tag does not exist yet); the clone stands in for them.

## Files read

- `two_truths_lie_study/release/README.md` (in full, before running anything).
- After the run, to locate the claims checker's count line (the TIER0_REPORT.md tail does not include it):
  `build/tier0/two_truths_lie_study/writeup/check_output.txt` and `build/tier0/two_truths_lie_study/release/tier0_report.json`
  (both outputs of the run, in `build/`). No other repository file was read; no failure needed diagnosing.

## Fresh environment

```
mkdir $F/uv_cache $F/uv_python          # both verified empty (ls -A printed nothing)
export UV_CACHE_DIR=$F/uv_cache
export UV_PYTHON_INSTALL_DIR=$F/uv_python
export UV_PYTHON_PREFERENCE=only-managed
```
(`$F` = `/tmp/claude-0/-home-user-edsl-wwil/4699dee8-10e0-5f40-a807-efe82da6461d/scratchpad/fresh_run`.) The same exports were used
for `make reproduce`. The ambient shell also had `UV_NATIVE_TLS=true` set by this machine's proxy setup (uv warned it is deprecated; harmless).
uv downloaded CPython 3.11.15 into `uv_python` (90 MB) and all 22 packages into `uv_cache` (347 MB).

## Commands

### 1. `make env` (run in `two_truths_lie_study/`)

- Command: `(time make env) > $F/make_env.out 2>&1`
- Start 2026-10-29T18:21:03Z, end 2026-10-29T18:22:42Z, exit code **0**, wall 1 m 38.5 s. Network used (python + package downloads).
- Make ran: `cd release && UV_PROJECT_ENVIRONMENT=.venv uv sync --frozen --python 3.11`
- First lines of output:
```
cd release && UV_PROJECT_ENVIRONMENT=.venv uv sync --frozen --python 3.11
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
Downloading cpython-3.11.15-linux-x86_64-gnu (download) (29.5MiB)
 Downloaded cpython-3.11.15-linux-x86_64-gnu (download)
Using CPython 3.11.15
Creating virtual environment at: .venv
```
- Last 40 lines of output:
```
Downloading pillow (6.8MiB)
Downloading pandas (12.2MiB)
Downloading statsmodels (11.5MiB)
Downloading matplotlib (9.4MiB)
 Downloaded kiwisolver
 Downloaded fonttools
 Downloaded pillow
 Downloaded matplotlib
 Downloaded statsmodels
 Downloaded pandas
 Downloaded numpy
 Downloaded scipy
Prepared 22 packages in 1m 35s
Installed 22 packages in 43ms
 + contourpy==1.3.3
 + cycler==0.12.1
 + fonttools==4.68.0
 + formulaic==1.2.2
 + interface-meta==2.0.1
 + kiwisolver==1.5.1
 + matplotlib==3.11.2
 + narwhals==2.28.0
 + numpy==2.4.6
 + packaging==26.3
 + pandas==2.3.3
 + patsy==1.0.3
 + pillow==13.0.0
 + pyparsing==3.3.3
 + python-dateutil==3.0.0
 + pytz==2026.6
 + scipy==1.17.1
 + six==1.17.0
 + statsmodels==0.15.0
 + typing-extensions==4.16.0
 + tzdata==2026.6
 + wrapt==2.5.1

real	1m38.528s
user	0m3.108s
sys	0m4.200s
```

### 2. `make reproduce` (run in `two_truths_lie_study/`, background)

- Command: `nohup bash -c "(time make reproduce) > $F/make_reproduce.out 2>&1; echo EXIT=\$? >> $F/make_reproduce.out" &`
  (same three UV_* exports). Waited with `until grep -q EXIT= ...; do sleep 20; done` (three waits). One copy only. No network needed or used by me during this step; no model/API calls.
- Start 2026-10-29T18:22:50Z, end 2026-10-29T18:49:19Z, exit code **0**.
- **Measured wall-clock: 26 m 29.3 s** (`time`: real 26m29.346s, user 68m0.360s, sys 0m20.206s). reproduce.py itself reported 1589 s (26.5 min); README states about 27 min / 1,596 s on 4 CPUs.
- Full output (33 lines, i.e. all of it):
```
release/.venv/bin/python release/tier0/reproduce.py --work build/tier0 --perm-chunks 1
environment: {'python': '3.11.15', 'numpy': '2.4.6', 'pandas': '2.3.3', 'patsy': '1.0.3', 'scipy': '1.17.1', 'statsmodels': '0.15.0', 'matplotlib': '3.11.2'}
work tree /tmp/claude-0/-home-user-edsl-wwil/4699dee8-10e0-5f40-a807-efe82da6461d/scratchpad/fresh_run/edsl_wwil/two_truths_lie_study/build/tier0/two_truths_lie_study ready in 6 s (15 record files decompressed)
[ok] s1.final                      16.5 s  final_report.json: identical, final_report.md: identical
[ok] s1.gpt5                        1.9 s  gpt5_same_units.json: identical
[ok] rv.final                     568.5 s  final_report.json: identical, final_report.md: identical
[ok] rv.perm_chunk                896.8 s  
[ok] rv.perm                        7.3 s  perm_check.json: identical
[ok] rv.posthoc_comp                3.7 s  posthoc_comprehension_parsed.json: identical
[ok] rv.posthoc_google             24.2 s  posthoc_google_testB.json: equal; only the recorded environment differs (/environment/python 3.11.17 -> 3.11.15), posthoc_google_testB.md: identical
[ok] p2.identity                    5.1 s  behavioral_result.json: equal; current code adds variant (950e8a7 added --variant after this result (2c8111c) was written)
[ok] p2.identity_novita             4.3 s  behavioral_result_novita.json: identical
[ok] p2.route                       1.1 s  regrade_direct.json: identical
[ok] p2.pilot.llama-3.1-8b-instruct     0.5 s  pilot_result.json: identical, PILOT.md: identical
[ok] p2.pilot.gemma-3-27b-it        0.6 s  pilot_result.json: identical, PILOT.md: identical
[ok] p2.pilot2.llama-3.1-8b-instruct     0.5 s  pilot2_result.json: identical, PILOT2.md: identical
[ok] p2.pilot2.gemma-3-27b-it       0.6 s  pilot2_result.json: identical, PILOT2.md: identical
[ok] p2.alphas                      0.0 s  confirmatory_alphas.json: identical
[ok] p2.mc.llama-3.1-8b-instruct     0.2 s  mc_precheck.json: identical, MC_PRECHECK.md: identical
[ok] p2.mc.gemma-3-27b-it           0.3 s  mc_precheck.json: identical, MC_PRECHECK.md: identical
[ok] p2.coherence                   1.4 s  coherence.json: equal; current code adds n_complete, generation_failed (Addendum 8 (f4a70a7) added these counts after this file (8e66e71) was written; 0 failures), grading_summary.json: identical, coherence.json: equal; current code adds n_complete, generation_failed (Addendum 8 (f4a70a7) added these counts after this file (8e66e71) was written; 0 failures), grading_summary.json: identical
[ok] p2.permcheck                  16.2 s  permutation_check.json: identical
[ok] p2.analyse                    17.0 s  stage2_result.json: identical, STAGE2.md: identical
[ok] w.levels                       6.5 s  levels.json: identical
[ok] w.build                        2.8 s  METHODS.md: identical, FINDINGS.md: identical, FIGURES.md: identical, CLAIMS_MANIFEST.csv: identical, fig1_study1_lift.png: identical, fig2_reversed_levels.png: identical, fig3_steering_levels.png: identical, fig4_method_check.png: identical
[ok] w.check                        6.9 s  

PASS: Tier 0 in 1589 s; rebuilt {'identical': 37, 'numerically equal': 0, 'equal': 4, 'DIFFERENT': 0, 'MISSING': 0}; report: /tmp/claude-0/-home-user-edsl-wwil/4699dee8-10e0-5f40-a807-efe82da6461d/scratchpad/fresh_run/edsl_wwil/two_truths_lie_study/build/tier0/two_truths_lie_study/release/TIER0_REPORT.md

real	26m29.346s
user	68m0.360s
sys	0m20.206s
EXIT=0
```

### 3. Post-run checks (read-only)

- 2026-10-29T18:49:34Z: `cat` of the output, `ls` of `build/tier0/two_truths_lie_study/release/`, `cat TIER0_REPORT.md`, `git status --short` (exit 0, empty).
- 2026-10-29T18:50:05Z: `git -C <clone> status --short --ignored` (exit 0):
```
!! two_truths_lie_study/build/
!! two_truths_lie_study/release/.venv/
!! two_truths_lie_study/release/tier0/netguard/__pycache__/
```
  No tracked file changed. The three ignored paths were created by `make env` / `make reproduce` (the `__pycache__` by Python importing `release/tier0/netguard`).
- Disk used: `release/.venv` 385 MB; `build/` 777 MB (of which 347 MB is a copy of `release/.venv` inside `build/tier0/two_truths_lie_study/release/.venv`); plus uv cache 347 MB and uv Python 90 MB outside the clone.

## TIER0_REPORT.md (full contents)

Path: `two_truths_lie_study/build/tier0/two_truths_lie_study/release/TIER0_REPORT.md`

````markdown
# Tier 0 report

**PASS** in 26.5 min (4 CPUs, Linux-6.18.44-fc-v185-x86_64-with-glibc2.39, Python 3.11.15).

Rebuilt files: 37 identical, 0 numerically equal, 4 equal, 0 DIFFERENT, 0 MISSING.

| step | what | seconds | outputs |
|---|---|---|---|
| s1.final | Study 1: registered final analysis (sections 4-8, Addenda 1-3) | 16.5 | `final_report.json` identical; `final_report.md` identical |
| s1.gpt5 | Study 1: post hoc, gpt-5 subsample units scored by the primary grader | 1.9 | `gpt5_same_units.json` identical |
| rv.final | Reversed note: registered final analysis (sections 4, 5, 7, 11a, 11) | 568.5 | `final_report.json` identical; `final_report.md` identical |
| rv.perm_chunk | Reversed note: blinded permutation check, sample chunks recomputed and compared | 896.8 | ok |
| rv.perm | Reversed note: permutation check assembled from its 20 chunks (section 4a) | 7.3 | `perm_check.json` identical |
| rv.posthoc_comp | Reversed note: post hoc, comprehension on parseable answers | 3.7 | `posthoc_comprehension_parsed.json` identical |
| rv.posthoc_google | Reversed note: post hoc, Test B from the Google grader | 24.2 | `posthoc_google_testB.json` equal; only the recorded environment differs (/environment/python 3.11.17 -> 3.11.15); `posthoc_google_testB.md` identical |
| p2.identity | Phase 2: identity check, behavioral equivalence (section 2) | 5.1 | `behavioral_result.json` equal; current code adds variant (950e8a7 added --variant after this result (2c8111c) was written) |
| p2.identity_novita | Phase 2: identity check, Gemma template re-test | 4.3 | `behavioral_result_novita.json` identical |
| p2.route | Phase 2: grading-route check summary from its stored labels (section 11) | 1.1 | `regrade_direct.json` identical |
| p2.pilot.llama-3.1-8b-instruct | Phase 2: stage-1 pilot coherence, meta-llama/llama-3.1-8b-instruct (section 6, Addendum 4) | 0.5 | `pilot_result.json` identical; `PILOT.md` identical |
| p2.pilot.gemma-3-27b-it | Phase 2: stage-1 pilot coherence, google/gemma-3-27b-it (section 6, Addendum 4) | 0.6 | `pilot_result.json` identical; `PILOT.md` identical |
| p2.pilot2.llama-3.1-8b-instruct | Phase 2: pilot with the Addendum 5 placebo, meta-llama/llama-3.1-8b-instruct | 0.5 | `pilot2_result.json` identical; `PILOT2.md` identical |
| p2.pilot2.gemma-3-27b-it | Phase 2: pilot with the Addendum 5 placebo, google/gemma-3-27b-it | 0.6 | `pilot2_result.json` identical; `PILOT2.md` identical |
| p2.alphas | Phase 2: confirmatory alphas from the two pilots (alpha rule, section 6) | 0.0 | `confirmatory_alphas.json` identical |
| p2.mc.llama-3.1-8b-instruct | Phase 2: method-check coherence pre-check, meta-llama/llama-3.1-8b-instruct (Addendum 7) | 0.2 | `mc_precheck.json` identical; `MC_PRECHECK.md` identical |
| p2.mc.gemma-3-27b-it | Phase 2: method-check coherence pre-check, google/gemma-3-27b-it (Addendum 7) | 0.3 | `mc_precheck.json` identical; `MC_PRECHECK.md` identical |
| p2.coherence | Phase 2: stage-2 coherence gate and grading summaries (sections 6, 7a) | 1.4 | `coherence.json` equal; current code adds n_complete, generation_failed (Addendum 8 (f4a70a7) added these counts after this file (8e66e71) was written; 0 failures); `grading_summary.json` identical; `coherence.json` equal; current code adds n_complete, generation_failed (Addendum 8 (f4a70a7) added these counts after this file (8e66e71) was written; 0 failures); `grading_summary.json` identical |
| p2.permcheck | Phase 2: blinded permutation check (section 10) | 16.2 | `permutation_check.json` identical |
| p2.analyse | Phase 2: registered stage-2 analysis (sections 7, 7a, 8, 9; Addendum 2) | 17.0 | `stage2_result.json` identical; `STAGE2.md` identical |
| w.levels | Write-up: descriptive levels for figures 2 and 3 | 6.5 | `levels.json` identical |
| w.build | Write-up: Methods, Findings, captions, figures, claims manifest | 2.8 | `METHODS.md` identical; `FINDINGS.md` identical; `FIGURES.md` identical; `CLAIMS_MANIFEST.csv` identical; `fig1_study1_lift.png` identical; `fig2_reversed_levels.png` identical; `fig3_steering_levels.png` identical; `fig4_method_check.png` identical |
| w.check | Write-up: claims check (every manifest value against the rebuilt sources) | 6.9 | ok |

Inputs carried over (not CPU-derivable), verified by sha256:

- `two_truths_lie/results/phase2/probe/gemma-3-27b-it/probe_result.json`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/probe/gemma-3-27b-it/vectors.npz`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/probe/gemma-3-27b-it/diagnostics.json`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/probe/gemma-3-27b-it/scale.json`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/probe/llama-3.1-8b-instruct/probe_result.json`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/probe/llama-3.1-8b-instruct/vectors.npz`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/probe/llama-3.1-8b-instruct/diagnostics.json`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/probe/llama-3.1-8b-instruct/scale.json`: sha256 ok (Tier 3 (GPU): needs the probe-stage activations)
- `two_truths_lie/results/phase2/pilot/llama-3.1-8b-instruct/setup.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/pilot/llama-3.1-8b-instruct/setup_placebo2.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/pilot/llama-3.1-8b-instruct/mc_precheck_setup.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/pilot/gemma-3-27b-it/setup.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/pilot/gemma-3-27b-it/setup_placebo2.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/pilot/gemma-3-27b-it/mc_precheck_setup.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/stage2/llama-3.1-8b-instruct/setup.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/stage2/llama-3.1-8b-instruct/natural.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/stage2/gemma-3-27b-it/setup.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/stage2/gemma-3-27b-it/natural.json`: sha256 ok (Tier 3 (GPU): computed on the pod from the model's activations)
- `two_truths_lie/results/phase2/identity_check/pod_run/records.jsonl`: sha256 ok (Tier 3 (GPU) generation, Tier 1 (API) grading)
- `two_truths_lie/results/phase2/identity_check/pod_run_novita/records.jsonl`: sha256 ok (Tier 3 (GPU) generation, Tier 1 (API) grading)
- `two_truths_lie/results/perfect_lie/interim_look/interim_blind.json`: sha256 ok (frozen at the interim by registration (section 6); the final analysis recomputes the gate and checks it matches)
- `two_truths_lie/results/perfect_lie_reversed/final_analysis/perm_chunks`: sha256 ok (decision counts per chunk; Tier 0 recomputes a sample (rv.perm_chunk), make reproduce-full all)

Claims check output (tail):

```
/llama-3.1-8b-instruct/probe_result.json
  7894aa3e7dd3ab156a2142c3d8c74d7b407f17189353ee1a7cc149de8a36c9a1  two_truths_lie/results/phase2/stage2/gemma-3-27b-it/coherence.json
  7717eb1ac8dab552fd47d11d206298970588d41030a4f10791ae075d520be0df  two_truths_lie/results/phase2/stage2/gemma-3-27b-it/grading_summary.json
  6a95660a570a524af5a6df01fca1cef2f1b05ec5c3ca1ce2a3401ecec450be71  two_truths_lie/results/phase2/stage2/llama-3.1-8b-instruct/coherence.json
  b0508f243113684707f90873b2712cdc841f743b8ec307fc108fe6f18477cd7b  two_truths_lie/results/phase2/stage2/llama-3.1-8b-instruct/grading_summary.json
  9c1e1e8edd85933eb7a1e69a274b47b7166ddb7a780cbbd1f8aa794022701874  two_truths_lie/results/phase2/stage2/permutation_check.json
  440c5b3ac56ed712d7e05c925d21c14a7aa3415802a1e7ce51c89f5f479db31a  two_truths_lie/results/phase2/stage2/stage2_result.json
spelled-out numbers in the texts (structural counts, for review): five x2, four x11, one x11, three x3, two x9
levels.json re-derived from the committed records; texts re-rendered by build.py

PASS: every manifest value matches its source, every number in the texts is a claim or a whitelisted identifier, and the texts and levels reproduce.
```
````

## Verdict

**(a) PASS or FAIL:** Tier 0 reported **PASS** (`PASS: Tier 0 in 1589 s; rebuilt {'identical': 37, 'numerically equal': 0, 'equal': 4, 'DIFFERENT': 0, 'MISSING': 0}`), exit code 0; `tier0_report.json` has `"passed": true`.

**(b) Claims manifest:** every value matched. The claims checker's lines (from `build/tier0/two_truths_lie_study/writeup/check_output.txt`, lines 1 and 39; the count line is *not* in TIER0_REPORT.md, whose tail starts mid-way through the source list):
```
claims checked: 446
by label: design constant (registration) 36; exploratory 14; post hoc (descriptive) 17; registered primary 151; registered secondary 228
sources (32), sha256 verified:
...
PASS: every manifest value matches its source, every number in the texts is a claim or a whitelisted identifier, and the texts and levels reproduce.
```
The PASS line is also in TIER0_REPORT.md. The `w.check` step reported ok.

**(c) Rebuilt files reported as other than "identical":** 4 files reported "equal" (none numerically equal, DIFFERENT or MISSING):
1. `posthoc_google_testB.json` (step rv.posthoc_google): "equal; only the recorded environment differs (/environment/python 3.11.17 -> 3.11.15)".
2. `behavioral_result.json` (step p2.identity): "equal; current code adds variant (950e8a7 added --variant after this result (2c8111c) was written)".
3. and 4. `coherence.json`, twice (step p2.coherence; presumably one per model, but the report prints bare file names so the two entries are indistinguishable): "equal; current code adds n_complete, generation_failed (Addendum 8 (f4a70a7) added these counts after this file (8e66e71) was written; 0 failures)".
This matches the README's statement that three released files predate fields the current code adds and one records the Python patch version. The rv.perm_chunk step recomputed 1 of 20 chunks (chunk 0) and reported `"identical_counts": true`. All 22 carried-over inputs reported "sha256 ok".

**(d) README issues for a newcomer** (observed, not speculated):
1. Heading says "Tier 0 in three commands", but the block has five command lines (clone, checkout, cd, make env, make reproduce). Minor.
2. The tag `perfect-lie-release-v1` does not exist yet (known; skipped per instructions). Until it is created, the `git checkout` line fails for a newcomer.
3. Disk: README says "about 1 GB of free disk". Measured: 385 MB `release/.venv` + 777 MB `build/` (which includes a 347 MB copy of the venv, since the work tree copy includes `release/.venv`) = about 1.16 GB inside the clone, plus about 437 MB of uv cache and managed Python outside it (about 1.6 GB total on a machine with no cached uv content). The figure is slightly low.
4. The Layout section lists `release/fresh_run/` ("the independent Tier 0 run on a fresh clone (log and report)"), but that directory does not exist at commit 9dc154e.
5. The README says where TIER0_REPORT.md is written, but not that the claims checker's full output (including the "claims checked: N" line) is at `build/tier0/two_truths_lie_study/writeup/check_output.txt`; the report only includes a tail that omits the count.
6. In the report, the p2.coherence row lists `coherence.json` and `grading_summary.json` twice each with no directory, so one cannot tell which model each refers to without opening `tier0_report.json` or the code.
7. Not a README defect, but worth knowing: `make env` downloads about 150 MB (Python 29.5 MB plus wheels) and took 1 m 38 s here; the README does not give a size or time for it.
Everything else the README states that I could observe held: `make env` produced Python 3.11 with the listed pins (numpy 2.4.6, pandas 2.3.3, scipy 1.17.1, statsmodels 0.15.0, matplotlib 3.11.2); `make reproduce` ended with PASS, wrote TIER0_REPORT.md and tier0_report.json at the stated path, and took 26.5 min on 4 CPUs (README: about 27 min, 1,596 s), with rv.final (568.5 s, about 9.5 min) and rv.perm_chunk (896.8 s, about 15 min) as the two long steps, as stated. Not tested: the Docker route, `make reproduce-full`, the unpinned-environment refusal, and whether Tier 0 blocks network access.
