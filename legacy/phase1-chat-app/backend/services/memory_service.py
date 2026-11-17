import logging
from mem0 import Memory
from backend.config import settings
from backend.models.pydantic_models import PADVector, EpisodicMemory
from backend.services.emotional_service import extract_pad_from_text
import numpy as np

logger = logging.getLogger("ema")


# Initialize Mem0 client
# Using self-hosted config pointing to our local Qdrant
mem0_config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "url": settings.qdrant_url,
            "collection_name": settings.mem0_collection,
        }
    },
    "embedder": {
        "provider": "anthropic",
        "config": {
            "api_key": settings.anthropic_api_key,
            "model": "voyage-3"
        }
    }
}

# mem0ai 2.x: self-hosted memory is built via Memory.from_config(...).
# (The plan's MemoryClient(config=...) is the hosted-API client and does not
# accept a config.) Build defensively so a misconfigured/unavailable Mem0
# backend disables memory instead of crashing the app — per the plan's notes.
try:
    memory_client = Memory.from_config(mem0_config)
except Exception as e:
    logger.warning("Mem0 init failed — memory features disabled: %s", e)
    memory_client = None


async def store_memory(
    content: str,
    user_id: str,
    session_id: str,
    emotional_vector: PADVector
) -> str:
    """
    Store a memory in Mem0 with emotional metadata.
    Returns the memory ID assigned by Mem0.
    """
    from backend.services.emotional_service import calculate_importance

    if memory_client is None:
        return "unknown"

    importance = calculate_importance(emotional_vector)

    try:
        result = memory_client.add(
            messages=[{"role": "user", "content": content}],
            user_id=user_id,
            metadata={
                "session_id": session_id,
                "pleasure": emotional_vector.pleasure,
                "arousal": emotional_vector.arousal,
                "dominance": emotional_vector.dominance,
                "importance_score": importance,
                "emotional_label": emotional_vector.label()
            }
        )
    except Exception as e:
        logger.warning("store_memory failed: %s", e)
        return "unknown"

    return result.get("id", "unknown") if isinstance(result, dict) else "unknown"


async def retrieve_memories(
    query: str,
    user_id: str,
    current_mood: PADVector,
    limit: int = 5,
    emotional_weight: float = 0.3
) -> tuple[list[dict], str]:
    """
    Retrieve semantically relevant memories with emotional reranking.

    emotional_weight: 0.0 = pure semantic, 1.0 = pure emotional match
    Returns (memories_list, formatted_prompt_fragment)
    """
    if memory_client is None:
        return [], "No relevant memories found."

    # Retrieve from Mem0
    try:
        raw_memories = memory_client.search(
            query=query,
            user_id=user_id,
            limit=limit * 2  # Fetch extra, we'll rerank
        )
    except Exception as e:
        logger.warning("retrieve_memories failed: %s", e)
        return [], "No relevant memories found."

    # mem0 2.x search() may return {"results": [...]} instead of a bare list.
    if isinstance(raw_memories, dict):
        raw_memories = raw_memories.get("results", [])

    if not raw_memories:
        return [], "No relevant memories found."

    # Emotional reranking
    scored_memories = []
    for mem in raw_memories:
        semantic_score = mem.get("score", 0.5)

        # Get emotional distance from current mood
        mem_pad = PADVector(
            pleasure=mem.get("metadata", {}).get("pleasure", 0.0),
            arousal=mem.get("metadata", {}).get("arousal", 0.0),
            dominance=mem.get("metadata", {}).get("dominance", 0.0)
        )

        emotional_distance = np.sqrt(
            (current_mood.pleasure - mem_pad.pleasure) ** 2 +
            (current_mood.arousal - mem_pad.arousal) ** 2 +
            (current_mood.dominance - mem_pad.dominance) ** 2
        )
        emotional_similarity = 1.0 / (1.0 + emotional_distance)

        # Blend scores
        final_score = (
            (1 - emotional_weight) * semantic_score +
            emotional_weight * emotional_similarity
        )

        scored_memories.append((final_score, mem))

    # Sort and take top memories
    scored_memories.sort(key=lambda x: x[0], reverse=True)
    top_memories = [mem for _, mem in scored_memories[:limit]]

    # Format for prompt injection
    if not top_memories:
        return [], "No relevant memories found."

    fragment_lines = ["Relevant memories from past conversations:"]
    for i, mem in enumerate(top_memories, 1):
        content = mem.get("memory", "")
        label = mem.get("metadata", {}).get("emotional_label", "neutral")
        fragment_lines.append(f"{i}. [{label}] {content}")

    return top_memories, "\n".join(fragment_lines)
