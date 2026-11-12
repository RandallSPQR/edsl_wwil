# Method-check coherence pre-check (alpha 1, placebo note, pilot categories): google/gemma-3-27b-it

**Coherent (steered and placebo both pass): yes**

| vector | viable (>= 0.95) | median ppl ratio (<= 2.0) | mean rep4 (<= 0.25) | median words | passes |
|---|---|---|---|---|---|
| unsteered | 1.00 | 1.00 | 0.009 | 372 | yes |
| mc_steered | 1.00 | 1.38 | 0.006 | 375 | yes |
| mc_placebo | 1.00 | 1.18 | 0.008 | 372 | yes |

Method-check vectors at the selected layer (per target):

| target | ||v_fp,t|| / ||v|| | cos(v_fp,t, v) | cos(placebo_fp,t, v_fp,t) | before projection | norm match | cos with main placebo |
|---|---|---|---|---|---|---|
| P1 | 1.473 | -0.273 | -1.5e-17 | 0.287 | 1.000000000000 | 0.194 |
| P2 | 1.357 | 0.215 | 5.6e-17 | -0.513 | 1.000000000000 | -0.365 |
| P3 | 0.784 | 0.140 | 3.5e-17 | 0.236 | 1.000000000000 | 0.406 |
| P5 | 1.253 | -0.245 | 0.0e+00 | -0.096 | 1.000000000000 | 0.441 |
| P6 | 1.253 | 0.245 | -7.6e-17 | -0.316 | 1.000000000000 | 0.319 |
