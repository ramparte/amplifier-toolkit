"""FastAPI server for Amplifier Voice Bridge."""

import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    ChatRequest,
    ChatResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    ErrorResponse,
    HealthResponse,
    SessionInfo,
    SessionListResponse,
)
from .session_manager import SessionManager

# Global state
_session_manager: Optional[SessionManager] = None
_start_time: float = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global _session_manager, _start_time
    _start_time = time.time()
    _session_manager = SessionManager()
    yield
    # Cleanup on shutdown


app = FastAPI(
    title="Amplifier Voice Bridge",
    description="Remote voice control for Amplifier sessions via iOS/CarPlay",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware for flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tailscale network only in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_session_manager() -> SessionManager:
    """Get the session manager instance."""
    if _session_manager is None:
        raise HTTPException(status_code=503, detail="Server not initialized")
    return _session_manager


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    manager = get_session_manager()
    sessions = await manager.list_sessions()
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        sessions_active=len(sessions),
        uptime_seconds=time.time() - _start_time,
    )


@app.post("/chat", response_model=ChatResponse, responses={500: {"model": ErrorResponse}})
async def chat(request: ChatRequest):
    """Primary endpoint for voice interaction.

    Sends a prompt to an Amplifier session and returns the response
    formatted for voice output.
    """
    manager = get_session_manager()

    result = await manager.execute_prompt(
        session_id=request.session,
        prompt=request.prompt,
        timeout=request.timeout,
        max_response_length=request.max_response_length,
    )

    if "error" in result:
        # Return error with partial response if available
        if result.get("partial_text"):
            return ChatResponse(
                text=f"There was an issue, but here's what I got: {result['partial_text']}",
                session_id=result["session_id"],
                turn_id=result["turn_id"],
                truncated=True,
                execution_time=result["execution_time"],
            )
        raise HTTPException(
            status_code=500,
            detail={
                "error": result["error"],
                "session_id": result.get("session_id"),
            },
        )

    return ChatResponse(
        text=result["text"],
        session_id=result["session_id"],
        turn_id=result["turn_id"],
        truncated=result["truncated"],
        execution_time=result["execution_time"],
    )


@app.get("/sessions", response_model=SessionListResponse)
async def list_sessions():
    """List all active sessions."""
    manager = get_session_manager()
    sessions_data = await manager.list_sessions()

    sessions = [
        SessionInfo(
            id=s["id"],
            status=s["status"],
            turn_count=s["turn_count"],
            created_at=s["created_at"],
            last_activity=s["last_activity"],
            working_directory=s.get("working_directory"),
            bundle=s.get("bundle"),
        )
        for s in sessions_data
    ]

    return SessionListResponse(sessions=sessions)


@app.post("/sessions", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """Create a new session."""
    manager = get_session_manager()

    # Check if session already exists
    existing = await manager.get_session_info(request.id)
    if existing:
        raise HTTPException(status_code=409, detail=f"Session '{request.id}' already exists")

    # Create the session
    await manager.get_or_create_session(
        session_id=request.id,
        bundle=request.bundle,
        working_directory=request.working_directory,
    )

    return CreateSessionResponse(session_id=request.id, status="created")


@app.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get information about a specific session."""
    manager = get_session_manager()
    info = await manager.get_session_info(session_id)

    if not info:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    return SessionInfo(
        id=info["id"],
        status=info["status"],
        turn_count=info["turn_count"],
        created_at=info["created_at"],
        last_activity=info["last_activity"],
        working_directory=info.get("working_directory"),
        bundle=info.get("bundle"),
    )


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    manager = get_session_manager()
    deleted = await manager.delete_session(session_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    return {"status": "deleted", "session_id": session_id}


# Simple mock mode for testing without Amplifier dependencies
_mock_mode = False


def enable_mock_mode():
    """Enable mock mode for testing without Amplifier."""
    global _mock_mode
    _mock_mode = True


@app.post("/mock/chat")
async def mock_chat(request: ChatRequest):
    """Mock chat endpoint for testing the iOS shortcut without Amplifier.

    Returns a simple echo response.
    """
    return ChatResponse(
        text=f"I heard you say: {request.prompt}. This is a mock response for testing.",
        session_id=request.session,
        turn_id="mock-001",
        truncated=False,
        execution_time=0.1,
    )
