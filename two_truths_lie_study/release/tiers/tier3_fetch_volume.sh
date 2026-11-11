#!/usr/bin/env bash
# Retrieve the Phase 2 artifacts that stayed on the study's RunPod network volume (u0isne6ams, EUR-IS-1), so they can
# be added to the dataset. NOT RUN for this release: it starts a pod (owner's approval; about $0.10 at RTX PRO 6000
# prices for a few minutes, less on a CPU pod where the volume's data centre offers one).
#
#   RUNPOD_API_KEY=... release/tiers/tier3_fetch_volume.sh --plan     # print the plan only (default)
#   RUNPOD_API_KEY=... release/tiers/tier3_fetch_volume.sh --go       # start the pod, fetch, terminate
#
# What it fetches (paths on the volume):
#   hf/hub/models--google--gemma-3-27b-it/snapshots/            -> the revision directory name (confirms hf_revisions.json)
#   hf/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/ -> likewise
#   phase2/probe/<slug>/pilot_vectors_v2.npz   the Addendum 5 placebo (unit vector, seed) and v at the selected layer
#   phase2/probe/<slug>/pilot_vectors.npz      the retired placebo
#   phase2/probe/<slug>/mc_vectors.npz         per-target v_fp,t and their placebos (Addendum 7)
#   phase2/probe/<slug>/natural.npz            the naturalness shifts
#   phase2/probe/<slug>/shard_*.npz            activations (optional, --with-activations: about 3.3 GB float32;
#                                              the selected-layer slice alone is about 70 MB)
set -euo pipefail
MODE="${1:---plan}"
VOLUME=u0isne6ams; DC=EUR-IS-1
cat <<EOF
Plan:
 1. Create a pod in $DC with network volume $VOLUME mounted at /workspace (image: any with python3 and numpy),
    watchdog 30 min, using the RunPod REST API (POST https://rest.runpod.io/v1/pods; see probe_stage.pod_api).
 2. On the pod: ls /workspace/hf/hub/models--*/snapshots/ ; tar the .npz files listed above (activations only with
    --with-activations); serve or upload the tarball; record sha256 of every file.
 3. Terminate the pod (DELETE /pods/<id>) and check no pod is left.
 4. Add the files to release/dataset/ (build_dataset.py copies phase2/probe/<slug>/*.npz when present) and update
    hf_revisions.json "evidence" with the snapshot directory names.
EOF
if [ "$MODE" != "--go" ]; then echo "(plan only; nothing started)"; exit 0; fi
echo "--go is deliberately not automated here: start the pod with the study's own pod_api helper so the watchdog and"
echo "cap logic are the reviewed ones, e.g. adapt probe_stage.pod_up with dockerStartCmd running step 2."
exit 2
