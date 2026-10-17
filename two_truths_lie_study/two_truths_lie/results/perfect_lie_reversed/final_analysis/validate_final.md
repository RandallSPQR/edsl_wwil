# Final-analysis validation (simulated data only)

- **Code:** after the review fixes. Data from `validate_final.py` and the follow-up checks below;
  the decision code is `reversed_analysis.decide_all`.
- **Simulated studies:** each has 4 liar models, and each model has 72 categories × 5 personas ×
  3 conditions × 1 replicate.
- **Heterogeneity:** S2 (first-study-like) unless stated otherwise.

## Main scenarios (`validate_final.json`)

| scenario | studies | efficacy: any model | efficacy: per model | equivalence: per model | 95% CI coverage | median error | fallback used |
|---|---|---|---|---|---|---|---|
| all four null (B = 0) | 300 | **0.040** | 0.010 | 0.794 | 0.942 | 0.000 | 11% |
| B = +0.10 | 150 | 0.993 | **0.880** | **0.007** | 0.965 | 0.000 | 10% |
| B = −0.10 (negative equivalence boundary) | 150 | 0.993 | 0.827 | **0.013** | 0.947 | +0.001 | 10% |
| B = +0.30 | 150 | 1.000 | 1.000 | 0.000 | 0.955 | +0.001 | 9% |
| discrete records through the full pipeline, B = 0; 30% of full lies for P1 and P5 failed | 100 | **0.040** | 0.010 | — | — | B median −0.002 | 19% |

## Mixed configuration: two models with B = 0.30, two with B = 0

| run | studies | any null model falsely rejected | per null model | power on the two effects |
|---|---|---|---|---|
| `validate_final.json` | 150 | 0.107 | 0.057 | 1.00 |
| `validate_mixed_450.json` | 450 | 0.062 | 0.031 | 1.00 |
| `validate_mixed_1500.json` | 1,500 | **0.059** [0.048, 0.072] | 0.030 | 1.00 |
| **pooled** | **2,100** | **0.063** [0.053, 0.074] | | |

## Calibration of a single null test (`validate_null_calibration.json`, 900 fits)

| local alpha | registered procedure | per-category t-test always |
|---|---|---|
| 0.0125 | 0.016 | 0.013 |
| 0.025 | 0.031 | 0.031 |
| 0.05 | 0.066 | 0.063 |

Monte Carlo SE at 0.05 is about 0.007.

## Reading

- **When every model is null**, familywise efficacy error is within α: 0.040 for Gaussian data,
  and 0.040 for discrete, bounded records with asymmetric missingness through the whole pipeline.
- **When true effects are rejected first**, the remaining null models are tested at Holm's looser
  levels (0.025, 0.05). There the error among the nulls is **about 0.06**, against a nominal 0.05.
  Pooled over 2,100 studies the interval is [0.053, 0.074].
- **Cause unresolved (corrected after the second independent review).** An earlier version of this
  file attributed the excess to the registered t-test. That is not established. In the supplied mixed-configuration simulations, at least one of the two null models was rejected in 132 of 2,100 studies (0.063; reported 95% interval 0.053–0.074), compared with nominal familywise alpha 0.05. The cause of this excess is unresolved. A 900-fit diagnostic showed similar empirical rates for the registered procedure and the always-category fallback, but a larger independent check of the balanced Gaussian fallback was nominal, consistent with its exact t reference distribution under that simulator. We retain the registered primary procedure, report this observation and its limitations, and will document any subsequent change as an amendment.
  - The 900-fit table above has a Monte Carlo SE of about 0.007 at 0.05, so it cannot separate a
    1.2× excess from sampling error, nor the mixed model's SE from the fallback's.
  - The reviewer's check of the always-category fallback (100,000 studies) gave 0.01255, 0.02517 and
    0.04980 at 0.0125, 0.025 and 0.05: nominal.
  - Not yet separated: the mixed model's standard error, the rule that selects the fallback, and
    Monte Carlo variability.
  - Seeds: `validate_final.json` mixed studies 170000–170149; `validate_mixed_450.json` 900000–900449;
    `validate_mixed_1500.json` 1300000–1301499; `validate_null_calibration.json` 700000–700899.
- **Equivalence error** at both margins is within α: 0.007 at +0.10 and 0.013 at −0.10.
- **Coverage** is 0.94–0.97, and the estimates are median-unbiased.

**Sign test:** passes; see `sign_test.json`.
