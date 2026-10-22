# Test B under the Google grader (post hoc, descriptive)

Owner's request, 2026-10-22, after unblinding; not registered; no new model calls. Test B = full - reversed, from the Google grader's annotations (gemini-2.5-flash graded every lie), with the registered lies, cue pool (gate exclusions ['historical_anchor', 'emotional_appeal']) and fit/fallback; only the grader differs. **The Google grader shares a family with the Gemma 3 27B and Gemini 2.5 Flash-Lite liars**, so agreement on those two rows is weaker evidence of grader-robustness than on the other two.

| liar | primary label | primary B [95% CI] | Google B [95% CI] | Google - primary | Google method | lies (primary / Google) | primary rejections preserved | grader same family |
|---|---|---|---|---|---|---|---|---|
| Llama 3.1 8B | belief-tracking | +0.246 [+0.220, +0.273] | +0.269 [+0.243, +0.296] | +0.023 | per-category t-test (fallback) | 1077 / 1077 | True | no |
| Gemma 3 27B | belief-tracking | +0.430 [+0.395, +0.464] | +0.394 [+0.361, +0.428] | -0.035 | per-category t-test (fallback) | 1067 / 1067 | True | yes |
| gpt-4o-mini | belief-tracking | +0.391 [+0.343, +0.438] | +0.401 [+0.356, +0.446] | +0.010 | per-category t-test (fallback) | 1078 / 1078 | True | no |
| Gemini 2.5 Flash-Lite | belief-tracking | +0.348 [+0.306, +0.391] | +0.368 [+0.323, +0.413] | +0.020 | per-category t-test (fallback) | 1074 / 1074 | True | yes |

Preserved = the primary efficacy rejection holds for the Google B at the local Holm alpha at which the primary rejected (reversed_analysis.holds). Descriptive only: it changes no registered label.
