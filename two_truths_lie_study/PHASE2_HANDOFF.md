# Phase 2 handoff (2026-10-22): read this first in a new session

Branch `claude/confident-babbage-fljgmx` of RandallSPQR/edsl_wwil. The previous session ended here
because the grading key (`PL_GRADER_KEY`, an Anthropic API key) is only visible to a new session.

## State

- Reversed-note study: complete and published on OSF (brief `PERFECT_LIE.md`, item 37).
- Phase 2 identity check: complete. Both models linked to the API (Llama without the template's date
  header; Gemma with the Novita rendering, no newline after `<start_of_turn>model`).
  `two_truths_lie/results/phase2/identity_check/` (RULES.md, DIAGNOSTIC_SUMMARY.md, BEHAVIORAL_SUMMARY.md).
- Grading-route check: done 2026-10-22 (commit d09a144). Kappa 0.915 over all cue labels -> all Phase 2
  grading goes through the Anthropic API directly (`src/perfect_lie/grader_direct.py`, strict tool call).
  Grading needs a session that sees `PL_GRADER_KEY` (only sessions started after it was added do).
- Phase 2 pre-registration: **frozen** as `PREREG_PHASE2.md` (revision 4, with a hash table). The owner
  posts it on OSF and creates the tag in the GitHub UI.

## Next steps, in order

Steps 1-3 of the earlier list are done (grading-route check, route recorded, frozen; OSF posted, tag
`perfect-lie-phase2-prereg-v1` at bc1c179). The owner confirmed the OSF post and said: **start the probe stage.**

**Probe stage: DONE 2026-10-22 (see 'Probe stage result' below).** It was: code done, nothing run. Addendum 1 (`PREREG_PHASE2_ADDENDA.md`) hashes the probe code. The code is in
`two_truths_lie/results/phase2/probe/` (items.py, pod_server_phase2.py, probe_stage.py), plus
`src/perfect_lie/phase2_probe.py` and `tests/test_phase2_probe.py` (26 tests with the grader tests, all pass).
Local setup: `pip install scipy pytest platformdirs pyyaml "git+https://github.com/RandallSPQR/SAE-Ethos-Calibration@v1.1.0"`.

The previous session stopped because `HF_TOKEN` (needed if Llama 3.1 8B is not cached on the volume) is only
visible to a new session. There was no GPU free in EUR-IS-1 at the time; no pod was created, nothing was spent
(RunPod balance $36.57).

1. Check `HF_TOKEN` is visible (`env | cut -d= -f1`; never print the value). Generate a pod key in the scratchpad
   (`python -c "import secrets;print(secrets.token_hex(24))" > <scratchpad>/pod_key`).
2. `cd two_truths_lie/results/phase2/probe && python probe_stage.py pod-up --commit <HEAD of the branch, pushed>
   --key-file <pod_key> --poll-hours 3` (run in the background; it retries every 5 min until a GPU is free).
   When it prints a pod id, start a local watchdog: sleep 2.5 h, then `python probe_stage.py pod-down --pod ID`.
   Cap $8 for the probe stage.
3. Wait for the server (`GET https://<pod>-8000.proxy.runpod.net/health` with the bearer key; the pod pip-installs
   first). Then `python probe_stage.py extract --pod ID --key-file K --model google/gemma-3-27b-it`, then
   `analyse` for the same model; then the same two for `meta-llama/llama-3.1-8b-instruct`.
4. `pod-down` as soon as both analyses are downloaded. Commit `gemma-3-27b-it/` and `llama-3.1-8b-instruct/`
   (probe_result.json, vectors.npz, PROBE.md, extract_log.json; `results/` is gitignored, use `git add -f`).
5. Report the gate per model to the owner (section 4: PASS needs held-out personas AND all three wordings at some
   candidate layer). A model that fails stops before steering, and that is its reported result. **Stop there**:
   the dose-finding pilot needs the owner's go.

## Probe stage result (2026-10-22)

- Pod `30divt8wyoiafl` (RTX PRO 6000, EUR-IS-1, $2.49/h), about 18 min; terminated, no pods left. Spend about
  $0.56 (balance $36.57 -> $36.01). Results committed under `two_truths_lie/results/phase2/probe/<slug>/`.
- **Gemma 3 27B: PASS, layer 35** (held-out personas 0.768; wordings A/B/C 1.000; passing layers 35-38, 40, 41).
- **Llama 3.1 8B: PASS, layer 12** (held-out personas 0.828; wordings 1.000; every candidate 11-21 passes; 12-15 tie at
  mean wording AUROC 1.0, ties go to the lower layer).
- **Cue-mention control is degenerate (reported, not part of the stop rule):** every placebo item is byte-identical
  to another target's full item (placebo note = another persona's full note; the prompt never names the target),
  so c_L = -v_L/2 exactly, control AUROC ~0, outside [0.40, 0.60] at every layer, both models. Owner to decide
  whether an addendum replaces it.
- **Held-out-persona intervals are near zero width** (e.g. 0.720 [0.720, 0.720]); several AUROCs are exact multiples
  of 1/25, consistent with near-perfect separation within each held-out persona and a pooled AUROC set by
  between-fold score offsets. Computed as registered; not verified at item level (activations stay on the volume,
  `/workspace/phase2/probe/<slug>/`).
- **Next: the dose-finding pilot needs the owner's go.** Also pending: Addendum 2 (Google 20% subsample) to post on
  OSF, and its grading/analysis code to write and hash before any stage-2 lie is graded.

## Addendum 3 diagnostics (2026-10-22)

- Addendum 3 written and hashed at `2b47b53` before running; pod `acm3ydm7ylkmfg` about 6 min, terminated; spend
  about $0.28 (balance $36.01 -> $35.73). Results: `<slug>/diagnostics.json`, `DIAGNOSTICS.md`.
- **Stop rule holds for both models** (all 24 mean null AUROCs inside [0.40, 0.60]): held-out personas 0.498-0.501;
  wordings 0.537-0.559 (slightly above 0.5, consistent with each pair's own difference entering v, as in
  simulation). Every observed AUROC is above every permuted value (p = 0.001, the minimum with 1,000 permutations);
  recomputed observed AUROCs match the registered ones.
- **Within-fold persona AUROC:** Gemma 1.000 in every fold at layers 29-41 (selected 35; registered pooled 0.768);
  Llama 1.000 in every fold at 11-15 (selected 12; pooled 0.828). The pooled figure is lowered by between-fold
  offsets in projection level (Gemma's mid-layer projections are in the thousands), not by within-persona
  separation.
- **Next:** owner posts Addenda 2 and 3 on OSF; the dose-finding pilot needs the owner's go.

## Steering scale before the pilot (2026-10-23)

- Section 6: the steering vector is unit(v_L*) x alpha x ||v_L*|| (alpha = 1 adds the pooled mean full - reversed
  shift); one vector per model, the same for every persona and position. Not raw units, not the residual norm.
- Per persona at the selected layer (`<slug>/scale.json`, `SCALE.md`; code `aea6d12`; pod `564qszrsktgy9n`, A100,
  about 2 min, terminated): residual norm varies 1.02x (Gemma, median about 44,400) and 1.01x (Llama, about 7.5);
  ||v|| / residual norm 0.040-0.041 (Gemma) and 0.037 (Llama) for every persona. The full - reversed gap on unit v
  varies 2.98x for Gemma (P1 921 to P2 2,739) and 1.29x for Llama.
- A residual-norm-relative alpha would rescale every persona by the same constant, so it changes nothing; no
  addendum proposed. Gemma's gap heterogeneity is recorded for the per-target reporting.
- RunPod balance $35.27 (2026-10-23; includes network-volume storage, about $0.019/h).

## Stage-1 dose-finding pilot (2026-10-23): DONE

- Addendum 4 (pilot code, hashed; two revisions of the hook check before any steered lie, now an exact bitwise
  check). Pods: `ht0a8t3cabu5ok` (A100, about 8 min, stopped at the hook check; smoke test only) and
  `we7filrngfuht9` (RTX PRO 6000, about 1 h 57 min). Both terminated. Pilot spend about $5.1 (balance $35.27 -> $30.21).
- **Confirmatory alphas (committed before stage 2, `results/phase2/pilot/confirmatory_alphas.json`):**
  Gemma H1 1.0, H2 1.0; Llama H1 4.0, H2 4.0. Llama was coherent at every grid alpha (4.0 is the grid's top).
  Gemma's perplexity ratio breaks above 1.0 (H1 at 2.0: steered 1.63 passes, placebo 2.46 fails; H2 at 2.0: 2.13 / 2.24).
- Nothing graded, no cue scored. Records (text, ids, NLL) gzipped under `results/phase2/pilot/<slug>/`.
  Descriptive (not registered): `divergence.json`, the first token where each lie departs from its unsteered twin.
- **Open decision before stage 2: the covariance-matched placebo is aligned with v.** cos(v, placebo) = 0.64
  (Gemma) and 0.24 (Llama): `placebo_cov` draws from the covariance of the full and reversed training items, and
  the full - reversed split is a large share of that variance. The steered - placebo contrast then compares v with
  a vector carrying 0.64 (Gemma) of v's own component. Options for the owner (an addendum before stage 2).
- **Next:** owner posts Addendum 4 on OSF and decides the placebo question; stage 2 needs the owner's go and the
  analysis-code addendum (incl. the Addendum 2 grading code).

## Addendum 5 placebo and pilot rerun (2026-10-23): DONE

- New placebo (within-condition covariance, v projected out, norm matched): cos(placebo, v) = -5.9e-17 (Gemma) and
  1.7e-18 (Llama); before the projection -0.138 and 0.022; cos with the retired placebo -0.343 and 0.236; norm match 1.
- Placebo half of the pilot rerun (pod `1epi4sfusw0r5r`, RTX PRO 6000, about 57 min, terminated; about $2.40, cap $4).
- **Confirmatory alphas now (supersede the retired placebo's): Gemma H1 2.0, H2 1.0; Llama H1 4.0, H2 4.0.**
  Gemma H1 rose from 1.0 (the retired placebo failed at 2.0 with ratio 2.46; the new one passes at 1.64).
  `results/phase2/pilot/confirmatory_alphas.json`, `<slug>/PILOT2.md`, `pilot2_result.json`.
- Addendum 6 (stage-2 analysis and grading code, hashed, 26 tests) committed `b389b68`. Still needed before stage 2:
  the stage-2 generation addendum (pod extension and driver; the method check's placebo construction for v_fp is an
  open detail), OSF posts of Addenda 4-6, and the owner's go.

## Addendum 7 and the method-check pre-check (2026-10-26): DONE

- The registered method-check direction v_fp is zero by construction (placebo items = other targets' full items):
  ||v_fp|| / ||v|| = 3e-7 (Gemma), 6e-7 (Llama). Owner chose a per-target v_fp,t (Addendum 7), placebo per target
  orthogonal to v_fp,t (Addendum 5 procedure), norm matched.
- Addendum 7 (stage-2 generation code, hashed, commit `6133228`): items, plan (1,280 lies per model), seeds, hook
  checks, stage-2 coherence gate, naturalness; driver steps grade / screens / permcheck / analyse (unblinding flag).
- Method-check pre-check (pod `nl3lxw5wv8owdd`, about 27 min, about $1.12, cap $2; terminated): **coherent on both
  models at alpha 1** (Gemma: steered ppl ratio 1.38, placebo 1.18; Llama 1.00 / 1.01; all viable). Placebo cos with
  v_fp,t <= 8e-17, norm match 1, all targets. ||v_fp,t|| / ||v||: Gemma 0.78-1.47, Llama 1.19-1.74.
  `results/phase2/pilot/<slug>/MC_PRECHECK.md`.
- **Next: stage 2 needs the owner's go** (and the OSF post of Addenda 4-7). Stage 2 GPU estimate: about 3 h on an RTX
  PRO 6000 (Gemma about 2 h, Llama about 45 min), about $7.5; grading 2,560 lies about $33 (direct) + about $1
  (Google subsample).

## Stage 2 (2026-10-26): generated and graded; NOT analysed

- Owner's go 2026-10-26. Generation: pod `yzmvlwjpjybo4p` (RTX PRO 6000, 2 h 49 min, about $7.05, cap $10;
  terminated). 1,280 lies per model; **all four tests pass the stage-2 coherence gate (testable)**. Naturalness:
  cos(v, last-token shift, evaluation categories) 0.999 Gemma / 0.998 Llama; first generated token 0.39 / 0.10.
- Grading (direct route, strict accepted throughout): Llama 8 / 1,280 failed cells, Gemma 10 / 1,280; Google
  subsample 256 + 256, 0 failed. Spend about $36.53 direct (cap $40) and $0.61 OpenRouter (cap $2).
- Background commands are limited to 2 h in this environment: long jobs are now started detached (setsid nohup);
  the first generation, grading and watchdog jobs were killed at 2 h and resumed without loss or duplicates.
- **Screens (section 10): 2 matches, both the refusal pattern ("I can't deny ...", "I can't say I've ever felt
  ..."), 0 confession patterns. Listed blind in `results/phase2/stage2/screen_matches.json` for the owner's
  adjudication** (write `screen_adjudication.json`: id -> "confession" | "not a confession").
- Owner adjudicated both screen matches "not a confession" (2026-10-27; `screen_adjudication.json`).
- **Blinded permutation check (section 10; 10,000 within-cell swaps, seed 20261035; shares only):** efficacy
  rejections 1.15% (Gemma H1), 1.30% (Gemma H2), 1.35% (Llama H1), 1.30% (Llama H2), as designed (about 1.3% per
  test in simulation; the reversed-note study 1.27-1.41%). Equivalence rejections under the permuted null 94-98%.
- **Next:** owner's go -> `stage2_stage.py analyse --i-am-unblinding`. No grade has been summarised.

## Standing rules (owner)

- No model calls or spend without explicit approval; caps as approved. Kill on breach.
- Never print API keys (`OPEN_ROUTER_API_KEY`, `RUNPOD_API_KEY`, `PL_GRADER_KEY`, `HF_TOKEN`).
- Report results without unblinding before the pre-registered steps; no model identifiers in repo
  artifacts except the commit trailer.
- Pods: RunPod REST/GraphQL via curl (Cloudflare blocks urllib's signature); network volume
  `u0isne6ams` in EUR-IS-1 holds the Gemma weights (`/workspace/hf/hub`); set a watchdog that
  terminates every pod; terminate when work ends. RunPod balance $18.21 (2026-10-26, after stage-2 generation; the network volume accrues about $0.019/h).
- Commit trailer: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and the current session's
  `Claude-Session:` link.
