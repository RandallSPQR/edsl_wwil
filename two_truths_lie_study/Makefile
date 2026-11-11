# The Perfect Lie: release targets. Run from two_truths_lie_study/. See release/README.md.
#   make env               create release/.venv (Python 3.11, uv.lock) - needs the network once
#   make reproduce         Tier 0: rebuild every CPU-derivable result, the write-up and the figures; check every claim
#   make reproduce-full    Tier 0 with all 20 permutation chunks recomputed (about 4.8 h on 4 cores)
#   make docker-image      build the pinned image (needs the network once)
#   make docker-reproduce  Tier 0 inside the image with --network none
#   make dataset           build the release dataset into build/dataset
#   make clean             remove build/
PY ?= $(if $(wildcard release/.venv/bin/python),release/.venv/bin/python,python3.11)
WORK ?= build/tier0

.PHONY: env reproduce reproduce-full docker-image docker-reproduce dataset clean

env:
	cd release && UV_PROJECT_ENVIRONMENT=.venv uv sync --frozen --python 3.11

reproduce:
	$(PY) release/tier0/reproduce.py --work $(WORK) --perm-chunks 1

reproduce-full:
	$(PY) release/tier0/reproduce.py --work $(WORK) --perm-chunks 20

docker-image:
	docker build -t perfect-lie-tier0 -f release/Dockerfile release

docker-reproduce:
	docker run --rm --network none -v "$(CURDIR)":/study -w /study perfect-lie-tier0 \
		python release/tier0/reproduce.py --work /study/build/tier0 --perm-chunks 1

dataset:
	$(PY) release/dataset/build_dataset.py --out build/dataset

clean:
	rm -rf build
