# Identity check, part 1: temperature-0 diagnostic (not a gate) — 2026-10-21

Run with `diagnostic.py` (committed before the run, `bc24be8`); raw output `diagnostic.json`.
Pods: Gemma 3 27B IT on H100 SXM (EUR-IS-3), Llama 3.1 8B Instruct on A40 (CA-MTL-1); vLLM v0.9.2,
bf16, HF weights. API: OpenRouter with the run's pins (CoreWeave / Novita, bf16, no fallback); every
API answer was served by the pinned provider. Cost: RunPod $2.48, API $0.005. Pods terminated.

## Llama 3.1 8B (20 prompts, no errors)

- First divergence (token index): 0 ×7, 1 ×3, 5, 6, 8 ×4, 9, 12, 14, 18. **10 of 20 at 0–2.**
- **Template mismatch on every prompt:** the pod's prompt is 19 tokens longer than CoreWeave
  reports. The pod's Llama 3.1 template inserts "Cutting Knowledge Date: December 2023 / Today Date:
  26 Jul 2024" into the system turn (seen via /tokenize + /detokenize); 19 tokens is that header.
  CoreWeave evidently renders without it.
- Both sides stop normally; the completions are coherent and similar in content and style.

## Gemma 3 27B (20 prompts)

- **The pod's Gemma inference is broken.** Its completions are degenerate ("the the the…",
  "**Storyteller." repeated) and run to the token limit; a trivial prompt ("What is the capital of
  France?") also gets incoherent text. The chat template it renders looks correct
  (`<bos><start_of_turn>user … <end_of_turn>\n<start_of_turn>model\n`), and prompt token counts
  match Novita within 1 token. The fault is in the pod's inference, not the prompt.
- 11 prompts diverge at token 0; 5 could not be tokenised and 4 timed out (both from degenerate
  pod output). No Gemma comparison is usable.
- **Observation on the API side:** all 20 Novita completions begin with a newline or a colon,
  which is atypical at the start of a model turn. Unresolved; to be checked against a working pod.

## Reading under the rules

- Most prompts diverge at token 0–2 (Llama 10/20, Gemma all usable ones), so the chat template is
  checked first: Llama's template differs (date header); Gemma's template matches by count but the
  pod is broken.
- Nothing here is a gate. Before the behavioral comparison: (1) fix the Gemma pod; (2) render
  Llama without the date header to match CoreWeave; (3) re-run this diagnostic.
