"""Cost estimate for the follow-up full run, from the first study's measured cost per complete
cell (study1_parameters.json), dropping the stages the follow-up does not run (post-story
elicitation and its B-hat grading). No model calls."""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
p = json.loads((HERE / "study1_parameters.json").read_text())["cost"]
per = p["per_complete_cell"]
keep = ["liar", "judges_4", "grade_primary", "grade_google", "grade_secondary", "other_retries_and_failed_call_bounds"]
cell = sum(per[k] for k in keep)
billed_ratio = p["billed_spend"] / p["counted_spend_all_cells"]
out = {"per_cell_usd": {k: per[k] for k in keep}, "per_cell_total_usd": cell,
       "dropped_per_cell_usd": {k: v for k, v in per.items() if k not in keep},
       "billed_over_counted_first_study": billed_ratio, "designs": {}}
for name, (K, R) in {"owner draft: 24 categories x 3 replicates": (24, 3),
                     "alternative: 72 categories x 1 replicate": (72, 1),
                     "alternative: 48 categories x 2 replicates": (48, 2)}.items():
    n = K * 3 * 5 * 4 * R
    out["designs"][name] = {"cells": n, "counted_usd": n * cell, "billed_usd_expected": n * cell * billed_ratio,
                            "with_10pct_contingency_usd": n * cell * 1.10}
out["note"] = ("Per-cell cost is the first study's measured mean, including gpt-5 on its 25% subsample, failed-call "
               "bounds and parse retries. The follow-up's notes are the same length class, so liar input barely "
               "changes; grading dominates (primary grader ~79% of the cost).")
(HERE / "cost.json").write_text(json.dumps(out, indent=1) + "\n")
print(json.dumps(out, indent=1))
