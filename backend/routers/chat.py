from fastapi import APIRouter, Depends
from backend.models.pydantic_models import ChatRequest, ChatResponse, PADVector
from backend.services import (
    memory_service,
    llm_service,
    emotional_service,
    grounding_service,
    mood_service
)
from backend.db.database import get_db
import uuid

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, db=Depends(get_db)):
    """
    Full EMA pipeline per message:
    1. Get current mood from Redis
    2. Retrieve relevant memories from Mem0
    3. Build system prompt (canaries + mood + memories)
    4. Select model based on emotional state
    5. Generate response
    6. Verify grounding (canary check)
    7. Recover if grounding failed
    8. Extract emotional tag from response
    9. Update mood state
    10. Store interaction as new memory
    11. Return enriched response to frontend
    """

    # Step 1 — Get current mood
    current_mood = await mood_service.get_mood(request.user_id)

    # Step 2 — Retrieve memories
    memories, memories_fragment = await memory_service.retrieve_memories(
        query=request.message,
        user_id=request.user_id,
        current_mood=current_mood,
        limit=5
    )

    # Step 3 — Build system prompt
    mood_fragment = mood_service.mood_to_prompt_fragment(current_mood)
    system_prompt = grounding_service.build_canary_system_prompt(
        base_prompt="",
        mood_fragment=mood_fragment,
        memories_fragment=memories_fragment
    )

    # Step 4 — Select model
    model = llm_service.select_model(current_mood, request.message)

    # Step 5 — Generate response
    raw_response = await llm_service.generate_response(
        system_prompt=system_prompt,
        message=request.message,
        pad=current_mood,
        model=model
    )

    # Step 6 — Verify grounding
    grounding_result = grounding_service.verify_response(raw_response)

    # Step 7 — Recover if needed (silent, user never sees this)
    final_response = raw_response
    if not grounding_result.passed:
        final_response, strategy = await grounding_service.recover_response(
            original_response=raw_response,
            violations=grounding_result.violations,
            context=request.message
        )
        grounding_result.recovery_applied = True
        grounding_result.recovery_strategy = strategy

    # Step 8 — Extract emotional tag from response
    emotional_tag = await emotional_service.extract_pad_from_text(final_response)

    # Step 9 — Update mood state (blend current with new signal)
    new_mood = await mood_service.update_mood(request.user_id, emotional_tag)

    # Step 10 — Store as new memory
    combined_content = f"User: {request.message}\nEMA: {final_response}"
    await memory_service.store_memory(
        content=combined_content,
        user_id=request.user_id,
        session_id=request.session_id,
        emotional_vector=emotional_tag
    )

    # Step 11 — Return enriched response
    return ChatResponse(
        response=final_response,
        model_used=model,
        memories_retrieved=len(memories),
        current_mood=new_mood,
        emotional_tag=emotional_tag,
        canary_verified=grounding_result.passed,
        session_id=request.session_id
    )
