"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for the /chat endpoint."""

    prompt: str = Field(..., description="The user's voice input/prompt")
    session: str = Field(default="default", description="Session identifier")
    max_response_length: int = Field(
        default=500, description="Max characters for voice response"
    )
    timeout: int = Field(default=120, description="Timeout in seconds")


class ChatResponse(BaseModel):
    """Response model for the /chat endpoint."""

    text: str = Field(..., description="The response text for voice output")
    session_id: str = Field(..., description="Session identifier")
    turn_id: str = Field(..., description="Unique identifier for this turn")
    truncated: bool = Field(default=False, description="Whether response was truncated")
    execution_time: float = Field(..., description="Execution time in seconds")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    partial_text: Optional[str] = Field(None, description="Partial response if available")
    session_id: Optional[str] = Field(None, description="Session identifier")


class SessionInfo(BaseModel):
    """Information about a session."""

    id: str
    status: str  # "active", "idle", "executing", "expired"
    turn_count: int
    created_at: datetime
    last_activity: datetime
    working_directory: Optional[str] = None
    bundle: Optional[str] = None


class SessionListResponse(BaseModel):
    """Response for listing sessions."""

    sessions: list[SessionInfo]


class CreateSessionRequest(BaseModel):
    """Request to create a new session."""

    id: str = Field(..., description="Session identifier")
    bundle: Optional[str] = Field(None, description="Bundle to use")
    working_directory: Optional[str] = Field(None, description="Working directory")


class CreateSessionResponse(BaseModel):
    """Response after creating a session."""

    session_id: str
    status: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    sessions_active: int
    uptime_seconds: float
