# Final-analysis validation (simulated data only)

- **Data model:** `validate_final.py`, with the decision code `reversed_analysis.decide_all`.
- **Simulated studies:** each has 4 liar models, and each model has 72 categories × 5 personas ×
  3 conditions × 1 replicate.
- **Heterogeneity:** scenario S2 from `design/power.py`, matching the first study.
- **Model fits:** every fit uses the registered mixed model, with the per-category fallback.

| | true B = 0 (300 studies) | true B = 0.10 (150) | true B = 0.30 (150) |
|---|---|---|---|
| efficacy rejection, any of the 4 models (familywise) | **0.040** (α 0.05) | 0.993 | 1.000 |
| efficacy rejection, per model | 0.010 | **0.878** | 1.000 |
| equivalence (TOST ±0.10) declared, per model | 0.794 | **0.007** | 0.000 |
| 95% CI coverage of B | 0.942 | 0.965 | 0.955 |
| median (estimate − truth) | 0.000 | 0.000 | +0.001 |
| share of estimates below truth | 0.502 | 0.500 | 0.492 |
| fits that took the registered fallback | 23% | 23% | 20% |

**How to read the table:**
- **False positives:** the familywise rate stays at or below α (0.040 against 0.05).
- **Equivalence:** at B = 0.10, exactly at the margin, it is declared 0.7% of the time, within the
  0.05 limit.
- **Estimation:** coverage is close to 95% and the estimates are median-unbiased.
- **Agreement with the pre-registered power (section 8):**
  - Power at B = 0.10 per model is 0.88. The registration gives 0.74 at the strictest Holm level and
    0.88 at the loosest, so the Holm procedure lands at the upper end.
  - Equivalence at B = 0 is 0.79 per model. The registration gives 0.64 at 0.0125; the Holm levels
    up to 0.05 raise it.

**Sign test:** passes; see `sign_test.json`.
- Synthetic data with more named cues under full gives B = +0.30 to +0.36, labelled
  "belief-tracking".
- The reverse gives B = −0.19 to −0.24, labelled "fewer named cues under full than under reversed".
  It shrinks towards zero because *s* is floored at 0.
