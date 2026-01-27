#!/usr/bin/env python3
"""
Deep analysis of GPT-5's catastrophic lying failure.

GPT-5 as storyteller: Only fooled judges 4/30 times (13.3% success)
This is the worst performance ever recorded.

Questions:
1. What patterns emerge in the 26 detected lies?
2. How do they differ from successful lies by other models?
3. Can we identify the failure mode?
"""

import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))

from src.storage import ResultStore


def analyze_gpt5_lies():
    """Analyze GPT-5's lies when acting as storyteller."""
    print("\n" + "="*70)
    print("GPT-5 LYING FAILURE ANALYSIS")
    print("="*70 + "\n")

    store = ResultStore("results/phase3_flagship")

    # Find rounds where GPT-5 was a storyteller
    gpt5_rounds = []
    for round_id in store.list_rounds():
        result = store.get_round(round_id)
        if "gpt-5-2025-08-07_storyteller" in (result.setup.condition_id or ""):
            gpt5_rounds.append(result)

    print(f"Found {len(gpt5_rounds)} rounds with GPT-5 as storyteller\n")

    if not gpt5_rounds:
        print("No GPT-5 storyteller rounds found")
        return

    # Separate successful vs detected lies
    successful_lies = []
    detected_lies = []

    for result in gpt5_rounds:
        # Find which storyteller was GPT-5 (the liar)
        gpt5_id = next(s.id for s in result.setup.storytellers if s.role == "fibber")

        if result.outcome.detection_correct:
            # Judge correctly identified GPT-5 as liar
            detected_lies.append((result, gpt5_id))
        else:
            # GPT-5 fooled the judge!
            successful_lies.append((result, gpt5_id))

    print(f"GPT-5 Performance:")
    print(f"  Successful lies (fooled judge): {len(successful_lies)} ({len(successful_lies)/len(gpt5_rounds)*100:.1f}%)")
    print(f"  Detected lies: {len(detected_lies)} ({len(detected_lies)/len(gpt5_rounds)*100:.1f}%)")
    print()

    # Analyze detected lies
    print("="*70)
    print("DETECTED LIES - What Gave GPT-5 Away?")
    print("="*70 + "\n")

    for i, (result, gpt5_id) in enumerate(detected_lies[:5], 1):  # Show first 5
        gpt5_story = next(s for s in result.stories if s.storyteller_id == gpt5_id)

        print(f"Example {i}:")
        print(f"Story excerpt: {gpt5_story.content[:250]}...")
        print(f"\nJudge's verdict:")
        print(f"  Accused: {result.verdict.accused_id}")
        print(f"  Confidence: {result.verdict.confidence}/10")
        print(f"  Reasoning: {result.verdict.reasoning[:300]}...")
        print("\n" + "-"*70 + "\n")

    # Analyze successful lies (rare!)
    if successful_lies:
        print("="*70)
        print("SUCCESSFUL LIES - What Worked for GPT-5?")
        print("="*70 + "\n")

        for i, (result, gpt5_id) in enumerate(successful_lies, 1):
            gpt5_story = next(s for s in result.stories if s.storyteller_id == gpt5_id)

            print(f"Success {i}:")
            print(f"Story excerpt: {gpt5_story.content[:250]}...")
            print(f"\nJudge incorrectly accused: {result.verdict.accused_id} (not {gpt5_id})")
            print(f"Confidence: {result.verdict.confidence}/10")
            print("\n" + "-"*70 + "\n")

    # Pattern analysis
    print("="*70)
    print("PATTERN ANALYSIS")
    print("="*70 + "\n")

    # Analyze story characteristics
    detected_lengths = []
    successful_lengths = []

    for result, gpt5_id in detected_lies:
        story = next(s for s in result.stories if s.storyteller_id == gpt5_id)
        detected_lengths.append(story.word_count)

    for result, gpt5_id in successful_lies:
        story = next(s for s in result.stories if s.storyteller_id == gpt5_id)
        successful_lengths.append(story.word_count)

    print("Story Length:")
    if detected_lengths:
        print(f"  Detected lies: {sum(detected_lengths)/len(detected_lengths):.0f} words avg")
    if successful_lengths:
        print(f"  Successful lies: {sum(successful_lengths)/len(successful_lengths):.0f} words avg")

    # Analyze judge confidence
    detected_confidences = [r.verdict.confidence for r, _ in detected_lies]
    successful_confidences = [r.verdict.confidence for r, _ in successful_lies]

    print(f"\nJudge Confidence (when detecting GPT-5):")
    if detected_confidences:
        print(f"  Average: {sum(detected_confidences)/len(detected_confidences):.1f}/10")
        print(f"  Range: {min(detected_confidences)}-{max(detected_confidences)}")

    if successful_confidences:
        print(f"\nJudge Confidence (when GPT-5 fooled them):")
        print(f"  Average: {sum(successful_confidences)/len(successful_confidences):.1f}/10")

    return detected_lies, successful_lies


def compare_with_haiku():
    """Compare GPT-5's failures with old Haiku's successes."""
    print("\n\n" + "="*70)
    print("COMPARISON: GPT-5 vs OLD CLAUDE-HAIKU")
    print("="*70 + "\n")

    # Load Phase 1 results for old Haiku
    store1 = ResultStore("results/phase1_older")

    haiku_rounds = []
    for round_id in store1.list_rounds():
        result = store1.get_round(round_id)
        if "claude-3-haiku-20240307_storyteller" in (result.setup.condition_id or ""):
            haiku_rounds.append(result)

    if not haiku_rounds:
        print("No Haiku storyteller rounds found")
        return

    # Analyze Haiku's successful lies
    haiku_successful = []
    haiku_detected = []

    for result in haiku_rounds:
        haiku_id = next(s.id for s in result.setup.storytellers if s.role == "fibber")

        if result.outcome.detection_correct:
            haiku_detected.append((result, haiku_id))
        else:
            haiku_successful.append((result, haiku_id))

    print(f"Old Claude-Haiku Performance:")
    print(f"  Successful lies: {len(haiku_successful)}/30 ({len(haiku_successful)/30*100:.1f}%)")
    print(f"  Detected lies: {len(haiku_detected)}/30 ({len(haiku_detected)/30*100:.1f}%)")
    print()

    print(f"GPT-5 vs Haiku:")
    print(f"  GPT-5 success rate: 13.3%")
    print(f"  Haiku success rate: {len(haiku_successful)/30*100:.1f}%")
    print(f"  Difference: {len(haiku_successful)/30*100 - 13.3:.1f} percentage points")
    print()

    # Show examples of Haiku's successful lies
    print("="*70)
    print("HAIKU'S SUCCESSFUL LIES (What GPT-5 Should Learn)")
    print("="*70 + "\n")

    for i, (result, haiku_id) in enumerate(haiku_successful[:3], 1):
        haiku_story = next(s for s in result.stories if s.storyteller_id == haiku_id)

        print(f"Success {i}:")
        print(f"Story: {haiku_story.content[:300]}...")
        print(f"\nJudge verdict: Accused {result.verdict.accused_id} (not {haiku_id})")
        print(f"Confidence: {result.verdict.confidence}/10")
        print(f"Why it worked: Judge was fooled despite {result.verdict.confidence}/10 confidence")
        print("\n" + "-"*70 + "\n")


def main():
    """Run complete analysis."""
    detected, successful = analyze_gpt5_lies()
    compare_with_haiku()

    print("\n" + "="*70)
    print("HYPOTHESIS")
    print("="*70 + "\n")

    print("GPT-5's catastrophic lying failure likely stems from:\n")

    print("1. OVER-OPTIMIZATION FOR TRUTHFULNESS")
    print("   - GPT-5 trained heavily on factual accuracy")
    print("   - Creates logical but implausible scenarios")
    print("   - Judges easily spot factual inconsistencies\n")

    print("2. LACK OF CREATIVE PLAUSIBILITY")
    print("   - GPT-5 focuses on logical coherence")
    print("   - Misses what makes stories 'believable'")
    print("   - Old Haiku better at natural-sounding fabrication\n")

    print("3. REASONING CURSE")
    print("   - Excellent analytical abilities make it a great judge (95.2%)")
    print("   - Same abilities prevent believable deception")
    print("   - Can't 'think like a creative liar'\n")

    print("RECOMMENDED EXPERIMENTS:")
    print("1. Test GPT-5 with CoT: 'Think creatively, not logically'")
    print("2. Compare GPT-4 vs GPT-5 lying strategies")
    print("3. Fine-tune on successful lies from Haiku")
    print("4. Test if temperature=2.0 improves GPT-5's lying")

    print("\n" + "="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
