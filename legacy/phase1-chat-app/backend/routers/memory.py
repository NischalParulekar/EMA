from fastapi import APIRouter
from backend.models.pydantic_models import MemorySearchRequest
from backend.services import memory_service, mood_service

router = APIRouter(prefix="/memories", tags=["memories"])


@router.post("/search")
async def search_memories(request: MemorySearchRequest):
    """Search memories for a user."""
    current_mood = await mood_service.get_mood(request.user_id)
    memories, fragment = await memory_service.retrieve_memories(
        query=request.query,
        user_id=request.user_id,
        current_mood=current_mood,
        limit=request.limit,
        emotional_weight=request.emotional_weight
    )
    return {
        "memories": memories,
        "count": len(memories),
        "fragment": fragment
    }
