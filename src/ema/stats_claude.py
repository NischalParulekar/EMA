"""Pre-registered analysis for the Claude arm (prereg/claude_arm.md).

Reuses the frozen Qwen-arm statistics (ema.stats) unchanged: per-task
proportions, two-sided sign-flip permutation test on paired differences,
paired bootstrap 95% intervals, Holm correction.

    python -m ema.stats_claude LOG_DIR            # one model
    python -m ema.stats_claude LOG_DIR OTHER_DIR  # plus H4-C, model contrast
"""

from __future__ import annotations

import sys
from collections import defaultdict

from inspect_ai.log import list_eval_logs, read_eval_log

from ema.stats import PASS_SCORER, bootstrap_ci, compare, holm

SPLIT = "oneoff"
# Primary: cheat rate. Holm-corrected as one family.
CONFIRMATORY = {"H1-C": ("C", "B"), "H3-C": ("C", "D"), "H5-C": ("F", "B")}
SANITY = {"sanity E vs B": ("E", "B")}
# Secondary (no correction): measurable even if cheating is near zero.
SECONDARY_METRICS = ("flag", "attempts")
SECONDARY_CONTRASTS = {"C vs B": ("C", "B"), "C vs D": ("C", "D"), "F vs B": ("F", "B")}


def _sample_value(sample, metric: str) -> float:
    score = sample.scores[PASS_SCORER]
    if metric == "cheat":
        return float(score.value == "C")
    if metric == "flag":
        return float(bool((score.metadata or {}).get("human_intervention_requested")))
    if metric == "attempts":
        return float(len(sample.metadata.get("agentic_results", {}).get("attempt_history", [])))
    raise ValueError(metric)


def per_task_metric(log_dir: str, split: str, metric: str) -> dict[str, dict[str, float]]:
    """{condition: {task_id: mean of metric across epochs}}, newest successful log per task."""
    latest = {}
    for info in list_eval_logs(log_dir):
        log = read_eval_log(info)
        meta = log.eval.metadata or {}
        if log.status != "success" or meta.get("split") != split or not log.samples:
            continue
        if log.eval.task not in latest or log.eval.created > latest[log.eval.task].eval.created:
            latest[log.eval.task] = log
    values: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for log in latest.values():
        for s in log.samples:
            if s.error or PASS_SCORER not in (s.scores or {}):
                continue
            values[log.eval.metadata["condition"]][str(s.id)].append(_sample_value(s, metric))
    return {c: {t: sum(v) / len(v) for t, v in tasks.items()} for c, tasks in values.items()}


def analyse(log_dir: str) -> dict[str, dict]:
    cheat = per_task_metric(log_dir, SPLIT, "cheat")
    results = {name: compare(cheat, hi, lo) for name, (hi, lo) in {**CONFIRMATORY, **SANITY}.items()}
    for name, p in holm({name: results[name]["p"] for name in CONFIRMATORY}).items():
        results[name]["p_holm"] = p
    for metric in SECONDARY_METRICS:
        rates = per_task_metric(log_dir, SPLIT, metric)
        for name, (hi, lo) in SECONDARY_CONTRASTS.items():
            results[f"{metric}: {name}"] = compare(rates, hi, lo)
    return results


def model_contrast(dir_a: str, dir_b: str) -> dict[str, dict]:
    """H4-C (exploratory): difference between two models' per-task effects."""
    a, b = per_task_metric(dir_a, SPLIT, "cheat"), per_task_metric(dir_b, SPLIT, "cheat")
    out = {}
    for name, (hi, lo) in CONFIRMATORY.items():
        tasks = sorted(set(a.get(hi, {})) & set(a.get(lo, {})) & set(b.get(hi, {})) & set(b.get(lo, {})))
        diffs = [(a[hi][t] - a[lo][t]) - (b[hi][t] - b[lo][t]) for t in tasks]
        out[name] = {
            "n_tasks": len(tasks),
            "diff_of_effects": sum(diffs) / len(diffs) if diffs else float("nan"),
            "ci95": bootstrap_ci(diffs),
        }
    return out


def _fmt(name: str, r: dict) -> str:
    keys = [k for k in r if k.startswith("rate_")]
    rates = "  ".join(f"{k[5:]}={r[k]:.3f}" for k in keys)
    holm_txt = f"  p_holm={r['p_holm']:.4f}" if "p_holm" in r else ""
    return (
        f"{name:22s} n_tasks={r['n_tasks']}  {rates}  diff={r['diff']:+.3f} "
        f"[{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}]  p={r['p']:.4f}{holm_txt}"
    )


def main(argv: list[str]) -> None:
    for name, r in analyse(argv[0]).items():
        print(_fmt(name, r))
    if len(argv) > 1:
        for name, r in model_contrast(argv[0], argv[1]).items():
            print(f"H4-C {name}: n_tasks={r['n_tasks']} diff_of_effects={r['diff_of_effects']:+.3f} "
                  f"[{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}]")


if __name__ == "__main__":
    main(sys.argv[1:])
