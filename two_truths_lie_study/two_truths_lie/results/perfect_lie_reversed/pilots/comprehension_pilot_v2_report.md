# Pilot 4c: comprehension check with randomised option and line order

Rule: comprehension holds if the balanced-accuracy lower 95% bound is >= 0.85. c > 0 leans "convincing", c < 0 leans "suspicious".
10 full + 10 reversed samples per model (40 lines each); intervals are wide at pilot size.

| model | parsed (strict / tolerant / not) | acc full | acc reversed | balanced accuracy [95%] | J [95%] | criterion c [95%] | c, convincing first / suspicious first | holds |
|---|---|---|---|---|---|---|---|---|
| Llama | 8 / 9 / 3 | 0.62 | 0.15 | 0.39 [0.29, 0.52] | -0.11 [-0.36, 0.22] | 0.60 [0.17, 1.31] | 0.14 / 1.18 | no |
| Gemma | 20 / 0 / 0 | 1.00 | 0.80 | 0.90 [0.84, 0.95] | 0.80 [0.68, 0.90] | 0.72 [0.51, 0.90] | 0.67 / 0.47 | no |
| gpt-4o-mini | 20 / 0 / 0 | 0.68 | 1.00 | 0.84 [0.74, 0.94] | 0.68 [0.47, 0.88] | -0.90 [-1.16, -0.57] | -1.00 / -0.44 | no |
| Gemini | 20 / 0 / 0 | 1.00 | 1.00 | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | -0.00 [-0.00, 0.00] | -0.06 / 0.03 | yes |

Unrandomised Pilot 4b, same metrics, for comparison:

| model | balanced accuracy [95%] | J | criterion c [95%] | holds |
|---|---|---|---|---|
| Llama | 0.30 [0.19, 0.41] | -0.26 | 0.47 [0.21, 0.76] | no |
| Gemma | 0.93 [0.89, 0.96] | 0.85 | 0.63 [0.44, 0.76] | yes |
| gpt-4o-mini | 0.81 [0.70, 0.91] | 0.62 | -0.97 [-1.25, -0.67] | no |
| Gemini | 1.00 [1.00, 1.00] | 1.00 | -0.00 [-0.00, 0.00] | yes |

Placebo format check, parsed of 10: Llama 7, Gemma 10, gpt-4o-mini 10, Gemini 10.
