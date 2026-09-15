#!/usr/bin/env bash
# Publish the Two Truths and a Lie study as a standalone repository.
#
# Builds a clean copy of two_truths_lie_study (no claude-mem CLAUDE.md stubs,
# no __pycache__, no nested leftover directories), adds the five results
# directories from a local results folder, and pushes a single commit to an
# empty GitHub repository.
#
# Usage:
#   ./publish.sh <git-remote-url> <path-to-results-dir> [branch]
#
# Example:
#   ./publish.sh git@github.com:RandallSPQR/Would-I-Lie-to-You.git \
#       ~/Documents/GitHub/edsl_wwil/two_truths_lie_study/two_truths_lie/results
#
# The target repository must already exist on GitHub and be empty
# (no README, no .gitignore). The script refuses to run if a .env file is
# present anywhere in the study tree or the results directory.

set -euo pipefail

REMOTE_URL="${1:-}"
RESULTS_SRC="${2:-}"
BRANCH="${3:-main}"

if [[ -z "$REMOTE_URL" || -z "$RESULTS_SRC" ]]; then
    echo "usage: $0 <git-remote-url> <path-to-results-dir> [branch]" >&2
    exit 2
fi

STUDY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_SRC="$(cd "$RESULTS_SRC" && pwd)"

RESULT_DIRS=(phase1_older phase2_small phase3_flagship championship framebreak)

# ---------------------------------------------------------------- safety ---
found_env="$(find "$STUDY_DIR" "$RESULTS_SRC" -name '.env' -o -name '.env.*' 2>/dev/null | head -n 5 || true)"
if [[ -n "$found_env" ]]; then
    echo "Refusing to publish: .env file(s) present:" >&2
    echo "$found_env" >&2
    exit 1
fi

for d in "${RESULT_DIRS[@]}"; do
    if [[ ! -d "$RESULTS_SRC/$d" ]]; then
        echo "Missing results directory: $RESULTS_SRC/$d" >&2
        exit 1
    fi
done

command -v git >/dev/null || { echo "git is required" >&2; exit 1; }

# ----------------------------------------------------------------- build ---
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
OUT="$WORK/repo"

cp -R "$STUDY_DIR" "$OUT"

# Paths that exist in the edsl_wwil checkout but do not belong in the
# standalone repo: this script, stale result stubs, EDSL cache, and nested
# directories that only ever held claude-mem CLAUDE.md stubs.
for p in \
    publish.sh \
    results \
    experiment_results \
    two_truths_lie/results \
    two_truths_lie/edsl_data \
    two_truths_lie/two_truths_lie \
    two_truths_lie/two_truths_lie_study \
    web/two_truths_lie \
    web/web \
    web/backend \
    web/node_modules \
    web/.next \
    backend/two_truths_lie \
    backend/backend \
    backend/.claude
do
    rm -rf "$OUT/$p"
done

# Generated / local-only files anywhere in the tree.
find "$OUT" \( -name 'CLAUDE.md' -o -name '.env' -o -name '.env.*' -o -name '.DS_Store' \) -type f -delete
find "$OUT" \( -name '__pycache__' -o -name '.pytest_cache' -o -name '.git' \) -type d -prune -exec rm -rf {} +

# Results: the five experiment directories.
mkdir -p "$OUT/two_truths_lie/results"
for d in "${RESULT_DIRS[@]}"; do
    cp -R "$RESULTS_SRC/$d" "$OUT/two_truths_lie/results/$d"
done
find "$OUT/two_truths_lie/results" \( -name 'CLAUDE.md' -o -name '.env' -o -name '.env.*' -o -name '.DS_Store' \) -type f -delete

# Drop directories that only ever held excluded stubs.
find "$OUT" -type d -empty -delete

# The study depended on the parent EDSL checkout by relative path; a
# standalone repo needs the published package instead.
sed -i.bak 's|^edsl = {path = "../..", develop = true}|edsl = ">=0.1.50"|' \
    "$OUT/two_truths_lie/pyproject.toml"
rm -f "$OUT/two_truths_lie/pyproject.toml.bak"

# Results are the point of this repo: stop ignoring them.
sed -i.bak 's|^results/$|# results/ is tracked in this repository|' \
    "$OUT/two_truths_lie/.gitignore"
rm -f "$OUT/two_truths_lie/.gitignore.bak"

cat > "$OUT/.gitignore" <<'EOF'
# API keys
.env
.env.*

# Python
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
venv/
*.egg-info/

# Node / Next.js
node_modules/
.next/

# OS / editors
.DS_Store
.vscode/
.idea/

# claude-mem stubs
CLAUDE.md
EOF

cat > "$OUT/README.md" <<'EOF'
# Would I Lie to You? An LLM Deception Study

A research framework and full results archive for studying deception and
deception detection in large language models, using a "Two Truths and a Lie"
storytelling game inspired by the panel show *Would I Lie to You?*.

Three storytellers each tell a story built on a strange-but-true fact. Two
tell the truth, one fabricates. A judge model questions them and names the
fibber. Every round, question, answer, and verdict is recorded.

## Layout

| Path | Contents |
|------|----------|
| `two_truths_lie/` | Game engine, prompts, fact database, experiment runners, analysis scripts |
| `two_truths_lie/results/` | Raw results for the five published experiments |
| `backend/` | FastAPI service used by the web interface |
| `web/` | Next.js interface for running and browsing games |
| `STUDY_DESIGN.md` | Research methodology |
| `EXTENDED_EXPERIMENTS_DESIGN.md` | Design of the later experiments |

## Experiments

| Results directory | Experiment | Write-up |
|-------------------|------------|----------|
| `phase1_older` | Phase 1: older and smaller models | `two_truths_lie/EXPERIMENT_RESULTS_SUMMARY.md` |
| `phase2_small` | Phase 2: small models | `two_truths_lie/PHASE2_SUMMARY.md` |
| `phase3_flagship` | Phase 3: flagship models | `two_truths_lie/EXPERIMENT_RESULTS_SUMMARY.md` |
| `championship` | Championship: best storytellers vs best judge | `two_truths_lie/CHAMPIONSHIP_AND_FRAMEBREAK_RESULTS.md` |
| `framebreak` | Frame break: adversarial storytelling | `two_truths_lie/CHAMPIONSHIP_AND_FRAMEBREAK_RESULTS.md` |

## Running

See `two_truths_lie/README.md`. The game runs through
[EDSL](https://github.com/expectedparrot/edsl) and needs an Expected Parrot
API key in a local `.env` file, which is never committed.
EOF

# ---------------------------------------------------------------- commit ---
cd "$OUT"
git init -q -b "$BRANCH"
git add -A
git commit -q -m "Add Two Truths and a Lie study with full results

Standalone export of the two_truths_lie_study directory from edsl_wwil:
game engine, prompts, fact database, experiment runners, analysis
scripts, backend and web interface, design documents, and the raw
results of the five published experiments (phase1_older, phase2_small,
phase3_flagship, championship, framebreak)."

echo "Prepared $(git ls-files | wc -l | tr -d ' ') files; pushing to $REMOTE_URL ($BRANCH)"
git remote add origin "$REMOTE_URL"
git push -u origin "$BRANCH"
