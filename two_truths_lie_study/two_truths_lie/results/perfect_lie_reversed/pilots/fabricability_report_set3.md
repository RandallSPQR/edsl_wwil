# Pilot 4a: fabricability (placebo, 16 lies per category, T=0.6, top_p 0.9)

Criterion D as amended 2026-10-09: grader content-filter blocks are counted separately, not as failures.

Spend $0.83 (cap $3). Cells 64/64 complete, 0 failed.

| category | new | lies | failed | grader blocks | refusal / confession matches | non-viable | A: highest unnamed cue rate (Wilson LB) | placebo share of target cues (share of lies at 0) | verdict |
|---|---|---|---|---|---|---|---|---|---|
| astrology | yes | 16 | 0 | 0 | 0 / 0 | 0 | direct_quotation 8/9 (0.57) | 0.30 (25%) | FAIL: A |
| volcanoes | yes | 16 | 0 | 0 | 0 / 0 | 0 | historical_anchor 5/10 (0.24) | 0.24 (44%) | PASS |
| parks | yes | 16 | 0 | 0 | 0 / 0 | 0 | direct_quotation 5/9 (0.27) | 0.23 (50%) | PASS |
| fossils |  | 16 | 0 | 0 | 0 / 0 | 0 | historical_anchor 5/9 (0.27) | 0.10 (69%) | PASS |

| model | lies | failed | grader blocks | degenerate | B (<5%) | D (<=1 failed) | median words |
|---|---|---|---|---|---|---|---|
| Llama | 16 | 0 | 0 | 0 | pass | pass | 345 |
| Gemma | 16 | 0 | 0 | 0 | pass | pass | 369 |
| gpt-4o-mini | 16 | 0 | 0 | 0 | pass | pass | 384 |
| Gemini | 16 | 0 | 0 | 0 | pass | pass | 361 |

Screen matches (read by hand before any category is failed on V): 0.
