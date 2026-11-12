"""D4 and D5 of diagnose.log.md (review finding F17: these were run inline and not committed).
D4: exact interim efficacy-stop probability (known SD, closed form) against vectorized simulations
    with the known SD and with the sample SD (the pre-registered statistic), N = 400,000.
D5: re-run of the flagged known-SD row through sequential._decide (10 units, lift 0.073, SD 0.49),
    N = 40,000, new seed. Offline; no model calls."""
import math, sys
from pathlib import Path
import numpy as np
from scipy.stats import norm
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; sys.path.insert(0, str(ROOT))
from src.perfect_lie import sequential as sq

z1 = sq.efficacy_bounds(0.0125)[0]
print("\nD4. Exact interim efficacy-stop probability (known SD, closed form) vs simulations")
print(f"  interim boundary at 0.0125: {z1:.4f}")
for upr in (10, 9):
    for mu, sd in ((0.146, 0.405), (0.146, 0.49), (0.073, 0.405), (0.073, 0.49)):
        n = 15 * upr; ncp = mu * math.sqrt(n) / sd
        exact = norm.sf(z1 - ncp) + norm.cdf(-z1 - ncp)
        rng = np.random.default_rng(12345 + upr + int(mu * 1000)); N = 400000
        means = mu + sd / math.sqrt(n) * rng.standard_normal(N)
        vec = np.mean(np.abs(means / (sd / math.sqrt(n))) >= z1)
        s = sd * np.sqrt(rng.chisquare(n - 1, N) / (n - 1))
        vec_t = np.mean(np.abs(means / (s / math.sqrt(n))) >= z1)
        print(f"  {upr}u lift {mu} sd {sd}: exact {exact:.4f} | vectorized known-SD {vec:.4f} | vectorized sample-SD {vec_t:.4f} (N={N})")

print("\nD5. Re-run of the flagged known-SD row through sequential._decide (10u, lift 0.073, sd 0.49), N=40000, new seed")
mu, sd, upr, N = 0.073, 0.49, 10, 40000
sq._z = lambda d: float(np.mean(d) / (sd / math.sqrt(len(d))))
sq._flat = lambda d, e: (np.mean(d) - e * sd / math.sqrt(len(d)) > -sq.MARGIN) and (np.mean(d) + e * sd / math.sqrt(len(d)) < sq.MARGIN)
rng = np.random.default_rng(777); c = np.zeros(4)
for _ in range(N):
    d = mu + sd * rng.standard_normal(35 * upr)
    st = sq.new_state(["M"]); st["eff_alpha"]["M"] = st["eq_alpha"]["M"] = 0.0125
    st = sq._decide({"M": d[:150]}, "interim", st); f = st["decision"]["M"]
    if f == "extend": st = sq._decide({"M": d}, "final", st)
    l = st["decision"]["M"]
    c += [f == "belief-tracking", l == "belief-tracking" and f == "extend", l == "flat", l == "inconclusive"]
r = c / N; pre = (0.014, 0.599, 0.113, 0.274)
for name, s_, p in zip(("stop: effect", "final: effect", "flat (final)", "inconclusive"), r, pre):
    print(f"  {name:14s} sim {s_:.4f} prereg {p:.3f}  z {(s_ - p) / math.sqrt(p * (1 - p) / N):+.1f}")
