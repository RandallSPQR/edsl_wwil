V1. Stagewise median-unbiased estimate and 95% CI, single model at local 0.0125, normal d
  theta 0.073: P(MUE < theta) 0.491 (target 0.5, SE 0.011); CI coverage 0.950 (target 0.95, SE 0.005); stage-1 stops 50, of which MUE == naive: 50
  theta 0.146: P(MUE < theta) 0.510 (target 0.5, SE 0.011); CI coverage 0.951 (target 0.95, SE 0.005); stage-1 stops 970, of which MUE == naive: 970
  theta 0.0: P(MUE < theta) 0.498 (target 0.5, SE 0.011); CI coverage 0.946 (target 0.95, SE 0.005); stage-1 stops 1, of which MUE == naive: 1

V2. Conditional MUE (additional) given a stage-1 stop: median relative to theta
  theta 0.146: median naive 0.172 (inflated); median conditional MUE 0.148; P(cond MUE < theta) 0.486 (target 0.5); not identified 1 of 1500

V3. run_final on synthetic graded records (known effects)
  meta-llama/llama-3.1-8b-instruct   true +0.25-scaled | decision belief-tracking dir positive mean +0.218 MUE +0.218 n 147
  google/gemma-3-27b-it              true +0.10-scaled | decision extend (extension not run) dir None     mean +0.013 MUE +nan n 146
  openai/gpt-4o-mini                 true +0.00-scaled | decision extend (extension not run) dir None     mean +0.056 MUE +nan n 146
  google/gemini-2.5-flash-lite       true -0.15-scaled | decision extend (extension not run) dir None     mean -0.098 MUE +nan n 147
  stage-1 MUE equals naive mean for every model stopped at the interim: True
  empty-cue exclusions: breakdown total 0 vs unit_lifts count 0
  tipping point: missing units 14
    meta-llama/llama-3.1-8b-instruct: 3 missing; delta to reverse None (reversible False); z with all missing at worst 4.32 vs boundary 4.02
  mixed model converged: [True, False, True, True]
  sensitivity keys: ['drop_flagged_cues', 'pooled_gate_all_scorable', 'nonviable_excluded_added_post_registration_before_data', 'nonviable_counts_by_condition']
  gpt-5 subsample lies 542; pooled kappa 0.77
  P4 cues ['hedged_claim', 'self_deprecation', 'skeptic_acknowledgment', 'emotional_appeal']
  IV Wald (acceptance rises with named cues in the simulation, so positive where the first stage is positive): llama-3.1- +0.25, gemma-3-27 +2.59, gpt-4o-min -1.16, gemini-2.5 +0.43
  B-hat manipulation check (simulated B-hat copies story labels with noise, so it tracks the effect): llama-3.1- +0.139, gemma-3-27 +0.029, gpt-4o-min -0.015, gemini-2.5 -0.050

V4. Tipping point on a constructed case near the boundary
  observed Z 4.167; 10 missing units; delta -0.0564; Z at delta 4.0163 vs boundary 4.0163

V5. Empty-cue breakdown vs unit_lifts with emotional_appeal excluded (as at the real interim)
  unit_lifts empty_cue_set 60 vs breakdown total 60; by prompt x persona {'technology|P6': 60}

V7. Review fixes
  F1 alpha at decision independent of list order: True; |Z| {'A': 3.51, 'B': 3.5, 'C': 10.8, 'D': 10.58}; alpha {'A': None, 'B': None, 'C': 0.0125, 'D': 0.016666666666666666} (largest |Z| decided first, at 0.0125)
  F8 no extension data -> decisions {'A': 'extend (extension not run)', 'E': 'extend (extension not run)'}; final efficacy alpha {'A': 0.025, 'E': 0.025}
  F6 flat model: decision flat; repeated CI family equivalence at alpha 0.05, e 2.776
  F11 conditional MUE at Z = c1 + 0.02: estimate -1.1243983175521928, ci [-6.6287700048836, 0.12340574059939656], note None
