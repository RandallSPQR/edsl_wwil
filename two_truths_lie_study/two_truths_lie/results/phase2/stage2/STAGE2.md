# Phase 2 stage 2: primary analysis (section 7)

| test | label | Delta | 95% CI | K | p | method check |
|---|---|---|---|---|---|---|
| google/gemma-3-27b-it|H1 | **inconclusive: method check failed** | +0.020 | [-0.034, +0.074] | 32 | 0.4618 | False |
| google/gemma-3-27b-it|H2 | **inconclusive: method check failed** | -0.030 | [-0.080, +0.020] | 32 | 0.2291 | False |
| meta-llama/llama-3.1-8b-instruct|H1 | **steerable** | +0.093 | [+0.044, +0.142] | 32 | 0.0005188 | True |
| meta-llama/llama-3.1-8b-instruct|H2 | **steerable** | -0.124 | [-0.182, -0.066] | 32 | 0.0001346 | True |
