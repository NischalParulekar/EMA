import anthropic
from backend.config import settings
from backend.models.pydantic_models import PADVector, ModelTier

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


def select_model(pad: PADVector, message: str) -> ModelTier:
    """
    Basic model routing based on emotional state and task complexity.
    Phase 7 will make this significantly more sophisticated.

    Current logic:
    - High arousal (stressed/overwhelmed) → Haiku (lighter, faster)
    - Low dominance (overwhelmed) → Haiku (simpler responses)
    - Default → Sonnet
    - Very complex technical messages → Sonnet (Opus later)
    """
    # Detect overwhelm
    if pad.dominance < -0.5 or (pad.arousal > 0.7 and pad.pleasure < -0.3):
        return ModelTier.HAIKU

    # Detect casual conversation
    if len(message) < 50 and pad.arousal < settings.haiku_arousal_threshold:
        return ModelTier.HAIKU

    # Default to Sonnet
    return ModelTier.SONNET


async def generate_response(
    system_prompt: str,
    message: str,
    pad: PADVector,
    model: ModelTier
) -> str:
    """
    Call Claude API with full context.
    System prompt includes canaries + mood + memories.
    """
    response = client.messages.create(
        model=model.value,
        max_tokens=1000,
        system=system_prompt,
        messages=[
            {"role": "user", "content": message}
        ]
    )

    return response.content[0].text
