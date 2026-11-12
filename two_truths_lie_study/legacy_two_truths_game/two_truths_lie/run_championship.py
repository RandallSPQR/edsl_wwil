#!/usr/bin/env python3
"""
Championship Rounds: Best vs Best, Balanced vs Balanced, Worst vs Worst

Tests the ultimate matchups:
1. DeepSeek (perfect judge) vs GPT-5 (best liar)
2. GPT-5 (strong judge) vs DeepSeek (weak liar)
3. GPT-5 vs Claude Sonnet 4 (balanced champions)
4. Old Haiku vs DeepSeek (worst matchup)

Total: 150 rounds
"""

import sys
from pathlib import Path
import argparse

sys.path.insert(0, str(Path(__file__).parent))

from src.config.schema import ConditionConfig, LLMConfig, GameConfig
from src.engine import GameEngine
from src.storage import ResultStore
from src.facts.database import get_default_facts
from src.edsl_adapter import EDSLAdapter

# Championship matchups
MATCHES = [
    {
        "name": "DeepSeek vs GPT-5",
        "judge": "deepseek-chat",
        "storyteller": "gpt-5-2025-08-07",
        "rounds": 30,
        "description": "Perfect detector vs Best liar - Can DeepSeek maintain 100%?"
    },
    {
        "name": "GPT-5 vs DeepSeek",
        "judge": "gpt-5-2025-08-07",
        "storyteller": "deepseek-chat",
        "rounds": 30,
        "description": "Strong judge vs Weak liar - Should be decisive"
    },
    {
        "name": "GPT-5 vs Sonnet-4 (Judge)",
        "judge": "gpt-5-2025-08-07",
        "storyteller": "claude-sonnet-4-20250514",
        "rounds": 30,
        "description": "Balanced champion as judge"
    },
    {
        "name": "GPT-5 vs Sonnet-4 (Storyteller)",
        "judge": "claude-sonnet-4-20250514",
        "storyteller": "gpt-5-2025-08-07",
        "rounds": 30,
        "description": "Balanced champion as liar"
    },
    {
        "name": "Haiku-old vs DeepSeek (Control)",
        "judge": "claude-3-haiku-20240307",
        "storyteller": "deepseek-chat",
        "rounds": 30,
        "description": "Worst judge vs Weak liar - Control experiment"
    },
]

BASELINE_MODEL = "claude-3-5-haiku-20241022"


def create_condition(judge_model: str, storyteller_model: str) -> ConditionConfig:
    """Create championship match condition."""
    return ConditionConfig(
        judge_model=LLMConfig(name=judge_model, temperature=1.0),
        storyteller_model=LLMConfig(name=storyteller_model, temperature=1.0),
        game=GameConfig(
            num_storytellers=3,
            num_truth_tellers=2,
            questions_per_storyteller=1,
            story_word_min=250,
            story_word_max=500,
            answer_word_min=25,
            answer_word_max=150,
            game_type="standard",
        ),
        storyteller_strategy="baseline",
        judge_question_style="curious",
        fact_category=None,
    )


def run_championship(results_dir: str = "results/championship"):
    """Run all championship matches."""

    # Initialize infrastructure
    fact_db = get_default_facts()
    default_game_config = GameConfig()
    adapter = EDSLAdapter(LLMConfig(name=BASELINE_MODEL, temperature=1.0))
    engine = GameEngine(default_game_config, adapter, fact_db)
    store = ResultStore(results_dir)

    total_rounds = sum(m["rounds"] for m in MATCHES)
    completed_rounds = 0

    print(f"\n{'='*70}")
    print(f"CHAMPIONSHIP ROUNDS: BEST vs BEST")
    print(f"{'='*70}\n")
    print(f"Total matches: {len(MATCHES)}")
    print(f"Total rounds: {total_rounds}")
    print(f"Results directory: {results_dir}\n")

    for i, match in enumerate(MATCHES, 1):
        print(f"{'='*70}")
        print(f"MATCH {i}/{len(MATCHES)}: {match['name']}")
        print(f"{'='*70}")
        print(f"Judge: {match['judge']}")
        print(f"Storyteller: {match['storyteller']}")
        print(f"{match['description']}")
        print(f"Rounds: {match['rounds']}\n")

        condition_id = f"championship_{match['judge']}_vs_{match['storyteller']}"
        condition = create_condition(match['judge'], match['storyteller'])

        match_correct = 0
        match_failed = 0

        for round_num in range(match['rounds']):
            try:
                # Run the round
                round_result = engine.run_round(condition)
                round_result.setup.condition_id = condition_id

                # Save result
                store.save_round(round_result)

                completed_rounds += 1
                if round_result.outcome.detection_correct:
                    match_correct += 1

                # Log progress every 5 rounds
                if (round_num + 1) % 5 == 0:
                    acc = match_correct / (round_num + 1 - match_failed) if (round_num + 1 - match_failed) > 0 else 0
                    progress = (completed_rounds / total_rounds) * 100
                    print(f"  Round {round_num + 1}/{match['rounds']} "
                          f"(judge accuracy: {acc:.1%}, overall: {progress:.1f}%)")

            except Exception as e:
                match_failed += 1
                print(f"  ❌ Round {round_num + 1} failed: {e}")
                continue

        # Match summary
        successful = match['rounds'] - match_failed
        accuracy = match_correct / successful if successful > 0 else 0

        print(f"\n  ✅ Match complete:")
        print(f"     Judge accuracy: {accuracy:.1%} ({match_correct}/{successful})")
        print(f"     Failed rounds: {match_failed}")
        print()

    print(f"{'='*70}")
    print(f"✅ CHAMPIONSHIP COMPLETE")
    print(f"{'='*70}")
    print(f"Total rounds: {completed_rounds}/{total_rounds}")
    print(f"Results: {results_dir}")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Championship Matches")
    parser.add_argument(
        "--results-dir",
        default="results/championship",
        help="Directory to save results"
    )
    args = parser.parse_args()

    run_championship(results_dir=args.results_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
