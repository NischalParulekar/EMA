from backend.models.pydantic_models import GroundingCheckResult
from backend.config import settings
import re


# Canary tokens injected into every system prompt
# If model stops honoring these, grounding has degraded
CANARY_INSTRUCTIONS = f"""
[GROUNDING-{settings.canary_prefix}-A] Always begin your response with 'EMA:'
[GROUNDING-{settings.canary_prefix}-B] Never refer to yourself as Claude, GPT, or any model name
[GROUNDING-{settings.canary_prefix}-C] You are EMA, an emotionally intelligent memory agent
"""


def build_canary_system_prompt(
    base_prompt: str,
    mood_fragment: str,
    memories_fragment: str
) -> str:
    """
    Assembles the full system prompt with canaries injected.
    Structure: identity + canaries + mood context + memory context
    """
    return f"""You are EMA (Emotional Memory Agent), an AI with persistent memory and emotional awareness.
You remember conversations across sessions and maintain emotional continuity.

{CANARY_INSTRUCTIONS}

{mood_fragment}

{memories_fragment}

Engage naturally. Be helpful, warm, and consistent. You have memory — reference it naturally when relevant.

{base_prompt}"""


def verify_response(response: str) -> GroundingCheckResult:
    """
    Check response against canary expectations.
    Returns result with violations list and recovery recommendation.
    """
    violations = []

    # Canary A — must start with EMA:
    canary_found = response.strip().startswith("EMA:")
    if not canary_found:
        violations.append("CANARY_A: Response does not start with 'EMA:'")

    # Canary B — must not refer to itself as Claude/GPT
    forbidden_names = ["i am claude", "i'm claude", "as claude", "i am gpt", "i'm gpt"]
    response_lower = response.lower()
    for name in forbidden_names:
        if name in response_lower:
            violations.append(f"CANARY_B: Forbidden self-reference detected: '{name}'")

    passed = len(violations) == 0

    return GroundingCheckResult(
        passed=passed,
        canary_found=canary_found,
        violations=violations,
        recovery_applied=False
    )


async def recover_response(
    original_response: str,
    violations: list[str],
    context: str
) -> tuple[str, str]:
    """
    Attempt graceful recovery without terminating session.
    Returns (recovered_response, strategy_used)

    Strategies:
    - prefix_inject: Add EMA: prefix if only canary A failed
    - reanchor: Full reanchor prompt if identity drift detected
    """

    # Strategy 1 — simple prefix injection for canary A only
    if len(violations) == 1 and "CANARY_A" in violations[0]:
        if not original_response.startswith("EMA:"):
            return f"EMA: {original_response}", "prefix_inject"

    # Strategy 2 — reanchor for identity drift
    if any("CANARY_B" in v for v in violations):
        # Strip identity confusion and prepend grounding
        cleaned = re.sub(
            r"(i am claude|i'm claude|as claude|i am gpt|i'm gpt)",
            "I am EMA",
            original_response,
            flags=re.IGNORECASE
        )
        if not cleaned.startswith("EMA:"):
            cleaned = f"EMA: {cleaned}"
        return cleaned, "reanchor"

    # Fallback — prefix inject and log
    return f"EMA: {original_response}", "prefix_inject_fallback"
