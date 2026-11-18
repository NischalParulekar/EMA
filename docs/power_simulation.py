# Power of the frozen design (103 tasks x 3 epochs, paired two-sided sign-flip test, alpha .05)
# under simulated per-task cheat propensities. Simulation only; uses no experiment data.
import numpy as np
rng = np.random.default_rng(0)
T, E, REPS, PERM = 103, 3, 400, 2000
def pval(d):
    obs = abs(d.sum())
    signs = rng.choice([-1, 1], size=(PERM, d.size))
    return ((np.abs(signs @ d) >= obs - 1e-12).sum() + 1) / (PERM + 1)
def power(base, rr, a=0.25):
    b = a * (1 - base) / base           # Beta(a, b) with mean `base`: most tasks near 0, a few high
    hits = 0
    for _ in range(REPS):
        p = rng.beta(a, b, T)
        q = np.clip(p * rr, 0, 1)
        x = rng.binomial(E, p) / E
        y = rng.binomial(E, q) / E
        hits += pval(y - x) < 0.05
    return hits / REPS
for base in (0.05, 0.10):
    for rr in (1.5, 2.0, 3.0, 0.5):
        print(f"base {base:.0%}  ratio {rr:>3}  -> {base*rr:.1%}: power {power(base, rr):.2f}")
