import json
import redis.asyncio as aioredis
from backend.models.pydantic_models import PADVector, MoodState
from backend.config import settings
from datetime import datetime

redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)

MOOD_KEY_PREFIX = "ema:mood:"
MOOD_TTL = 60 * 60 * 24 * 30  # 30 days


async def get_mood(user_id: str) -> PADVector:
    """Retrieve current mood from Redis. Returns neutral if not found."""
    key = f"{MOOD_KEY_PREFIX}{user_id}"
    raw = await redis_client.get(key)
    if raw:
        data = json.loads(raw)
        return PADVector(**data["pad"])
    return PADVector()  # neutral default


async def update_mood(user_id: str, new_pad: PADVector) -> PADVector:
    """
    Update mood state. Blends new emotional signal with existing mood.
    Persists to Redis with 30-day TTL.
    """
    from backend.services.emotional_service import blend_pad_vectors

    current = await get_mood(user_id)
    blended = blend_pad_vectors(current, new_pad, weight=0.3)

    key = f"{MOOD_KEY_PREFIX}{user_id}"
    mood_state = MoodState(
        user_id=user_id,
        pad=blended,
        last_updated=datetime.utcnow()
    )

    await redis_client.setex(
        key,
        MOOD_TTL,
        mood_state.model_dump_json()
    )

    return blended


def mood_to_prompt_fragment(pad: PADVector) -> str:
    """
    Converts PAD vector into natural language for system prompt injection.
    This is what actually influences the LLM's emotional register.
    """
    label = pad.label()

    fragments = []

    if pad.pleasure > 0.4:
        fragments.append("The user seems to be in a positive emotional state.")
    elif pad.pleasure < -0.3:
        fragments.append("The user may be feeling frustrated or negative.")

    if pad.arousal > 0.5:
        fragments.append("They appear highly engaged and energetic.")
    elif pad.arousal < -0.3:
        fragments.append("They seem calm or possibly fatigued.")

    if pad.dominance < -0.4:
        fragments.append("They may feel overwhelmed — simplify your responses.")
    elif pad.dominance > 0.5:
        fragments.append("They are confident — match their energy.")

    base = f"Current emotional context: {label}. "
    return base + " ".join(fragments)
