import json
import re
from backend.models.pydantic_models import PADVector
from backend.config import settings
import anthropic

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

# PAD reference anchors from psychological research
PAD_ANCHORS = {
    "happy":     PADVector(pleasure=0.81, arousal=0.51, dominance=0.46),
    "excited":   PADVector(pleasure=0.62, arousal=0.75, dominance=0.38),
    "calm":      PADVector(pleasure=0.40, arousal=-0.30, dominance=0.15),
    "neutral":   PADVector(pleasure=0.0,  arousal=0.0,  dominance=0.0),
    "sad":       PADVector(pleasure=-0.63, arousal=-0.27, dominance=-0.33),
    "frustrated":PADVector(pleasure=-0.51, arousal=0.59, dominance=0.25),
    "fear":      PADVector(pleasure=-0.62, arousal=0.82, dominance=-0.43),
    "angry":     PADVector(pleasure=-0.51, arousal=0.59, dominance=0.25),
    "overwhelmed":PADVector(pleasure=-0.40, arousal=0.60, dominance=-0.60),
    "content":   PADVector(pleasure=0.70, arousal=-0.10, dominance=0.30),
}


async def extract_pad_from_text(text: str) -> PADVector:
    """
    Ask Claude to analyze text and return a PAD emotional vector.
    Uses structured prompting to get consistent JSON output.
    """
    prompt = f"""Analyze the emotional content of this text and return a PAD (Pleasure-Arousal-Dominance) vector.

Text to analyze:
{text}

Rules:
- Pleasure: -1.0 (very negative) to 1.0 (very positive)
- Arousal: -1.0 (very calm) to 1.0 (very excited/agitated)
- Dominance: -1.0 (overwhelmed/submissive) to 1.0 (in control/dominant)
- Be precise, use values like 0.62 not just 0 or 1
- Return ONLY valid JSON, no explanation

Return exactly this format:
{{"pleasure": 0.0, "arousal": 0.0, "dominance": 0.0}}"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",  # Use Haiku for this — cheap, fast
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        raw = response.content[0].text.strip()
        # Clean any accidental markdown
        raw = re.sub(r"```json|```", "", raw).strip()
        data = json.loads(raw)
        return PADVector(**data)
    except Exception:
        # Safe fallback to neutral
        return PADVector()


def blend_pad_vectors(
    current: PADVector,
    new: PADVector,
    weight: float = 0.3
) -> PADVector:
    """
    Blend current mood with new emotional signal.
    Weight controls how much the new signal shifts the current mood.
    Low weight = stable mood. High weight = reactive mood.
    Default 0.3 = gradual shift, feels natural.
    """
    return PADVector(
        pleasure=round((1 - weight) * current.pleasure + weight * new.pleasure, 4),
        arousal=round((1 - weight) * current.arousal + weight * new.arousal, 4),
        dominance=round((1 - weight) * current.dominance + weight * new.dominance, 4),
    )


def calculate_importance(pad: PADVector, base_score: float = 0.5) -> float:
    """
    Higher emotional intensity = higher importance score.
    Memories with strong emotion (positive or negative) decay slower.
    """
    intensity = (abs(pad.pleasure) + abs(pad.arousal) + abs(pad.dominance)) / 3.0
    return round(min(base_score + (intensity * 0.5), 1.0), 4)
