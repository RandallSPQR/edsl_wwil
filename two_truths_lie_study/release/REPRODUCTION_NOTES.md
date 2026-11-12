# Reproduction notes

What building Tier 0 found, and how Tier 0 handles each. None of it changes a registered result.

1. **Package versions change a registered fit.** Under numpy 2.5 / pandas 3.0 / scipy 1.18 (Python 3.13), Gemma 3 27B's
   primary mixed model in the reversed-note study converges instead of falling back to the registered per-category
   t-test: Test B +0.431 (SE 0.0201) instead of the registered +0.430 (SE 0.0171). The label is unchanged.
   Tier 0 pins the versions (`ENVIRONMENT.md`, `environment_evidence/`).

2. **The BLAS thread count changes a robustness flag.** With 4 OpenBLAS threads, the reversed-note robustness model m1
   flips its convergence flag for three liars (16th-digit differences), which changes the write-up's "primary
   rejections preserved: 2 of 4". With one thread every value is bit-identical. Tier 0 sets one thread for every step.

3. **Two released files predate fields added later to the code that writes them.** The rebuilt files carry the extra
   keys; every released value is reproduced:
   - `results/phase2/identity_check/behavioral_result.json` (written at 2c8111c): `--variant` support (950e8a7) added
     `"variant": null`;
   - `results/phase2/stage2/<model>/coherence.json` (written at 8e66e71): Addendum 8 (f4a70a7) added `n_complete` and
     `generation_failed` (0 failures).
   Tier 0 accepts exactly these keys for exactly these files, reports them, and keeps the released bytes.

4. **The reversed-note permutation check ran before the screen adjudication.** Its chunks (2026-10-17 to 10-19) were
   computed when `screen_adjudication.json` did not exist, so every confession-screen match was excluded as a
   confession. The adjudication (465ae50, 2026-10-20) kept 15 of the 16 matches, and `reversed_analysis.lie_table` now
   loads it by default: re-running `perm_check_chunked.py` today permutes a slightly different table and does not
   reproduce its own chunks (chunk 00: efficacy counts 6/4/2/7 against the stored 7/4/2/9). Tier 0 recomputes chunks
   with the pre-adjudication table (`adj={}`, as the check was run) and assembles `perm_check.json` from the stored
   chunks. The registered final analysis uses the adjudication, as registered.

5. **Not rebuilt on a CPU** (inputs to Tier 0, verified by sha256; regenerated only by Tier 3 or Tier 1): the probe
   results, vectors, diagnostics and scale reports (they need the activations, which stayed on the RunPod volume), the
   steering setups and naturalness (computed on the pod), the identity check's pod lies, and the grading-route check's
   API calls (its summary is rebuilt from the stored labels).

6. **Weight revisions were not logged at load time.** `dataset/hf_revisions.json` records each repository's `main`
   revision, unchanged since before the first Phase 2 pod run; confirm against the volume's snapshot directory names
   (`tiers/tier3_fetch_volume.sh`).

7. **Hand-assembled file.** `results/phase2/pilot/confirmatory_alphas.json` was assembled from the two pilot results;
   `tier0/rebuild_alphas.py` re-applies the alpha rule and rebuilds it byte-identically.

8. **One file records its own environment.** `posthoc_google_testB.json` stores the versions that wrote it
   (`environment`: Python 3.11.17 and the pinned packages). uv installs Python 3.11.15 and the Docker image has 3.11.18;
   every other byte is identical. Tier 0 accepts a different Python 3.11 patch version in that field only, reports it,
   and keeps the released bytes.

9. **Found by the independent run: the repository ignored the release's own data files.** The repository root's
   `.gitignore` (EDSL defaults) ignores `*json`, `*csv`, `*txt`, `*png`, so the first fresh clone lacked
   `tier0/EXPECTED.json`, the claims manifest, the figures, the pip lock file and the levels file, and Tier 0 stopped
   at once. `two_truths_lie_study/.gitignore` now re-includes them. Logs: `fresh_run/attempt1/` (the failure),
   `fresh_run/attempt2/` (PASS, 446 claims, after the fix), `fresh_run/final/` (PASS on the release commit's code).

10. **Found by the Docker run: the figures depended on the machine's matplotlib configuration.** The build machine has a
    system-wide `/etc/matplotlib/matplotlibrc` (`text.hinting: no_hinting`), which the first figures inherited; in the
    Docker image (no such file) the PNGs came out a few pixels different. `writeup/build.py` now resets matplotlib to
    its built-in defaults before applying its own style, and draws only with matplotlib's bundled fonts (DejaVu), so the
    PNGs are byte-identical on the build machine and in the image. The figures were redrawn once; every number and
    text is unchanged.
