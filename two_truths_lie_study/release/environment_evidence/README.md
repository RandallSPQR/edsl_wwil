# Environment evidence (2026-10-29)

Two probes, run from `two_truths_lie_study/two_truths_lie/` on the released reversed-note records
(`python <probe> $PWD`). Each fits only the models in question and compares them with the released
`final_report.json`. Output captured in `probe_output.txt`.

- `probe_primary.py`: the registered primary fit (`reversed_analysis.fit_model`; random slopes by category, with the
  registered per-category t-test fallback). The method and B for each liar; `True` = bit-identical to the release.
- `probe_m1.py`: the registered robustness model m1 (`(1|category) + (1|persona)` variance components). Converged
  flag, B bit-identical to the release, and the released flag.

Machine: 4 vCPU x86_64 (Linux 6.18), OpenBLAS from the numpy wheels.
