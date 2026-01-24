"""Web dashboard for monitoring and controlling the swarm."""

import asyncio
import json
import logging
import os
import signal
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .database import TaskDatabase

logger = logging.getLogger(__name__)


class DashboardServer:
    """FastAPI server for swarm dashboard."""

    def __init__(self, db_path: Path, static_dir: Optional[Path] = None):
        self.db_path = db_path
        self.db = TaskDatabase(db_path)
        self.app = FastAPI(title="Amplifier Swarm Dashboard")

        # WebSocket connections for real-time updates
        self.active_connections: list[WebSocket] = []

        # Static files
        if static_dir is None:
            static_dir = Path(__file__).parent.parent.parent / "static"
        self.static_dir = static_dir

        # Set up routes
        self._setup_routes()

        # Background task for broadcasting updates
        self.update_task: Optional[asyncio.Task] = None

    def _setup_routes(self):
        """Set up API routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """Serve the dashboard HTML."""
            html_path = self.static_dir / "dashboard.html"
            if html_path.exists():
                return HTMLResponse(content=html_path.read_text())
            return HTMLResponse("<h1>Dashboard</h1><p>Static files not found</p>")

        @self.app.get("/api/status")
        async def get_status():
            """Get overall system status."""
            summary = self.db.get_tasks_summary()
            workers = self.db.get_all_workers()
            
            return {
                "tasks": summary,
                "workers": {
                    "total": len(workers),
                    "active": len([w for w in workers if w["status"] == "active"]),
                    "workers": workers,
                },
            }

        @self.app.get("/api/tasks")
        async def get_tasks(status: Optional[str] = None):
            """Get all tasks, optionally filtered by status."""
            tasks = self.db.get_all_tasks(status=status)
            return {"tasks": tasks}

        @self.app.get("/api/tasks/{task_id}")
        async def get_task(task_id: str):
            """Get a specific task with its execution log."""
            task = self.db.get_task(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            log = self.db.get_task_log(task_id)
            
            return {
                "task": task,
                "log": log,
            }

        @self.app.get("/api/workers")
        async def get_workers():
            """Get all workers."""
            workers = self.db.get_all_workers()
            return {"workers": workers}

        @self.app.get("/api/log")
        async def get_log(limit: int = 100):
            """Get recent log entries."""
            log = self.db.get_recent_log(limit=limit)
            return {"log": log}

        @self.app.post("/api/tasks/{task_id}/retry")
        async def retry_task(task_id: str):
            """Retry a failed task."""
            task = self.db.get_task(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            if task["status"] not in ["failed", "completed"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot retry task with status: {task['status']}"
                )
            
            # Reset task to not_started
            with self.db.connection() as conn:
                conn.execute(
                    """
                    UPDATE tasks
                    SET status = 'not_started',
                        worker_id = NULL,
                        claimed_at = NULL,
                        started_at = NULL,
                        completed_at = NULL,
                        builder_session_id = NULL,
                        validator_session_id = NULL,
                        last_error = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (task_id,),
                )
                
                self.db.log_event(
                    conn,
                    task_id=task_id,
                    worker_id=None,
                    event_type="manual_retry",
                    message="Task manually reset for retry via dashboard",
                )
            
            await self._broadcast_update()
            
            return {"success": True, "message": f"Task {task_id} reset for retry"}

        @self.app.post("/api/tasks/{task_id}/kill")
        async def kill_task_session(task_id: str):
            """Kill the Amplifier sessions for a task."""
            task = self.db.get_task(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            if task["status"] not in ["claimed", "in_progress"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot kill task with status: {task['status']}"
                )
            
            # Try to kill the Amplifier processes
            killed = []
            errors = []
            
            # Kill builder session
            if task["builder_session_id"]:
                try:
                    # TODO: Implement actual session killing
                    # For now, we'll just mark it as killed
                    killed.append(f"builder:{task['builder_session_id']}")
                except Exception as e:
                    errors.append(f"builder: {str(e)}")
            
            # Kill validator session
            if task["validator_session_id"]:
                try:
                    killed.append(f"validator:{task['validator_session_id']}")
                except Exception as e:
                    errors.append(f"validator: {str(e)}")
            
            # Mark task as failed
            self.db.fail_task(
                task_id,
                task["worker_id"],
                "Task killed via dashboard",
            )
            
            await self._broadcast_update()
            
            return {
                "success": True,
                "killed": killed,
                "errors": errors,
                "message": f"Task {task_id} killed and marked as failed",
            }

        @self.app.post("/api/emergency-stop")
        async def emergency_stop():
            """Send emergency stop signal to orchestrator."""
            # Find orchestrator process and send SIGUSR1
            try:
                # Get all workers
                workers = self.db.get_all_workers()
                
                # Set all active workers to stopping
                with self.db.connection() as conn:
                    for worker in workers:
                        if worker["status"] == "active":
                            conn.execute(
                                "UPDATE workers SET status = 'stopping' WHERE worker_id = ?",
                                (worker["worker_id"],),
                            )
                
                # Try to find and signal orchestrator process
                # This is a bit hacky - we look for the parent process of workers
                orchestrator_pid = None
                for worker in workers:
                    try:
                        import psutil
                        proc = psutil.Process(worker["pid"])
                        parent = proc.parent()
                        if parent and "amplifier-swarm" in " ".join(parent.cmdline()):
                            orchestrator_pid = parent.pid
                            break
                    except Exception:
                        pass
                
                if orchestrator_pid:
                    logger.warning(f"Sending SIGUSR1 to orchestrator (PID {orchestrator_pid})")
                    os.kill(orchestrator_pid, signal.SIGUSR1)
                    message = f"Emergency stop signal sent to orchestrator (PID {orchestrator_pid})"
                else:
                    message = "Workers marked for stopping, but could not find orchestrator process"
                
                await self._broadcast_update()
                
                return {"success": True, "message": message}
                
            except Exception as e:
                logger.error(f"Emergency stop failed: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Emergency stop failed: {str(e)}")

        @self.app.post("/api/graceful-shutdown")
        async def graceful_shutdown():
            """Send graceful shutdown signal to orchestrator."""
            try:
                workers = self.db.get_all_workers()
                
                # Find orchestrator process
                orchestrator_pid = None
                for worker in workers:
                    try:
                        import psutil
                        proc = psutil.Process(worker["pid"])
                        parent = proc.parent()
                        if parent and "amplifier-swarm" in " ".join(parent.cmdline()):
                            orchestrator_pid = parent.pid
                            break
                    except Exception:
                        pass
                
                if orchestrator_pid:
                    logger.info(f"Sending SIGTERM to orchestrator (PID {orchestrator_pid})")
                    os.kill(orchestrator_pid, signal.SIGTERM)
                    message = f"Graceful shutdown signal sent to orchestrator (PID {orchestrator_pid})"
                else:
                    message = "Could not find orchestrator process"
                
                await self._broadcast_update()
                
                return {"success": True, "message": message}
                
            except Exception as e:
                logger.error(f"Graceful shutdown failed: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Graceful shutdown failed: {str(e)}")

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                # Send initial status
                status = await get_status()
                await websocket.send_json({"type": "status", "data": status})
                
                # Keep connection alive and listen for messages
                while True:
                    # Just keep the connection alive
                    await websocket.receive_text()
                    
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.active_connections:
                    self.active_connections.remove(websocket)

    async def _broadcast_update(self):
        """Broadcast status update to all connected WebSocket clients."""
        if not self.active_connections:
            return
        
        # Get current status
        summary = self.db.get_tasks_summary()
        workers = self.db.get_all_workers()
        
        status = {
            "tasks": summary,
            "workers": {
                "total": len(workers),
                "active": len([w for w in workers if w["status"] == "active"]),
                "workers": workers,
            },
        }
        
        # Send to all connections
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json({"type": "status", "data": status})
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                dead_connections.append(connection)
        
        # Remove dead connections
        for connection in dead_connections:
            self.active_connections.remove(connection)

    async def _periodic_broadcast(self):
        """Periodically broadcast updates to connected clients."""
        while True:
            await asyncio.sleep(5)  # Update every 5 seconds
            await self._broadcast_update()

    async def start(self):
        """Start background tasks."""
        self.update_task = asyncio.create_task(self._periodic_broadcast())

    async def stop(self):
        """Stop background tasks."""
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass


def create_app(db_path: Path, static_dir: Optional[Path] = None) -> FastAPI:
    """Create and configure the FastAPI app."""
    server = DashboardServer(db_path, static_dir)
    
    @server.app.on_event("startup")
    async def startup():
        await server.start()
    
    @server.app.on_event("shutdown")
    async def shutdown():
        await server.stop()
    
    return server.app


def main():
    """Entry point for running dashboard server."""
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Amplifier Swarm Dashboard")
    parser.add_argument("--db", type=Path, required=True, help="Path to SQLite database")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    parser.add_argument("--static-dir", type=Path, help="Static files directory")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [DASHBOARD] [%(levelname)s] %(message)s",
    )

    app = create_app(args.db, args.static_dir)

    logger.info(f"Starting dashboard on http://{args.host}:{args.port}")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
