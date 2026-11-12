#!/usr/bin/env python3
"""
Parallel Experiment Runner: Launch all three experiments simultaneously.

Experiments:
1. Championship (150 rounds) - Best vs Best matchups
2. Frame Break (90 rounds) - Invalid game state detection
3. Language Test (90 rounds) - Cross-linguistic deception

Total: 330 rounds running in parallel
Estimated time: 3-4 hours (vs 9-12 hours sequential)
"""

import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime
import argparse

# Python executable (use the same one running this script)
PYTHON_EXE = sys.executable

# Experiment configurations
EXPERIMENTS = [
    {
        "name": "Championship",
        "script": "run_championship.py",
        "results_dir": "results/championship",
        "rounds": 150,
        "description": "Best vs Best matchups"
    },
    {
        "name": "Frame Break",
        "script": "run_framebreak.py",
        "results_dir": "results/framebreak",
        "rounds": 90,
        "description": "Invalid game state detection"
    },
    {
        "name": "Language Test",
        "script": "run_language_test.py",
        "results_dir": "results/language_test",
        "rounds": 90,
        "description": "Cross-linguistic deception"
    },
]


def run_parallel_experiments(no_confirm: bool = False):
    """Launch all experiments as background processes."""

    print("\n" + "="*70)
    print("PARALLEL EXPERIMENT LAUNCHER")
    print("="*70 + "\n")

    # Get working directory
    working_dir = Path(__file__).parent

    print(f"Working directory: {working_dir}")
    print(f"Python executable: {PYTHON_EXE}\n")

    print("Experiments to run:")
    for i, exp in enumerate(EXPERIMENTS, 1):
        print(f"  {i}. {exp['name']}: {exp['rounds']} rounds - {exp['description']}")

    total_rounds = sum(exp["rounds"] for exp in EXPERIMENTS)
    print(f"\nTotal rounds: {total_rounds}")
    print("Estimated time: 3-4 hours (running in parallel)\n")

    # Confirm launch
    if not no_confirm:
        response = input("Launch all experiments in parallel? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return 1
    else:
        print("Auto-launching all experiments (--no-confirm mode)\n")

    # Create output directory for logs
    log_dir = working_dir / "logs"
    log_dir.mkdir(exist_ok=True)

    # Launch each experiment as background process
    processes = []
    start_time = datetime.now()

    print("\n" + "="*70)
    print("LAUNCHING EXPERIMENTS")
    print("="*70 + "\n")

    for exp in EXPERIMENTS:
        script_path = working_dir / exp["script"]
        log_file = log_dir / f"{exp['name'].lower().replace(' ', '_')}_{start_time.strftime('%Y%m%d_%H%M%S')}.log"

        print(f"Starting {exp['name']}...")
        print(f"  Script: {script_path}")
        print(f"  Results: {exp['results_dir']}")
        print(f"  Log: {log_file}")

        # Open log file
        log_handle = open(log_file, 'w')

        # Launch process
        cmd = [
            PYTHON_EXE,
            str(script_path),
            "--results-dir",
            exp['results_dir']
        ]

        process = subprocess.Popen(
            cmd,
            cwd=working_dir,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True
        )

        processes.append({
            "name": exp["name"],
            "process": process,
            "log_file": log_file,
            "log_handle": log_handle,
            "start_time": datetime.now()
        })

        print(f"  ✅ Launched (PID: {process.pid})\n")

    print("="*70)
    print(f"ALL {len(EXPERIMENTS)} EXPERIMENTS RUNNING")
    print("="*70 + "\n")

    print("Monitoring progress...\n")

    # Monitor processes
    completed = []
    failed = []

    try:
        while len(completed) + len(failed) < len(processes):
            for proc_info in processes:
                if proc_info["name"] in completed or proc_info["name"] in failed:
                    continue

                # Check if process has finished
                returncode = proc_info["process"].poll()

                if returncode is not None:
                    duration = (datetime.now() - proc_info["start_time"]).total_seconds() / 60

                    if returncode == 0:
                        completed.append(proc_info["name"])
                        print(f"✅ {proc_info['name']} COMPLETED ({duration:.1f} minutes)")
                    else:
                        failed.append(proc_info["name"])
                        print(f"❌ {proc_info['name']} FAILED (exit code: {returncode})")

                    # Close log file
                    proc_info["log_handle"].close()

                    # Show last 10 lines of log
                    print(f"   Last log lines from {proc_info['log_file']}:")
                    with open(proc_info["log_file"], 'r') as f:
                        lines = f.readlines()
                        for line in lines[-10:]:
                            print(f"   {line.rstrip()}")
                    print()

            # Status update every 60 seconds
            if len(completed) + len(failed) < len(processes):
                time.sleep(60)

                elapsed = (datetime.now() - start_time).total_seconds() / 60
                print(f"[{elapsed:.1f} min] Status: {len(completed)} complete, "
                      f"{len(failed)} failed, "
                      f"{len(processes) - len(completed) - len(failed)} running...")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Terminating processes...\n")

        # Terminate all running processes
        for proc_info in processes:
            if proc_info["process"].poll() is None:
                proc_info["process"].terminate()
                proc_info["log_handle"].close()
                print(f"Terminated: {proc_info['name']}")

        return 1

    # Final summary
    total_time = (datetime.now() - start_time).total_seconds() / 60

    print("\n" + "="*70)
    print("EXPERIMENT SUMMARY")
    print("="*70 + "\n")

    print(f"Total time: {total_time:.1f} minutes ({total_time/60:.1f} hours)")
    print(f"Completed: {len(completed)}/{len(processes)}")
    print(f"Failed: {len(failed)}/{len(processes)}\n")

    if completed:
        print("Completed experiments:")
        for name in completed:
            print(f"  ✅ {name}")
        print()

    if failed:
        print("Failed experiments:")
        for name in failed:
            print(f"  ❌ {name}")
        print()

    print("Results directories:")
    for exp in EXPERIMENTS:
        print(f"  {exp['name']}: {exp['results_dir']}/")
    print()

    print("Log files:")
    for proc_info in processes:
        print(f"  {proc_info['name']}: {proc_info['log_file']}")
    print()

    print("="*70)
    print("Next steps:")
    print("  1. Review results in results/ directories")
    print("  2. Run analysis scripts on each experiment")
    print("  3. Compare findings across all phases")
    print("="*70 + "\n")

    return 0 if len(failed) == 0 else 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run all experiments in parallel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all experiments (interactive)
  python run_all_experiments.py

  # Run without confirmation (for background execution)
  python run_all_experiments.py --no-confirm

  # Monitor progress
  tail -f logs/championship_*.log
  tail -f logs/frame_break_*.log
  tail -f logs/language_test_*.log
        """
    )

    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompt and auto-launch experiments"
    )

    args = parser.parse_args()

    return run_parallel_experiments(no_confirm=args.no_confirm)


if __name__ == "__main__":
    sys.exit(main())
