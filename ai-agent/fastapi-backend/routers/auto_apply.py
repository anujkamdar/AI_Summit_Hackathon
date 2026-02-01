"""
Auto-Apply Router
Handles the complete job ranking and auto-apply workflow with WebSocket streaming
"""

from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from typing import List, Optional
from datetime import datetime
import logging
import asyncio
import os
from bson import ObjectId

from models import JobStatus, RankedJob
from database import get_db
from auth import get_current_user
from agent import Ranking_agent, Application_agent, get_sandbox_job_by_id
from agno.knowledge.embedder.huggingface import HuggingfaceCustomEmbedder
from websocket_manager import (
    manager, 
    create_log_message, 
    create_queue_update, 
    create_status_update,
    create_job_update,
    create_process_update
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auto-apply", tags=["auto-apply"])

# Initialize embedder (singleton pattern)
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = HuggingfaceCustomEmbedder("sentence-transformers/all-MiniLM-L6-v2")
    return _embedder


# ============== AUTO-APPLY WORKFLOW ==============

async def run_auto_apply_workflow(
    user_email: str,
    max_jobs: int = 10,
    auto_apply: bool = True
):
    """
    Complete workflow: Rank jobs → Add to queue → Auto-apply
    Streams progress via WebSocket
    """
    db = get_db()
    
    try:
        # ===== PHASE 1: INITIALIZATION =====
        await manager.send_personal_message(
            create_log_message("info", "🚀 Starting Auto-Apply workflow..."),
            user_email
        )
        await manager.send_personal_message(
            create_status_update({"agentStatus": "running", "currentPhase": "initializing"}),
            user_email
        )
        
        # Fetch user's artifact
        artifact_doc = await db.student_artifacts.find_one(
            {"user_email": user_email},
            sort=[("created_at", -1)]
        )
        
        if not artifact_doc:
            await manager.send_personal_message(
                create_log_message("error", "❌ No resume artifact found. Please upload your resume first."),
                user_email
            )
            await manager.send_personal_message(
                create_status_update({"agentStatus": "error", "currentPhase": "failed"}),
                user_email
            )
            return {"success": False, "error": "No artifact found"}
        
        student_artifact = artifact_doc.get("artifact_data", {})
        await manager.send_personal_message(
            create_log_message("success", "✅ Resume artifact loaded successfully"),
            user_email
        )
        
        # ===== PHASE 2: RANKING JOBS =====
        await manager.send_personal_message(
            create_log_message("info", "🔍 Ranking jobs based on your profile..."),
            user_email
        )
        await manager.send_personal_message(
            create_status_update({"agentStatus": "running", "currentPhase": "ranking"}),
            user_email
        )
        await manager.send_personal_message(
            create_process_update("ranking", 0, max_jobs, {"message": "Analyzing job listings..."}),
            user_email
        )
        
        # Get embedder and run ranking
        embedder = get_embedder()
        mongo_uri = os.getenv("MONGO_URI")
        
        search_results = Ranking_agent(
            mdb_connection_string=mongo_uri,
            student_artifact=student_artifact,
            embedder=embedder
        )
        
        # Extract student skills for matching
        student_skills = set()
        if "student_profile" in student_artifact:
            profile = student_artifact["student_profile"]
            if "skills" in profile:
                skills_obj = profile["skills"]
                student_skills.update(skills_obj.get("languages", []))
                student_skills.update(skills_obj.get("frameworks", []))
                student_skills.update(skills_obj.get("tools", []))
                student_skills.update(skills_obj.get("other", []))
        
        # Process ranked jobs
        ranked_jobs = []
        for idx, result in enumerate(search_results[:max_jobs]):
            try:
                if isinstance(result, dict):
                    job_id = result.get("id")
                    match_score = result.get("score", 0.5) * 100
                else:
                    continue
                
                if not job_id:
                    continue
                
                job_doc = get_sandbox_job_by_id(job_id)
                if not job_doc:
                    continue
                
                required_skills = job_doc.get("requiredSkills", [])
                matched_skills = list(set(required_skills) & student_skills)
                
                if match_score == 0:
                    match_score = max(10, 100 - (idx * 2))
                
                ranked_job = {
                    "job_id": str(job_doc.get("_id", "")),
                    "title": job_doc.get("title", "Unknown"),
                    "company": job_doc.get("company", "Unknown"),
                    "location": job_doc.get("location", "Unknown"),
                    "match_score": round(match_score, 2),
                    "matched_skills": matched_skills,
                    "description": job_doc.get("description", "")[:200] + "...",
                    "salary": job_doc.get("salary")
                }
                ranked_jobs.append(ranked_job)
                
                # Stream each ranked job
                await manager.send_personal_message(
                    create_job_update(ranked_job, "ranked"),
                    user_email
                )
                await manager.send_personal_message(
                    create_process_update("ranking", idx + 1, max_jobs, {
                        "message": f"Ranked: {ranked_job['title']} at {ranked_job['company']} ({ranked_job['match_score']:.1f}%)"
                    }),
                    user_email
                )
                await manager.send_personal_message(
                    create_log_message("info", f"📊 Ranked #{idx+1}: {ranked_job['title']} @ {ranked_job['company']} - {ranked_job['match_score']:.1f}% match"),
                    user_email
                )
                
            except Exception as e:
                logger.warning(f"Failed to process job: {e}")
                continue
        
        await manager.send_personal_message(
            create_log_message("success", f"✅ Found {len(ranked_jobs)} matching jobs"),
            user_email
        )
        
        if not ranked_jobs:
            await manager.send_personal_message(
                create_log_message("warning", "⚠️ No matching jobs found"),
                user_email
            )
            await manager.send_personal_message(
                create_status_update({"agentStatus": "idle", "currentPhase": "completed"}),
                user_email
            )
            return {"success": True, "ranked_jobs": [], "applied_jobs": []}
        
        # ===== PHASE 3: ADD TO QUEUE =====
        await manager.send_personal_message(
            create_log_message("info", "📝 Adding jobs to application queue..."),
            user_email
        )
        await manager.send_personal_message(
            create_status_update({"agentStatus": "running", "currentPhase": "queuing"}),
            user_email
        )
        
        queue_items = []
        for idx, job in enumerate(ranked_jobs):
            try:
                # Check if already in queue
                existing = await db.job_queue.find_one({
                    "user_email": user_email,
                    "job_id": job["job_id"]
                })
                
                if existing:
                    queue_items.append({
                        "queue_item_id": str(existing["_id"]),
                        "job_id": job["job_id"],
                        "title": job["title"],
                        "company": job["company"],
                        "match_score": job["match_score"],
                        "status": existing.get("status", "IN_PROGRESS"),
                        "existing": True
                    })
                    await manager.send_personal_message(
                        create_log_message("info", f"ℹ️ {job['title']} @ {job['company']} already in queue"),
                        user_email
                    )
                    continue
                
                # Create queue item
                queue_item = {
                    "user_email": user_email,
                    "job_id": job["job_id"],
                    "job_title": job["title"],
                    "company": job["company"],
                    "match_score": job["match_score"],
                    "status": JobStatus.IN_PROGRESS.value,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "cover_letter": None,
                    "error_message": None
                }
                
                result = await db.job_queue.insert_one(queue_item)
                queue_items.append({
                    "queue_item_id": str(result.inserted_id),
                    "job_id": job["job_id"],
                    "title": job["title"],
                    "company": job["company"],
                    "match_score": job["match_score"],
                    "status": "IN_PROGRESS",
                    "existing": False
                })
                
                await manager.send_personal_message(
                    create_log_message("success", f"➕ Added to queue: {job['title']} @ {job['company']}"),
                    user_email
                )
                await manager.send_personal_message(
                    create_process_update("queuing", idx + 1, len(ranked_jobs)),
                    user_email
                )
                
            except Exception as e:
                logger.error(f"Failed to add job to queue: {e}")
                await manager.send_personal_message(
                    create_log_message("error", f"❌ Failed to queue: {job['title']} - {str(e)}"),
                    user_email
                )
        
        # Send queue update
        await manager.send_personal_message(
            create_queue_update([{
                "id": item["queue_item_id"],
                "name": f"{item['title']} @ {item['company']}",
                "status": item["status"],
                "match_score": item["match_score"]
            } for item in queue_items]),
            user_email
        )
        
        if not auto_apply:
            await manager.send_personal_message(
                create_log_message("success", f"✅ Added {len(queue_items)} jobs to queue. Auto-apply disabled."),
                user_email
            )
            await manager.send_personal_message(
                create_status_update({"agentStatus": "idle", "currentPhase": "completed"}),
                user_email
            )
            return {"success": True, "ranked_jobs": ranked_jobs, "queue_items": queue_items}
        
        # ===== PHASE 4: AUTO-APPLY =====
        await manager.send_personal_message(
            create_log_message("info", "🤖 Starting auto-apply process..."),
            user_email
        )
        await manager.send_personal_message(
            create_status_update({"agentStatus": "running", "currentPhase": "applying"}),
            user_email
        )
        
        applied_jobs = []
        failed_jobs = []
        
        # Filter items that need applying (not already submitted)
        items_to_apply = [item for item in queue_items if not item.get("existing") or item.get("status") != "SUBMITTED"]
        
        for idx, item in enumerate(items_to_apply):
            queue_item_id = item["queue_item_id"]
            job_id = item["job_id"]
            
            try:
                await manager.send_personal_message(
                    create_log_message("info", f"📝 Applying to: {item['title']} @ {item['company']}..."),
                    user_email
                )
                await manager.send_personal_message(
                    create_process_update("applying", idx + 1, len(items_to_apply), {
                        "current_job": f"{item['title']} @ {item['company']}"
                    }),
                    user_email
                )
                
                # Update status to APPLYING
                await db.job_queue.update_one(
                    {"_id": ObjectId(queue_item_id)},
                    {"$set": {"status": JobStatus.APPLYING.value, "updated_at": datetime.utcnow()}}
                )
                
                # Fetch full job doc
                job_doc = get_sandbox_job_by_id(job_id)
                if not job_doc:
                    raise Exception("Job listing not found")
                
                job_listing = {
                    "_id": str(job_doc.get("_id", "")),
                    "title": job_doc.get("title", ""),
                    "company": job_doc.get("company", ""),
                    "location": job_doc.get("location", ""),
                    "type": job_doc.get("type", "Full-time"),
                    "salary": job_doc.get("salary"),
                    "description": job_doc.get("description", ""),
                    "requiredSkills": job_doc.get("requiredSkills", []),
                    "visa_sponsorship": job_doc.get("visa_sponsorship", False)
                }
                
                await manager.send_personal_message(
                    create_log_message("info", f"✍️ Generating tailored cover letter..."),
                    user_email
                )
                
                # Generate cover letter
                cover_letter = Application_agent(job_listing, student_artifact)
                
                # Update to SUBMITTED
                applied_at = datetime.utcnow()
                await db.job_queue.update_one(
                    {"_id": ObjectId(queue_item_id)},
                    {"$set": {
                        "status": JobStatus.SUBMITTED.value,
                        "cover_letter": cover_letter,
                        "updated_at": applied_at,
                        "error_message": None
                    }}
                )
                
                applied_jobs.append({
                    "queue_item_id": queue_item_id,
                    "job_id": job_id,
                    "title": item["title"],
                    "company": item["company"],
                    "cover_letter_preview": cover_letter[:200] + "..." if len(cover_letter) > 200 else cover_letter
                })
                
                await manager.send_personal_message(
                    create_job_update({
                        "queue_item_id": queue_item_id,
                        "job_id": job_id,
                        "title": item["title"],
                        "company": item["company"],
                        "status": "SUBMITTED"
                    }, "applied"),
                    user_email
                )
                await manager.send_personal_message(
                    create_log_message("success", f"✅ Successfully applied to: {item['title']} @ {item['company']}"),
                    user_email
                )
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to apply to {item['title']}: {error_msg}")
                
                await db.job_queue.update_one(
                    {"_id": ObjectId(queue_item_id)},
                    {"$set": {
                        "status": JobStatus.FAILED.value,
                        "error_message": error_msg,
                        "updated_at": datetime.utcnow()
                    }}
                )
                
                failed_jobs.append({
                    "queue_item_id": queue_item_id,
                    "job_id": job_id,
                    "title": item["title"],
                    "company": item["company"],
                    "error": error_msg
                })
                
                await manager.send_personal_message(
                    create_job_update({
                        "queue_item_id": queue_item_id,
                        "job_id": job_id,
                        "title": item["title"],
                        "company": item["company"],
                        "status": "FAILED",
                        "error": error_msg
                    }, "failed"),
                    user_email
                )
                await manager.send_personal_message(
                    create_log_message("error", f"❌ Failed to apply: {item['title']} @ {item['company']} - {error_msg}"),
                    user_email
                )
        
        # ===== PHASE 5: COMPLETION =====
        await manager.send_personal_message(
            create_log_message("success", f"🎉 Auto-apply complete! Applied: {len(applied_jobs)}, Failed: {len(failed_jobs)}"),
            user_email
        )
        await manager.send_personal_message(
            create_status_update({
                "agentStatus": "idle",
                "currentPhase": "completed",
                "tasksCompleted": len(applied_jobs),
                "tasksFailed": len(failed_jobs)
            }),
            user_email
        )
        await manager.send_personal_message(
            create_process_update("completed", len(items_to_apply), len(items_to_apply), {
                "applied": len(applied_jobs),
                "failed": len(failed_jobs)
            }),
            user_email
        )
        
        # Final queue update
        cursor = db.job_queue.find({"user_email": user_email})
        final_queue = await cursor.to_list(length=None)
        await manager.send_personal_message(
            create_queue_update([{
                "id": str(item["_id"]),
                "name": f"{item['job_title']} @ {item['company']}",
                "status": item["status"],
                "match_score": item.get("match_score", 0)
            } for item in final_queue]),
            user_email
        )
        
        return {
            "success": True,
            "ranked_jobs": ranked_jobs,
            "applied_jobs": applied_jobs,
            "failed_jobs": failed_jobs,
            "summary": {
                "total_ranked": len(ranked_jobs),
                "total_applied": len(applied_jobs),
                "total_failed": len(failed_jobs)
            }
        }
        
    except Exception as e:
        logger.error(f"Auto-apply workflow error: {str(e)}", exc_info=True)
        await manager.send_personal_message(
            create_log_message("error", f"❌ Workflow failed: {str(e)}"),
            user_email
        )
        await manager.send_personal_message(
            create_status_update({"agentStatus": "error", "currentPhase": "failed"}),
            user_email
        )
        return {"success": False, "error": str(e)}


# ============== API ENDPOINTS ==============

@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def start_auto_apply(
    background_tasks: BackgroundTasks,
    max_jobs: int = 10,
    auto_apply: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """
    Start the auto-apply workflow.
    
    This endpoint:
    1. Ranks jobs based on user's artifact
    2. Adds top jobs to the application queue
    3. Auto-applies to each job (generates cover letters)
    4. Streams progress via WebSocket
    
    Parameters:
    - max_jobs: Maximum number of jobs to process (default: 10)
    - auto_apply: Whether to auto-apply or just rank (default: True)
    """
    user_email = current_user["email"]
    
    # Check if user has an artifact
    db = get_db()
    artifact = await db.student_artifacts.find_one({"user_email": user_email})
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No resume artifact found. Please upload your resume first."
        )
    
    # Start the workflow in background
    background_tasks.add_task(
        run_auto_apply_workflow,
        user_email=user_email,
        max_jobs=max_jobs,
        auto_apply=auto_apply
    )
    
    return {
        "message": "Auto-apply workflow started",
        "user_email": user_email,
        "max_jobs": max_jobs,
        "auto_apply": auto_apply,
        "status": "Connect to WebSocket for real-time updates"
    }


@router.get("/status", status_code=status.HTTP_200_OK)
async def get_workflow_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get current workflow status and queue summary.
    """
    db = get_db()
    user_email = current_user["email"]
    
    # Get queue stats
    cursor = db.job_queue.find({"user_email": user_email})
    queue_items = await cursor.to_list(length=None)
    
    status_counts = {}
    for item in queue_items:
        s = item.get("status", "UNKNOWN")
        status_counts[s] = status_counts.get(s, 0) + 1
    
    return {
        "user_email": user_email,
        "total_in_queue": len(queue_items),
        "by_status": status_counts,
        "websocket_connected": manager.is_connected(user_email)
    }


@router.delete("/queue/clear", status_code=status.HTTP_200_OK)
async def clear_queue(
    current_user: dict = Depends(get_current_user)
):
    """
    Clear all jobs from user's queue.
    """
    db = get_db()
    user_email = current_user["email"]
    
    result = await db.job_queue.delete_many({"user_email": user_email})
    
    # Notify via WebSocket
    await manager.send_personal_message(
        create_queue_update([]),
        user_email
    )
    await manager.send_personal_message(
        create_log_message("info", f"🗑️ Cleared {result.deleted_count} jobs from queue"),
        user_email
    )
    
    return {
        "message": f"Cleared {result.deleted_count} jobs from queue"
    }
