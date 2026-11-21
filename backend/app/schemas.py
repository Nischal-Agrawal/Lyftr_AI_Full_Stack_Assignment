from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, field_validator


class ChatRequest(BaseModel):
    session_id: str
    message: str
    system_prompt: Optional[str] = None

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError("session_id must be a string")
        v_stripped = v.strip()
        if len(v_stripped) < 1 or len(v_stripped) > 128:
            raise ValueError("session_id must be between 1 and 128 characters")
        return v_stripped

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: Any) -> str:
        if not isinstance(v, str):
            raise ValueError("message must be a string")
        v_trimmed = v.strip()
        if len(v_trimmed) < 1:
            raise ValueError("message cannot be empty or whitespace only")
        if len(v_trimmed) > 4000:
            raise ValueError("message cannot exceed 4000 characters after trimming whitespace")
        return v_trimmed


class ChatMetadata(BaseModel):
    resolution_source: Literal["LIVE_INFERENCE", "LLM_CACHE"]
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    key_id: Optional[str] = None
    fallback_attempts: int


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    metadata: ChatMetadata


class MessageItem(BaseModel):
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class SessionMessagesResponse(BaseModel):
    session_id: str
    messages: List[MessageItem]


class HealthResponse(BaseModel):
    status: str = "ok"
    keys_configured: int
    cache_enabled: bool
