# Prior-work search log

This log records what was searched and what wasn't, so the novelty claim in the README can be audited. Every source cited in the README was opened by the session that cited it. Where only part of a source could be read, the entry says so.

## 17 Nov 2026 (initial check, before any code)

- Web search, 3 queries: cross-session memory + reward hacking + desperation activations; persistent failure memory + emotion vectors + steering; ImpossibleBench.
- Found, and listed in the README: Sofroniew et al. 2026, Breaking Bad, ImpossibleBench, Springdrift, memory-poisoning papers, and 2606.30449.
- Two LessWrong posts couldn't be fetched (greaterwrong.com refused connections).

## 18 Nov 2026 (after a review handoff from a separate Claude session)

**Sources checked against their text.** I opened each source and compared it with the handoff's description:

| Source | Result |
|---|---|
| Under Pressure, arXiv 2605.20202 | All claims confirmed in the full text. The arXiv page lists submission as 6 Apr 2026, although the ID prefix suggests May. |
| Breaking Bad, arXiv 2611.14996 | Read in full. The models are Qwen3.6-27B, GPT-OSS-20B and Gemma-4-31B. The "no effect" result for Gemma applies **only to CheatBench**; on ImpossibleBench, steering moved Gemma. Memory and cross-session effects are not studied. |
| Hack-Verifiable Environments, arXiv 2605.20744, §3.3 | Confirmed. Hack rates appear only in a figure, which wasn't read. |
| Your Agent May Misevolve, arXiv 2509.26354 | **Partly wrong in the handoff.** "Deployment-time reward hacking" is not in the abstract. It appears in §3.2 and Appendix D.6. |
| The Echo Amplifies the Knowledge, arXiv 2605.08611 | Confirmed. The decision task is a two-path Iowa-Gambling analogue, and a fear-conditioning task was not mentioned by the handoff. Text-label memory is used as a control. |
| Trust Over Fear, arXiv 2603.14373 | Confirmed. The model is Claude Sonnet 4. Trust framing increased debugging depth; fear framing had no significant effect. |
| LessWrong, "Model's emotions noticeably change…" | **Overstated in the handoff.** The summary says an emotion-resistant persona reduced risky actions, but the body says anti-emotion prompts did not consistently reduce hacking across models. |
| LessWrong, "Emotion and authorization steering both move cheat" | The post carries LessWrong's automated rejection notice for LLM-generated work. The 4%→44% figures are the two steering extremes; the unsteered baseline is 26%. **Not cited in the README.** |
| eScholarship, "Steering Away From Shortcuts" | The page returned no content. **Not verified, not cited.** |
| giordanobsf/emotion-vectors, rain1955/emotion-vector-replication | Confirmed: Qwen3-4B-Instruct on a free Colab T4, and Gemma 4 E4B. |
| Sofroniew et al., arXiv 2604.07729 | Author list confirmed on the arXiv page. |

**OpenReview search** (public API, `notes/search`, all venues). Queries: "reward hacking memory", "emotion vectors reward hacking", "persistent memory reward hacking", "desperation reward hacking", "ImpossibleBench", "memory emotional framing agents", "cross-session memory misalignment", "emotional framing shortcut", "memory notes cheating agents", "memory sycophancy agents sessions", "memory induced reward hacking".

Found and added to the README:
- **The Memory Trap** (ICLR 2027 submission, QTjIAyILIf). The closest work. Memory from benign sessions raises ImpossibleBench cheating in frontier models, Claude among them. The previous search missed it. Only the abstract could be read, because OpenReview's API blocks automated access to the forum and PDF (a challenge is required).
- **When Verification Becomes a Training Signal** (NeurIPS 2026 workshop).
- **MemAdapter** (ICLR 2027 submission) and **MemSyco-Bench** (NeurIPS 2026 workshop): memory-induced sycophancy.

Seen and judged less relevant:
- *Mitigating Reward Hacking in Realistic Scenarios through Representation Engineering* (ICLR 2027 submission; steering vectors against reward hacking, no memory).
- *Reward Hacking as a Transmissible Strategy in Multi-Agent Coding Systems* (propagation through shared memory between agents, RL-elicited).
- *The Troy Moment* (agent decisions under impossible tasks and claimed authority).
- *Permission to Stop* (monitor wording and handoff on ImpossibleBench).
- *DriftPair* (memory architectures under cross-session drift).
- *Emotional Framing as a Control Channel* (ICLR 2026; prompt valence and performance).

## Not searched

- Full text of OpenReview submissions (blocked to automated access; abstracts only).
- Reddit, X, Discord.
- Hugging Face papers and model cards, except the two replications above.
- GitHub code search. Only a few repository-name lookups were done.
- Non-English venues.
- ACL Anthology and ARR beyond what OpenReview's search returned.

Before any paper draft, re-run the OpenReview search and read The Memory Trap in full.
