import numpy as np
from scipy.stats import norm, multivariate_normal
from scipy.optimize import brentq
t1 = 15/35; r = np.sqrt(t1)
def obf_one_sided(a):
    a1 = 2 - 2*norm.cdf(norm.ppf(1 - a/2)/np.sqrt(t1))
    z1 = norm.ppf(1 - a1)
    mvn = multivariate_normal(mean=[0,0], cov=[[1,r],[r,1]])
    f = lambda z2: a1 + (norm.cdf(z1) - mvn.cdf([z1, z2])) - a
    return a1, z1, brentq(f, 1.0, 5.0)
print("EFFICACY two-sided local alpha (alpha/2 per side)")
for a in [0.0125, 0.05/3, 0.025, 0.05]:
    a1, z1, z2 = obf_one_sided(a/2); print(f"  {a:.4f}  spent {2*a1:.6f}  z1 {z1:.3f}  z2 {z2:.3f}")
print("EQUIVALENCE one-sided local alpha per TOST side (Holm levels)")
EQ = {}
for a in [0.0125, 0.05/3, 0.025, 0.05]:
    a1, e1, e2 = obf_one_sided(a); EQ[round(a,4)] = (e1, e2); print(f"  {a:.4f}  spent {a1:.6f}  e1 {e1:.3f}  e2 {e2:.3f}")

def sim(lift, sd, upr, eff_a=0.0125, eq_a=0.0125, N=200000, seed=20261006, margin=0.10):
    rng = np.random.default_rng(seed)
    _, z1, z2 = obf_one_sided(eff_a/2); _, e1, e2 = obf_one_sided(eq_a)
    n1, n2 = 15*upr, 35*upr
    m1 = lift + sd/np.sqrt(n1)*rng.standard_normal(N)
    inc = lift + sd/np.sqrt(n2-n1)*rng.standard_normal(N)
    m2 = (n1*m1 + (n2-n1)*inc)/n2
    se1, se2 = sd/np.sqrt(n1), sd/np.sqrt(n2)
    eff1 = np.abs(m1/se1) >= z1
    flat1 = (~eff1) & (m1 - e1*se1 > -margin) & (m1 + e1*se1 < margin)
    ext = ~(eff1 | flat1)
    eff2 = ext & (np.abs(m2/se2) >= z2)
    flat2 = ext & ~eff2 & (m2 - e2*se2 > -margin) & (m2 + e2*se2 < margin)
    inc2 = ext & ~eff2 & ~flat2
    pos = (eff1 & (m1>0)) | (eff2 & (m2>0))
    return [x.mean() for x in (eff1, flat1, ext, eff2, flat2, inc2, pos)] + [ext.mean()]

import sys
for label, eq in [("CHECK old (eq 0.05, 10 units)", 0.05)]:
    print(label)
    for lift, sd in [(0.146,0.405),(0.073,0.49),(0,0.405)]:
        print("  ", lift, sd, " ".join(f"{v:.3f}" for v in sim(lift, sd, 10, eq_a=eq)[:7]))
for upr in (10, 9):
    print(f"NEW: efficacy local 0.0125, equivalence Holm worst case 0.0125, {upr} units/replicate")
    for lift, sd in [(0.146,0.405),(0.146,0.49),(0.073,0.405),(0.073,0.49),(0,0.405),(0,0.49)]:
        v = sim(lift, sd, upr)
        cost_rep = 15 + 20*v[2]
        print(f"  {lift:5.3f} {sd:5.3f} | " + " ".join(f"{x:.3f}" for x in v[:7]) + f" | E[reps] {cost_rep:.1f}")
# best case equivalence at 0.05 (after three others resolved) for reference, 9 units
print("REF: 9 units, equivalence at 0.05 (Holm best case)")
for lift, sd in [(0.073,0.49),(0,0.49)]:
    print("  ", lift, sd, " ".join(f"{x:.3f}" for x in sim(lift, sd, 9, eq_a=0.05)[:7]))
# half-width at final for flat
for upr in (10,9):
  for sd in (0.405,0.49):
    for a in (0.0125,0.05):
      _,e1,e2=obf_one_sided(a); print(f"halfwidth upr {upr} sd {sd} eq {a}: interim {e1*sd/np.sqrt(15*upr):.3f} final {e2*sd/np.sqrt(35*upr):.3f}")
