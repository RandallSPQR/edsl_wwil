95 lies, primary vs Google, bootstrap over lies (2,000 resamples)
cue                      |   OLD v0.5 kappa [95%]            AC1 [95%] risk |   NEW v0.6 kappa [95%]            AC1 [95%]  pos risk
document_citation        |  0.79 [ 0.56, 0.95]   0.93 [ 0.86, 0.99]      |  0.81 [ 0.60, 0.96]   0.95 [ 0.89, 0.99]   14     
institutional_authority  |  0.82 [ 0.70, 0.93]   0.84 [ 0.73, 0.94]      |  0.70 [ 0.55, 0.85]   0.75 [ 0.61, 0.87]   40  YES
historical_anchor        |  0.77 [ 0.63, 0.89]   0.77 [ 0.64, 0.89]  YES |  0.73 [ 0.59, 0.85]   0.73 [ 0.58, 0.86]   51  YES
official_failure         |  0.63 [ 0.30, 0.88]   0.92 [ 0.85, 0.98]      |  0.59 [ 0.23, 0.85]   0.93 [ 0.86, 0.98]   11     
first_person_witness     |  0.89 [ 0.76, 0.98]   0.93 [ 0.86, 0.99]      |  0.89 [ 0.76, 0.97]   0.93 [ 0.86, 0.98]   25     
family_provenance        |  1.00 [ 1.00, 1.00]   1.00 [ 1.00, 1.00]      |  0.93 [ 0.81, 1.00]   0.97 [ 0.92, 1.00]   18     
direct_quotation         |  0.68 [ 0.51, 0.83]   0.73 [ 0.59, 0.86]  YES |  0.84 [ 0.71, 0.93]   0.86 [ 0.75, 0.95]   37     
mundane_aftermath        |  0.50 [ 0.25, 0.72]   0.79 [ 0.67, 0.90]  YES |  0.51 [ 0.25, 0.72]   0.83 [ 0.73, 0.92]   20     
emotional_appeal         |  0.77 [ 0.63, 0.89]   0.77 [ 0.64, 0.89]  YES |  0.65 [ 0.49, 0.80]   0.67 [ 0.52, 0.82]   47  YES
hedged_claim             |  0.41 [ 0.25, 0.57]   0.44 [ 0.25, 0.62]  YES |  0.34 [ 0.11, 0.57]   0.71 [ 0.56, 0.84]   27  YES
self_deprecation         |  0.58 [-0.02, 0.90]   0.95 [ 0.90, 0.99]      |  0.56 [-0.02, 1.00]   0.97 [ 0.93, 1.00]    5     
skeptic_acknowledgment   |  0.72 [ 0.47, 0.90]   0.92 [ 0.85, 0.97]      |  0.78 [ 0.51, 0.95]   0.95 [ 0.89, 0.99]   12     
humor                    |  0.73 [ 0.49, 0.90]   0.92 [ 0.83, 0.97]      |  0.81 [ 0.52, 1.00]   0.96 [ 0.91, 1.00]   10     

prevalence (primary / google), old -> new, for the revised cues:
  hedged_claim           0.51/0.27 -> 0.23/0.14
  direct_quotation       0.37/0.35 -> 0.35/0.36
  mundane_aftermath      0.22/0.14 -> 0.09/0.20
  historical_anchor      0.55/0.47 -> 0.51/0.43

at risk under v0.6 (both lower bounds < 0.70): ['institutional_authority', 'historical_anchor', 'emotional_appeal', 'hedged_claim']

WITHIN-GRADER CHANGE, old rubric -> new rubric, same lies (share of labels that flipped; definitions changed only for *)
  cue                       primary   google
  document_citation            0.01     0.02
  institutional_authority      0.03     0.11
  historical_anchor            0.04     0.08
  official_failure             0.01     0.05
  first_person_witness         0.02     0.02
  family_provenance            0.02     0.00
  direct_quotation*            0.04     0.07
  mundane_aftermath*           0.17     0.11
  emotional_appeal             0.09     0.21
  hedged_claim*                0.27     0.18
  self_deprecation             0.01     0.04
  skeptic_acknowledgment       0.05     0.05
  humor                        0.04     0.05

WORST-CASE POOL under v0.6 (the four at-risk cues excluded)
  P1: ['document_citation', 'official_failure'] (2) -> primary pool
  P2: ['first_person_witness', 'family_provenance', 'humor'] (3) -> primary pool
  P3: ['direct_quotation', 'mundane_aftermath'] (2) -> primary pool
  P4: ['self_deprecation', 'skeptic_acknowledgment'] (2) -> secondary (P4)
  P5: ['family_provenance', 'direct_quotation'] (2) -> primary pool
  P6: ['first_person_witness', 'humor'] (2) -> primary pool
  dropped unit: technology P6 (no placebo-free cue left)
  units per replicate per liar: 9 (10 with no exclusions; 5 in the previous worst case)
