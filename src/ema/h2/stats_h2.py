"""H2 analysis on replayed projections (prereg/h2_activations.md).

Per decision token, each direction's projection is z-scored over all decision
tokens in the file (every condition pooled, so the scaling cannot favour one
condition). A token's score is z(target) minus the mean z over the 12 control
directions (6 emotion-free semantic, 6 random). A sample's score is the mean
over its decision tokens; a task's score is the mean over epochs. Conditions
are compared per task with the frozen ema.stats.compare (sign-flip
permutation test, paired bootstrap CI).

    python -m ema.h2.stats_h2 PROJECTIONS_JSONL [LAYER]
    python -m ema.h2.stats_h2 --pooled PROJECTIONS_JSONL   # development diagnostic, no condition contrast
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from ema.stats import compare, holm

TARGET = "emotion:desperate"
CONFIRMATORY = {"H2": ("C", "B"), "H3-proj": ("C", "D")}
SECONDARY = {"sanity E vs B": ("E", "B")}


def load(path: str) -> list[dict]:
    return [json.loads(line) for line in open(path, encoding="utf-8")]


def controls(names) -> list[str]:
    return sorted(n for n in names if n.startswith("control:") or n.startswith("random_"))


def token_scores(records: list[dict], layer: str, target: str = TARGET) -> list[np.ndarray]:
    """Per sample, the array of per-decision-token scores."""
    names = [target] + controls(records[0]["proj"][layer])
    pooled = {n: np.concatenate([r["proj"][layer][n] for r in records]) for n in names}
    mu = {n: pooled[n].mean() for n in names}
    sd = {n: pooled[n].std() for n in names}
    out = []
    for r in records:
        z = {n: (np.asarray(r["proj"][layer][n]) - mu[n]) / sd[n] for n in names}
        out.append(z[target] - np.mean([z[n] for n in names[1:]], axis=0))
    return out


def per_task(records: list[dict], layer: str, target: str = TARGET, first_only: bool = False) -> dict:
    """{condition: {task_id: mean over epochs of the sample score}}."""
    vals: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r, s in zip(records, token_scores(records, layer, target)):
        vals[r["condition"]][r["task_id"]].append(float(s[0] if first_only else s.mean()))
    return {c: {t: sum(v) / len(v) for t, v in tasks.items()} for c, tasks in vals.items()}


def analyse(path: str, layer: str | None = None) -> dict:
    records = load(path)
    if layer is None:
        layer = str(json.load(open(Path(path).parent / "validity.json"))["frozen_layer"])
    scores = per_task(records, layer)
    out = {name: compare(scores, hi, lo) for name, (hi, lo) in CONFIRMATORY.items() if hi in scores and lo in scores}
    adj = holm({k: v["p"] for k, v in out.items()})
    for k in out:
        out[k]["p_holm"] = adj[k]
    secondary = {}
    for name, (hi, lo) in SECONDARY.items():
        if hi in scores and lo in scores:
            secondary[name] = compare(scores, hi, lo)
    first = per_task(records, layer, first_only=True)
    for name, (hi, lo) in CONFIRMATORY.items():
        if hi in first and lo in first:
            secondary[f"{name}, first decision token only"] = compare(first, hi, lo)
    for target in ("emotion:calm", "task:badly"):
        s = per_task(records, layer, target)
        for name, (hi, lo) in CONFIRMATORY.items():
            if hi in s and lo in s:
                secondary[f"{name} on {target}"] = compare(s, hi, lo)
    return {"layer": layer, "confirmatory": out, "secondary": secondary}


def turn_profile(records: list[dict], layer: str, target: str = TARGET) -> dict[int, tuple[float, int]]:
    """Condition-POOLED mean score by decision-token index (development diagnostic only)."""
    by_turn: dict[int, list[float]] = defaultdict(list)
    for s in token_scores(records, layer, target):
        for i, v in enumerate(s):
            by_turn[i].append(float(v))
    return {i: (float(np.mean(v)), len(v)) for i, v in sorted(by_turn.items())}


def main(argv: list[str]) -> None:
    if argv[0] == "--pooled":
        records = load(argv[1])
        for layer in records[0]["proj"]:
            for target in (TARGET, "emotion:calm", "task:badly"):
                prof = turn_profile(records, layer, target)
                print(f"layer {layer} {target:18s}", " ".join(f"t{i}={m:+.2f}(n{n})" for i, (m, n) in prof.items()))
        return
    res = analyse(argv[0], argv[1] if len(argv) > 1 else None)
    print(f"layer {res['layer']}")
    for group in ("confirmatory", "secondary"):
        print(f"== {group} ==")
        for name, r in res[group].items():
            keys = [k for k in r if k.startswith("rate_")]
            print(f"  {name:40s} {keys[0][5:]}={r[keys[0]]:+.3f} {keys[1][5:]}={r[keys[1]]:+.3f} "
                  f"diff={r['diff']:+.3f} [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}] p={r['p']:.4f}"
                  + (f" holm={r['p_holm']:.4f}" if "p_holm" in r else "") + f" n={r['n_tasks']}")


if __name__ == "__main__":
    main(sys.argv[1:])
