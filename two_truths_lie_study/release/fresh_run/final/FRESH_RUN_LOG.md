# Fresh Tier 0 run log (README-only reproducer)

## When and where

- Log written: 2026-10-29T19:50:13Z (UTC). Session started 2026-10-29T19:21:37Z.
- `nproc`: 4
- `uname -a`: Linux vm 6.18.44-fc-v185 #1 SMP PREEMPT_DYNAMIC @0 x86_64 x86_64 x86_64 GNU/Linux
- `uv --version`: uv 0.11.32 (x86_64-unknown-linux-gnu) (at /root/.local/bin/uv)
- Clone: /tmp/claude-0/-home-user-edsl-wwil/4699dee8-10e0-5f40-a807-efe82da6461d/scratchpad/fresh_run/edsl_wwil
- `git -C <clone> rev-parse HEAD`: cfcd87068b63947d1e8af1b8ede7dbf526e2d0fb (clean working tree before the run)
- The README's `git clone` and `git checkout perfect-lie-release-v1` were skipped as instructed (tag not yet created); started from `cd two_truths_lie_study`.

## Files read

- Only `two_truths_lie_study/release/README.md`. No other repository file was opened; no failure needed diagnosing.
  (The run's outputs in `build/` — TIER0_REPORT.md and writeup/check_output.txt — were read because the README points to them.)

## Fresh environment

```
mkdir $FR/uv_cache $FR/uv_python           # both confirmed empty
export UV_CACHE_DIR=$FR/uv_cache
export UV_PYTHON_INSTALL_DIR=$FR/uv_python
export UV_PYTHON_PREFERENCE=only-managed
```
($FR = /tmp/claude-0/-home-user-edsl-wwil/4699dee8-10e0-5f40-a807-efe82da6461d/scratchpad/fresh_run; same exports used for both make commands.)

## Command 1: `make env`

- Run from `<clone>/two_truths_lie_study` as `(time make env) > $FR/make_env.out 2>&1`
- Start 2026-10-29T19:21:41Z, end 2026-10-29T19:21:51Z, exit code 0 (wall 10.0 s)
- uv downloaded its own CPython 3.11.15 into the empty uv_python dir and 22 packages into the empty cache (so nothing from the machine was reused).
- Full output (51 lines):

```
cd release && UV_PROJECT_ENVIRONMENT=.venv uv sync --frozen --python 3.11
warning: The `UV_NATIVE_TLS` environment variable is deprecated and will be removed in a future release. Use `UV_SYSTEM_CERTS` instead.
Downloading cpython-3.11.15-linux-x86_64-gnu (download) (29.5MiB)
 Downloaded cpython-3.11.15-linux-x86_64-gnu (download)
Using CPython 3.11.15
Creating virtual environment at: .venv
Downloading scipy (33.7MiB)
Downloading matplotlib (9.4MiB)
Downloading pillow (6.8MiB)
Downloading fonttools (5.2MiB)
Downloading statsmodels (11.5MiB)
Downloading numpy (16.1MiB)
Downloading kiwisolver (1.4MiB)
Downloading pandas (12.2MiB)
 Downloaded kiwisolver
 Downloaded fonttools
 Downloaded pillow
 Downloaded matplotlib
 Downloaded statsmodels
 Downloaded pandas
 Downloaded numpy
 Downloaded scipy
Prepared 22 packages in 7.13s
Installed 22 packages in 52ms
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

real	0m9.994s
user	0m2.344s
sys	0m1.751s
EXIT=0
```

Note: the `UV_NATIVE_TLS` deprecation warning comes from this machine's environment (proxy setup), not from the README.

## Command 2: `make reproduce`

- Launched in the background: `cd <clone>/two_truths_lie_study && (time make reproduce) > $FR/make_reproduce.out 2>&1; echo EXIT=$? >> $FR/make_reproduce.out` (with nohup; same exports). One copy only.
- Start 2026-10-29T19:22:01Z, end 2026-10-29T19:49:05Z, exit code 0
- Measured wall-clock: **27 min 3.8 s (1623.8 s)** by `time`; reproduce.py itself reports 1624 s (27.1 min). README's figure: about 27 min (measured 1,596 s) on 4 CPUs.
- Network: was available on this machine during the run (no isolation was imposed); the output shows no download activity. I did not independently verify that Tier 0 makes no network access.
- Full output (33 lines, i.e. all of it):

```
release/.venv/bin/python release/tier0/reproduce.py --work build/tier0 --perm-chunks 1
environment: {'python': '3.11.15', 'numpy': '2.4.6', 'pandas': '2.3.3', 'patsy': '1.0.3', 'scipy': '1.17.1', 'statsmodels': '0.15.0', 'matplotlib': '3.11.2'}
work tree /tmp/claude-0/-home-user-edsl-wwil/4699dee8-10e0-5f40-a807-efe82da6461d/scratchpad/fresh_run/edsl_wwil/two_truths_lie_study/build/tier0/two_truths_lie_study ready in 3 s (15 record files decompressed)
[ok] s1.final                      12.4 s  final_report.json: identical, final_report.md: identical
[ok] s1.gpt5                        1.6 s  gpt5_same_units.json: identical
[ok] rv.final                     570.1 s  final_report.json: identical, final_report.md: identical
[ok] rv.perm_chunk                911.0 s  
[ok] rv.perm                        9.6 s  perm_check.json: identical
[ok] rv.posthoc_comp                6.0 s  posthoc_comprehension_parsed.json: identical
[ok] rv.posthoc_google             26.4 s  posthoc_google_testB.json: equal; only the recorded environment differs (/environment/python 3.11.17 -> 3.11.15), posthoc_google_testB.md: identical
[ok] p2.identity                    6.3 s  behavioral_result.json: equal; current code adds variant (950e8a7 added --variant after this result (2c8111c) was written)
[ok] p2.identity_novita             5.5 s  behavioral_result_novita.json: identical
[ok] p2.route                       3.0 s  regrade_direct.json: identical
[ok] p2.pilot.llama-3.1-8b-instruct     0.7 s  llama-3.1-8b-instruct/pilot_result.json: identical, llama-3.1-8b-instruct/PILOT.md: identical
[ok] p2.pilot.gemma-3-27b-it        0.9 s  gemma-3-27b-it/pilot_result.json: identical, gemma-3-27b-it/PILOT.md: identical
[ok] p2.pilot2.llama-3.1-8b-instruct     0.8 s  llama-3.1-8b-instruct/pilot2_result.json: identical, llama-3.1-8b-instruct/PILOT2.md: identical
[ok] p2.pilot2.gemma-3-27b-it       0.8 s  gemma-3-27b-it/pilot2_result.json: identical, gemma-3-27b-it/PILOT2.md: identical
[ok] p2.alphas                      0.0 s  confirmatory_alphas.json: identical
[ok] p2.mc.llama-3.1-8b-instruct     0.4 s  llama-3.1-8b-instruct/mc_precheck.json: identical, llama-3.1-8b-instruct/MC_PRECHECK.md: identical
[ok] p2.mc.gemma-3-27b-it           0.4 s  gemma-3-27b-it/mc_precheck.json: identical, gemma-3-27b-it/MC_PRECHECK.md: identical
[ok] p2.coherence                   1.7 s  llama-3.1-8b-instruct/coherence.json: equal; current code adds n_complete, generation_failed (Addendum 8 (f4a70a7) added these counts after this file (8e66e71) was written; 0 failures), llama-3.1-8b-instruct/grading_summary.json: identical, gemma-3-27b-it/coherence.json: equal; current code adds n_complete, generation_failed (Addendum 8 (f4a70a7) added these counts after this file (8e66e71) was written; 0 failures), gemma-3-27b-it/grading_summary.json: identical
[ok] p2.permcheck                  19.4 s  permutation_check.json: identical
[ok] p2.analyse                    20.2 s  stage2_result.json: identical, STAGE2.md: identical
[ok] w.levels                       8.7 s  levels.json: identical
[ok] w.build                        4.3 s  METHODS.md: identical, FINDINGS.md: identical, FIGURES.md: identical, CLAIMS_MANIFEST.csv: identical, fig1_study1_lift.png: identical, fig2_reversed_levels.png: identical, fig3_steering_levels.png: identical, fig4_method_check.png: identical
[ok] w.check                       10.0 s  check_output.txt: identical

PASS: Tier 0 in 1624 s; rebuilt {'identical': 38, 'numerically equal': 0, 'equal': 4, 'DIFFERENT': 0, 'MISSING': 0}; report: /tmp/claude-0/-home-user-edsl-wwil/4699dee8-10e0-5f40-a807-efe82da6461d/scratchpad/fresh_run/edsl_wwil/two_truths_lie_study/build/tier0/two_truths_lie_study/release/TIER0_REPORT.md

real	27m3.813s
user	69m15.333s
sys	0m10.512s
EXIT=0
```

## Post-run checks

- `git -C <clone> status --short --ignored`: only `!! two_truths_lie_study/build/` and `!! two_truths_lie_study/release/.venv/`; `git diff` empty. No tracked file was changed.
- Disk: build/ 429 MB; release/.venv 347 MB (hard-linked to the uv cache, link count 2, so shared); uv_cache 347 MB; uv_python 90 MB. Total roughly 0.9 GB, inside the README's "about 2 GB".

## TIER0_REPORT.md (full contents)

Path: `build/tier0/two_truths_lie_study/release/TIER0_REPORT.md`

````
# Tier 0 report

**PASS** in 27.1 min (4 CPUs, Linux-6.18.44-fc-v185-x86_64-with-glibc2.39, Python 3.11.15).

Rebuilt files: 38 identical, 0 numerically equal, 4 equal, 0 DIFFERENT, 0 MISSING.

| step | what | seconds | outputs |
|---|---|---|---|
| s1.final | Study 1: registered final analysis (sections 4-8, Addenda 1-3) | 12.4 | `final_report.json` identical; `final_report.md` identical |
| s1.gpt5 | Study 1: post hoc, gpt-5 subsample units scored by the primary grader | 1.6 | `gpt5_same_units.json` identical |
| rv.final | Reversed note: registered final analysis (sections 4, 5, 7, 11a, 11) | 570.1 | `final_report.json` identical; `final_report.md` identical |
| rv.perm_chunk | Reversed note: blinded permutation check, sample chunks recomputed and compared | 911.0 | ok |
| rv.perm | Reversed note: permutation check assembled from its 20 chunks (section 4a) | 9.6 | `perm_check.json` identical |
| rv.posthoc_comp | Reversed note: post hoc, comprehension on parseable answers | 6.0 | `posthoc_comprehension_parsed.json` identical |
| rv.posthoc_google | Reversed note: post hoc, Test B from the Google grader | 26.4 | `posthoc_google_testB.json` equal; only the recorded environment differs (/environment/python 3.11.17 -> 3.11.15); `posthoc_google_testB.md` identical |
| p2.identity | Phase 2: identity check, behavioral equivalence (section 2) | 6.3 | `behavioral_result.json` equal; current code adds variant (950e8a7 added --variant after this result (2c8111c) was written) |
| p2.identity_novita | Phase 2: identity check, Gemma template re-test | 5.5 | `behavioral_result_novita.json` identical |
| p2.route | Phase 2: grading-route check summary from its stored labels (section 11) | 3.0 | `regrade_direct.json` identical |
| p2.pilot.llama-3.1-8b-instruct | Phase 2: stage-1 pilot coherence, meta-llama/llama-3.1-8b-instruct (section 6, Addendum 4) | 0.7 | `llama-3.1-8b-instruct/pilot_result.json` identical; `llama-3.1-8b-instruct/PILOT.md` identical |
| p2.pilot.gemma-3-27b-it | Phase 2: stage-1 pilot coherence, google/gemma-3-27b-it (section 6, Addendum 4) | 0.9 | `gemma-3-27b-it/pilot_result.json` identical; `gemma-3-27b-it/PILOT.md` identical |
| p2.pilot2.llama-3.1-8b-instruct | Phase 2: pilot with the Addendum 5 placebo, meta-llama/llama-3.1-8b-instruct | 0.8 | `llama-3.1-8b-instruct/pilot2_result.json` identical; `llama-3.1-8b-instruct/PILOT2.md` identical |
| p2.pilot2.gemma-3-27b-it | Phase 2: pilot with the Addendum 5 placebo, google/gemma-3-27b-it | 0.8 | `gemma-3-27b-it/pilot2_result.json` identical; `gemma-3-27b-it/PILOT2.md` identical |
| p2.alphas | Phase 2: confirmatory alphas from the two pilots (alpha rule, section 6) | 0.0 | `confirmatory_alphas.json` identical |
| p2.mc.llama-3.1-8b-instruct | Phase 2: method-check coherence pre-check, meta-llama/llama-3.1-8b-instruct (Addendum 7) | 0.4 | `llama-3.1-8b-instruct/mc_precheck.json` identical; `llama-3.1-8b-instruct/MC_PRECHECK.md` identical |
| p2.mc.gemma-3-27b-it | Phase 2: method-check coherence pre-check, google/gemma-3-27b-it (Addendum 7) | 0.4 | `gemma-3-27b-it/mc_precheck.json` identical; `gemma-3-27b-it/MC_PRECHECK.md` identical |
| p2.coherence | Phase 2: stage-2 coherence gate and grading summaries (sections 6, 7a) | 1.7 | `llama-3.1-8b-instruct/coherence.json` equal; current code adds n_complete, generation_failed (Addendum 8 (f4a70a7) added these counts after this file (8e66e71) was written; 0 failures); `llama-3.1-8b-instruct/grading_summary.json` identical; `gemma-3-27b-it/coherence.json` equal; current code adds n_complete, generation_failed (Addendum 8 (f4a70a7) added these counts after this file (8e66e71) was written; 0 failures); `gemma-3-27b-it/grading_summary.json` identical |
| p2.permcheck | Phase 2: blinded permutation check (section 10) | 19.4 | `permutation_check.json` identical |
| p2.analyse | Phase 2: registered stage-2 analysis (sections 7, 7a, 8, 9; Addendum 2) | 20.2 | `stage2_result.json` identical; `STAGE2.md` identical |
| w.levels | Write-up: descriptive levels for figures 2 and 3 | 8.7 | `levels.json` identical |
| w.build | Write-up: Methods, Findings, captions, figures, claims manifest | 4.3 | `METHODS.md` identical; `FINDINGS.md` identical; `FIGURES.md` identical; `CLAIMS_MANIFEST.csv` identical; `fig1_study1_lift.png` identical; `fig2_reversed_levels.png` identical; `fig3_steering_levels.png` identical; `fig4_method_check.png` identical |
| w.check | Write-up: claims check (every manifest value against the rebuilt sources) | 10.0 | `check_output.txt` identical |

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

Claims check output (head and tail; in full in the work tree's `writeup/check_output.txt`):

```
claims checked: 446
by label: design constant (registration) 36; exploratory 14; post hoc (descriptive) 17; registered primary 151; registered secondary 228
sources (32), sha256 verified:
  e728effbf3db6bffc4e28469a7f1301244ed524ecfe8f684d2f341ab996e78fb  PREREG_DRAFT.md
  349cbe5a6757357920eb55c5c2
...
b8ec307fc108fe6f18477cd7b  two_truths_lie/results/phase2/stage2/llama-3.1-8b-instruct/grading_summary.json
  9c1e1e8edd85933eb7a1e69a274b47b7166ddb7a780cbbd1f8aa794022701874  two_truths_lie/results/phase2/stage2/permutation_check.json
  440c5b3ac56ed712d7e05c925d21c14a7aa3415802a1e7ce51c89f5f479db31a  two_truths_lie/results/phase2/stage2/stage2_result.json
spelled-out numbers in the texts (structural counts, for review): five x2, four x11, one x11, three x3, two x9
levels.json re-derived from the committed records; texts re-rendered by build.py

PASS: every manifest value matches its source, every number in the texts is a claim or a whitelisted identifier, and the texts and levels reproduce.
```
````

## Verdict

**(a) Tier 0 result: PASS.** Final line: `PASS: Tier 0 in 1624 s; rebuilt {'identical': 38, 'numerically equal': 0, 'equal': 4, 'DIFFERENT': 0, 'MISSING': 0}`; `make reproduce` exit code 0.

**(b) Claims manifest: every value matched.** From `build/tier0/two_truths_lie_study/writeup/check_output.txt`:
- `claims checked: 446`
- `by label: design constant (registration) 36; exploratory 14; post hoc (descriptive) 17; registered primary 151; registered secondary 228`
- `sources (32), sha256 verified:`
- `PASS: every manifest value matches its source, every number in the texts is a claim or a whitelisted identifier, and the texts and levels reproduce.`
The rebuilt check_output.txt itself was reported "identical" to the released one.

**(c) Rebuilt files not reported "identical"** (4 files, all "equal", none DIFFERENT or MISSING):
1. `posthoc_google_testB.json` (rv.posthoc_google): "equal; only the recorded environment differs (/environment/python 3.11.17 -> 3.11.15)"
2. `behavioral_result.json` (p2.identity): "equal; current code adds variant (950e8a7 added --variant after this result (2c8111c) was written)"
3. `llama-3.1-8b-instruct/coherence.json` (p2.coherence): "equal; current code adds n_complete, generation_failed (Addendum 8 (f4a70a7) added these counts after this file (8e66e71) was written; 0 failures)"
4. `gemma-3-27b-it/coherence.json` (p2.coherence): same reason as 3.
These match the README's statement that three released files predate fields the current code adds and one records the Python patch version. The rv.perm_chunk step lists no output file (its outputs column reads "ok").
All 22 carried-over GPU/API inputs: "sha256 ok".

**(d) README observations for a newcomer** (nothing blocked the run; the commands worked as written):
1. Everything the README states that I could check matched: 22 packages; Python 3.11; pinned versions (numpy 2.4.6, pandas 2.3.3, scipy 1.17.1, statsmodels 0.15.0, matplotlib 3.11.2, printed by reproduce.py); runtime ~27 min on 4 CPUs (1624 s vs README 1,596 s); rv.final ~10 min (570 s) and the permutation chunk ~15 min (911 s); report and check_output.txt paths; PASS/FAIL ending.
2. `make env` took 10 s here, not "about 2 min" (fast network; the README figure is an estimate, so not wrong, just conservative). Download size: CPython 29.5 MiB plus the eight large wheels listed at ~96 MiB, consistent with "about 150 MB".
3. Python patch version: uv installed CPython 3.11.15, while a released file records 3.11.17. The README only says "Python 3.11" and explains that one file records the patch version, and Tier 0 handled it ("equal"), so this is consistent; a newcomer may still wonder which 3.11 patch is expected — the README does not say.
4. The README says "no network" for Tier 0 but `make reproduce` does not itself cut the network on the uv route (only the Docker route says `--network none`). I ran with the network available and cannot confirm the no-network claim from this run.
5. No minimum uv version is given; uv 0.11.32 worked.
6. Disk estimates are generous (observed about 0.9 GB total, the venv being hard-linked to the uv cache); not a problem.
