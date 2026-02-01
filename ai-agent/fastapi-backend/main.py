from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
import logging
from jose import jwt, JWTError
import os
from dotenv import load_dotenv

from database import connect_db, disconnect_db, get_db
from routers import auth, users, jobs
from routers.auto_apply import router as auto_apply_router
from websocket_manager import manager, create_log_message
from auth import SECRET_KEY, ALGORITHM

load_dotenv()
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(title="Job Application Tracker API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(auto_apply_router)


# ============== DATABASE LIFECYCLE ==============

@app.on_event("startup")
async def startup_db():
    await connect_db()


@app.on_event("shutdown")
async def shutdown_db():
    await disconnect_db()

# ============== API ENDPOINTS ==============

@app.get("/")
async def root():
    return {"message": "Job Application Tracker API - Running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = get_db()
        return {
            "status": "healthy",
            "database": "connected" if db is not None else "disconnected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e)
        }


# ============== WEBSOCKET ENDPOINTS ==============

def get_user_from_token(token: str) -> dict:
    """Validate JWT token and return user info"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"email": payload.get("sub"), "valid": True}
    except JWTError as e:
        return {"valid": False, "error": str(e)}


@app.websocket("/ws/dashboard")
async def websocket_dashboard(
    websocket: WebSocket,
    token: str = Query(None)
):
    """
    WebSocket endpoint for real-time dashboard updates.
    
    Connect with: ws://localhost:8000/ws/dashboard?token=<your_jwt_token>
    
    Message types received:
    - log: Real-time log messages
    - queue_update: Job queue updates
    - status_update: Agent status updates
    - job_update: Individual job status changes
    - process_update: Progress updates during auto-apply
    """
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return
    
    user_info = get_user_from_token(token)
    if not user_info.get("valid"):
        await websocket.close(code=4002, reason=user_info.get("error", "Invalid token"))
        return
    
    user_email = user_info["email"]
    
    await manager.connect(websocket, user_email)
    
    try:
        # Send initial connection success message
        await manager.send_personal_message(
            create_log_message("success", "🔗 Connected to dashboard"),
            user_email
        )
        
        # Send initial queue state
        db = get_db()
        if db is not None:
            cursor = db.job_queue.find({"user_email": user_email})
            queue_items = await cursor.to_list(length=None)
            await websocket.send_json({
                "type": "queue_update",
                "queue": [{
                    "id": str(item["_id"]),
                    "name": f"{item['job_title']} @ {item['company']}",
                    "status": item["status"],
                    "match_score": item.get("match_score", 0)
                } for item in queue_items]
            })
            
            # Send initial status
            status_counts = {}
            for item in queue_items:
                s = item.get("status", "UNKNOWN")
                status_counts[s] = status_counts.get(s, 0) + 1
            
            await websocket.send_json({
                "type": "status_update",
                "status": {
                    "agentStatus": "idle",
                    "connected": True,
                    "tasksCompleted": status_counts.get("SUBMITTED", 0),
                    "tasksInProgress": status_counts.get("APPLYING", 0) + status_counts.get("IN_PROGRESS", 0)
                }
            })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                # Handle ping/pong for keepalive
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except Exception:
                # Continue listening even if message parsing fails
                pass
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {user_email}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_email}: {e}")
    finally:
        await manager.disconnect(websocket, user_email)

