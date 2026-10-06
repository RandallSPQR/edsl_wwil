
CHECK 1: primary (v0.6) vs gpt-5 (v0.6) (94 lies; bootstrap over lies, 2,000 resamples, seed 20261006)
  cue                       pos  kappa [95% CI]          AC1 [95% CI]        at risk
  document_citation          10   0.81 [ 0.52,  1.00]    0.96 [ 0.91,  1.00]   
  institutional_authority    32   0.85 [ 0.73,  0.95]    0.89 [ 0.79,  0.96]   
  historical_anchor          49   0.66 [ 0.51,  0.80]    0.67 [ 0.51,  0.81]   YES
  official_failure            9   0.47 [-0.03,  0.82]    0.93 [ 0.86,  0.98]   
  first_person_witness       21   0.97 [ 0.89,  1.00]    0.98 [ 0.95,  1.00]   
  family_provenance          18   0.89 [ 0.75,  1.00]    0.96 [ 0.90,  1.00]   
  direct_quotation*          38   0.84 [ 0.71,  0.94]    0.86 [ 0.75,  0.95]   
  mundane_aftermath*         17   0.46 [ 0.16,  0.71]    0.85 [ 0.74,  0.93]   
  emotional_appeal           64   0.48 [ 0.32,  0.62]    0.45 [ 0.27,  0.62]   YES
  hedged_claim*              27   0.52 [ 0.29,  0.71]    0.76 [ 0.62,  0.87]   YES
  self_deprecation            5   0.74 [ 0.00,  1.00]    0.98 [ 0.94,  1.00]   
  skeptic_acknowledgment     15   0.71 [ 0.47,  0.90]    0.92 [ 0.84,  0.97]   
  humor                      15   0.77 [ 0.54,  0.95]    0.93 [ 0.86,  0.99]   
  at risk: ['historical_anchor', 'emotional_appeal', 'hedged_claim']

reference: primary (v0.5) vs gpt-5 (v0.5), Stage 1 (95 lies; bootstrap over lies, 2,000 resamples, seed 20261006)
  cue                       pos  kappa [95% CI]          AC1 [95% CI]        at risk
  document_citation          12   0.71 [ 0.42,  0.92]    0.94 [ 0.87,  0.99]   
  institutional_authority    32   0.88 [ 0.77,  0.97]    0.91 [ 0.82,  0.98]   
  historical_anchor          52   0.73 [ 0.60,  0.85]    0.73 [ 0.60,  0.85]   YES
  official_failure            9   0.59 [ 0.16,  0.86]    0.94 [ 0.88,  0.99]   
  first_person_witness       23   0.91 [ 0.79,  1.00]    0.95 [ 0.89,  1.00]   
  family_provenance          18   1.00 [ 1.00,  1.00]    1.00 [ 1.00,  1.00]   
  direct_quotation*          46   0.67 [ 0.52,  0.81]    0.70 [ 0.54,  0.83]   YES
  mundane_aftermath*         21   0.59 [ 0.36,  0.79]    0.84 [ 0.73,  0.93]   
  emotional_appeal           66   0.58 [ 0.42,  0.73]    0.59 [ 0.42,  0.75]   YES
  hedged_claim*              48   0.56 [ 0.41,  0.71]    0.58 [ 0.40,  0.73]   YES
  self_deprecation            6   0.65 [-0.01,  1.00]    0.97 [ 0.92,  1.00]   
  skeptic_acknowledgment     24   0.63 [ 0.42,  0.81]    0.83 [ 0.72,  0.92]   
  humor                      18   0.76 [ 0.55,  0.92]    0.91 [ 0.83,  0.97]   
  at risk: ['historical_anchor', 'direct_quotation', 'emotional_appeal', 'hedged_claim']

reference: primary (v0.5, Stage 1) vs Google RETEST (v0.5) (95 lies; bootstrap over lies, 2,000 resamples, seed 20261006)
  cue                       pos  kappa [95% CI]          AC1 [95% CI]        at risk
  document_citation          16   0.79 [ 0.56,  0.95]    0.93 [ 0.86,  0.99]   
  institutional_authority    42   0.73 [ 0.59,  0.87]    0.76 [ 0.63,  0.88]   YES
  historical_anchor          52   0.77 [ 0.64,  0.89]    0.77 [ 0.64,  0.89]   YES
  official_failure           14   0.56 [ 0.23,  0.82]    0.90 [ 0.81,  0.96]   
  first_person_witness       26   0.83 [ 0.69,  0.95]    0.90 [ 0.81,  0.97]   
  family_provenance          18   1.00 [ 1.00,  1.00]    1.00 [ 1.00,  1.00]   
  direct_quotation*          40   0.68 [ 0.51,  0.82]    0.73 [ 0.58,  0.86]   YES
  mundane_aftermath*         24   0.55 [ 0.32,  0.74]    0.80 [ 0.68,  0.90]   YES
  emotional_appeal           54   0.68 [ 0.53,  0.83]    0.68 [ 0.54,  0.83]   YES
  hedged_claim*              48   0.54 [ 0.39,  0.69]    0.56 [ 0.39,  0.72]   YES
  self_deprecation            7   0.58 [-0.02,  0.92]    0.95 [ 0.90,  0.99]   
  skeptic_acknowledgment     16   0.68 [ 0.42,  0.88]    0.90 [ 0.82,  0.97]   
  humor                      15   0.77 [ 0.55,  0.94]    0.93 [ 0.86,  0.99]   
  at risk: ['institutional_authority', 'historical_anchor', 'direct_quotation', 'mundane_aftermath', 'emotional_appeal', 'hedged_claim']

CHECK 2: Google grader label-change rates (share of lies whose label differs; n = 95, 95, 95)
  cue                      old run1->old run2  old run1->new  old run2->new    prev old1/old2/new
  document_citation                      0.00           0.02           0.02    0.17/0.17/0.15
  institutional_authority                0.08           0.11           0.08    0.42/0.42/0.40
  historical_anchor                      0.06           0.08           0.06    0.47/0.43/0.43
  official_failure                       0.02           0.05           0.05    0.12/0.14/0.11
  first_person_witness                   0.02           0.02           0.02    0.26/0.26/0.26
  family_provenance                      0.00           0.00           0.00    0.19/0.19/0.19
  direct_quotation*                      0.02           0.07           0.07    0.35/0.33/0.36
  mundane_aftermath*                     0.01           0.11           0.09    0.14/0.15/0.20
  emotional_appeal                       0.08           0.21           0.15    0.49/0.47/0.41
  hedged_claim*                          0.08           0.18           0.16    0.27/0.27/0.14
  self_deprecation                       0.02           0.04           0.04    0.05/0.05/0.03
  skeptic_acknowledgment                 0.03           0.05           0.04    0.09/0.11/0.11
  humor                                  0.03           0.05           0.04    0.13/0.12/0.07

  gpt-5 v0.5 -> v0.6 change (n = 94; temperature 1.0, so this mixes rubric and sampling):
  document_citation 0.01, institutional_authority 0.02, historical_anchor 0.05, official_failure 0.04, first_person_witness 0.00, family_provenance 0.01, direct_quotation 0.06, mundane_aftermath 0.09, emotional_appeal 0.07, hedged_claim 0.10, self_deprecation 0.01, skeptic_acknowledgment 0.07, humor 0.03
