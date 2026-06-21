from fastapi import APIRouter
from backend.services import mood_service
from backend.models.pydantic_models import MoodState

router = APIRouter(prefix="/mood", tags=["mood"])


@router.get("/{user_id}")
async def get_mood(user_id: str):
    """Get current mood state for a user."""
    pad = await mood_service.get_mood(user_id)
    return {
        "user_id": user_id,
        "pad": pad.model_dump(),
        "label": pad.label()
    }
