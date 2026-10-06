RULE (brief §8 item 26)
  A emotional_appeal primary-Google: v0.6 kappa 0.6520 AC1 0.6736 -> v0.7 kappa 0.6716 AC1 0.7336: MET
  B max change, other cues: primary 0.063, google 0.126 (band 0.08): NOT MET [('google', 'institutional_authority', 0.08421052631578947), ('google', 'mechanism_explanation', 0.09473684210526316), ('google', 'hedged_claim', 0.12631578947368421)]
  cap not breached: True; lies valid for both: 95 (need 90)
  => FREEZE v0.6

CHANGE RATES (share of lies whose label differs), heatmap-only marked h
  cue                        prim v06->v07 goog v06->v07 prim retest v07 gpt5 v06->v07
  document_citation                 0.000         0.021            0.011         0.011
  institutional_authority           0.000         0.084!           0.011         0.021
  named_expert h                    0.000         0.063            0.000         0.000
  historical_anchor                 0.011         0.032            0.011         0.043
  official_failure                  0.000         0.032            0.000         0.021
  first_person_witness              0.011         0.021            0.011         0.000
  family_provenance                 0.000         0.000            0.000         0.000
  sensory_detail h                  0.021         0.053            0.021         0.032
  direct_quotation                  0.011         0.032            0.011         0.032
  mundane_aftermath                 0.011         0.074            0.021         0.021
  mechanism_explanation h           0.063         0.095!           0.021         0.043
  emotional_appeal                  0.126         0.105            0.021         0.117
  hedged_claim                      0.032         0.126!           0.032         0.053
  self_deprecation                  0.000         0.011            0.000         0.011
  skeptic_acknowledgment            0.011         0.042            0.000         0.053
  humor                             0.021         0.032            0.011         0.011

AGREEMENT primary vs Google, v0.7 (bootstrap over lies, 2,000 resamples, seed 20261006)
  document_citation        pos  16  kappa  0.73 [ 0.49,  0.92]  AC1  0.92 [ 0.84,  0.97]  prev 0.11/0.17  
  institutional_authority  pos  36  kappa  0.79 [ 0.65,  0.91]  AC1  0.83 [ 0.72,  0.93]  prev 0.31/0.36  
  historical_anchor        pos  50  kappa  0.73 [ 0.58,  0.85]  AC1  0.73 [ 0.59,  0.86]  prev 0.49/0.42  AT RISK
  official_failure         pos  10  kappa  0.64 [ 0.27,  0.90]  AC1  0.94 [ 0.87,  0.99]  prev 0.06/0.09  
  first_person_witness     pos  24  kappa  0.91 [ 0.80,  1.00]  AC1  0.95 [ 0.89,  1.00]  prev 0.23/0.24  
  family_provenance        pos  18  kappa  0.93 [ 0.80,  1.00]  AC1  0.97 [ 0.92,  1.00]  prev 0.17/0.19  
  direct_quotation         pos  37  kappa  0.84 [ 0.72,  0.95]  AC1  0.86 [ 0.76,  0.96]  prev 0.34/0.37  
  mundane_aftermath        pos  19  kappa  0.48 [ 0.21,  0.72]  AC1  0.83 [ 0.72,  0.92]  prev 0.08/0.19  
  emotional_appeal         pos  39  kappa  0.67 [ 0.50,  0.82]  AC1  0.73 [ 0.58,  0.86]  prev 0.31/0.37  AT RISK
  hedged_claim             pos  26  kappa  0.45 [ 0.21,  0.67]  AC1  0.76 [ 0.62,  0.86]  prev 0.20/0.18  AT RISK
  self_deprecation         pos   4  kappa  0.66 [ 0.00,  1.00]  AC1  0.98 [ 0.94,  1.00]  prev 0.04/0.02  
  skeptic_acknowledgment   pos  10  kappa  0.81 [ 0.52,  1.00]  AC1  0.96 [ 0.91,  1.00]  prev 0.09/0.08  
  humor                    pos  10  kappa  0.73 [ 0.39,  0.94]  AC1  0.95 [ 0.89,  0.99]  prev 0.11/0.06  

AGREEMENT primary vs gpt-5, v0.7 (bootstrap over lies, 2,000 resamples, seed 20261006)
  document_citation        pos  11  kappa  0.75 [ 0.46,  0.94]  AC1  0.95 [ 0.89,  0.99]  prev 0.11/0.08  
  institutional_authority  pos  30  kappa  0.90 [ 0.80,  0.98]  AC1  0.93 [ 0.85,  0.98]  prev 0.31/0.28  
  historical_anchor        pos  49  kappa  0.68 [ 0.54,  0.82]  AC1  0.69 [ 0.54,  0.83]  prev 0.49/0.38  AT RISK
  official_failure         pos  10  kappa  0.54 [ 0.14,  0.83]  AC1  0.93 [ 0.86,  0.98]  prev 0.06/0.08  
  first_person_witness     pos  23  kappa  0.94 [ 0.84,  1.00]  AC1  0.97 [ 0.91,  1.00]  prev 0.23/0.23  
  family_provenance        pos  18  kappa  0.89 [ 0.73,  1.00]  AC1  0.96 [ 0.90,  1.00]  prev 0.17/0.18  
  direct_quotation         pos  39  kappa  0.80 [ 0.65,  0.91]  AC1  0.82 [ 0.70,  0.93]  prev 0.34/0.39  AT RISK
  mundane_aftermath        pos  16  kappa  0.49 [ 0.19,  0.73]  AC1  0.87 [ 0.77,  0.94]  prev 0.08/0.15  
  emotional_appeal         pos  60  kappa  0.41 [ 0.28,  0.56]  AC1  0.35 [ 0.17,  0.54]  prev 0.31/0.63  AT RISK
  hedged_claim             pos  25  kappa  0.33 [ 0.06,  0.55]  AC1  0.74 [ 0.59,  0.85]  prev 0.20/0.14  AT RISK
  self_deprecation         pos   5  kappa  0.74 [ 0.00,  1.00]  AC1  0.98 [ 0.94,  1.00]  prev 0.04/0.04  
  skeptic_acknowledgment   pos  16  kappa  0.68 [ 0.43,  0.87]  AC1  0.90 [ 0.82,  0.96]  prev 0.09/0.17  
  humor                    pos  16  kappa  0.73 [ 0.51,  0.92]  AC1  0.92 [ 0.84,  0.98]  prev 0.11/0.17  
