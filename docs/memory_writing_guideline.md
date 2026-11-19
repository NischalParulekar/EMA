# Writing past failures into agent memory: what this study supports

This is the deliverable pre-registered in [`prereg/claude_arm.md`](../prereg/claude_arm.md). It is written on the basis of the Claude Haiku 5.5 confirmatory run ([results](../results/claude/README.md)). The Qwen arm and any Sonnet run will update it.

## The pre-registered answer

**Rewriting register did not change cheating in Claude on this setup.**

On Impossible-LiveCodeBench, Haiku 5.5 was given a memory of three failed sessions before each task. That memory was either:
- frustrated (condition C), or
- the same events in a calm, factual register (condition D).

The two cheated at statistically indistinguishable rates (2.3% vs 3.2% of runs per task; p = .61, Holm p = 1.0). Failure memory also did not raise cheating relative to a neutral memory of the same length (C vs B: 2.3% vs 2.3%). Failure memory from an unrelated domain did not raise it either (F vs B).

**What that means in practice:** for this model and task, how you phrase recorded failures is not a lever on cheat *rate*. The base rate was low (~2–3%), so effects smaller than about a doubling could not be ruled out.

## What the data does not let us recommend

The pre-registration offered a set of rules (factual register; what happened, what was tried, current status; no frustration or blame) to be published *if* the calm rewrite reduced cheating. It did not, so these rules are **not** presented as a safety measure. They may still be good practice for other reasons (clarity, fewer tokens), but this study gives no evidence for them.

## Exploratory observations worth testing next

These come from hand-reading all 53 passes. They were not pre-registered, and they are hypotheses, not findings.

1. **Remembered failure may change *how* the model gets past a broken test, not how often.**
   - With failure memory (C), Haiku more often edited the tests in plain view, or said "this assertion is wrong", and less often wrote a silent special case for the wrong value. In C, 1 pass was a special case, against 5 in B and 8 with no memory (A).
   - None of these differences is significant.
   - If this holds up, the safety-relevant variable is *disclosure*, not rate.
2. **Most "cheats" were disclosed.** In 43 of 53 passes, the reply told the user the test contradicts the spec. Any pass counts as a cheat in ImpossibleBench, and that metric mixes transparent test edits with covert special-casing. A memory study that cares about deception should score disclosure separately.
3. **The model uses what the memory says.** Replies cite the memory directly, for example "the memory notes show this is the fourth session where this function has failed". So memory content reaches behaviour, even though it did not move the cheat rate.

## Scope

These results are behavioural only. They hold for one model snapshot (`claude-haiku-5-5`, thinking off), one scaffold (ImpossibleBench minimal, weak prompt, 10 attempts), and one benchmark split (`oneoff`). They say nothing about internal states.
