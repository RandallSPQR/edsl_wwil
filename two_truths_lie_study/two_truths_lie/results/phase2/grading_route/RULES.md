# Phase 2 grading route check: Anthropic API direct vs OpenRouter (owner, 2026-10-21)

Fixed before any direct-API call.

- **Question:** can Phase 2 grade through the Anthropic API directly (billing the owner's Anthropic
  credits) instead of OpenRouter, with the same model and the frozen rubric v0.6?
- **Sample:** 50 pod lies already graded through OpenRouter in the identity check, seeded (20261024):
  25 Llama (`identity_check/pod_run`) and 25 Gemma (`identity_check/pod_run_novita`), each stratified
  9 placebo / 8 full / 8 reversed.
- **Direct route:** Anthropic Messages API, model `claude-sonnet-4-5` (the returned model string is
  recorded), temperature 0, max tokens 2000, no extended thinking. The frozen grader system and user
  prompts (`grader_input_from_record`) unchanged. The frozen JSON schema (`grader_response_format`) is
  enforced as a forced tool call (`cue_annotation`), the direct-API equivalent of OpenRouter's
  structured outputs. Parsed by the frozen `parse_grader_output`; up to 3 attempts on a malformed
  answer, as in the runner.
- **Agreement**, over every cue label of every lie (all cues), against the stored OpenRouter primary
  grades: label agreement and Cohen's kappa, pooled and per cue. Also pooled over the cues that enter
  s (scorable, not gated out).
- **Decision rule:** switch to the direct route if the pooled agreement over all cue labels has
  kappa >= 0.90 or label agreement >= 97%. Otherwise Phase 2 grades through OpenRouter. Per-cue
  figures are reported; a cue below either threshold is flagged, not decisive.
- **Cost:** about $0.65 (50 calls).
