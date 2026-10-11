# Comprehension check: comprehension_pilot

120/120 calls complete, 0 failed; spend $0.021.

Scoring: tolerant parse (strict first); an unparsed sample counts as incorrect (rate = correct / all samples).
Placebo is a format check only (expected answer: convincing for every line).

| model | condition | n | parsed strict / tolerant / not | comprehension rate [95% Wilson] | per-line accuracy (parsed) | unmatched lines |
|---|---|---|---|---|---|---|
| Gemini | full | 10 | 10 / 0 / 0 | 1.00 [0.72, 1.00] | 1.00 | 0 |
| Gemini | placebo | 10 | 10 / 0 / 0 | 1.00 [0.72, 1.00] | 1.00 | 0 |
| Gemini | reversed | 10 | 10 / 0 / 0 | 1.00 [0.72, 1.00] | 1.00 | 0 |
| Gemma | full | 10 | 10 / 0 / 0 | 1.00 [0.72, 1.00] | 1.00 | 0 |
| Gemma | placebo | 10 | 10 / 0 / 0 | 1.00 [0.72, 1.00] | 1.00 | 0 |
| Gemma | reversed | 10 | 10 / 0 / 0 | 0.40 [0.17, 0.69] | 0.85 | 0 |
| Llama | full | 10 | 4 / 5 / 1 | 0.00 [0.00, 0.28] | 0.47 | 5 |
| Llama | placebo | 10 | 6 / 4 / 0 | 0.00 [0.00, 0.28] | 0.57 | 2 |
| Llama | reversed | 10 | 6 / 3 / 1 | 0.00 [0.00, 0.28] | 0.19 | 0 |
| gpt-4o-mini | full | 10 | 10 / 0 / 0 | 0.30 [0.11, 0.60] | 0.62 | 0 |
| gpt-4o-mini | placebo | 10 | 10 / 0 / 0 | 0.40 [0.17, 0.69] | 0.75 | 0 |
| gpt-4o-mini | reversed | 10 | 10 / 0 / 0 | 1.00 [0.72, 1.00] | 1.00 | 0 |

Parse errors: meta-llama/llama-3.1-8b-instruct|full: no JSON list or object; meta-llama/llama-3.1-8b-instruct|reversed: no JSON list or object
