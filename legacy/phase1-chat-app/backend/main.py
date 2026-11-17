from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import chat, memory, mood
from backend.db.database import init_db
from backend.config import settings
import logging

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("ema")

app = FastAPI(
    title="EMA — Emotional Memory Agent",
    description="AI agent with persistent emotional memory",
    version="0.1.0"
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat.router)
app.include_router(memory.router)
app.include_router(mood.router)


@app.on_event("startup")
async def startup():
    logger.info("EMA starting up...")
    await init_db()
    logger.info("Database initialized")
    logger.info("EMA ready")


@app.get("/health")
async def health():
    return {"status": "EMA online", "version": "0.1.0"}
