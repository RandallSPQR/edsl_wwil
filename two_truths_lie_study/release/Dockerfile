# Tier 0 environment for The Perfect Lie: Python 3.11 with the exact package versions of uv.lock
# (requirements_review.txt plus matplotlib for the figures), installed from requirements.lock.txt with hashes.
# See ENVIRONMENT.md for why the versions are exact.
#
# Build once (needs the network):   docker build -t perfect-lie-tier0 -f release/Dockerfile release
# Run Tier 0 with no network at all, from the repository's two_truths_lie_study/ directory:
#   docker run --rm --network none -v "$PWD":/study -w /study perfect-lie-tier0 \
#       python release/tier0/reproduce.py --work /tmp/tier0
FROM python:3.11-slim-bookworm@sha256:94a8fee35252d06ab75856f15f12c7bae67b10e8a6da93c7fded82b2610926cd

ENV PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PIP_DISABLE_PIP_VERSION_CHECK=1
COPY requirements.lock.txt /env/requirements.lock.txt
RUN python -m pip install --no-cache-dir --require-hashes --only-binary=:all: -r /env/requirements.lock.txt && \
    python -c "import numpy, pandas, scipy, statsmodels, matplotlib; print(numpy.__version__, pandas.__version__, scipy.__version__, statsmodels.__version__, matplotlib.__version__)"
WORKDIR /study
