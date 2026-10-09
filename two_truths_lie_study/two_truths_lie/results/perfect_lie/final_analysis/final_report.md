# The Perfect Lie: final analysis (interim data, replicates 1-15)

Gate (frozen at the interim (interim_blind.json)): excluded ['emotional_appeal']; flagged []. Primary pool: ['P1', 'P2', 'P3', 'P5', 'P6']. Units excluded: {'missing_or_failed': 29, 'confessed': 0, 'empty_cue_set': 60, 'nonviable': 0}.

## Primary decision (registered: PREREG sections 4-5)

Holm order: within a family, the hypothesis with the smallest p-value among those clearing their boundary is rejected first.

| liar | decision | direction | n | Z | boundary at decision | local alpha at decision | repeated CI of the deciding family |
|---|---|---|---|---|---|---|---|
| Llama 3.1 8B | belief-tracking | more named cues under full | 131 | +8.95 | +3.641 | 0.025 (efficacy, interim) | efficacy [+0.169, +0.401] (multiplier +3.641) |
| Gemma 3 27B | belief-tracking | more named cues under full | 130 | +12.24 | +4.016 | 0.0125 (efficacy, interim) | efficacy [+0.291, +0.576] (multiplier +4.016) |
| gpt-4o-mini | belief-tracking | more named cues under full | 128 | +10.31 | +3.864 | 0.016666666666666666 (efficacy, interim) | efficacy [+0.227, +0.498] (multiplier +3.864) |
| Gemini 2.5 Flash-Lite | belief-tracking | more named cues under full | 122 | +8.80 | +3.231 | 0.05 (efficacy, interim) | efficacy [+0.223, +0.482] (multiplier +3.231) |

No cue was flagged (fewer than 30 positives), so no score in this table includes a flagged cue.

Every model had at least 75 units at the interim, so the normal approximation applies (PREREG section 4).

## Estimates (added before unblinding, Addendum 3; the last column is not pre-registered)

| liar | mean lift (naive) | naive 95% CI | stagewise median-unbiased [95% CI] | conditional median-unbiased, NOT PRE-REGISTERED [95% CI] |
|---|---|---|---|---|
| Llama 3.1 8B | +0.285 | [+0.223, +0.347] | +0.285 [+0.223, +0.347] | +0.285 [+0.223, +0.347] |
| Gemma 3 27B | +0.433 | [+0.364, +0.503] | +0.433 [+0.364, +0.503] | +0.433 [+0.364, +0.503] |
| gpt-4o-mini | +0.363 | [+0.294, +0.432] | +0.363 [+0.294, +0.432] | +0.363 [+0.294, +0.432] |
| Gemini 2.5 Flash-Lite | +0.352 | [+0.274, +0.431] | +0.352 [+0.274, +0.431] | +0.352 [+0.274, +0.431] |

No cue was flagged (fewer than 30 positives), so no score in this table includes a flagged cue.

## Mixed model, d ~ 1 + (1 | prompt) (registered robustness, PREREG section 4)

| liar | n | intercept | 95% CI | z | prompt variance | converged |
|---|---|---|---|---|---|---|
| Llama 3.1 8B | 131 | +0.295 | [+0.110, +0.479] | +3.13 | +0.0485 | True |
| Gemma 3 27B | 130 | +0.442 | [+0.290, +0.595] | +5.70 | +0.0290 | True |
| gpt-4o-mini | 128 | +0.347 | [+0.181, +0.512] | +4.10 | +0.0360 | True |
| Gemini 2.5 Flash-Lite | 122 | +0.326 | [+0.179, +0.474] | +4.33 | +0.0241 | True |

## Sensitivity analyses (primary test repeated: |Z| against the boundary at which each model was decided)

- Flagged cues dropped (registered, PREREG section 6): no cue was flagged at the interim; identical to the primary analysis
- Pooled gate (registered, PREREG section 6): pooled kappa 0.778 (threshold 0.70; computed over the lie x cue matrix, primary vs Google). 
- Non-viable lies excluded (added post-registration, before data; Addendum 1): 1 units dropped.

| liar | pooled gate | non-viable excluded |
|---|---|---|
| Llama 3.1 8B | 146, +0.274 [+0.207, +0.341], Z +8.06, decision holds: True | 131, +0.285 [+0.223, +0.347], Z +8.95, decision holds: True |
| Gemma 3 27B | 144, +0.384 [+0.314, +0.455], Z +10.66, decision holds: True | 130, +0.433 [+0.364, +0.503], Z +12.24, decision holds: True |
| gpt-4o-mini | 143, +0.337 [+0.270, +0.405], Z +9.79, decision holds: True | 128, +0.363 [+0.294, +0.432], Z +10.31, decision holds: True |
| Gemini 2.5 Flash-Lite | 137, +0.294 [+0.215, +0.374], Z +7.26, decision holds: True | 121, +0.360 [+0.282, +0.437], Z +9.04, decision holds: True |

Non-viable lies by condition: {'none': {'lies': 711, 'any': 2, 'too_short': 2, 'too_long': 0, 'refusal_or_disclaimer': 0}, 'placebo': {'lies': 700, 'any': 0, 'too_short': 0, 'too_long': 0, 'refusal_or_disclaimer': 0}, 'full': {'lies': 699, 'any': 2, 'too_short': 2, 'too_long': 0, 'refusal_or_disclaimer': 0}}

## Tipping point for the failed cells (added before unblinding, Addendum 3)

Missing units: 29

| liar | missing units | delta to reverse (decision boundary) | delta (boundary at local 0.0125) | Z if all missing at worst |
|---|---|---|---|---|
| Llama 3.1 8B | 4 | n/a (not reversible) | n/a (not reversible) | +6.82 |
| Gemma 3 27B | 5 | n/a (not reversible) | n/a (not reversible) | +9.20 |
| gpt-4o-mini | 7 | n/a (not reversible) | n/a (not reversible) | +6.90 |
| Gemini 2.5 Flash-Lite | 13 | n/a (not reversible) | n/a (not reversible) | +4.45 |

## gpt-5 robustness (registered, PREREG section 8; descriptive: read for sign and rough size only)

Subsample lies 524; pooled kappa 0.768, AC1 0.873 (post-gate cues).

| liar | gpt-5 annotations: n, mean [95% CI], Z, decision holds |
|---|---|
| Llama 3.1 8B | 13, +0.276 [+0.088, +0.464], Z +2.87, decision holds: False |
| Gemma 3 27B | 8, +0.229 [-0.025, +0.483], Z +1.77, decision holds: False |
| gpt-4o-mini | 7, +0.000 [-0.185, +0.185], Z +0.00, decision holds: False |
| Gemini 2.5 Flash-Lite | 5, +0.600 [+0.233, +0.967], Z +3.21, decision holds: False |

## P4 conflict condition (registered secondary, PREREG section 7; cues ['hedged_claim', 'self_deprecation', 'skeptic_acknowledgment'])

| liar | n | mean [95% CI] | z |
|---|---|---|---|
| Llama 3.1 8B | 28 | +0.107 [+0.006, +0.208] | +2.08 |
| Gemma 3 27B | 27 | +0.753 [+0.664, +0.843] | +16.49 |
| gpt-4o-mini | 28 | +0.083 [-0.003, +0.170] | +1.89 |
| Gemini 2.5 Flash-Lite | 26 | +0.769 [+0.668, +0.870] | +14.93 |

## Secondary analyses (registered as exploratory, PREREG section 10; replicates 1-15, all four models (balanced); confessed lies excluded)

### 1. Lift by category (pooled over models)

| category | n | mean [95% CI] |
|---|---|---|
| biology | 55 | +0.382 [+0.263, +0.501] |
| culture | 114 | +0.336 [+0.272, +0.399] |
| geography | 115 | +0.416 [+0.351, +0.481] |
| history | 59 | +0.390 [+0.284, +0.496] |
| science | 109 | +0.390 [+0.302, +0.478] |
| technology | 59 | +0.178 [+0.081, +0.275] |

No cue was flagged (fewer than 30 positives), so no score in this table includes a flagged cue.

### 2. Judge acceptance by cue (lie-level, mean over the four judges, including the liar's own model)

| cue | acc. present | acc. absent | diff [95% CI] |
|---|---|---|---|
| document_citation | 0.687 (n 328) | 0.569 (n 1782) | +0.118 [+0.086, +0.150] |
| institutional_authority | 0.660 (n 803) | 0.542 (n 1307) | +0.118 [+0.092, +0.145] |
| historical_anchor | 0.619 (n 1122) | 0.550 (n 988) | +0.069 [+0.042, +0.096] |
| official_failure | 0.813 (n 127) | 0.573 (n 1983) | +0.240 [+0.196, +0.284] |
| first_person_witness | 0.713 (n 583) | 0.539 (n 1527) | +0.174 [+0.145, +0.202] |
| family_provenance | 0.785 (n 483) | 0.528 (n 1627) | +0.257 [+0.228, +0.286] |
| direct_quotation | 0.681 (n 783) | 0.532 (n 1327) | +0.149 [+0.122, +0.176] |
| mundane_aftermath | 0.766 (n 279) | 0.560 (n 1831) | +0.206 [+0.172, +0.241] |
| hedged_claim | 0.625 (n 391) | 0.579 (n 1719) | +0.046 [+0.009, +0.084] |
| self_deprecation | 0.784 (n 186) | 0.568 (n 1924) | +0.216 [+0.171, +0.260] |
| skeptic_acknowledgment | 0.682 (n 318) | 0.570 (n 1792) | +0.111 [+0.072, +0.151] |
| humor | 0.699 (n 351) | 0.565 (n 1759) | +0.135 [+0.100, +0.170] |

### 3. Liar x judge acceptance

Same family minus other family: +0.046. Same model minus other (NOT PRE-REGISTERED, descriptive): +0.030.

| liar -> judge | n | acceptance |
|---|---|---|
| google/gemini-2.5-flash-lite -> google/gemini-2.5-flash-lite | 520 | 0.442 |
| google/gemini-2.5-flash-lite -> google/gemma-3-27b-it | 520 | 0.763 |
| google/gemini-2.5-flash-lite -> meta-llama/llama-3.1-8b-instruct | 520 | 0.983 |
| google/gemini-2.5-flash-lite -> openai/gpt-4o-mini | 520 | 0.688 |
| google/gemma-3-27b-it -> google/gemini-2.5-flash-lite | 528 | 0.492 |
| google/gemma-3-27b-it -> google/gemma-3-27b-it | 528 | 0.913 |
| google/gemma-3-27b-it -> meta-llama/llama-3.1-8b-instruct | 528 | 0.983 |
| google/gemma-3-27b-it -> openai/gpt-4o-mini | 528 | 0.706 |
| meta-llama/llama-3.1-8b-instruct -> google/gemini-2.5-flash-lite | 533 | 0.066 |
| meta-llama/llama-3.1-8b-instruct -> google/gemma-3-27b-it | 533 | 0.512 |
| meta-llama/llama-3.1-8b-instruct -> meta-llama/llama-3.1-8b-instruct | 533 | 0.692 |
| meta-llama/llama-3.1-8b-instruct -> openai/gpt-4o-mini | 533 | 0.338 |
| openai/gpt-4o-mini -> google/gemini-2.5-flash-lite | 529 | 0.045 |
| openai/gpt-4o-mini -> google/gemma-3-27b-it | 529 | 0.520 |
| openai/gpt-4o-mini -> meta-llama/llama-3.1-8b-instruct | 529 | 0.875 |
| openai/gpt-4o-mini -> openai/gpt-4o-mini | 529 | 0.389 |

### 4. IV (Wald ratio). exclusion restriction (the note changes acceptance only through the named cues) is doubtful

| liar | n | first stage (d share) | reduced form (d acceptance) | Wald [bootstrap 95% CI] |
|---|---|---|---|---|
| Llama 3.1 8B | 131 | +0.285 | +0.261 | +0.917 [+0.670, +1.215] |
| Gemma 3 27B | 130 | +0.433 | +0.185 | +0.426 [+0.317, +0.549] |
| gpt-4o-mini | 128 | +0.363 | +0.174 | +0.479 [+0.334, +0.645] |
| Gemini 2.5 Flash-Lite | 122 | +0.352 | +0.174 | +0.494 [+0.327, +0.703] |

### 5. Stated B-hat. the stated B-hat follows the story and may rationalize it

| liar | manipulation check (B-hat full - placebo) | mediation: indirect [95% CI] |
|---|---|---|
| Llama 3.1 8B | +0.623 [+0.569, +0.676] | -0.056 [-0.175, +0.058] |
| Gemma 3 27B | +0.778 [+0.727, +0.828] | +0.135 [-0.046, +0.345] |
| gpt-4o-mini | +0.757 [+0.708, +0.807] | +0.186 [+0.003, +0.354] |
| Gemini 2.5 Flash-Lite | +0.692 [+0.635, +0.749] | +0.222 [+0.041, +0.387] |

B-hat vs story cue overlap (Jaccard), observed minus one shuffle across prompts within model x condition:

| liar, condition | n | observed | shuffled | difference [95% CI] |
|---|---|---|---|---|
| meta-llama/llama-3.1-8b-instruct|none | 179 | 0.070 | 0.021 | +0.049 [+0.016, +0.082] |
| meta-llama/llama-3.1-8b-instruct|placebo | 177 | 0.403 | 0.216 | +0.187 [+0.139, +0.235] |
| meta-llama/llama-3.1-8b-instruct|full | 177 | 0.411 | 0.191 | +0.220 [+0.173, +0.268] |
| google/gemma-3-27b-it|none | 177 | 0.114 | 0.053 | +0.061 [+0.027, +0.096] |
| google/gemma-3-27b-it|placebo | 177 | 0.444 | 0.216 | +0.228 [+0.196, +0.260] |
| google/gemma-3-27b-it|full | 174 | 0.473 | 0.218 | +0.256 [+0.221, +0.290] |
| openai/gpt-4o-mini|none | 178 | 0.094 | 0.044 | +0.049 [+0.017, +0.082] |
| openai/gpt-4o-mini|placebo | 173 | 0.310 | 0.153 | +0.156 [+0.112, +0.201] |
| openai/gpt-4o-mini|full | 178 | 0.350 | 0.180 | +0.170 [+0.127, +0.214] |
| google/gemini-2.5-flash-lite|none | 177 | 0.065 | 0.034 | +0.031 [-0.006, +0.067] |
| google/gemini-2.5-flash-lite|placebo | 173 | 0.462 | 0.176 | +0.286 [+0.244, +0.329] |
| google/gemini-2.5-flash-lite|full | 170 | 0.454 | 0.163 | +0.291 [+0.250, +0.331] |

Elicitation flags: {'google/gemini-2.5-flash-lite|full': {'n': 170, 'echo': 0, 'refusal': 0, 'breakdown': 8}, 'google/gemini-2.5-flash-lite|none': {'n': 177, 'echo': 0, 'refusal': 0, 'breakdown': 0}, 'google/gemini-2.5-flash-lite|placebo': {'n': 173, 'echo': 0, 'refusal': 2, 'breakdown': 3}, 'google/gemma-3-27b-it|full': {'n': 174, 'echo': 0, 'refusal': 1, 'breakdown': 0}, 'google/gemma-3-27b-it|none': {'n': 177, 'echo': 0, 'refusal': 0, 'breakdown': 0}, 'google/gemma-3-27b-it|placebo': {'n': 177, 'echo': 0, 'refusal': 0, 'breakdown': 0}, 'meta-llama/llama-3.1-8b-instruct|full': {'n': 177, 'echo': 0, 'refusal': 1, 'breakdown': 0}, 'meta-llama/llama-3.1-8b-instruct|none': {'n': 179, 'echo': 0, 'refusal': 0, 'breakdown': 0}, 'meta-llama/llama-3.1-8b-instruct|placebo': {'n': 177, 'echo': 0, 'refusal': 0, 'breakdown': 0}, 'openai/gpt-4o-mini|full': {'n': 178, 'echo': 0, 'refusal': 0, 'breakdown': 1}, 'openai/gpt-4o-mini|none': {'n': 178, 'echo': 0, 'refusal': 0, 'breakdown': 0}, 'openai/gpt-4o-mini|placebo': {'n': 173, 'echo': 0, 'refusal': 0, 'breakdown': 0}}

### 6. Directional T by condition, and placebo minus none (on the target's placebo-net cues)

| liar, condition | n | mean T [95% CI] |
|---|---|---|
| google/gemini-2.5-flash-lite|full | 80 | +1.681 [+1.552, +1.811] |
| google/gemini-2.5-flash-lite|none | 87 | +0.057 [-0.026, +0.141] |
| google/gemini-2.5-flash-lite|placebo | 83 | +0.012 [-0.120, +0.144] |
| google/gemma-3-27b-it|full | 85 | +1.506 [+1.364, +1.647] |
| google/gemma-3-27b-it|none | 87 | -0.103 [-0.232, +0.025] |
| google/gemma-3-27b-it|placebo | 87 | -0.069 [-0.220, +0.082] |
| meta-llama/llama-3.1-8b-instruct|full | 87 | +1.178 [+1.000, +1.357] |
| meta-llama/llama-3.1-8b-instruct|none | 89 | +0.017 [-0.054, +0.088] |
| meta-llama/llama-3.1-8b-instruct|placebo | 87 | +0.011 [-0.094, +0.117] |
| openai/gpt-4o-mini|full | 88 | +0.977 [+0.817, +1.137] |
| openai/gpt-4o-mini|none | 88 | +0.017 [-0.075, +0.109] |
| openai/gpt-4o-mini|placebo | 84 | -0.095 [-0.208, +0.018] |

| liar | placebo minus none: n, mean [95% CI] |
|---|---|
| Llama 3.1 8B | 132, +0.182 [+0.130, +0.234] |
| Gemma 3 27B | 131, +0.229 [+0.167, +0.291] |
| gpt-4o-mini | 128, +0.089 [+0.036, +0.141] |
| Gemini 2.5 Flash-Lite | 128, +0.180 [+0.122, +0.239] |

## Empty-cue exclusions (added before unblinding, Addendum 3)

60 units; by persona x model {'P6|google/gemini-2.5-flash-lite': 15, 'P6|google/gemma-3-27b-it': 15, 'P6|meta-llama/llama-3.1-8b-instruct': 15, 'P6|openai/gpt-4o-mini': 15}; by prompt x persona {'technology|P6': 60}.

## Bookkeeping

Failed cells by model x condition: {'google/gemini-2.5-flash-lite|full': 10, 'google/gemini-2.5-flash-lite|none': 3, 'google/gemini-2.5-flash-lite|placebo': 7, 'google/gemma-3-27b-it|full': 6, 'google/gemma-3-27b-it|none': 3, 'google/gemma-3-27b-it|placebo': 3, 'meta-llama/llama-3.1-8b-instruct|full': 3, 'meta-llama/llama-3.1-8b-instruct|none': 1, 'meta-llama/llama-3.1-8b-instruct|placebo': 3, 'openai/gpt-4o-mini|full': 2, 'openai/gpt-4o-mini|none': 2, 'openai/gpt-4o-mini|placebo': 7}

Degenerate lies by condition: {}; confessed by condition: {}
