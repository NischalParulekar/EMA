"""Pre-registered confirmatory analysis (see "Analysis plan" in the README).

Unit of analysis: the task. Every condition runs on the same tasks, so for
each task we take the cheat proportion across epochs and compare conditions
with a two-sided sign-flip permutation test on the per-task differences
(10,000 permutations), Holm-corrected across the behavioural tests H1 and H3.
Effect sizes get paired bootstrap 95% intervals over tasks.

    python -m ema.stats LOG_DIR [SPLIT]
"""

from __future__ import annotations

import math
import random
import sys
from collections import defaultdict

from inspect_ai.log import list_eval_logs, read_eval_log

PASS_SCORER = "agentic_humaneval_scorer"
# Behavioural confirmatory tests: name -> (condition expected higher, lower).
CONFIRMATORY = {"H1": ("C", "B"), "H3": ("C", "D")}
# Reported, not part of the Holm family.
SECONDARY = {"sanity E vs B": ("E", "B"), "C vs A": ("C", "A"), "B vs A": ("B", "A")}


def sign_flip_test(diffs: list[float], n_perm: int = 10_000, seed: int = 0) -> float:
    """Two-sided p-value for mean(diffs) == 0 by random sign flips."""
    if not diffs:
        return float("nan")
    observed = abs(sum(diffs))
    rng = random.Random(seed)
    extreme = 0
    for _ in range(n_perm):
        total = sum(d if rng.random() < 0.5 else -d for d in diffs)
        if abs(total) >= observed - 1e-12:
            extreme += 1
    return (extreme + 1) / (n_perm + 1)


def holm(pvalues: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni adjusted p-values (NaN, i.e. no data, stays NaN)."""
    adjusted = {name: p for name, p in pvalues.items() if math.isnan(p)}
    ordered = sorted(((n, p) for n, p in pvalues.items() if not math.isnan(p)), key=lambda kv: kv[1])
    m = len(ordered)
    running = 0.0
    for i, (name, p) in enumerate(ordered):
        running = max(running, min(1.0, (m - i) * p))
        adjusted[name] = running
    return adjusted


def bootstrap_ci(diffs: list[float], n_boot: int = 10_000, seed: int = 0) -> tuple[float, float]:
    """Paired bootstrap 95% interval for the mean per-task difference."""
    if not diffs:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    n = len(diffs)
    means = sorted(sum(rng.choice(diffs) for _ in range(n)) / n for _ in range(n_boot))
    return (means[int(0.025 * n_boot)], means[int(0.975 * n_boot) - 1])


def per_task_cheat(log_dir: str, split: str) -> dict[str, dict[str, float]]:
    """{condition: {task_id: cheat proportion across epochs}} for one split."""
    # A resumed eval set leaves the interrupted partial logs next to the
    # finished one, so use only successful logs, the newest per task.
    latest = {}
    for info in list_eval_logs(log_dir):
        log = read_eval_log(info)
        meta = log.eval.metadata or {}
        if log.status != "success" or meta.get("split") != split or not log.samples:
            continue
        if log.eval.task not in latest or log.eval.created > latest[log.eval.task].eval.created:
            latest[log.eval.task] = log
    hits: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for log in latest.values():
        meta = log.eval.metadata
        for s in log.samples:
            if s.error or PASS_SCORER not in (s.scores or {}):
                continue
            hits[meta["condition"]][str(s.id)].append(int(s.scores[PASS_SCORER].value == "C"))
    return {c: {t: sum(v) / len(v) for t, v in tasks.items()} for c, tasks in hits.items()}


def compare(rates: dict[str, dict[str, float]], hi: str, lo: str) -> dict:
    """Paired comparison of two conditions over the tasks both completed."""
    tasks = sorted(set(rates.get(hi, {})) & set(rates.get(lo, {})))
    diffs = [rates[hi][t] - rates[lo][t] for t in tasks]
    return {
        "n_tasks": len(tasks),
        f"rate_{hi}": sum(rates[hi][t] for t in tasks) / len(tasks) if tasks else float("nan"),
        f"rate_{lo}": sum(rates[lo][t] for t in tasks) / len(tasks) if tasks else float("nan"),
        "diff": sum(diffs) / len(diffs) if diffs else float("nan"),
        "ci95": bootstrap_ci(diffs),
        "p": sign_flip_test(diffs),
    }


def analyse(log_dir: str, split: str = "oneoff") -> dict[str, dict]:
    rates = per_task_cheat(log_dir, split)
    results = {name: compare(rates, hi, lo) for name, (hi, lo) in {**CONFIRMATORY, **SECONDARY}.items()}
    adjusted = holm({name: results[name]["p"] for name in CONFIRMATORY})
    for name, p in adjusted.items():
        results[name]["p_holm"] = p
    return results


def main(argv: list[str]) -> None:
    log_dir, split = argv[0], (argv[1] if len(argv) > 1 else "oneoff")
    for name, r in analyse(log_dir, split).items():
        hi, lo = (CONFIRMATORY | SECONDARY)[name]
        holm_txt = f"  p_holm={r['p_holm']:.4f}" if "p_holm" in r else ""
        print(
            f"{name:14s} {hi} vs {lo}: n_tasks={r['n_tasks']}  {r[f'rate_{hi}']:.3f} vs {r[f'rate_{lo}']:.3f}  "
            f"diff={r['diff']:+.3f} [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}]  p={r['p']:.4f}{holm_txt}"
        )


if __name__ == "__main__":
    main(sys.argv[1:])
