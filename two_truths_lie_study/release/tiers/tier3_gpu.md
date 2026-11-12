# Tier 3: Phase 2 on a GPU

Run from `two_truths_lie_study/two_truths_lie/results/phase2/probe/`. Every driver starts a RunPod pod with a watchdog
(`--watchdog-hours`), refuses a pod whose hourly price times the watchdog exceeds `--cap-usd`, and needs
`RUNPOD_API_KEY`, a pod key file (`--key-file`) and, for the gated weights, `HF_TOKEN`. Pods fetch the driver code from
GitHub at the commit you pass (`--commit`), so use the release tag's commit. Write to a copy of the repository: every
step writes into `results/phase2/`.

| order | command | writes |
|---|---|---|
| 1 | `python ../identity_check/behavioral.py generate --pod ID --key-file K` (+ `grade`, `analyse`; then `--variant novita`) | identity check (section 2) |
| 2 | `python probe_stage.py pod-up --commit SHA --key-file K`; `extract --pod ID --key-file K --model M`; `analyse ...` | activations, `probe_result.json`, `vectors.npz` |
| 3 | `python diag_stage.py pod-up ...`; `run --pod ID --key-file K --model M` | `diagnostics.json` (Addendum 3) |
| 4 | `python scale_stage.py ...` | `scale.json` |
| 5 | `python pilot_stage.py pod-up ...`; `run --pod ID --key-file K --model M` | pilot lies, NLL, `pilot_result.json` |
| 6 | `python pilot2_stage.py ...` | Addendum 5 placebo rerun, `pilot2_result.json` |
| 7 | `python stage2_stage.py pod-up ...`; `mc-precheck ...`; `run --pod ID --key-file K --model M` | stage-2 lies, NLL, coherence, naturalness |
| 8 | `python stage2_stage.py grade --model M` (Tier 1 route, `PL_GRADER_KEY`) | graded lies |
| 9 | `python stage2_stage.py screens`; owner adjudication; `permcheck`; `analyse --i-am-unblinding` | `stage2_result.json` |
| always | `python <driver> pod-down --pod ID` | |

Models: `google/gemma-3-27b-it` and `meta-llama/llama-3.1-8b-instruct` (driver names); weights pinned in
`release/dataset/hf_revisions.json`. Pod image, GPU types and data centre are constants at the top of `probe_stage.py`.

What a Tier 3 rerun can and cannot match: see `README.md` (hardware caveats). Compare the new probe AUROCs and
steering contrasts with the released intervals; do not expect identical activations or lies.
