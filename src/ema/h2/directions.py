"""Directions from story activations (Sofroniew et al. 2026 recipe).

For one family of labels: direction = mean(label) - mean over the family's
label means, with the top principal components of neutral-text activations
(explaining NEUTRAL_VAR of their variance) projected out, then unit-normalised.
The task family has two labels, so its single direction is "going badly"
minus "going well". Random controls are seeded Gaussian unit vectors.
"""

from __future__ import annotations

import numpy as np

NEUTRAL_VAR = 0.5
N_RANDOM = 6


def neutral_basis(neutral: np.ndarray, var_frac: float = NEUTRAL_VAR) -> np.ndarray:
    """Orthonormal rows spanning the top PCs of the neutral activations (n x d)."""
    x = neutral - neutral.mean(0)
    _, s, vt = np.linalg.svd(x, full_matrices=False)
    explained = np.cumsum(s**2) / np.sum(s**2)
    k = int(np.searchsorted(explained, var_frac) + 1)
    return vt[:k]


def _clean(v: np.ndarray, basis: np.ndarray) -> np.ndarray:
    v = v - basis.T @ (basis @ v)
    return v / np.linalg.norm(v)


def family_directions(acts: dict[str, np.ndarray], basis: np.ndarray) -> dict[str, np.ndarray]:
    """acts: label -> (n, d) story activations. Returns label -> unit direction."""
    means = {k: a.mean(0) for k, a in acts.items()}
    grand = np.mean(list(means.values()), axis=0)
    return {k: _clean(m - grand, basis) for k, m in means.items()}


def task_direction(bad: np.ndarray, good: np.ndarray, basis: np.ndarray) -> np.ndarray:
    return _clean(bad.mean(0) - good.mean(0), basis)


def random_directions(d: int, n: int = N_RANDOM, seed: int = 0) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    out = {}
    for i in range(n):
        v = rng.standard_normal(d)
        out[f"random_{i}"] = v / np.linalg.norm(v)
    return out


def auroc(pos: np.ndarray, neg: np.ndarray) -> float:
    """P(score of a random positive > score of a random negative), ties counted half."""
    pos, neg = np.asarray(pos)[:, None], np.asarray(neg)[None, :]
    return float((pos > neg).mean() + 0.5 * (pos == neg).mean())
