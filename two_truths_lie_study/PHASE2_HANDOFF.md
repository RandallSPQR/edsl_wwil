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

**Probe stage: code done, nothing run.** Addendum 1 (`PREREG_PHASE2_ADDENDA.md`) hashes the probe code. The code is in
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

## Standing rules (owner)

- No model calls or spend without explicit approval; caps as approved. Kill on breach.
- Never print API keys (`OPEN_ROUTER_API_KEY`, `RUNPOD_API_KEY`, `PL_GRADER_KEY`, `HF_TOKEN`).
- Report results without unblinding before the pre-registered steps; no model identifiers in repo
  artifacts except the commit trailer.
- Pods: RunPod REST/GraphQL via curl (Cloudflare blocks urllib's signature); network volume
  `u0isne6ams` in EUR-IS-1 holds the Gemma weights (`/workspace/hf/hub`); set a watchdog that
  terminates every pod; terminate when work ends. RunPod balance $36.57 (2026-10-22).
- Commit trailer: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and the current session's
  `Claude-Session:` link.
