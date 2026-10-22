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

## Next steps, in order (steps 1-3 done 2026-10-22)

1. **Grading-route check** (about $0.65), rules fixed in
   `two_truths_lie/results/phase2/grading_route/RULES.md`:
   ```
   cd two_truths_lie_study/two_truths_lie
   python results/phase2/grading_route/regrade_direct.py
   ```
   It reads the key from `PL_GRADER_KEY` (never print it). Decision: switch Phase 2 grading to the
   Anthropic API directly if pooled agreement over all cue labels has kappa >= 0.90 or label agreement
   >= 97%; otherwise grade through OpenRouter. Report per-cue agreement to the owner. Commit the output.
2. **Record the route** in `PREREG_PHASE2_DRAFT.md` section 12 (the only open item) and section 11.
3. **Freeze:** rename to `PREREG_PHASE2.md`, add a frozen-file hash table (as `PREREG_REVERSED.md`
   does: the paraphrase sets, the identity-check rules and renderers, the pod server, the analysis
   code once written), commit, and give the owner the commit hash and the text for OSF. Tag and release
   pushes are blocked in cloud sessions (403); the owner creates the tag in the GitHub UI.
4. **Wait for the owner to confirm the OSF post** before any Phase 2 compute. Then: probe stage first
   (activation extraction on the training categories), the probe gate and stop rule (section 4), and
   only for models that pass, the coherence-only pilot, then stage 2.

## Standing rules (owner)

- No model calls or spend without explicit approval; caps as approved. Kill on breach.
- Never print API keys (`OPEN_ROUTER_API_KEY`, `RUNPOD_API_KEY`, `PL_GRADER_KEY`, `HF_TOKEN`).
- Report results without unblinding before the pre-registered steps; no model identifiers in repo
  artifacts except the commit trailer.
- Pods: RunPod REST/GraphQL via curl (Cloudflare blocks urllib's signature); network volume
  `u0isne6ams` in EUR-IS-1 holds the Gemma weights (`/workspace/hf/hub`); set a watchdog that
  terminates every pod; terminate when work ends. RunPod balance was $37.03.
- Commit trailer:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_013SE24WnjYMuptK8z4542YA
  ```
