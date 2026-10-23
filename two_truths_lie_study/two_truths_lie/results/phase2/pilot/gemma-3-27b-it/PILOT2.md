# Dose-finding pilot, Addendum 5 placebo (coherence only): google/gemma-3-27b-it

## H1 (reversed note, +alpha v): **confirmatory alpha = 2.0**

Unsteered (alpha 0, n 40): viable 1.00, rep4 0.005, median words 349.

| alpha | vector | viable (>= 0.95) | median ppl ratio (<= 2.0) | mean rep4 (<= 0.25) | median words | passes | coherent |
|---|---|---|---|---|---|---|---|
| 0.25 | steered | 1.00 | 1.00 | 0.004 | 346 | yes | yes |
| 0.25 | placebo | 1.00 | 1.00 | 0.005 | 350 | yes | yes |
| 0.5 | steered | 1.00 | 1.02 | 0.005 | 347 | yes | yes |
| 0.5 | placebo | 1.00 | 1.03 | 0.005 | 346 | yes | yes |
| 1.0 | steered | 1.00 | 1.09 | 0.005 | 350 | yes | yes |
| 1.0 | placebo | 1.00 | 1.12 | 0.006 | 354 | yes | yes |
| 2.0 | steered | 1.00 | 1.63 | 0.006 | 350 | yes | yes |
| 2.0 | placebo | 1.00 | 1.64 | 0.006 | 351 | yes | yes |
| 4.0 | steered | 1.00 | 11.36 | 0.013 | 356 | no | no |
| 4.0 | placebo | 0.93 | 11.39 | 0.034 | 358 | no | no |

## H2 (full note, -alpha v): **confirmatory alpha = 1.0**

Unsteered (alpha 0, n 40): viable 1.00, rep4 0.007, median words 364.

| alpha | vector | viable (>= 0.95) | median ppl ratio (<= 2.0) | mean rep4 (<= 0.25) | median words | passes | coherent |
|---|---|---|---|---|---|---|---|
| 0.25 | steered | 1.00 | 1.01 | 0.005 | 363 | yes | yes |
| 0.25 | placebo | 1.00 | 1.00 | 0.007 | 364 | yes | yes |
| 0.5 | steered | 1.00 | 1.04 | 0.006 | 362 | yes | yes |
| 0.5 | placebo | 1.00 | 1.04 | 0.007 | 362 | yes | yes |
| 1.0 | steered | 1.00 | 1.15 | 0.008 | 361 | yes | yes |
| 1.0 | placebo | 1.00 | 1.16 | 0.006 | 369 | yes | yes |
| 2.0 | steered | 1.00 | 2.13 | 0.006 | 354 | no | no |
| 2.0 | placebo | 1.00 | 1.95 | 0.007 | 362 | yes | no |
| 4.0 | steered | 1.00 | 14.07 | 0.012 | 368 | no | no |
| 4.0 | placebo | 1.00 | 10.56 | 0.010 | 360 | no | no |

