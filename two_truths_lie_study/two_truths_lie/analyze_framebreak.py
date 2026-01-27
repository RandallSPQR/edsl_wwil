#!/usr/bin/env python3
"""
Analyze Frame Break Results: Invalid Game State Detection

Tests if top judges can detect when game rules are violated:
1. 0 liars (all truth) - should recognize no liar exists
2. 2 liars - can judge identify multiple liars?
3. 3 liars (all lying) - should recognize impossible state
"""

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from src.storage import ResultStore


def analyze_framebreak():
    """Analyze frame break test results."""

    print("\n" + "="*70)
    print("FRAME BREAK RESULTS ANALYSIS")
    print("="*70 + "\n")

    store = ResultStore("results/framebreak")

    # Group by judge and scenario
    results = defaultdict(lambda: defaultdict(lambda: {
        'rounds': [],
        'accused_ids': [],
        'confidences': [],
        'detections': []
    }))

    for round_id in store.list_rounds():
        result = store.get_round(round_id)
        condition_id = result.setup.condition_id or "unknown"

        # Parse condition_id: framebreak_{judge}_{scenario}
        # Scenarios are: all_truth, majority_lies, all_lies
        if '_all_truth' in condition_id:
            scenario = 'all_truth'
            judge = condition_id.replace('framebreak_', '').replace('_all_truth', '')
        elif '_majority_lies' in condition_id:
            scenario = 'majority_lies'
            judge = condition_id.replace('framebreak_', '').replace('_majority_lies', '')
        elif '_all_lies' in condition_id:
            scenario = 'all_lies'
            judge = condition_id.replace('framebreak_', '').replace('_all_lies', '')
        else:
            continue

        results[judge][scenario]['rounds'].append(result)
        results[judge][scenario]['accused_ids'].append(result.verdict.accused_id)
        results[judge][scenario]['confidences'].append(result.verdict.confidence)
        results[judge][scenario]['detections'].append(result.outcome.detection_correct)

    # Scenario descriptions
    scenario_info = {
        'all_truth': {
            'name': '0 Liars (All Truth)',
            'description': 'All 3 storytellers told truth - no liar exists',
            'expected': 'Judge should recognize impossible state or guess randomly'
        },
        'majority_lies': {
            'name': '2 Liars',
            'description': 'Only 1 truth-teller among 3 storytellers',
            'expected': 'Judge faces harder task with 2 possible correct answers'
        },
        'all_lies': {
            'name': '3 Liars (All Lying)',
            'description': 'All 3 storytellers lied - can\'t determine single liar',
            'expected': 'Judge should recognize all are lying or guess randomly'
        }
    }

    # Judge names
    judge_names = {
        'deepseek-chat': 'DeepSeek (100% baseline)',
        'gpt-5-2025-08-07': 'GPT-5 (95.2% baseline)',
        'claude-opus-4-5-20251101': 'Claude Opus 4.5 (96.7% baseline)'
    }

    # Analyze each judge
    for judge in sorted(results.keys()):
        print(f"{'='*70}")
        print(f"JUDGE: {judge_names.get(judge, judge)}")
        print(f"{'='*70}\n")

        judge_stats = results[judge]

        for scenario in ['all_truth', 'majority_lies', 'all_lies']:
            if scenario not in judge_stats:
                continue

            stats = judge_stats[scenario]
            info = scenario_info[scenario]

            total = len(stats['rounds'])
            if total == 0:
                continue

            avg_confidence = sum(stats['confidences']) / total
            detection_rate = sum(stats['detections']) / total * 100

            # Count accused distribution
            accused_counts = defaultdict(int)
            for accused in stats['accused_ids']:
                accused_counts[accused] += 1

            print(f"  Scenario: {info['name']}")
            print(f"  {info['description']}")
            print(f"  Expected: {info['expected']}")
            print(f"\n  Results ({total} rounds):")
            print(f"    Detection Correct: {detection_rate:.1f}%")
            print(f"    Avg Confidence: {avg_confidence:.1f}/10")
            print(f"    Accused Distribution:")
            for accused, count in sorted(accused_counts.items()):
                pct = count / total * 100
                print(f"      {accused}: {count}/{total} ({pct:.1f}%)")
            print()

    # Summary across all judges
    print(f"{'='*70}")
    print("CROSS-JUDGE SUMMARY")
    print(f"{'='*70}\n")

    for scenario in ['all_truth', 'majority_lies', 'all_lies']:
        info = scenario_info[scenario]
        print(f"{info['name']}:")

        all_detections = []
        all_confidences = []

        for judge in results.keys():
            if scenario in results[judge]:
                stats = results[judge][scenario]
                all_detections.extend(stats['detections'])
                all_confidences.extend(stats['confidences'])

        if all_detections:
            detection_rate = sum(all_detections) / len(all_detections) * 100
            avg_confidence = sum(all_confidences) / len(all_confidences)
            print(f"  Overall Detection: {detection_rate:.1f}% ({sum(all_detections)}/{len(all_detections)})")
            print(f"  Avg Confidence: {avg_confidence:.1f}/10")
        print()

    # Total rounds
    total_rounds = sum(len(stats['rounds']) for judge_stats in results.values() for stats in judge_stats.values())
    print(f"Total Frame Break Rounds: {total_rounds}")
    print()


if __name__ == "__main__":
    analyze_framebreak()
