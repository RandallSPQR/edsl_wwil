(i) NULL: four models, true lift 0, through final_analysis (interim + final, Holm)
  normal d, sd 0.405, 10 units     N=10000: per-model false-positive 0.0129 (design 0.0125, SE 0.0006); family-wise 0.0500 (design <= 0.05, SE 0.0022); lift>0 calls 0.0069
  normal d, sd 0.49, 9 units       N=10000: per-model false-positive 0.0131 (design 0.0125, SE 0.0006); family-wise 0.0502 (design <= 0.05, SE 0.0022); lift>0 calls 0.0064
  discrete d via unit_lifts, p=0.3 N=1000: per-model false-positive 0.0165 (design 0.0125, SE 0.0018); family-wise 0.0640 (SE 0.0069); units per replicate 10

(ii) OPERATING CHARACTERISTICS, one model at the worst-case Holm level (0.0125 both families), through the real look logic (sequential._decide); N=5000 per row
  10 units per replicate                    stop: effect |     stop: flat |         extend |  final: effect |    final: flat |   inconclusive | P(lift>0 call)
  lift 0.146 sd 0.405 sim              0.664 |          0.000 |          0.336 |          0.336 |          0.000 |          0.000 |          1.000
                     prereg           0.655 |          0.000 |          0.345 |          0.345 |          0.000 |          0.000 |          1.000
  lift 0.146 sd 0.490 sim              0.360 |          0.000 |          0.640 |          0.639 |          0.000 |          0.001 |          0.999
                     prereg           0.357 |          0.000 |          0.643 |          0.642 |          0.000 |          0.001 |          0.999
  lift 0.073 sd 0.405 sim              0.041 |          0.000 |          0.959 |          0.764 |          0.158 |          0.037 |          0.804
                     prereg           0.035 |          0.000 |          0.965 |          0.773 |          0.160 |          0.032 |          0.808
  lift 0.073 sd 0.490 sim              0.018 |          0.000 |          0.982 |          0.591 |          0.119 |          0.272 |          0.610
                     prereg           0.014 |          0.000 |          0.986 |          0.599 |          0.113 |          0.274 |          0.613
  lift 0.000 sd 0.405 sim              0.000 |          0.000 |          1.000 |          0.013 |          0.980 |          0.007 |          0.007
                     prereg           0.000 |          0.000 |          1.000 |          0.012 |          0.983 |          0.005 |          0.006   <-- beyond 3 SE: ['stop: effect', 'extend']
  lift 0.000 sd 0.490 sim              0.000 |          0.000 |          1.000 |          0.013 |          0.879 |          0.108 |          0.007
                     prereg           0.000 |          0.000 |          1.000 |          0.012 |          0.885 |          0.103 |          0.006   <-- beyond 3 SE: ['stop: effect', 'extend']
  9 units per replicate                    stop: effect |     stop: flat |         extend |  final: effect |    final: flat |   inconclusive | P(lift>0 call)
  lift 0.146 sd 0.405 sim              0.565 |          0.000 |          0.435 |          0.435 |          0.000 |          0.000 |          1.000
                     prereg           0.567 |          0.000 |          0.433 |          0.433 |          0.000 |          0.000 |          1.000   <-- beyond 3 SE: ['inconclusive', 'P(lift>0 call)']
  lift 0.146 sd 0.490 sim              0.289 |          0.000 |          0.711 |          0.708 |          0.000 |          0.003 |          0.997
                     prereg           0.290 |          0.000 |          0.710 |          0.707 |          0.000 |          0.002 |          0.998
  lift 0.073 sd 0.405 sim              0.032 |          0.000 |          0.968 |          0.719 |          0.148 |          0.100 |          0.751
                     prereg           0.027 |          0.000 |          0.973 |          0.730 |          0.145 |          0.098 |          0.757
  lift 0.073 sd 0.490 sim              0.013 |          0.000 |          0.987 |          0.540 |          0.105 |          0.342 |          0.553
                     prereg           0.011 |          0.000 |          0.989 |          0.546 |          0.103 |          0.340 |          0.557
  lift 0.000 sd 0.405 sim              0.000 |          0.000 |          1.000 |          0.015 |          0.965 |          0.020 |          0.008
                     prereg           0.000 |          0.000 |          1.000 |          0.012 |          0.968 |          0.020 |          0.006   <-- beyond 3 SE: ['stop: effect', 'extend']
  lift 0.000 sd 0.490 sim              0.000 |          0.000 |          1.000 |          0.015 |          0.827 |          0.158 |          0.008
                     prereg           0.000 |          0.000 |          1.000 |          0.012 |          0.832 |          0.156 |          0.006   <-- beyond 3 SE: ['stop: effect', 'extend']
  largest |difference| in simulation-error units: 13.97 (flag above 3)

(iii) STAGE 2 PERMUTATION SANITY CHECK (real gate, pool, unit_lifts, interim_decisions)
  Stage 2: 46 complete lies, all `full`. Gate on 46 lies: excluded ['historical_anchor']; flagged (<30 positives) 12 of 13
  2000 random labelings; pseudo-units per labeling 18 (about 4 per model)
  mean of pooled d across labelings +0.0002 (expected 0 by symmetry; SD across labelings 0.119)
  interim decisions across labelings x models: extend 1.0000
