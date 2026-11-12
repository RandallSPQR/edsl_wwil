#!/usr/bin/env python3
"""
Frame Break Testing: Can models detect invalid game states?

Tests if models can recognize when the game rules are violated:
1. 0 liars (all telling truth) - should judge say "no liar found"?
2. 2 liars - can judge identify both?
3. 3 liars (all lying) - should judge recognize impossible state?

Total: 90 rounds across 3 top judges (DeepSeek, GPT-5, Opus 4.5)
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

# Test the top 3 judges
TEST_JUDGES = [
    "deepseek-chat",           # Perfect 100% detector
    "gpt-5-2025-08-07",        # 95.2% detector
    "claude-opus-4-5-20251101" # 96.7% detector
]

BASELINE_MODEL = "claude-3-5-haiku-20241022"

# Frame break scenarios
SCENARIOS = [
    {
        "game_type": "all_truth",
        "num_truth_tellers": 3,
        "description": "All telling truth - no liar exists",
        "rounds": 10  # Per judge
    },
    {
        "game_type": "majority_lies",
        "num_truth_tellers": 1,
        "description": "Two liars - double deception",
        "rounds": 10  # Per judge
    },
    {
        "game_type": "all_lies",
        "num_truth_tellers": 0,
        "description": "All lying - impossible to determine single liar",
        "rounds": 10  # Per judge
    },
]


def create_framebreak_condition(
    judge_model: str,
    game_type: str,
    num_truth_tellers: int
) -> ConditionConfig:
    """Create frame break test condition."""
    num_storytellers = 3

    return ConditionConfig(
        judge_model=LLMConfig(name=judge_model, temperature=1.0),
        storyteller_model=LLMConfig(name=BASELINE_MODEL, temperature=1.0),
        game=GameConfig(
            num_storytellers=num_storytellers,
            num_truth_tellers=num_truth_tellers,
            questions_per_storyteller=1,
            story_word_min=250,
            story_word_max=500,
            answer_word_min=25,
            answer_word_max=150,
            game_type=game_type,
        ),
        storyteller_strategy="baseline",
        judge_question_style="curious",
        fact_category=None,
    )


def run_framebreak_experiments(results_dir: str = "results/framebreak"):
    """Run all frame break testing scenarios."""

    # Initialize infrastructure
    fact_db = get_default_facts()
    default_game_config = GameConfig()
    adapter = EDSLAdapter(LLMConfig(name=BASELINE_MODEL, temperature=1.0))
    engine = GameEngine(default_game_config, adapter, fact_db)
    store = ResultStore(results_dir)

    total_rounds = len(TEST_JUDGES) * sum(s["rounds"] for s in SCENARIOS)
    completed_rounds = 0

    print(f"\n{'='*70}")
    print(f"FRAME BREAK TESTING: INVALID GAME STATES")
    print(f"{'='*70}\n")
    print(f"Judges to test: {len(TEST_JUDGES)}")
    print(f"Scenarios: {len(SCENARIOS)}")
    print(f"Total rounds: {total_rounds}")
    print(f"Results directory: {results_dir}\n")

    for judge_model in TEST_JUDGES:
        print(f"{'='*70}")
        print(f"TESTING JUDGE: {judge_model}")
        print(f"{'='*70}\n")

        for scenario in SCENARIOS:
            game_type = scenario["game_type"]
            num_truth_tellers = scenario["num_truth_tellers"]
            num_rounds = scenario["rounds"]

            print(f"  Scenario: {game_type}")
            print(f"  {scenario['description']}")
            print(f"  Rounds: {num_rounds}\n")

            condition_id = f"framebreak_{judge_model}_{game_type}"
            condition = create_framebreak_condition(
                judge_model,
                game_type,
                num_truth_tellers
            )

            scenario_results = []

            for round_num in range(num_rounds):
                try:
                    # Run the round
                    round_result = engine.run_round(condition)
                    round_result.setup.condition_id = condition_id

                    # Save result
                    store.save_round(round_result)
                    scenario_results.append(round_result)

                    completed_rounds += 1

                    # Log progress every 5 rounds
                    if (round_num + 1) % 5 == 0:
                        progress = (completed_rounds / total_rounds) * 100
                        print(f"    Round {round_num + 1}/{num_rounds} "
                              f"(overall: {progress:.1f}%)")

                except Exception as e:
                    print(f"    ❌ Round {round_num + 1} failed: {e}")
                    continue

            # Scenario summary
            print(f"    ✅ Scenario complete: {len(scenario_results)}/{num_rounds} rounds\n")

    print(f"{'='*70}")
    print(f"✅ FRAME BREAK TESTING COMPLETE")
    print(f"{'='*70}")
    print(f"Total rounds: {completed_rounds}/{total_rounds}")
    print(f"Results: {results_dir}")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Frame Break Tests")
    parser.add_argument(
        "--results-dir",
        default="results/framebreak",
        help="Directory to save results"
    )
    args = parser.parse_args()

    run_framebreak_experiments(results_dir=args.results_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
