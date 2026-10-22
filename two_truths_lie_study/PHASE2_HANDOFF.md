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

## Standing rules (owner)

- No model calls or spend without explicit approval; caps as approved. Kill on breach.
- Never print API keys (`OPEN_ROUTER_API_KEY`, `RUNPOD_API_KEY`, `PL_GRADER_KEY`, `HF_TOKEN`).
- Report results without unblinding before the pre-registered steps; no model identifiers in repo
  artifacts except the commit trailer.
- Pods: RunPod REST/GraphQL via curl (Cloudflare blocks urllib's signature); network volume
  `u0isne6ams` in EUR-IS-1 holds the Gemma weights (`/workspace/hf/hub`); set a watchdog that
  terminates every pod; terminate when work ends. RunPod balance $35.73 (2026-10-22, after the Addendum 3 diagnostics).
- Commit trailer: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and the current session's
  `Claude-Session:` link.
