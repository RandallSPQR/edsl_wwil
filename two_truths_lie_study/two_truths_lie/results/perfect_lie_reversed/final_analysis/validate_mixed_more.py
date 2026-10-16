import os, sys, json
os.environ["OMP_NUM_THREADS"]="1"; os.environ["OPENBLAS_NUM_THREADS"]="1"
sys.path.insert(0,"."); sys.path.insert(0,"results/perfect_lie_reversed/final_analysis"); sys.path.insert(0,"results/perfect_lie_reversed/design")
import validate_final as V
r = V.mixed(1500, 1300000, 3)
print(json.dumps(r, indent=1))
