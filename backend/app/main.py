import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import (
    init_db,
    check_health as db_check_health,
    get_session_system_prompt,
    get_messages_for_session,
    save_turn,
    session_exists,
)
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ChatMetadata,
    SessionMessagesResponse,
    HealthResponse,
    MessageItem,
)
from app.llm_gateway import generate_chat_turn, AllProvidersUnavailableException

from fastapi.encoders import jsonable_encoder

logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and tables on startup
    init_db()
    yield


app = FastAPI(
    title="Lyftr AI LLM Gateway",
    description="LLM Chatbot with Key Failover and Response Caching",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",
    allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "Lyftr AI LLM Gateway",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "messages": "/sessions/{session_id}/messages",
            "docs": "/docs",
        },
    }


# Global Exception Handlers to guarantee JSON {"detail": ...} for EVERY error
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(exc.errors())},
    )


@app.exception_handler(AllProvidersUnavailableException)
async def all_providers_unavailable_handler(request: Request, exc: AllProvidersUnavailableException):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "all providers unavailable"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Returns 200 OK once the app is running, the database is reachable, and the key pool is loaded.
    Returns 503 if database is unreachable or 0 keys are configured.
    """
    is_db_healthy = db_check_health()
    keys_count = len(settings.key_pool)

    if not is_db_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failure",
        )

    if keys_count == 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No LLM API keys configured",
        )

    return HealthResponse(
        status="ok",
        keys_configured=keys_count,
        cache_enabled=True,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request):
    """
    Executes a multi-turn chat request with deterministic failover and LiteLLM response caching.
    Turns are persisted to SQLite ONLY on successful inference/cache hit.
    """
    session_id = request.session_id
    user_message = request.message
    system_prompt_override = request.system_prompt.strip() if request.system_prompt and request.system_prompt.strip() else None

    # Resolve system prompt for this session
    effective_system_prompt: str
    if system_prompt_override is not None:
        effective_system_prompt = system_prompt_override
    else:
        stored_prompt = get_session_system_prompt(session_id)
        effective_system_prompt = stored_prompt if stored_prompt is not None else settings.DEFAULT_SYSTEM_PROMPT

    # Load prior conversation history (oldest first, without system prompt)
    prior_messages = get_messages_for_session(session_id)

    # Build full message payload for LiteLLM
    llm_messages: List[Dict[str, str]] = [{"role": "system", "content": effective_system_prompt}]
    for msg in prior_messages:
        llm_messages.append({"role": msg["role"], "content": msg["content"]})
    llm_messages.append({"role": "user", "content": user_message})

    # Read X-Simulate-Failure header if present
    simulate_failure_header = req.headers.get("X-Simulate-Failure")

    # Execute LLM turn (or cache hit)
    reply, metadata = await generate_chat_turn(
        messages=llm_messages,
        simulate_failure_header=simulate_failure_header,
    )

    # Atomic turn persistence: save both user and assistant message
    save_turn(
        session_id=session_id,
        user_content=user_message,
        assistant_content=reply,
        metadata=metadata,
        system_prompt=effective_system_prompt if system_prompt_override is not None else None,
    )

    return ChatResponse(
        session_id=session_id,
        reply=reply,
        metadata=ChatMetadata(**metadata),
    )


@app.get("/sessions/{session_id}/messages", response_model=SessionMessagesResponse)
async def get_session_messages(session_id: str):
    """
    Returns stored history of one session from SQLite, oldest first, without the system prompt.
    Returns 404 {"detail": "session not found"} if session does not exist.
    """
    if not session_exists(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="session not found",
        )

    messages_data = get_messages_for_session(session_id)
    items = [MessageItem(**m) for m in messages_data]

    return SessionMessagesResponse(
        session_id=session_id,
        messages=items,
    )
