# Dose-finding pilot, Addendum 5 placebo (coherence only): meta-llama/llama-3.1-8b-instruct

## H1 (reversed note, +alpha v): **confirmatory alpha = 4.0**

Unsteered (alpha 0, n 40): viable 1.00, rep4 0.014, median words 326.

| alpha | vector | viable (>= 0.95) | median ppl ratio (<= 2.0) | mean rep4 (<= 0.25) | median words | passes | coherent |
|---|---|---|---|---|---|---|---|
| 0.25 | steered | 1.00 | 1.00 | 0.013 | 326 | yes | yes |
| 0.25 | placebo | 1.00 | 1.00 | 0.012 | 320 | yes | yes |
| 0.5 | steered | 1.00 | 1.00 | 0.011 | 324 | yes | yes |
| 0.5 | placebo | 1.00 | 1.00 | 0.012 | 320 | yes | yes |
| 1.0 | steered | 1.00 | 1.00 | 0.015 | 331 | yes | yes |
| 1.0 | placebo | 1.00 | 1.00 | 0.015 | 323 | yes | yes |
| 2.0 | steered | 1.00 | 1.00 | 0.013 | 335 | yes | yes |
| 2.0 | placebo | 1.00 | 1.00 | 0.017 | 328 | yes | yes |
| 4.0 | steered | 0.97 | 1.09 | 0.014 | 341 | yes | yes |
| 4.0 | placebo | 1.00 | 1.08 | 0.012 | 328 | yes | yes |

## H2 (full note, -alpha v): **confirmatory alpha = 4.0**

Unsteered (alpha 0, n 40): viable 1.00, rep4 0.016, median words 342.

| alpha | vector | viable (>= 0.95) | median ppl ratio (<= 2.0) | mean rep4 (<= 0.25) | median words | passes | coherent |
|---|---|---|---|---|---|---|---|
| 0.25 | steered | 1.00 | 1.00 | 0.017 | 340 | yes | yes |
| 0.25 | placebo | 1.00 | 1.00 | 0.015 | 336 | yes | yes |
| 0.5 | steered | 1.00 | 1.00 | 0.019 | 330 | yes | yes |
| 0.5 | placebo | 1.00 | 1.00 | 0.021 | 332 | yes | yes |
| 1.0 | steered | 1.00 | 0.99 | 0.016 | 327 | yes | yes |
| 1.0 | placebo | 1.00 | 1.00 | 0.018 | 340 | yes | yes |
| 2.0 | steered | 1.00 | 0.99 | 0.014 | 326 | yes | yes |
| 2.0 | placebo | 1.00 | 1.00 | 0.015 | 340 | yes | yes |
| 4.0 | steered | 1.00 | 1.09 | 0.018 | 324 | yes | yes |
| 4.0 | placebo | 1.00 | 1.02 | 0.017 | 338 | yes | yes |

