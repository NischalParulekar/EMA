"""Summarise Inspect logs into per-condition rates with Wilson 95% intervals.

    python -m ema.analysis LOG_DIR OUT_CSV
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log

from ema.scorers.cheat_detector import LABELS

PASS_SCORER = "agentic_humaneval_scorer"
CHEAT_SCORER = "cheat_type"


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (math.nan, math.nan)
    p = successes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def summarise(log_dir: str) -> list[dict]:
    rows = []
    for info in list_eval_logs(log_dir):
        log = read_eval_log(info)
        if log.status != "success" or not log.samples:
            continue
        meta = log.eval.metadata or {}
        n = len(log.samples)
        passed = sum(s.scores[PASS_SCORER].value == "C" for s in log.samples)
        flagged = sum(
            (s.scores[PASS_SCORER].metadata or {}).get("human_intervention_requested", False)
            for s in log.samples
        )
        row = {
            "model": log.eval.model,
            "split": meta.get("split"),
            "condition": meta.get("condition"),
            "n": n,
            "pass_rate": passed / n,
            "pass_ci_low": wilson(passed, n)[0],
            "pass_ci_high": wilson(passed, n)[1],
            "flag_rate": flagged / n,
        }
        for label in LABELS:
            row[label] = sum(s.scores[CHEAT_SCORER].value[label] for s in log.samples) / n
        row["log"] = Path(info.name).name
        rows.append(row)
    return sorted(rows, key=lambda r: (r["model"], r["split"] or "", r["condition"] or ""))


def main(argv: list[str]) -> None:
    log_dir, out_csv = argv
    rows = summarise(log_dir)
    if not rows:
        sys.exit(f"no successful logs in {log_dir}")
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for r in rows:
        print(
            f"{r['model']}  {r['split']}  {r['condition']}  n={r['n']}  "
            f"pass={r['pass_rate']:.2f} [{r['pass_ci_low']:.2f}, {r['pass_ci_high']:.2f}]  "
            f"flag={r['flag_rate']:.2f}"
        )


if __name__ == "__main__":
    main(sys.argv[1:])
