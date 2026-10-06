D3. design P(interim efficacy stop | lift 0) at local 0.0125 = 0.000059 (printed as 0.000 in the PREREG table)

D1a. SAMPLE SD (the pre-registered statistic, as coded): |z| vs PREREG table, N=5000 per row
  10u lift 0.146 sd 0.405    max |z|  1.3
  10u lift 0.146 sd 0.49     max |z|  0.4
  10u lift 0.073 sd 0.405    max |z|  2.1   stop: effect 0.041 vs 0.035 (+2.1 SE); extend 0.959 vs 0.965 (-2.1 SE); inconclusive 0.037 vs 0.032 (+2.1 SE)
  10u lift 0.073 sd 0.49     max |z|  2.5   stop: effect 0.018 vs 0.014 (+2.5 SE); extend 0.982 vs 0.986 (-2.5 SE)
  10u lift 0.0 sd 0.405      max |z|  1.7
  10u lift 0.0 sd 0.49       max |z|  1.4
  9u lift 0.146 sd 0.405     max |z|  0.3
  9u lift 0.146 sd 0.49      max |z|  1.3
  9u lift 0.073 sd 0.405     max |z|  2.2   stop: effect 0.032 vs 0.027 (+2.2 SE); extend 0.968 vs 0.973 (-2.2 SE)
  9u lift 0.073 sd 0.49      max |z|  1.6
  9u lift 0.0 sd 0.405       max |z|  1.7
  9u lift 0.0 sd 0.49        max |z|  1.7

D1b. KNOWN SD (the PREREG power simulation's assumption): |z| vs PREREG table, N=5000 per row
  10u lift 0.146 sd 0.405    max |z|  0.7
  10u lift 0.146 sd 0.49     max |z|  1.3
  10u lift 0.073 sd 0.405    max |z|  2.5   stop: effect 0.042 vs 0.035 (+2.5 SE); extend 0.958 vs 0.965 (-2.5 SE)
  10u lift 0.073 sd 0.49     max |z|  3.7   stop: effect 0.020 vs 0.014 (+3.7 SE); extend 0.980 vs 0.986 (-3.7 SE)
  10u lift 0.0 sd 0.405      max |z|  1.3
  10u lift 0.0 sd 0.49       max |z|  1.8
  9u lift 0.146 sd 0.405     max |z|  0.8
  9u lift 0.146 sd 0.49      max |z|  1.3
  9u lift 0.073 sd 0.405     max |z|  0.7
  9u lift 0.073 sd 0.49      max |z|  2.2   final: effect 0.561 vs 0.546 (+2.2 SE); inconclusive 0.326 vs 0.340 (-2.1 SE)
  9u lift 0.0 sd 0.405       max |z|  1.3
  9u lift 0.0 sd 0.49        max |z|  1.3

D2. discrete null via unit_lifts, cue p=0.3, N=5000: per-model 0.0121 (design 0.0125, SE 0.0008, z -0.5); family-wise 0.0466 (design 0.05, SE 0.0031, z -1.1)

D2. discrete null via unit_lifts, cue p=0.15, N=3000: per-model 0.0116 (design 0.0125, SE 0.0010, z -0.9); family-wise 0.0460 (design 0.05, SE 0.0040, z -1.0)

D4. Exact interim efficacy-stop probability (known SD, closed form) vs simulations
  interim boundary at 0.0125: 4.0163
  10u lift 0.146 sd 0.405: exact 0.6550 | vectorized known-SD 0.6559 | vectorized sample-SD 0.6545 (N=400000)
  10u lift 0.146 sd 0.49: exact 0.3568 | vectorized known-SD 0.3570 | vectorized sample-SD 0.3632 (N=400000)
  10u lift 0.073 sd 0.405: exact 0.0352 | vectorized known-SD 0.0352 | vectorized sample-SD 0.0394 (N=400000)
  10u lift 0.073 sd 0.49: exact 0.0142 | vectorized known-SD 0.0142 | vectorized sample-SD 0.0163 (N=400000)
  9u lift 0.146 sd 0.405: exact 0.5684 | vectorized known-SD 0.5671 | vectorized sample-SD 0.5680 (N=400000)
  9u lift 0.146 sd 0.49: exact 0.2897 | vectorized known-SD 0.2890 | vectorized sample-SD 0.2976 (N=400000)
  9u lift 0.073 sd 0.405: exact 0.0273 | vectorized known-SD 0.0273 | vectorized sample-SD 0.0316 (N=400000)
  9u lift 0.073 sd 0.49: exact 0.0111 | vectorized known-SD 0.0111 | vectorized sample-SD 0.0135 (N=400000)

D5. Re-run of the flagged known-SD row through sequential._decide (10u, lift 0.073, sd 0.49), N=40000, new seed
  stop: effect   sim 0.0150 prereg 0.014  z +1.7
  final: effect  sim 0.5957 prereg 0.599  z -1.3
  flat (final)   sim 0.1119 prereg 0.113  z -0.7
  inconclusive   sim 0.2774 prereg 0.274  z +1.5
