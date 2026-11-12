# Validation of `sequential.py` (brief §8 item 29)

Offline, no model calls. Scripts: `validate.py` and `diagnose.py`. Logs: `validation.log.md` and
`diagnose.log.md`.

## Verdict

The code implements the pre-registered design. All three checks agree with the design within
simulation error, with one stated exception.

**The exception.** The pre-registered test statistic (section 4) divides by the *sample* SD of d and
uses the normal reference. The power tables in section 9 were computed with the *true* SD. With the
sample SD, interim efficacy stops are slightly more frequent than the tables say, by 0.2 to 0.6
percentage points at half the pilot effect. Examples, from 400,000 draws:

| setting | known SD (table) | sample SD (the statistic) |
|---|---|---|
| 10 units per replicate, lift 0.073, SD 0.49 | 0.0142 | 0.0163 |
| 10 units per replicate, lift 0.073, SD 0.405 | 0.0352 | 0.0394 |

This is a property of the pre-registered statistic, not a coding error. The known-SD replay through
the real code matches the closed form, and false-positive rates are unaffected (check i).

## (i) Null: false-positive rate

Four models, true lift 0, through `final_analysis` (both looks, Holm). The design value per model is
0.0125; the family-wise design value is at most 0.05.

| data | N | per model | family-wise |
|---|---|---|---|
| normal d, SD 0.405, 10 units per replicate | 10,000 | 0.0129 (SE 0.0006) | 0.0500 |
| normal d, SD 0.49, 9 units per replicate | 10,000 | 0.0131 (SE 0.0006) | 0.0502 |
| discrete d from synthetic graded lies via `unit_lifts`, cue p 0.3 | 5,000 | 0.0121 (SE 0.0008) | 0.0466 |
| the same, cue p 0.15 | 3,000 | 0.0116 (SE 0.0010) | 0.0460 |

A first discrete run with N = 1,000 gave 0.0165 (+2.2 SE). Rerun with N = 5,000, it is 0.0121.

## (ii) Pilot effect and half effect: operating characteristics against PREREG section 9

One model at the worst-case Holm level (0.0125 in both families), through the real look logic.
N = 5,000 per row, 12 rows (10 and 9 units per replicate; lift 0.146, 0.073 and 0; SD 0.405 and
0.49), 7 rates per row.
- **As coded (sample SD):** largest deviation 2.5 SE, at the half-effect interim efficacy stop,
  explained above. Every other rate is within 2 SE.
- **Known-SD replay:** one cell came out at 3.7 SE out of 84 comparisons. Rerun with N = 40,000, it
  gives 0.0150 against an exact 0.0142 (+1.4 SE). The closed form matches the table in every row.
- **Stop-for-effect rates at the interim:**
  - pilot effect: 0.66 and 0.36 (10 units per replicate); 0.57 and 0.29 (9 units per replicate);
  - half effect: 0.04 and 0.02 (10 units per replicate);
  - all within 0.01 of the table.
- **Detection by the final look:** at least 0.997 at the pilot effect, and 0.55 to 0.80 at half the
  effect, as tabled.

## (iii) Stage 2 with randomly assigned condition labels

- **Data.** Stage 2 holds 46 complete lies, all `full`, so they contain no real contrast and give no
  estimate.
- **Labelling.** Each model's two lies for a persona were labelled `full` and `placebo` at random
  and given one prompt id. This yields about 18 pseudo-units per labelling (about 4 per model).
- **Code exercised.** The real gate, pool, `unit_lifts` and `interim_decisions`.
- **Gate (label-free, on 46 lies).** It excluded historical_anchor; 12 of 13 cues have fewer than 30
  positives and were flagged, not gated.
- **Results over 2,000 labellings:**
  - mean pooled d +0.0002 (zero by symmetry; SD across labellings 0.119);
  - every decision was "extend": with about 4 units per model the interim boundaries cannot be
    reached, which is correct behaviour.
- **What this shows.** The pipeline runs end to end on real records and is centred at zero under
  random labels.
