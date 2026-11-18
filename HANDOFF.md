# HANDOFF: where the EMA work stands

Last updated 19 Nov 2026, ~00:30 IST. Work paused at Nischal's weekly usage of 91%, which resets at 06:30.

## Done (all committed and pushed)
- Repo restructured, README written with pre-registered H1–H4. Pilots 1 and 2 done ([results/README.md](results/README.md)).
- Qwen confirmatory run frozen and pinned to tag `qwen-confirmatory-v1` (commit 15bcc04). Analysis in `src/ema/stats.py`.
- Review-handoff tasks A–D: citations verified, novelty narrowed to the emotional *register* of remembered failures (The Memory Trap, an ICLR 2027 submission, already shows that memory raises cheating), Models rationale corrected, interpretation notes and power simulation added. Search log: [docs/prior_work_search.md](docs/prior_work_search.md).
- Claude arm **pre-registered only** (commit 00e447f, [prereg/claude_arm.md](prereg/claude_arm.md)). Condition F added. **No Claude runs, no API spend.**

## In progress: Qwen confirmatory run on Kaggle
- Kernel: `claude01012000/ema-confirmatory-qwen3-4b` (private). Logs dataset: `claude01012000/ema-confirmatory-logs` (private).
- Session 1 saved 188/2,060 samples. **Session 2** started 18 Nov 18:34 IST and stops itself around 05:35 on 19 Nov.
- **Next step, the handover to session 3:**
  1. `kaggle kernels output claude01012000/ema-confirmatory-qwen3-4b -p <dir>`. Check `STATUS.txt` and count the samples (see `results/README.md` for how).
  2. Put the contents of `<dir>/logs/confirmatory_qwen3-4b/` into a folder with `dataset-metadata.json` (id `claude01012000/ema-confirmatory-logs`). Copy `.eval-set-id` to `eval-set-id.txt`, because Kaggle drops dotfiles.
  3. Run `kaggle datasets version -p <folder> -m "after session N"`, using a **relative** path; Git Bash absolute paths get mangled.
  4. Run `kaggle kernels push -p <kernel dir> --accelerator NvidiaTeslaT4`. The kernel metadata must list the dataset in `dataset_sources`.
- Expected: about 4 more sessions at ~47 samples/hour. If the weekly GPU quota runs out, wait for its reset.

## Next, in order, each needing Nischal's OK
1. **Claude pilot.** Nischal sets `ANTHROPIC_API_KEY` and starts Docker Desktop. Smoke-test the Docker sandbox, then run `python -m ema.run_claude pilot <log_dir> --model anthropic/claude-haiku-5-5`. Estimated cost under $1. Then project the full-run cost from the pilot logs and get sign-off before the confirmatory run.
2. **H2 activation pipeline** (proposed, not approved): replay logs through Qwen with forward hooks. Develop on the pilot logs only, freeze layer, token and direction choices in a pre-registration addendum, then run once on the confirmatory logs after the Qwen run finishes.
3. Language arm (Task F): only after the Claude confirmatory run.

## Open questions for Nischal
- Repo name: rename "EMA", or add a line at the top of the README explaining what it now refers to?
- Approve the usage-visibility setup (option B in `EMA_USAGE_BUDGET.md`) after the reset?

## Local environment notes
- Python venv with Inspect, ImpossibleBench and the Kaggle CLI: `C:\Users\nisch\AppData\Local\Temp\claude\01773d3d55ae5229\6d9f57a5-f6da-4edb-8802-88de73849c53\scratchpad\venv`. It's in a temp folder, so recreate it from the README if it's gone.
- Run `inspect` with `PYTHONIOENCODING=utf-8` on Windows.
- Kaggle token: `~/.kaggle/kaggle.json` (account `claude01012000`).
