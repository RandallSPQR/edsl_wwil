#!/usr/bin/env python3
"""
Analyze Championship Results: Best vs Best

Analyzes the ultimate matchups:
1. DeepSeek (perfect judge) vs GPT-5 (best liar)
2. GPT-5 (strong judge) vs DeepSeek (weak liar)
3. GPT-5 vs Claude Sonnet 4 (balanced champions)
4. Old Haiku vs DeepSeek (control)
"""

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from src.storage import ResultStore


def analyze_championship():
    """Analyze championship match results."""

    print("\n" + "="*70)
    print("CHAMPIONSHIP RESULTS ANALYSIS")
    print("="*70 + "\n")

    store = ResultStore("results/championship")

    # Group by match (condition_id)
    matches = defaultdict(lambda: {
        'rounds': [],
        'judge_correct': 0,
        'judge_total': 0,
        'confidences': []
    })

    for round_id in store.list_rounds():
        result = store.get_round(round_id)
        condition_id = result.setup.condition_id or "unknown"

        matches[condition_id]['rounds'].append(result)
        matches[condition_id]['judge_total'] += 1

        if result.outcome.detection_correct:
            matches[condition_id]['judge_correct'] += 1

        matches[condition_id]['confidences'].append(result.verdict.confidence)

    # Expected matches
    expected_matches = {
        "championship_deepseek-chat_vs_gpt-5-2025-08-07": {
            "name": "DeepSeek vs GPT-5",
            "judge": "DeepSeek (100% baseline)",
            "storyteller": "GPT-5 (86.7% liar success)",
            "hypothesis": "Can GPT-5's excellent lying break DeepSeek's perfect detection?"
        },
        "championship_gpt-5-2025-08-07_vs_deepseek-chat": {
            "name": "GPT-5 vs DeepSeek",
            "judge": "GPT-5 (95.2% baseline)",
            "storyteller": "DeepSeek (13.3% liar success)",
            "hypothesis": "Should be decisive - strong judge vs weak liar"
        },
        "championship_gpt-5-2025-08-07_vs_claude-sonnet-4-20250514": {
            "name": "GPT-5 (Judge) vs Sonnet-4",
            "judge": "GPT-5 (95.2% baseline)",
            "storyteller": "Claude Sonnet 4 (40% liar success)",
            "hypothesis": "Strong judge vs moderate liar"
        },
        "championship_claude-sonnet-4-20250514_vs_gpt-5-2025-08-07": {
            "name": "Sonnet-4 (Judge) vs GPT-5",
            "judge": "Claude Sonnet 4 (90% baseline)",
            "storyteller": "GPT-5 (86.7% liar success)",
            "hypothesis": "Good judge vs best liar - close match"
        },
        "championship_claude-3-haiku-20240307_vs_deepseek-chat": {
            "name": "Old Haiku vs DeepSeek (Control)",
            "judge": "Old Claude Haiku (43.3% baseline)",
            "storyteller": "DeepSeek (13.3% liar success)",
            "hypothesis": "Worst judge vs weak liar - control experiment"
        }
    }

    # Analyze each match
    results_summary = []

    for condition_id, stats in sorted(matches.items()):
        if stats['judge_total'] == 0:
            continue

        accuracy = stats['judge_correct'] / stats['judge_total'] * 100
        avg_confidence = sum(stats['confidences']) / len(stats['confidences']) if stats['confidences'] else 0

        # Get expected match info
        match_info = expected_matches.get(condition_id, {
            "name": condition_id,
            "judge": "Unknown",
            "storyteller": "Unknown",
            "hypothesis": "N/A"
        })

        results_summary.append({
            'condition_id': condition_id,
            'name': match_info['name'],
            'judge': match_info['judge'],
            'storyteller': match_info['storyteller'],
            'hypothesis': match_info['hypothesis'],
            'accuracy': accuracy,
            'correct': stats['judge_correct'],
            'total': stats['judge_total'],
            'avg_confidence': avg_confidence
        })

    # Print results
    for i, result in enumerate(results_summary, 1):
        print(f"{'='*70}")
        print(f"MATCH {i}: {result['name']}")
        print(f"{'='*70}")
        print(f"Judge: {result['judge']}")
        print(f"Storyteller: {result['storyteller']}")
        print(f"\nHypothesis: {result['hypothesis']}")
        print(f"\nRESULTS:")
        print(f"  Rounds: {result['total']}")
        print(f"  Judge Accuracy: {result['accuracy']:.1f}% ({result['correct']}/{result['total']})")
        print(f"  Avg Confidence: {result['avg_confidence']:.1f}/10")
        print()

    # Summary
    print(f"{'='*70}")
    print("KEY FINDINGS")
    print(f"{'='*70}\n")

    # Sort by judge accuracy
    sorted_results = sorted(results_summary, key=lambda x: x['accuracy'], reverse=True)

    print("Judge Performance Ranking:")
    for i, result in enumerate(sorted_results, 1):
        print(f"  {i}. {result['name']}: {result['accuracy']:.1f}%")

    print(f"\nTotal Championship Rounds: {sum(r['total'] for r in results_summary)}")
    print(f"Overall Average Accuracy: {sum(r['correct'] for r in results_summary) / sum(r['total'] for r in results_summary) * 100:.1f}%")

    return results_summary


if __name__ == "__main__":
    analyze_championship()
