#!/usr/bin/env python3
"""Standalone Voice Bridge Server with Session Discovery.

This server can discover and report on running Amplifier sessions
without requiring Amplifier as a dependency.

Usage:
    python3 standalone_server.py
    python3 standalone_server.py --port 8765

Voice commands supported:
    "What sessions are running?"
    "What's the status of [project]?"
    "What are the tasks for [project]?"
    "What's being worked on?"
    "Help"
"""

import argparse
import json
import sys
import time
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

# Add src to path for local imports
sys.path.insert(0, str(__file__).replace("standalone_server.py", "src"))

try:
    from amplifier_voice_bridge.command_handler import CommandHandler
    from amplifier_voice_bridge.session_discovery import SessionDiscovery
    DISCOVERY_AVAILABLE = True
except ImportError:
    DISCOVERY_AVAILABLE = False
    print("Note: Session discovery not available (import error)")

try:
    from amplifier_voice_bridge.amplifier_bridge import SyncBridge, is_amplifier_available
    BRIDGE_AVAILABLE = is_amplifier_available()
except ImportError:
    BRIDGE_AVAILABLE = False
    SyncBridge = None

# Global bridge instance (lazy initialized)
_bridge_instance = None

def get_bridge():
    """Get or create the global bridge instance."""
    global _bridge_instance
    if _bridge_instance is None and BRIDGE_AVAILABLE and SyncBridge:
        _bridge_instance = SyncBridge()
    return _bridge_instance


# Simple conversation storage
conversations: dict[str, list[dict[str, str]]] = {}


class VoiceBridgeHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the voice bridge."""

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        """Send a JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        """Handle GET requests."""
        if self.path == "/health":
            self._handle_health()
        elif self.path == "/sessions" or self.path == "/amplifier/sessions":
            self._handle_list_sessions()
        elif self.path == "/":
            self._handle_root()
        else:
            self._send_json(404, {"error": f"Not found: {self.path}"})

    def do_POST(self) -> None:
        """Handle POST requests."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else "{}"

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        if self.path == "/chat":
            self._handle_chat(data)
        elif self.path == "/mock/chat":
            self._handle_mock_chat(data)
        else:
            self._send_json(404, {"error": f"Not found: {self.path}"})

    def _handle_health(self) -> None:
        """Health check endpoint."""
        session_count = 0
        running_sessions = []
        if DISCOVERY_AVAILABLE:
            try:
                discovery = SessionDiscovery()
                sessions = discovery.get_running_sessions()
                session_count = len(sessions)
                running_sessions = [s.project_name for s in sessions[:5]]
            except Exception:
                pass

        self._send_json(200, {
            "status": "healthy",
            "version": "0.3.0",
            "discovery_available": DISCOVERY_AVAILABLE,
            "bridge_available": BRIDGE_AVAILABLE,
            "amplifier_sessions": session_count,
            "running_sessions": running_sessions,
            "uptime_seconds": time.time() - start_time,
        })

    def _handle_list_sessions(self) -> None:
        """List Amplifier sessions."""
        if not DISCOVERY_AVAILABLE:
            self._send_json(200, {
                "sessions": [],
                "error": "Session discovery not available",
            })
            return

        try:
            discovery = SessionDiscovery()
            sessions = discovery.discover_sessions()
            result = []
            for s in sessions:
                todos_summary = []
                for t in s.todos[:3]:
                    todos_summary.append({
                        "content": t.content,
                        "status": t.status,
                    })

                result.append({
                    "session_id": s.session_id,
                    "project": s.project_name,
                    "directory": s.directory,
                    "is_running": s.is_running,
                    "pid": s.pid,
                    "turn_count": s.turn_count,
                    "todos": todos_summary,
                    "last_activity": (
                        s.last_activity.isoformat() if s.last_activity else None
                    ),
                })

            self._send_json(200, {"sessions": result})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def _handle_root(self) -> None:
        """Root endpoint with API info."""
        self._send_json(200, {
            "name": "Amplifier Voice Bridge",
            "version": "0.2.0",
            "discovery_available": DISCOVERY_AVAILABLE,
            "endpoints": {
                "GET /health": "Health check",
                "GET /sessions": "List Amplifier sessions",
                "POST /chat": "Voice command (uses session discovery)",
                "POST /mock/chat": "Mock chat (echo mode)",
            },
        })

    def _handle_chat(self, data: dict[str, Any]) -> None:
        """Handle voice commands with session discovery."""
        prompt = data.get("prompt", "")
        session_name = data.get("session", "default")
        max_length = data.get("max_response_length", 500)

        if not prompt:
            self._send_json(400, {"error": "No prompt provided"})
            return

        start = time.time()

        # Initialize conversation
        if session_name not in conversations:
            conversations[session_name] = []
        conversations[session_name].append({"role": "user", "content": prompt})

        # Use command handler if available
        if DISCOVERY_AVAILABLE:
            try:
                handler = CommandHandler()
                result = handler.handle(prompt)
                extra = {}

                # If the command needs Amplifier execution, try to run it
                if result.needs_amplifier and BRIDGE_AVAILABLE:
                    bridge = get_bridge()
                    if bridge:
                        bridge_result = bridge.execute(
                            result.amplifier_prompt or prompt,
                            continue_session=result.session_id,
                        )
                        if bridge_result.success:
                            response_text = bridge_result.text
                            extra["executed_by"] = "amplifier"
                            extra["execution_time"] = bridge_result.execution_time
                        else:
                            # Bridge failed, fall back to status message
                            response_text = result.text
                            extra["bridge_error"] = bridge_result.error
                    else:
                        response_text = result.text
                        extra["note"] = "Bridge not initialized"
                else:
                    response_text = result.text

                # Add metadata for the client
                if result.needs_amplifier and not BRIDGE_AVAILABLE:
                    extra["needs_amplifier"] = True
                    extra["amplifier_prompt"] = result.amplifier_prompt
                if result.session_id:
                    extra["target_session_id"] = result.session_id

            except Exception as e:
                response_text = f"Error processing command: {e}"
                extra = {"error": True}
        else:
            # Fall back to mock responses
            response_text = self._mock_response(prompt, session_name)
            extra = {"mode": "mock"}

        # Truncate if needed
        truncated = False
        if len(response_text) > max_length:
            response_text = response_text[:max_length].rsplit(" ", 1)[0] + "..."
            truncated = True

        conversations[session_name].append({
            "role": "assistant",
            "content": response_text,
        })

        response = {
            "text": response_text,
            "session_id": session_name,
            "turn_id": str(uuid.uuid4())[:8],
            "truncated": truncated,
            "execution_time": time.time() - start,
            **extra,
        }

        self._send_json(200, response)
        self._log_interaction(session_name, prompt, response_text)

    def _handle_mock_chat(self, data: dict[str, Any]) -> None:
        """Handle mock chat (echo mode)."""
        prompt = data.get("prompt", "")
        session_name = data.get("session", "mock")

        if not prompt:
            self._send_json(400, {"error": "No prompt provided"})
            return

        response_text = self._mock_response(prompt, session_name)

        self._send_json(200, {
            "text": response_text,
            "session_id": session_name,
            "turn_id": str(uuid.uuid4())[:8],
            "mode": "mock",
        })

    def _mock_response(self, prompt: str, session_name: str) -> str:
        """Generate mock response for testing."""
        prompt_lower = prompt.lower()

        if any(w in prompt_lower for w in ["time", "clock"]):
            return f"The time is {datetime.now().strftime('%I:%M %p')}."
        if any(w in prompt_lower for w in ["date", "today"]):
            return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."
        if any(w in prompt_lower for w in ["hello", "hi", "hey"]):
            return "Hello! Voice bridge is working. Session discovery is not available in mock mode."
        if any(w in prompt_lower for w in ["help", "what can"]):
            return "I can check sessions, show tasks, and relay commands. Try: what sessions are running?"
        if any(w in prompt_lower for w in ["session", "running", "status"]):
            return "Session discovery requires the full server. This is mock mode for testing connectivity."

        return f"Mock mode: I heard '{prompt}'. For real responses, ensure session discovery is available."

    def _log_interaction(self, session: str, prompt: str, response: str) -> None:
        """Log interaction to console."""
        p = prompt[:50] + "..." if len(prompt) > 50 else prompt
        r = response[:50] + "..." if len(response) > 50 else response
        print(f"[{session}] User: {p}")
        print(f"[{session}] Bot: {r}")

    def log_message(self, format: str, *args) -> None:
        """Custom log format."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


def main():
    """Main entry point."""
    global start_time
    start_time = time.time()

    parser = argparse.ArgumentParser(description="Voice Bridge Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), VoiceBridgeHandler)

    print("=" * 60)
    print("  Amplifier Voice Bridge Server")
    print("=" * 60)
    print()
    print(f"  Server: http://{args.host}:{args.port}")
    print(f"  Discovery: {'ENABLED' if DISCOVERY_AVAILABLE else 'DISABLED'}")
    print()
    print("  Voice Commands:")
    print('    "What sessions are running?"')
    print('    "What\'s the status of [project]?"')
    print('    "What are the tasks for [project]?"')
    print('    "What\'s being worked on?"')
    print()
    print("  Test:")
    print(f"    curl http://localhost:{args.port}/health")
    print(f"    curl http://localhost:{args.port}/sessions")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


start_time = time.time()

if __name__ == "__main__":
    main()
