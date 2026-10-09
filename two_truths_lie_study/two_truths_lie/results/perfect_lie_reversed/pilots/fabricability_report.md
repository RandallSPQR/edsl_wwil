# Pilot 2: fabricability (placebo, 16 lies per category, T=0.6, top_p 0.9)

Spend $5.02 (cap $10). Cells 381/384 complete, 3 failed.

| category | new | lies | failed | refusal / confession matches | non-viable | A: highest unnamed cue rate (Wilson LB) | placebo share of target cues (share of lies at 0) | verdict |
|---|---|---|---|---|---|---|---|---|
| science |  | 16 | 1 | 0 / 0 | 0 | institutional_authority 9/13 (0.42) | 0.21 (53%) | PASS |
| history |  | 16 | 0 | 0 / 0 | 0 | historical_anchor 9/10 (0.60) | 0.29 (44%) | FAIL: A |
| biology |  | 16 | 1 | 0 / 0 | 0 | historical_anchor 6/10 (0.31) | 0.13 (67%) | PASS |
| geography |  | 16 | 0 | 0 / 0 | 0 | historical_anchor 5/9 (0.27) | 0.16 (69%) | PASS |
| technology |  | 16 | 0 | 0 / 0 | 0 | historical_anchor 5/10 (0.24) | 0.23 (44%) | PASS |
| culture |  | 16 | 0 | 0 / 0 | 0 | direct_quotation 5/9 (0.27) | 0.22 (56%) | PASS |
| sports | yes | 16 | 0 | 1 / 0 | 0 | historical_anchor 9/10 (0.60) | 0.38 (19%) | FAIL: V, A |
| food | yes | 16 | 0 | 0 / 0 | 0 | direct_quotation 6/9 (0.35) | 0.29 (50%) | PASS |
| music | yes | 16 | 0 | 0 / 0 | 0 | historical_anchor 6/9 (0.35) | 0.29 (31%) | PASS |
| art | yes | 16 | 0 | 0 / 0 | 0 | direct_quotation 7/10 (0.40) | 0.22 (38%) | PASS |
| architecture | yes | 16 | 0 | 0 / 0 | 0 | historical_anchor 5/9 (0.27) | 0.13 (69%) | PASS |
| transportation | yes | 16 | 0 | 0 / 0 | 0 | historical_anchor 7/10 (0.40) | 0.37 (31%) | PASS |
| business | yes | 16 | 0 | 0 / 0 | 0 | historical_anchor 7/10 (0.40) | 0.28 (38%) | PASS |
| language | yes | 16 | 0 | 0 / 0 | 0 | direct_quotation 6/10 (0.31) | 0.27 (44%) | PASS |
| weather | yes | 16 | 0 | 0 / 0 | 0 | historical_anchor 6/10 (0.31) | 0.23 (38%) | PASS |
| astronomy | yes | 16 | 0 | 0 / 0 | 0 | historical_anchor 6/9 (0.35) | 0.23 (50%) | PASS |
| oceans | yes | 16 | 0 | 0 / 0 | 0 | direct_quotation 5/10 (0.24) | 0.16 (62%) | PASS |
| agriculture | yes | 16 | 1 | 0 / 0 | 0 | family_provenance 4/9 (0.19) | 0.27 (40%) | PASS |
| aviation | yes | 16 | 0 | 0 / 0 | 0 | historical_anchor 7/9 (0.45) | 0.22 (50%) | PASS |
| film | yes | 16 | 0 | 0 / 0 | 0 | historical_anchor 7/10 (0.40) | 0.18 (56%) | PASS |
| literature | yes | 16 | 0 | 0 / 0 | 0 | historical_anchor 8/9 (0.57) | 0.32 (38%) | FAIL: A |
| mathematics | yes | 16 | 0 | 0 / 0 | 0 | direct_quotation 6/10 (0.31) | 0.18 (56%) | PASS |
| games | yes | 16 | 0 | 0 / 0 | 0 | direct_quotation 4/9 (0.19) | 0.19 (62%) | PASS |
| fashion | yes | 16 | 0 | 0 / 0 | 0 | emotional_appeal 6/13 (0.23) | 0.24 (44%) | PASS |

| model | lies | failed | degenerate | B (<5%) | D (<=1 failed) | median words |
|---|---|---|---|---|---|---|
| Llama | 96 | 0 | 0 | pass | pass | 333 |
| Gemma | 96 | 3 | 0 | pass | FAIL | 368 |
| gpt-4o-mini | 96 | 0 | 0 | pass | pass | 386 |
| Gemini | 96 | 0 | 0 | pass | pass | 366 |

Screen matches (read by hand before any category is failed on V): 1.
- sports / Gemini / refusal: "I can't"
