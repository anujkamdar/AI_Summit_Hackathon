"""
WebSocket Manager for Real-time Dashboard Updates
Handles connections, broadcasting, and user-specific messaging
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # user_email -> list of WebSocket connections (user can have multiple tabs)
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, user_email: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        async with self.lock:
            if user_email not in self.active_connections:
                self.active_connections[user_email] = []
            self.active_connections[user_email].append(websocket)
        logger.info(f"WebSocket connected for user: {user_email}")
    
    async def disconnect(self, websocket: WebSocket, user_email: str):
        """Remove a WebSocket connection"""
        async with self.lock:
            if user_email in self.active_connections:
                if websocket in self.active_connections[user_email]:
                    self.active_connections[user_email].remove(websocket)
                if not self.active_connections[user_email]:
                    del self.active_connections[user_email]
        logger.info(f"WebSocket disconnected for user: {user_email}")
    
    async def send_personal_message(self, message: dict, user_email: str):
        """Send a message to a specific user (all their connections)"""
        if user_email in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[user_email]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message to {user_email}: {e}")
                    dead_connections.append(connection)
            
            # Clean up dead connections
            for dead in dead_connections:
                await self.disconnect(dead, user_email)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected users"""
        for user_email in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_email)
    
    def is_connected(self, user_email: str) -> bool:
        """Check if a user has any active connections"""
        return user_email in self.active_connections and len(self.active_connections[user_email]) > 0


# Global connection manager instance
manager = ConnectionManager()


# ============== MESSAGE HELPERS ==============

def create_log_message(level: str, message: str, extra_data: dict = None) -> dict:
    """Create a log message for WebSocket"""
    msg = {
        "type": "log",
        "level": level,  # info, success, warning, error
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    if extra_data:
        msg.update(extra_data)
    return msg


def create_queue_update(queue: list) -> dict:
    """Create a queue update message"""
    return {
        "type": "queue_update",
        "queue": queue,
        "timestamp": datetime.utcnow().isoformat()
    }


def create_status_update(status: dict) -> dict:
    """Create a status update message"""
    return {
        "type": "status_update",
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    }


def create_job_update(job_data: dict, action: str) -> dict:
    """Create a job-specific update message"""
    return {
        "type": "job_update",
        "action": action,  # ranking, applying, completed, failed
        "job": job_data,
        "timestamp": datetime.utcnow().isoformat()
    }


def create_process_update(stage: str, progress: int, total: int, details: dict = None) -> dict:
    """Create a process progress update"""
    msg = {
        "type": "process_update",
        "stage": stage,  # ranking, adding_to_queue, applying, completed
        "progress": progress,
        "total": total,
        "percentage": round((progress / total) * 100, 1) if total > 0 else 0,
        "timestamp": datetime.utcnow().isoformat()
    }
    if details:
        msg["details"] = details
    return msg
