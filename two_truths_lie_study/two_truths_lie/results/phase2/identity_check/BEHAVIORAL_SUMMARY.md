# Identity check, part 2: behavioral equivalence, pod vs API — 2026-10-21

Rules: RULES.md (fixed before any pod lie; K = 36, seed 20261022). Code: behavioral.py (committed
`fb466ab` before generation). Pod lies: `pod_run/records.jsonl`; result: `behavioral_result.json`.

- Pod: RTX PRO 6000 Blackwell, EUR-IS-1 (network volume), transformers 4.53.2 / torch 2.8, bf16,
  T 0.6 / top_p 0.9, seeded batches. Llama rendered without the date header; Gemma with its
  standard template.
- 1,080 pod lies (540 per model); 1,072 graded by the primary grader through the frozen runner;
  8 failed grading (malformed grader output after 3 attempts, as in the API run's policy).
  0 confessions. Gate as registered in the reversed-note run.
- TOST at +/-0.10, 90% CI on 35 df, paired by category (K = 36).

| model | quantity | pod | API | pod - API [90% CI] | within +/-0.10 |
|---|---|---|---|---|---|
| Llama 3.1 8B | B | 0.238 | 0.241 | -0.004 [-0.060, +0.052] | yes |
| | s placebo | 0.194 | 0.217 | -0.022 [-0.058, +0.014] | yes |
| | s full | 0.542 | 0.586 | -0.044 [-0.082, -0.006] | yes |
| | s reversed | 0.300 | 0.345 | -0.045 [-0.078, -0.011] | yes |
| Gemma 3 27B | B | 0.499 | 0.427 | +0.073 [+0.015, +0.131] | **no** |
| | s placebo | 0.270 | 0.242 | +0.028 [-0.011, +0.068] | yes |
| | s full | 0.797 | 0.782 | +0.015 [-0.028, +0.057] | yes |
| | s reversed | 0.293 | 0.356 | -0.064 [-0.104, -0.023] | **no** |

**Result under the rules:**
- **Llama 3.1 8B: pass.** All four TOSTs inside +/-0.10. The API link is established for Llama.
- **Gemma 3 27B: fail.** B and reversed-note s are not shown equivalent: the pod's reversed-note
  lies carry fewer target cues, so the pod's B is larger. Under the rules, Phase 2 uses pod-only
  references for Gemma and the write-up states that the API link is not established for Gemma.
  Phase 2 is not blocked.

**Context, not part of the decision:**
- Llama's s is a little lower on the pod in full and reversed (about -0.04), inside the margin.
- A known rendering difference exists for Gemma: Novita's prompt evidently ends without the newline
  after `<start_of_turn>model` (template-end test: 20/20 pod completions then begin with a newline or
  colon, as all of Novita's do; first divergence moves from token 0 to a median near 10). The pod run
  used the standard template. Whether this difference explains the Gemma result is untested.
- Gemma's pod B (0.499) is larger than its API B, in the direction of a stronger belief effect.

**Cost:** RunPod $7.01 across the identity check (diagnostics $4.07, behavioral run $2.64, the
network volume's storage over the period $0.30; the failed launch cost nothing); OpenRouter grading $13.88; API diagnostics $0.01.
