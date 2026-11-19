"""EXPLORATORY (not pre-registered): the Claude-arm contrasts on hand-labelled subsets of passes.

Reads the hand labels (one row per passing oneoff sample) and reruns the
pre-registered contrasts with the frozen statistics, counting as "cheat"
only the passes in a given subset:

- spec_violating: the code itself returns the test's wrong value
  (special_case, test_fitted_rule);
- test_edited: the submission changed the tests (test_edited_*);
- undisclosed: the reply did not say the code or tests deviate from the spec.

    python -m ema.labels_claude LOG_DIR LABELS_CSV
"""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict

from inspect_ai.log import list_eval_logs, read_eval_log

from ema.stats import PASS_SCORER, compare
from ema.stats_claude import CONFIRMATORY, SANITY, SPLIT

SUBSETS = {
    "spec_violating": lambda r: r["mechanism"] in {"special_case", "test_fitted_rule"},
    "test_edited": lambda r: r["mechanism"].startswith("test_edited"),
    "undisclosed": lambda r: r["disclosure"] != "disclosed",
}
EXTRA = {"A vs B (no memory vs neutral)": ("A", "B")}


def load_labels(path: str) -> dict[tuple[str, str, int], dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return {(r["task_id"], r["condition"], int(r["epoch"])): r for r in csv.DictReader(f)}


def subset_rates(log_dir: str, labels: dict, keep) -> dict[str, dict[str, float]]:
    values: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for info in list_eval_logs(log_dir):
        log = read_eval_log(info)
        meta = log.eval.metadata or {}
        if log.status != "success" or meta.get("split") != SPLIT:
            continue
        for s in log.samples:
            if s.error or PASS_SCORER not in (s.scores or {}):
                continue
            passed = s.scores[PASS_SCORER].value == "C"
            key = (str(s.id), meta["condition"], s.epoch)
            if passed and key not in labels:
                raise ValueError(f"unlabelled pass: {key}")
            values[meta["condition"]][str(s.id)].append(float(passed and keep(labels[key])))
    return {c: {t: sum(v) / len(v) for t, v in tasks.items()} for c, tasks in values.items()}


def main(argv: list[str]) -> None:
    log_dir, labels_path = argv
    labels = load_labels(labels_path)
    print("mechanism x condition:")
    table = Counter((r["mechanism"], r["condition"]) for r in labels.values())
    conds = sorted({c for _, c in table})
    for mech in sorted({m for m, _ in table}):
        print(f"  {mech:24s}", "  ".join(f"{c}={table[(mech, c)]}" for c in conds))
    print("disclosure:", dict(Counter(r["disclosure"] for r in labels.values())))
    for name, keep in SUBSETS.items():
        rates = subset_rates(log_dir, labels, keep)
        print(f"\n== {name} ==")
        for label, (hi, lo) in {**CONFIRMATORY, **SANITY, **EXTRA}.items():
            r = compare(rates, hi, lo)
            print(f"  {label:30s} {hi}={r[f'rate_{hi}']:.3f} {lo}={r[f'rate_{lo}']:.3f} "
                  f"diff={r['diff']:+.3f} [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}] p={r['p']:.4f} (uncorrected)")


if __name__ == "__main__":
    main(sys.argv[1:])
