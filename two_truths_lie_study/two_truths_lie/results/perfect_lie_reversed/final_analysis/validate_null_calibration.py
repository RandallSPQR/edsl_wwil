import os, sys, json
os.environ["OMP_NUM_THREADS"]="1"; os.environ["OPENBLAS_NUM_THREADS"]="1"
sys.path.insert(0,"."); sys.path.insert(0,"results/perfect_lie_reversed/design")
import numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
import power as P
from src.perfect_lie import reversed_analysis as A
def one(seed):
    P.rng=np.random.default_rng(seed)
    y=P.simulate(72,1,0.0,0.0,**P.SCEN["S2 first-study-like"])
    idx=np.indices(y.shape).reshape(4,-1).T
    df=pd.DataFrame([dict(model="m",category=f"c{k}",persona=f"P{p}",condition=("placebo","full","reversed")[cc],s=float(v),cell_id="") for (k,p,cc,r),v in zip(idx,y.ravel())])
    f=A.fit_model(df); b=A.category_t(df,"full","reversed")
    return f["method"], A._p_two(f["B"],f["B_se"],f["df"]), A._p_two(b["est"],b["se"],b["df"])
if __name__=="__main__":
    with ProcessPoolExecutor(3) as ex: res=list(ex.map(one, range(700000,700900)))
    meth=np.array([r[0] for r in res]); p=np.array([r[1] for r in res]); pc=np.array([r[2] for r in res])
    out={}
    for name,mask in (("all",np.ones(len(res),bool)),("mixed model used",meth=="mixed model"),("fallback used",meth!="mixed model")):
        out[name]={"n":int(mask.sum()), **{f"reject@{a}":float(np.mean(p[mask]<=a)) for a in (0.0125,0.025,0.05)}}
    out["category_t_always"]={"n":len(res), **{f"reject@{a}":float(np.mean(pc<=a)) for a in (0.0125,0.025,0.05)}}
    print(json.dumps(out,indent=1))
