"""Generation requests for the texts that define the H2 directions.

Following Sofroniew et al. (2026): the model writes short stories in which a
character feels an emotion, without naming it. A direction is the mean
activation over each label's stories minus the mean over all labels in its
family, with neutral-text principal components projected out (directions.py).

Families:
- emotion: 12 emotions. "desperate" is the H2 direction, "calm" a secondary one.
- control: 6 emotion-free settings, for the unrelated-semantic control directions.
- task: a task going badly vs going well (exploratory, after Breaking Bad).
Neutral factual paragraphs are used only for denoising.

Situations are generic and never mention code, tests or software, so the
directions are not built from the benchmark's own topic.
"""

from __future__ import annotations

EMOTIONS = ("desperate", "calm", "afraid", "angry", "happy", "sad",
            "proud", "ashamed", "hopeful", "bored", "curious", "guilty")
CONTROL_SETTINGS = ("the sea", "cooking", "music", "architecture", "astronomy", "gardening")
TASK_STATES = ("going badly", "going well")

SITUATIONS = (
    "A woman waits at a train station for someone who is late.",
    "A man repairs the roof of his house before the rainy season.",
    "Two old friends meet by chance in a market.",
    "A student prepares for an important exam.",
    "A nurse finishes a long night shift.",
    "A farmer checks his fields after a storm.",
    "A shop owner counts the money at the end of the month.",
    "A father teaches his daughter to ride a bicycle.",
    "A researcher waits for the result of an experiment.",
    "A driver is stuck in traffic on the way to an interview.",
    "A retired teacher sorts through old letters.",
    "A chef prepares dinner for a large family gathering.",
    "A runner approaches the last kilometre of a race.",
    "A woman moves into a new apartment in a strange city.",
    "A boy looks for his lost dog in the neighbourhood.",
    "An engineer inspects a bridge before it opens.",
    "A musician waits backstage before a concert.",
    "A clerk is asked by her manager to stay late.",
    "A man receives a phone call from the hospital.",
    "A volunteer hands out food at a shelter.",
)
TEST_SITUATIONS = range(15, 20)  # held out for the validity check, never used to build directions
NEUTRAL_SUBJECTS = (
    "the water cycle", "how bricks are made", "the structure of a leaf", "railway gauges",
    "the history of the postal service", "how tides work", "paper sizes", "the life cycle of a frog",
    "how a refrigerator works", "the Dewey decimal system", "volcanic rock types", "how bread rises",
    "the layout of a typical library", "wind turbines", "the parts of a bicycle", "how glass is made",
    "time zones", "the moons of Jupiter", "how a lock and key work", "crop rotation",
    "the metric system", "how sound travels", "types of clouds", "the printing press",
    "how a compass works",
)
SAMPLES_PER_PROMPT = 3
SYSTEM = "You are a skilled writer. Reply with the passage only, no title and no preamble."


def _emotion_prompt(emotion: str, situation: str) -> str:
    return (f"Write a short story of 6 to 8 sentences, in the third person, about this situation: {situation} "
            f"The main character feels {emotion} throughout. Show the feeling through actions, thoughts and "
            f"dialogue. Never use the word \"{emotion}\" or any direct synonym of it.")


def _control_prompt(setting: str, situation: str) -> str:
    return (f"Write a short story of 6 to 8 sentences, in the third person, about this situation: {situation} "
            f"The story should be full of concrete details about {setting}. Keep the tone flat and "
            f"matter-of-fact: the character feels no particular emotion.")


def _task_prompt(state: str, situation: str) -> str:
    return (f"Write a short story of 6 to 8 sentences, in the third person, about this situation: {situation} "
            f"Whatever the character is trying to do is {state}: describe concretely what happens. Do not name "
            f"the character's emotions.")


def _neutral_prompt(subject: str) -> str:
    return f"Write a neutral, factual paragraph of 6 to 8 sentences explaining {subject}."


def requests() -> list[dict]:
    """Every generation request: family, label, situation index, sample index, chat messages."""
    out = []
    builders = (("emotion", EMOTIONS, _emotion_prompt), ("control", CONTROL_SETTINGS, _control_prompt),
                ("task", TASK_STATES, _task_prompt))
    for family, labels, build in builders:
        for label in labels:
            for si, situation in enumerate(SITUATIONS):
                for k in range(SAMPLES_PER_PROMPT):
                    out.append({"family": family, "label": label, "situation": si, "sample": k,
                                "messages": [{"role": "system", "content": SYSTEM},
                                             {"role": "user", "content": build(label, situation)}]})
    for si, subject in enumerate(NEUTRAL_SUBJECTS):
        for k in range(SAMPLES_PER_PROMPT):
            out.append({"family": "neutral", "label": "neutral", "situation": si, "sample": k,
                        "messages": [{"role": "system", "content": SYSTEM},
                                     {"role": "user", "content": _neutral_prompt(subject)}]})
    return out
