# Pilot 1: degeneration check (placebo, 24 lies per model per temperature, top_p 0.9)

Spend: $0.041 (cap $3).

| model | T | lies | failed | degenerate | non-viable | confessions | words min / median / max | lowest tail stop-word rate (degenerate below 0.15) |
|---|---|---|---|---|---|---|---|---|
| Llama 3.1 8B | 0.6 | 24 | 0 | 0 | 0 | 0 | 281 / 335 / 400 | 0.31 |
| Llama 3.1 8B | 0.8 | 24 | 0 | 0 | 0 | 0 | 286 / 334 / 386 | 0.27 |
| Gemma 3 27B | 0.6 | 24 | 0 | 0 | 0 | 0 | 319 / 370 / 424 | 0.23 |
| Gemma 3 27B | 0.8 | 24 | 0 | 0 | 0 | 0 | 336 / 368 / 413 | 0.21 |
| gpt-4o-mini | 0.6 | 24 | 0 | 0 | 0 | 0 | 347 / 383 / 436 | 0.28 |
| gpt-4o-mini | 0.8 | 24 | 0 | 0 | 1 | 0 | 362 / 387 / 508 | 0.26 |
| Gemini 2.5 Flash-Lite | 0.6 | 24 | 0 | 0 | 0 | 0 | 333 / 369 / 436 | 0.25 |
| Gemini 2.5 Flash-Lite | 0.8 | 24 | 0 | 0 | 0 | 0 | 290 / 360 / 412 | 0.24 |

Non-viable lies: gpt-4o-mini T=0.8: [('language', ['too_long(508)'])]

**Proposal (rule fixed in PILOT_RULES.md): temperature 0.6, top_p 0.9, for all four models.**
