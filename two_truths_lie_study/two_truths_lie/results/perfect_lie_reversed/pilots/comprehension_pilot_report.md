# Comprehension check: comprehension_pilot

120/120 calls complete, 0 failed; spend $0.021.

Placebo is a format check only (expected answer: convincing for every line).

| model | condition | n | parsed | sample accuracy [95% Wilson] | per-line accuracy | unmatched lines |
|---|---|---|---|---|---|---|
| Gemini | full | 10 | 10 | 1.00 [0.72, 1.00] | 1.00 | 0 |
| Gemini | placebo | 10 | 10 | 1.00 [0.72, 1.00] | 1.00 | 0 |
| Gemini | reversed | 10 | 10 | 1.00 [0.72, 1.00] | 1.00 | 0 |
| Gemma | full | 10 | 10 | 1.00 [0.72, 1.00] | 1.00 | 0 |
| Gemma | placebo | 10 | 10 | 1.00 [0.72, 1.00] | 1.00 | 0 |
| Gemma | reversed | 10 | 10 | 0.40 [0.17, 0.69] | 0.85 | 0 |
| Llama | full | 10 | 4 | 0.00 [0.00, 0.49] | 0.62 | 0 |
| Llama | placebo | 10 | 6 | 0.00 [0.00, 0.39] | 0.58 | 0 |
| Llama | reversed | 10 | 6 | 0.00 [0.00, 0.39] | 0.17 | 0 |
| gpt-4o-mini | full | 10 | 10 | 0.30 [0.11, 0.60] | 0.62 | 0 |
| gpt-4o-mini | placebo | 10 | 10 | 0.40 [0.17, 0.69] | 0.75 | 0 |
| gpt-4o-mini | reversed | 10 | 10 | 1.00 [0.72, 1.00] | 1.00 | 0 |

Parse errors: meta-llama/llama-3.1-8b-instruct|full: no JSON list; meta-llama/llama-3.1-8b-instruct|full: Extra data: line 2 column 1 (char 131); meta-llama/llama-3.1-8b-instruct|full: Expecting ':' delimiter: line 3 column 152 (char 428); meta-llama/llama-3.1-8b-instruct|full: Expecting ':' delimiter: line 2 column 112 (char 238); meta-llama/llama-3.1-8b-instruct|full: Extra data: line 2 column 1 (char 108); meta-llama/llama-3.1-8b-instruct|placebo: Extra data: line 2 column 1 (char 125); meta-llama/llama-3.1-8b-instruct|placebo: no JSON list; meta-llama/llama-3.1-8b-instruct|placebo: Expecting ':' delimiter: line 4 column 154 (char 435); meta-llama/llama-3.1-8b-instruct|placebo: no JSON list; meta-llama/llama-3.1-8b-instruct|reversed: Extra data: line 2 column 1 (char 131); meta-llama/llama-3.1-8b-instruct|reversed: Extra data: line 2 column 1 (char 128); meta-llama/llama-3.1-8b-instruct|reversed: Extra data: line 2 column 1 (char 110); meta-llama/llama-3.1-8b-instruct|reversed: no JSON list
