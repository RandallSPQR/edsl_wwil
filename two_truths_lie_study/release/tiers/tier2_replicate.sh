#!/usr/bin/env bash
# Tier 2 (replication, not reproduction): new lies from the same instrument and models. This script makes NO model
# calls: it runs both runners' environment checks and dry runs (cell counts, cost estimates from OpenRouter's current
# prices) and prints the live commands. Run from two_truths_lie_study/ in the EDSL environment (see
# two_truths_lie/results/perfect_lie_reversed/final_analysis/requirements_review.txt), with OPEN_ROUTER_API_KEY set.
set -euo pipefail
cd "$(dirname "$0")/../../two_truths_lie"

echo "== Study 1 (PREREG_DRAFT.md): environment and dry run"
python run_perfect_lie.py --check-env
python run_perfect_lie.py --dry-run --class C1 --tier full || python run_perfect_lie.py --dry-run --class C1

echo "== Reversed note (PREREG_REVERSED.md): dry run"
python run_perfect_lie_reversed.py --dry-run

cat <<'EOF'

Live commands (each prints its estimate and refuses unless the confirmed spend covers it; registered caps shown):
  python run_perfect_lie.py --full --confirm-spend 80          # study 1, two-look design; then results/perfect_lie/
                                                                 interim_look/ and final_analysis/ scripts
  python run_perfect_lie_reversed.py --go --cap 125            # reversed note (owner's lock must be lifted in a copy)
  python results/perfect_lie_reversed/final_analysis/run_final.py --run-dir <new run dir> --out <out dir>
Write the new run to a new directory; never over the released records. Report the result as a replication.
EOF
