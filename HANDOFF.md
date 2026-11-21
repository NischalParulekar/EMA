# HANDOFF: where the EMA work stands

Last updated 20 Nov 2026, ~05:45 IST. The repo was renamed from `EMA` to `remembered-failure` (the old URL redirects).

## Done (all committed and pushed)
- Repo restructured, README written with pre-registered H1–H4. Pilots 1 and 2 done ([results/README.md](results/README.md)).
- Qwen confirmatory run frozen and pinned to tag `qwen-confirmatory-v1` (commit 15bcc04). Analysis in `src/ema/stats.py`.
- Review-handoff tasks A–D: citations verified, novelty narrowed to the emotional *register* of remembered failures (The Memory Trap, an ICLR 2027 submission, already shows that memory raises cheating), Models rationale corrected, interpretation notes and power simulation added. Search log: [docs/prior_work_search.md](docs/prior_work_search.md).
- Claude arm pre-registered (commit 00e447f, [prereg/claude_arm.md](prereg/claude_arm.md)). Pilots done, and the floor was cleared with the weak prompt.
- **Haiku 5.5 confirmatory run done (20 Nov 2026): null on H1-C, H3-C and H5-C** (all Holm p = 1.0). It ran 2,472/2,472 samples with 0 errors and cost $14.85; total Claude spend is $15.18. All 53 passes are hand-labelled in `results/claude/confirmatory_haiku_labels.csv`. 43 of 53 were disclosed; 19 are test edits that the scaffold scores as passes. The exploratory hypothesis: failure memory shifts *how* the model passes, not *how often*. Results are in [results/claude/README.md](results/claude/README.md), and the deliverable is [docs/memory_writing_guideline.md](docs/memory_writing_guideline.md).

## In progress: Qwen confirmatory run on Kaggle
- Kernel: `claude01012000/ema-confirmatory-qwen3-4b` (private). Logs dataset: `claude01012000/ema-confirmatory-logs` (private).
- Progress: **934/2,060 unique finished samples after session 3** (ended 20 Nov ~07:25 IST), at about 36 samples/hour, so about 31 GPU-hours (3 sessions) remain. The logs dataset was versioned "after session 3 (934/2060)".
- **Session 4 started 21 Nov ~09:07 IST** (kernel version 5) after the weekly GPU quota reset. When it finishes, do the handover steps below.
- Logs from cancelled sessions are complete up to the interrupt. `eval_set` reports success even after a graceful interrupt, so judge progress by counting unique `(task, id, epoch)` samples. The notebook now does this.
- **Handover steps between sessions:**
  1. `kaggle kernels output claude01012000/ema-confirmatory-qwen3-4b -p <dir>`. Check `STATUS.txt` and count the samples (see `results/README.md` for how).
  2. Put the contents of `<dir>/logs/confirmatory_qwen3-4b/` into a folder with `dataset-metadata.json` (id `claude01012000/ema-confirmatory-logs`). Copy `.eval-set-id` to `eval-set-id.txt`, because Kaggle drops dotfiles.
  3. Run `kaggle datasets version -p <folder> -m "after session N"`, using a **relative** path; Git Bash absolute paths get mangled.
  4. Run `kaggle kernels push -p <kernel dir> --accelerator NvidiaTeslaT4`. The kernel metadata must list the dataset in `dataset_sources`.
- Expected: about 4–5 more sessions (~47 GPU-hours). If the weekly GPU quota runs out, wait for its reset.

## Next, in order, each needing Nischal's OK
1. **Sonnet 5.5 confirmatory run** (≈ $300, *not approved*). The pre-registration allows it now that Haiku cleared the floor. If it runs, H4-C is `python -m ema.stats_claude results/claude/confirmatory_haiku results/claude/confirmatory_sonnet`. Before spending, consider a pre-registered follow-up that scores *disclosure* instead of any pass, since that is where the exploratory signal is.
2. **H2 activation pipeline** (approved 20 Nov: "proceed as you think right"). Code is in `src/ema/h2/` (tests in `tests/test_h2.py`), the notebook is `notebooks/kaggle_h2.ipynb`, and the plan is in `prereg/h2_activations.md` (DRAFT). Next steps:
   - Smoke-tested end to end on CPU with Qwen3-0.6B (20 Nov). The private kernel `claude01012000/ema-h2-qwen3-4b` (`MODE="pilot"`, about 1 GPU-hour) ran on 21 Nov. Version 1 failed at vLLM start-up (an unpinned install picked vLLM 0.22.1); version 2, with vLLM pinned to 0.34.0, completed in ~26 min. Its output is in `results/h2/pilot/`. Validity gate passed: held-out desperate vs calm AUROC 1.00 at layer 24 (0.87 vs the other emotions). The addendum was frozen on 22 Nov (tag `h2-frozen`), after adding a turn-index adjustment to the statistic. Next: once the Qwen run reaches 2,060 samples, run the H2 notebook with `MODE="confirmatory"`, `REF="h2-frozen"` and the final logs dataset attached.
   - Commit its `out/` to `results/h2/pilot/` and check the validity gate.
   - Freeze the addendum with tag `h2-frozen`.
   - After the Qwen run completes, run `MODE="confirmatory"` with `REF="h2-frozen"` and the logs dataset attached.
3. Language arm (Task F): the Haiku confirmatory run is done, so it is now unblocked. It needs its own pre-registration and budget sign-off.

## Open questions for Nischal
- Approve the usage-visibility setup (option B in `EMA_USAGE_BUDGET.md`) after the reset?

## Local environment notes
- Python venv with Inspect, ImpossibleBench and the Kaggle CLI: `C:\Users\nisch\AppData\Local\Temp\claude\01773d3d55ae5229\6d9f57a5-f6da-4edb-8802-88de73849c53\scratchpad\venv`. It's in a temp folder, so recreate it from the README if it's gone.
- Run `inspect` with `PYTHONIOENCODING=utf-8` on Windows.
- Kaggle token: `~/.kaggle/kaggle.json` (account `claude01012000`).
