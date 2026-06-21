from pydantic import BaseModel, field_validator, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ModelTier(str, Enum):
    HAIKU = "claude-haiku-4-5-20251001"
    SONNET = "claude-sonnet-4-6"
    OPUS = "claude-opus-4-6"


class PADVector(BaseModel):
    """
    Pleasure-Arousal-Dominance emotional vector.
    All values must be between -1.0 and 1.0.

    Pleasure:   positive = happy, negative = sad/angry
    Arousal:    positive = excited/alert, negative = calm/sleepy
    Dominance:  positive = in control, negative = overwhelmed
    """
    pleasure: float = 0.0
    arousal: float = 0.0
    dominance: float = 0.0

    @field_validator("pleasure", "arousal", "dominance")
    @classmethod
    def validate_range(cls, v: float) -> float:
        if not -1.0 <= v <= 1.0:
            raise ValueError(f"PAD values must be between -1.0 and 1.0, got {v}")
        return round(v, 4)

    def to_list(self) -> list[float]:
        return [self.pleasure, self.arousal, self.dominance]

    def label(self) -> str:
        """Returns human readable emotion label based on PAD values."""
        if self.pleasure > 0.5 and self.arousal > 0.3:
            return "excited"
        elif self.pleasure > 0.5 and self.arousal <= 0.3:
            return "content"
        elif self.pleasure < -0.3 and self.arousal > 0.5:
            return "frustrated"
        elif self.pleasure < -0.3 and self.arousal <= 0.3:
            return "sad"
        elif self.arousal > 0.7:
            return "alert"
        elif self.dominance < -0.5:
            return "overwhelmed"
        else:
            return "neutral"


class EpisodicMemory(BaseModel):
    """A single memory unit stored in Mem0 + Qdrant."""
    id: Optional[str] = None
    content: str
    user_id: str
    session_id: str
    emotional_vector: PADVector = Field(default_factory=PADVector)
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    retrieval_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("importance_score")
    @classmethod
    def validate_importance(cls, v: float) -> float:
        return round(v, 4)


class ChatRequest(BaseModel):
    """Incoming chat message from frontend."""
    message: str = Field(..., min_length=1, max_length=10000)
    user_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    """Outgoing response to frontend."""
    response: str
    model_used: ModelTier
    memories_retrieved: int
    current_mood: PADVector
    emotional_tag: PADVector
    canary_verified: bool
    session_id: str


class MoodState(BaseModel):
    """Current running mood state stored in Redis."""
    user_id: str
    pad: PADVector
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    interaction_count: int = 0


class MemorySearchRequest(BaseModel):
    """Request to search memories."""
    query: str
    user_id: str
    limit: int = Field(default=5, ge=1, le=20)
    emotional_weight: float = Field(default=0.3, ge=0.0, le=1.0)


class GroundingCheckResult(BaseModel):
    """Result of grounding verification on a response."""
    passed: bool
    canary_found: bool
    violations: list[str] = []
    recovery_applied: bool = False
    recovery_strategy: Optional[str] = None
