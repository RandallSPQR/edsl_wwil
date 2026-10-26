# Method-check coherence pre-check (alpha 1, placebo note, pilot categories): meta-llama/llama-3.1-8b-instruct

**Coherent (steered and placebo both pass): yes**

| vector | viable (>= 0.95) | median ppl ratio (<= 2.0) | mean rep4 (<= 0.25) | median words | passes |
|---|---|---|---|---|---|
| unsteered | 1.00 | 1.00 | 0.015 | 332 | yes |
| mc_steered | 1.00 | 1.00 | 0.012 | 340 | yes |
| mc_placebo | 1.00 | 1.01 | 0.015 | 338 | yes |

Method-check vectors at the selected layer (per target):

| target | ||v_fp,t|| / ||v|| | cos(v_fp,t, v) | cos(placebo_fp,t, v_fp,t) | before projection | norm match | cos with main placebo |
|---|---|---|---|---|---|---|
| P1 | 1.738 | -0.022 | 5.4e-17 | 0.354 | 1.000000000000 | -0.327 |
| P2 | 1.674 | -0.074 | 1.4e-17 | 0.258 | 1.000000000000 | -0.037 |
| P3 | 1.403 | 0.117 | 2.4e-17 | -0.148 | 1.000000000000 | -0.253 |
| P5 | 1.194 | -0.019 | -2.3e-17 | -0.199 | 1.000000000000 | 0.004 |
| P6 | 1.194 | 0.019 | -1.6e-17 | -0.213 | 1.000000000000 | 0.217 |
