#!/usr/bin/env python3
"""
CORRECTED storyteller rankings.

The previous analysis had the metric inverted.
"Storyteller accuracy" meant "judge's accuracy" not "liar's success rate".

This script calculates the CORRECT metric: How often did the liar fool the judge?
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.storage import ResultStore


def analyze_lying_success():
    """Calculate correct lying success rates for all models."""
    print("\n" + "="*70)
    print("CORRECTED STORYTELLER PERFORMANCE RANKINGS")
    print("="*70)
    print("\nMetric: % of times liar fooled the judge\n")

    all_results = {}

    # Phase 1
    store1 = ResultStore("results/phase1_older")
    for round_id in store1.list_rounds():
        result = store1.get_round(round_id)
        condition_id = result.setup.condition_id or ""
        if "_storyteller" in condition_id:
            parts = condition_id.split('_')
            if len(parts) >= 4:
                model = '_'.join(parts[2:-1])
                phase = "P1"

                key = f"[{phase}] {model}"
                if key not in all_results:
                    all_results[key] = {'fooled': 0, 'caught': 0}

                if result.outcome.detection_correct:
                    all_results[key]['caught'] += 1
                else:
                    all_results[key]['fooled'] += 1

    # Phase 2
    store2 = ResultStore("results/phase2_small")
    for round_id in store2.list_rounds():
        result = store2.get_round(round_id)
        condition_id = result.setup.condition_id or ""
        if "_storyteller" in condition_id:
            parts = condition_id.split('_')
            if len(parts) >= 4:
                model = '_'.join(parts[2:-1])
                phase = "P2"

                key = f"[{phase}] {model}"
                if key not in all_results:
                    all_results[key] = {'fooled': 0, 'caught': 0}

                if result.outcome.detection_correct:
                    all_results[key]['caught'] += 1
                else:
                    all_results[key]['fooled'] += 1

    # Phase 3
    store3 = ResultStore("results/phase3_flagship")
    for round_id in store3.list_rounds():
        result = store3.get_round(round_id)
        condition_id = result.setup.condition_id or ""
        if "_storyteller" in condition_id:
            parts = condition_id.split('_')
            if len(parts) >= 4:
                model = '_'.join(parts[2:-1])
                phase = "P3"

                key = f"[{phase}] {model}"
                if key not in all_results:
                    all_results[key] = {'fooled': 0, 'caught': 0}

                if result.outcome.detection_correct:
                    all_results[key]['caught'] += 1
                else:
                    all_results[key]['fooled'] += 1

    # Calculate success rates
    model_success = {}
    for model, stats in all_results.items():
        total = stats['fooled'] + stats['caught']
        if total > 0:
            success_rate = stats['fooled'] / total * 100
            model_success[model] = {
                'success_rate': success_rate,
                'fooled': stats['fooled'],
                'caught': stats['caught'],
                'total': total
            }

    # Sort by success rate
    sorted_models = sorted(model_success.items(), key=lambda x: x[1]['success_rate'], reverse=True)

    print("LYING SUCCESS RATE RANKINGS:")
    print("-" * 70)
    for i, (model, stats) in enumerate(sorted_models, 1):
        print(f"{i:2d}. {model:55s} {stats['success_rate']:5.1f}% ({stats['fooled']}/{stats['total']} fooled)")

    print("\n" + "="*70)
    print("KEY INSIGHTS")
    print("="*70 + "\n")

    # Find top 3 and bottom 3
    top3 = sorted_models[:3]
    bottom3 = sorted_models[-3:]

    print("BEST LIARS:")
    for i, (model, stats) in enumerate(top3, 1):
        print(f"  {i}. {model}: {stats['success_rate']:.1f}% success")

    print("\nWORST LIARS:")
    for i, (model, stats) in enumerate(reversed(bottom3), 1):
        print(f"  {len(sorted_models)-i+1}. {model}: {stats['success_rate']:.1f}% success")

    return model_success


if __name__ == "__main__":
    analyze_lying_success()
