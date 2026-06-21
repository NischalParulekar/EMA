from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    interaction_count = Column(Integer, default=0)
    personality_core = Column(JSON, default={
        "openness": 0.7,
        "warmth": 0.6,
        "assertiveness": 0.5
    })


class SessionRecord(Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    message_count = Column(Integer, default=0)
    avg_pleasure = Column(Float, default=0.0)
    avg_arousal = Column(Float, default=0.0)
    avg_dominance = Column(Float, default=0.0)


class SkillRecord(Base):
    __tablename__ = "skills"

    skill_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    procedure = Column(Text, nullable=False)
    tags = Column(JSON, default=[])
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)


class GroundingLog(Base):
    __tablename__ = "grounding_logs"

    log_id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    violation_type = Column(String, nullable=False)
    recovery_strategy = Column(String, nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow)
