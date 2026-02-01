from fastapi import APIRouter, Depends

from models import UserMetrics
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/api/user", tags=["Users"])


@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return {
        "id": str(current_user["_id"]),
        "email": current_user["email"],
        "created_at": current_user["created_at"],
        "has_resume": current_user.get("resume") is not None
    }


@router.get("/metrics", response_model=UserMetrics)
async def get_user_metrics(current_user: dict = Depends(get_current_user)):
    """Get job application metrics for the authenticated user"""
    db = get_db()
    user_email = current_user["email"]
    
    # Get all jobs for this user
    total_jobs = await db.jobs.count_documents({"user_email": user_email})
    applied_jobs = await db.jobs.count_documents({"user_email": user_email, "status": "SUBMITTED"})
    failed_jobs = await db.jobs.count_documents({"user_email": user_email, "status": "FAILED"})
    
    # Calculate success rate
    success_rate = "0%"
    if (applied_jobs + failed_jobs) > 0:
        success_rate = f"{int((applied_jobs / (applied_jobs + failed_jobs)) * 100)}%"
    
    # Get recent jobs (last 10)
    recent_jobs_cursor = db.jobs.find({"user_email": user_email}).sort("timestamp", -1).limit(10)
    recent_jobs = await recent_jobs_cursor.to_list(length=10)
    
    recent_jobs_list = []
    for job in recent_jobs:
        recent_jobs_list.append({
            "id": job.get("id"),
            "company": job.get("company"),
            "role": job.get("role"),
            "match_score": job.get("match_score"),
            "status": job.get("status"),
            "timestamp": job.get("timestamp").isoformat() if job.get("timestamp") else None
        })
    
    return {
        "user_email": user_email,
        "total_jobs": total_jobs,
        "applied_jobs": applied_jobs,
        "failed_jobs": failed_jobs,
        "success_rate": success_rate,
        "recent_jobs": recent_jobs_list
    }


@router.get("/jobs")
async def get_user_jobs(current_user: dict = Depends(get_current_user)):
    """Get all jobs for the authenticated user"""
    db = get_db()
    user_email = current_user["email"]
    
    jobs_cursor = db.jobs.find({"user_email": user_email}).sort("timestamp", -1)
    jobs = await jobs_cursor.to_list(length=None)
    
    result = []
    for job in jobs:
        result.append({
            "id": job.get("id"),
            "company": job.get("company"),
            "role": job.get("role"),
            "match_score": job.get("match_score"),
            "status": job.get("status"),
            "timestamp": job.get("timestamp")
        })
    
    return result


@router.get("/logs")
async def get_user_logs(current_user: dict = Depends(get_current_user)):
    """Get logs for the authenticated user"""
    db = get_db()
    user_email = current_user["email"]
    
    logs_cursor = db.logs.find({"user_email": user_email}).sort("time", -1).limit(50)
    logs = await logs_cursor.to_list(length=50)
    
    result = []
    for log in logs:
        result.append({
            "time": log.get("time"),
            "type": log.get("type"),
            "msg": log.get("msg")
        })
    
    return result
