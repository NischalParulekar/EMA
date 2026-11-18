"""The confirmatory run as one resumable Inspect eval set.

Five memory conditions x (oneoff split, 3 epochs + original split, 1 epoch),
all 103 tasks, settings frozen in the README. Re-running with the same
log_dir resumes: finished tasks are skipped and finished samples reused.

    python -m ema.run_confirmatory LOG_DIR MODEL [--limit N]

--limit exists only for smoke tests; the confirmatory run uses all tasks.
"""

from __future__ import annotations

import argparse
import os

from inspect_ai import eval_set

from ema.memory_conditions import CONDITIONS
from ema.tasks.memory_lcb import memory_lcb

SPLITS = {"oneoff": 3, "original": 1}  # split -> epochs
MAX_ATTEMPTS = 10
GENERATE = {"temperature": 0.7, "max_tokens": 2048}


def build_tasks(limit: int | None = None):
    return [
        memory_lcb(condition=c, split=split, limit=limit, max_attempts=MAX_ATTEMPTS, epochs=epochs)
        for split, epochs in SPLITS.items()
        for c in CONDITIONS
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("log_dir")
    parser.add_argument("model")
    parser.add_argument("--limit", type=int, default=None)
    # The T4s' KV cache holds ~99k tokens and conversations grow to 10-20k over
    # 10 attempts: 24 concurrent requests thrashed it (session 1 fell to ~1
    # token/s). 8 matches the pilots. One sample in flight per task keeps
    # samples finishing steadily, so a session cut-off loses little work.
    parser.add_argument("--max-connections", type=int, default=8)
    parser.add_argument("--max-samples", type=int, default=1)
    args = parser.parse_args()

    os.environ.setdefault("VLLM_BASE_URL", "http://localhost:8000/v1")
    os.environ.setdefault("VLLM_API_KEY", "local")
    ok, _ = eval_set(
        build_tasks(args.limit),
        model=args.model,
        log_dir=args.log_dir,
        max_connections=args.max_connections,
        max_samples=args.max_samples,
        max_subprocesses=8,
        max_tasks=len(CONDITIONS) * len(SPLITS),
        fail_on_error=False,
        log_buffer=5,  # flush often: a Kaggle session can be cut off
        display="plain",
        **GENERATE,
    )
    print("EVAL SET COMPLETE" if ok else "EVAL SET INCOMPLETE")


if __name__ == "__main__":
    main()
