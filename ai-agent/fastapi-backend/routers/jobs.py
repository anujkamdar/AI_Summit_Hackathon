from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional

from database import get_db
from auth import get_current_user

router = APIRouter(prefix="/api", tags=["Jobs"])


@router.get("/jobs/queue")
async def get_jobs(current_user: dict = Depends(get_current_user)):
    """Returns all jobs for the authenticated user sorted by timestamp (newest first)"""
    db = get_db()
    user_email = current_user["email"]
    jobs_cursor = db.jobs.find({"user_email": user_email}).sort("timestamp", -1)
    jobs = await jobs_cursor.to_list(length=None)
    
    # Convert MongoDB documents to Job models
    result = []
    for job in jobs:
        job["_id"] = str(job["_id"])  # Convert ObjectId to string
        result.append({
            "id": job.get("id"),
            "company": job.get("company"),
            "role": job.get("role"),
            "match_score": job.get("match_score"),
            "status": job.get("status"),
            "timestamp": job.get("timestamp"),
            "user_email": job.get("user_email")
        })
    
    return result


@router.get("/logs")
async def get_logs(current_user: dict = Depends(get_current_user)):
    """Returns the latest 50 logs for the authenticated user"""
    db = get_db()
    user_email = current_user["email"]
    logs_cursor = db.logs.find({"user_email": user_email}).sort("time", -1).limit(50)
    logs = await logs_cursor.to_list(length=50)
    
    result = []
    for log in logs:
        log["_id"] = str(log["_id"])
        result.append({
            "time": log.get("time"),
            "type": log.get("type"),
            "msg": log.get("msg"),
            "user_email": log.get("user_email")
        })
    
    return result


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    """Returns application statistics for the authenticated user"""
    db = get_db()
    user_email = current_user["email"]
    total = await db.jobs.count_documents({"user_email": user_email})
    applied = await db.jobs.count_documents({"user_email": user_email, "status": "SUBMITTED"})
    failed = await db.jobs.count_documents({"user_email": user_email, "status": "FAILED"})
    
    success_rate = "0%"
    if total > 0:
        success_rate = f"{int((applied / (applied + failed)) * 100)}%" if (applied + failed) > 0 else "0%"
    
    return {
        "total": total,
        "applied": applied,
        "successRate": success_rate
    }



