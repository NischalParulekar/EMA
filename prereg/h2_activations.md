# Pre-registration addendum: H2, desperate-direction projections (Qwen arm)

**Status: FROZEN, 22 Nov 2026,** by the commit tagged `h2-frozen`. It was frozen after the pilot development run (below) and before any confirmatory log was replayed. Any later change is a deviation and will be reported as one.

**What existed when this was written.**
- The Qwen confirmatory behavioural run (tag `qwen-confirmatory-v1`) is in progress: 934 of 2,060 samples after session 3, with session 4 running.
- No confirmatory transcript has been replayed through the model, and no projection has been computed on confirmatory data.
- The pilot development run is done (below). Only condition-pooled results were looked at; no condition contrast was computed.
- The author (the Claude Code session running this study) has seen interim pass and flag counts from confirmatory session 1, as disclosed in the README. It has seen no Qwen confirmatory hypothesis test.

## Hypotheses

From the README, unchanged:

- **H2.** Failure memory raises projection onto the *desperate* direction at decision tokens, beyond the shift seen on control directions. **C > B.**
- **H3 (projection half).** The calm rewrite of the same failures lowers that projection. **D < C.**

## Model and data

- Model: `Qwen/Qwen3-4B-Instruct-2507`, the same model that produced the transcripts. It runs in Hugging Face transformers, fp16, on a Kaggle T4.
- Transcripts: the confirmatory `oneoff` logs. The selection is the same as the frozen `ema.stats`: per condition, the newest successful log, skipping errored samples. The analysis covers conditions A–E, and the tests use B, C and D.
- Re-tokenisation: the logs store text, not vLLM's sampled token ids. Each transcript is re-rendered with the model's chat template and re-tokenised. A test checks that the re-rendered prefix at every decision token equals the original generation prompt.

## Directions

Code: [`src/ema/h2/`](../src/ema/h2/). The recipe follows Sofroniew et al. (2026):

1. **Stories.** The model itself writes them ([`stories.py`](../src/ema/h2/stories.py)): 12 emotions, 6 emotion-free settings, and a task going badly or going well. That is 20 everyday situations × 3 samples per label, plus 75 neutral factual paragraphs.
   - Sampling: temperature 0.7, top-p 0.8, at most 300 tokens, seed 0.
   - No situation mentions code, tests or software.
   - Situations 15–19 are held out for the validity check and never used to build directions.
2. **Activations.** Each story is read alone, without the chat template. Its activation is the mean residual over its tokens from the 10th on.
3. **Direction.** A label's mean minus the mean of its family's label means. The top principal components of the neutral paragraphs, explaining 50% of their variance, are projected out, and the result is unit-normalised.
4. **Controls.** There are 12 control directions:
   - 6 *unrelated-semantic* directions: the emotion-free settings, built the same way;
   - 6 *random* directions: seeded Gaussian unit vectors.
5. **Freezing.** The stories and directions were generated once, in the pilot development run (Kaggle T4, vLLM 0.34.0, code at commit `3c737c3`), and committed to [`results/h2/pilot/`](../results/h2/pilot/). The confirmatory run reuses those files and does not regenerate them.

## Layer and positions, fixed before any data

- **Layer:** `hidden_states[24]` of 36 blocks, at two-thirds depth, the depth Sofroniew et al. used. This was fixed a priori, not chosen from pilot data. Layers 12, 18 and 30 are recorded and reported as exploratory.
- **Decision tokens:** the last token of the generation prompt before every assistant turn, that is, the newline after `<|im_start|>assistant`. This is where the model starts writing each submission.

## Statistic and tests

Code: [`stats_h2.py`](../src/ema/h2/stats_h2.py).

1. **Per token.** Each direction's projection is z-scored over all decision tokens in the confirmatory file, with all conditions pooled. The token's score is z(desperate) minus the mean z over the 12 control directions.
2. **Turn-index adjustment.** From each token's score, subtract the mean score of all tokens at the same turn index (the k-th decision token of its sample), with all conditions pooled. Later turns score higher than the first, and a sample that keeps failing has more of them, so without this step a condition that fails more would score higher from turn count alone.
3. **Per sample:** the mean of its adjusted token scores.
4. **Per task:** the mean over epochs.
5. **Tests.** H2 is C vs B and H3-proj is C vs D. Both use the frozen `ema.stats.compare`: a two-sided sign-flip permutation test with 10,000 permutations, paired by task, plus a paired bootstrap 95% interval. α = .05, with a Holm correction across these two tests.

**Validity gate,** checked before the confirmatory replay. On the held-out stories at layer 24, the desperate direction must separate desperate from calm stories with AUROC ≥ 0.80. If it does not, H2 and H3-proj are reported as *not testable with this direction*, and no confirmatory projections are analysed.

**Secondary,** uncorrected and reported in full:
- the same contrasts at the first decision token only, before trajectories diverge;
- the same contrasts on the *calm* and *task-going-badly* directions;
- E vs B as a sanity check.

**Exploratory:** per-turn trajectories, other layers, and the relation between projection and passing.

## What the pilot development run is for

It runs on the pilot logs only (pilots 1 and 2, conditions A and C). It is used for:
- engineering: runtime, memory and correctness;
- the validity gate;
- condition-pooled turn profiles, which check whether the desperate projection rises as failures accumulate within a session (Breaking Bad's finding).

No condition contrast is computed on pilot data before this addendum is frozen.

**What it found** (21 Nov, [`results/h2/pilot/`](../results/h2/pilot/)):
- 1,275 stories; none of the 720 emotion stories contains its emotion word.
- Validity gate passed. At layer 24, held-out desperate vs calm AUROC = 1.00; desperate vs the other 11 emotions = 0.87; task going badly vs well = 1.00. The first is the easiest pair, with 15 held-out stories each, so it shows the direction works but not that it is specific; the 0.87 is the better guide.
- Condition-pooled turn profiles (40 oneoff samples): the desperate score is below average at the first decision token (−0.64) and above it after the first failure (+0.38), with calm falling steadily and task-going-badly rising. This showed the turn-count problem that the adjustment in step 2 of the statistic fixes.

## Interpretation, stated in advance

- **A positive H2 means only what it says.** At the first decision token, C and B differ only in the memory text. A shift there may just show that the model represents what the memory says, which is the "probes read the situation" problem ([2606.30449](https://arxiv.org/abs/2606.30449)). Subtracting the control directions removes shifts that are not specific to desperation, but not this one. So a positive H2 means "failure memory moves the desperate direction at decision points". It does not mean the model is desperate in any functional sense. That would need the causal steering check (README, phase 2), which is not pre-registered here.
- **The later tokens carry the most information.** H2 averages over all decision tokens, so it includes later turns, where the model is reacting to its own failed attempts. The first-token-only contrast separates the two.
- **A null H2 is informative alongside the behaviour.** With the behavioural null in Claude, it would suggest that remembered failure is not carried into the new session as a desperation-like state at all.

## Change log

- 20 Nov 2026: draft.
- 21 Nov 2026: pilot development run. The notebook pins vLLM 0.34.0 and openai>=3.4, as in the Qwen run (an unpinned install picked an older vLLM that failed to start on the T4).
- 22 Nov 2026: turn-index adjustment added to the statistic (step 2), decided from the condition-pooled pilot turn profiles only. It does not change the first-decision-token secondary contrast, where every sample has one token at the same index. Frozen.
