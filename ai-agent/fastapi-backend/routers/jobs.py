from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime
import logging
import os
from bson import ObjectId

from models import (
    RankingRequest, RankingResponse, RankedJob,
    JobQueueItem, QueueStatusResponse, JobStatus, ApplyResponse
)
from database import get_db
from auth import get_current_user
from agent import Ranking_agent, Application_agent, get_sandbox_job_by_id
from agno.knowledge.embedder.huggingface import HuggingfaceCustomEmbedder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# Initialize embedder (singleton pattern)
_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = HuggingfaceCustomEmbedder("sentence-transformers/all-MiniLM-L6-v2")
    return _embedder


@router.post("/rank", response_model=RankingResponse, status_code=status.HTTP_200_OK)
async def rank_jobs_for_user(
    request: RankingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Rank jobs based on user's artifact using vector similarity search.
    Uses the Ranking_agent to find top matching jobs from MongoDB.
    Automatically uses the latest artifact from the logged-in user.
    """
    try:
        db = get_db()
        user_email = current_user["email"]
        
        # Fetch user's latest artifact
        artifact_doc = await db.student_artifacts.find_one(
            {"user_email": user_email},
            sort=[("created_at", -1)]
        )
        
        if not artifact_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No artifact found for user. Please upload resume first."
            )
        
        student_artifact = artifact_doc.get("artifact_data", {})
        
        # Get MongoDB connection string from environment
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="MongoDB URI not configured"
            )
        
        # Get embedder
        embedder = get_embedder()
        
        # Call ranking agent
        logger.info(f"Ranking jobs for user: {user_email}")
        search_results = Ranking_agent(
            mdb_connection_string=mongo_uri,
            student_artifact=student_artifact,
            embedder=embedder
        )
        
        # Transform results to ranked jobs
        ranked_jobs = []
        
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
        
        for idx, result in enumerate(search_results[:request.max_results]):
            # Ranking_agent returns list of dicts with 'id' and 'score' keys
            try:
                # Extract job_id and score from result dict
                if isinstance(result, dict):
                    job_id = result.get("id")
                    # Score is already a similarity score (0-1), convert to percentage
                    match_score = result.get("score", 0.5) * 100
                else:
                    logger.warning(f"Unknown result type: {type(result)}")
                    continue
                
                if not job_id:
                    logger.warning(f"Skipping result without valid job ID")
                    continue
                
                # Fetch the actual job document from sandbox database
                job_doc = get_sandbox_job_by_id(job_id)
                
                if not job_doc:
                    logger.warning(f"Job {job_id} not found in database")
                    continue
                
                required_skills = job_doc.get("requiredSkills", [])
                matched_skills = list(set(required_skills) & student_skills)
                
                # Use position-based scoring as fallback (earlier results are more relevant)
                if match_score == 0:
                    match_score = max(10, 100 - (idx * 2))
                
                ranked_job = RankedJob(
                    job_id=str(job_doc.get("_id", "")),
                    title=job_doc.get("title", "Unknown"),
                    company=job_doc.get("company", "Unknown"),
                    location=job_doc.get("location", "Unknown"),
                    match_score=round(match_score, 2),
                    matched_skills=matched_skills,
                    description=job_doc.get("description", ""),
                    salary=job_doc.get("salary")
                )
                ranked_jobs.append(ranked_job)
            except Exception as e:
                logger.warning(f"Failed to process job result: {str(e)}")
                continue
        
        response = RankingResponse(
            user_email=user_email,
            ranked_jobs=ranked_jobs,
            total_jobs=len(ranked_jobs),
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"Successfully ranked {len(ranked_jobs)} jobs for user {user_email}")
        return response
        
    except Exception as e:
        logger.error(f"Error ranking jobs: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rank jobs: {str(e)}"
        )


@router.post("/queue/add", status_code=status.HTTP_201_CREATED)
async def add_job_to_queue(
    job_id: str,
    match_score: float,
    current_user: dict = Depends(get_current_user)
):
    """
    Add a job to user's application queue.
    """
    try:
        db = get_db()
        
        # Fetch job details from sandbox database
        job_doc = get_sandbox_job_by_id(job_id)
        if not job_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Check if already in queue
        existing = await db.job_queue.find_one({
            "user_email": current_user["email"],
            "job_id": job_id
        })
        
        if existing:
            return {
                "message": "Job already in queue",
                "queue_item_id": str(existing["_id"])
            }
        
        # Create queue item
        queue_item = {
            "user_email": current_user["email"],
            "job_id": job_id,
            "job_title": job_doc.get("title", ""),
            "company": job_doc.get("company", ""),
            "match_score": match_score,
            "status": JobStatus.IN_PROGRESS.value,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "cover_letter": None,
            "error_message": None
        }
        
        result = await db.job_queue.insert_one(queue_item)
        
        logger.info(f"Added job {job_id} to queue for user {current_user['email']}")
        
        return {
            "message": "Job added to queue successfully",
            "queue_item_id": str(result.inserted_id)
        }
        
    except Exception as e:
        logger.error(f"Error adding job to queue: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add job to queue: {str(e)}"
        )


@router.post("/queue/add-batch", status_code=status.HTTP_201_CREATED)
async def add_multiple_jobs_to_queue(
    jobs: List[dict],  # List of {job_id, match_score}
    current_user: dict = Depends(get_current_user)
):
    """
    Add multiple jobs to queue at once.
    Expected format: [{"job_id": "xxx", "match_score": 85.5}, ...]
    """
    try:
        db = get_db()
        added_count = 0
        skipped_count = 0
        
        for job_item in jobs:
            job_id = job_item.get("job_id")
            match_score = job_item.get("match_score", 0)
            
            if not job_id:
                continue
            
            # Check if already in queue
            existing = await db.job_queue.find_one({
                "user_email": current_user["email"],
                "job_id": job_id
            })
            
            if existing:
                skipped_count += 1
                continue
            
            # Fetch job details from sandbox database
            job_doc = get_sandbox_job_by_id(job_id)
            if not job_doc:
                skipped_count += 1
                continue
            
            # Create queue item
            queue_item = {
                "user_email": current_user["email"],
                "job_id": job_id,
                "job_title": job_doc.get("title", ""),
                "company": job_doc.get("company", ""),
                "match_score": match_score,
                "status": JobStatus.IN_PROGRESS.value,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "cover_letter": None,
                "error_message": None
            }
            
            await db.job_queue.insert_one(queue_item)
            added_count += 1
        
        logger.info(f"Added {added_count} jobs to queue for user {current_user['email']}")
        
        return {
            "message": "Batch operation completed",
            "added": added_count,
            "skipped": skipped_count
        }
        
    except Exception as e:
        logger.error(f"Error adding jobs to queue: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add jobs to queue: {str(e)}"
        )


@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's job queue status and items.
    """
    try:
        db = get_db()
        
        # Fetch all queue items for user
        cursor = db.job_queue.find({"user_email": current_user["email"]})
        queue_items = await cursor.to_list(length=None)
        
        # Convert to models
        jobs = []
        status_counts = {}
        
        for item in queue_items:
            queue_item = JobQueueItem(
                id=str(item["_id"]),
                user_email=item["user_email"],
                job_id=item["job_id"],
                job_title=item["job_title"],
                company=item["company"],
                match_score=item["match_score"],
                status=JobStatus(item["status"]),
                created_at=item.get("created_at"),
                updated_at=item.get("updated_at"),
                cover_letter=item.get("cover_letter"),
                error_message=item.get("error_message")
            )
            jobs.append(queue_item)
            
            # Count by status
            status_key = item["status"]
            status_counts[status_key] = status_counts.get(status_key, 0) + 1
        
        response = QueueStatusResponse(
            user_email=current_user["email"],
            total_in_queue=len(jobs),
            by_status=status_counts,
            jobs=jobs
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error fetching queue status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch queue status: {str(e)}"
        )


@router.delete("/queue/{queue_item_id}", status_code=status.HTTP_200_OK)
async def remove_from_queue(
    queue_item_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Remove a job from the application queue.
    """
    try:
        db = get_db()
        
        # Verify ownership
        item = await db.job_queue.find_one({"_id": ObjectId(queue_item_id)})
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Queue item not found"
            )
        
        if item["user_email"] != current_user["email"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot remove another user's queue item"
            )
        
        # Delete
        await db.job_queue.delete_one({"_id": ObjectId(queue_item_id)})
        
        logger.info(f"Removed queue item {queue_item_id} for user {current_user['email']}")
        
        return {"message": "Job removed from queue successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from queue: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove from queue: {str(e)}"
        )


@router.patch("/queue/{queue_item_id}/status", status_code=status.HTTP_200_OK)
async def update_queue_item_status(
    queue_item_id: str,
    new_status: JobStatus,
    error_message: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Update status of a queue item (for manual management or future automation).
    """
    try:
        db = get_db()
        
        # Verify ownership
        item = await db.job_queue.find_one({"_id": ObjectId(queue_item_id)})
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Queue item not found"
            )
        
        if item["user_email"] != current_user["email"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update another user's queue item"
            )
        
        # Update
        update_data = {
            "status": new_status.value,
            "updated_at": datetime.utcnow()
        }
        
        if error_message:
            update_data["error_message"] = error_message
        
        await db.job_queue.update_one(
            {"_id": ObjectId(queue_item_id)},
            {"$set": update_data}
        )
        
        logger.info(f"Updated queue item {queue_item_id} status to {new_status.value}")
        
        return {"message": "Queue item status updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating queue item: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update queue item: {str(e)}"
        )


@router.post("/queue/{queue_item_id}/apply", response_model=ApplyResponse, status_code=status.HTTP_200_OK)
async def apply_to_job(
    queue_item_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Apply to a job by generating a tailored cover letter using the Application Agent.
    
    This endpoint:
    1. Fetches the job details and user's artifact
    2. Calls Application_agent to generate a personalized cover letter
    3. Updates the queue item with the cover letter and status
    4. Returns the generated cover letter and application status
    """
    try:
        db = get_db()
        user_email = current_user["email"]
        
        # Fetch queue item and verify ownership
        queue_item = await db.job_queue.find_one({"_id": ObjectId(queue_item_id)})
        if not queue_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Queue item not found"
            )
        
        if queue_item["user_email"] != user_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot apply on behalf of another user"
            )
        
        # Check if already applied
        if queue_item.get("status") == JobStatus.SUBMITTED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already applied to this job"
            )
        
        # Update status to APPLYING
        await db.job_queue.update_one(
            {"_id": ObjectId(queue_item_id)},
            {"$set": {"status": JobStatus.APPLYING.value, "updated_at": datetime.utcnow()}}
        )
        
        # Fetch the full job listing from sandbox database
        job_id = queue_item["job_id"]
        job_doc = get_sandbox_job_by_id(job_id)
        if not job_doc:
            # Update status to FAILED
            await db.job_queue.update_one(
                {"_id": ObjectId(queue_item_id)},
                {"$set": {
                    "status": JobStatus.FAILED.value,
                    "error_message": "Job listing not found",
                    "updated_at": datetime.utcnow()
                }}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job listing not found"
            )
        
        # Fetch user's artifact
        artifact_doc = await db.student_artifacts.find_one(
            {"user_email": user_email},
            sort=[("created_at", -1)]
        )
        
        if not artifact_doc:
            await db.job_queue.update_one(
                {"_id": ObjectId(queue_item_id)},
                {"$set": {
                    "status": JobStatus.FAILED.value,
                    "error_message": "User artifact not found. Please upload resume first.",
                    "updated_at": datetime.utcnow()
                }}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User artifact not found. Please upload resume first."
            )
        
        student_artifact = artifact_doc.get("artifact_data", {})
        
        # Prepare job listing for the agent
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
        
        logger.info(f"Generating cover letter for job {job_id} for user {user_email}")
        
        try:
            # Call Application_agent to generate cover letter
            cover_letter = Application_agent(job_listing, student_artifact)
            
            # Update queue item with cover letter and SUBMITTED status
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
            
            logger.info(f"Successfully applied to job {job_id} for user {user_email}")
            
            return ApplyResponse(
                queue_item_id=queue_item_id,
                job_id=job_id,
                job_title=job_listing["title"],
                company=job_listing["company"],
                status=JobStatus.SUBMITTED,
                cover_letter=cover_letter,
                message="Successfully generated cover letter and applied to job",
                applied_at=applied_at
            )
            
        except Exception as agent_error:
            # Application agent failed - update status to FAILED
            error_msg = f"Cover letter generation failed: {str(agent_error)}"
            logger.error(error_msg)
            
            await db.job_queue.update_one(
                {"_id": ObjectId(queue_item_id)},
                {"$set": {
                    "status": JobStatus.FAILED.value,
                    "error_message": error_msg,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying to job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply to job: {str(e)}"
        )


@router.post("/queue/apply-batch", status_code=status.HTTP_200_OK)
async def apply_to_multiple_jobs(
    queue_item_ids: List[str],
    current_user: dict = Depends(get_current_user)
):
    """
    Apply to multiple jobs in the queue.
    Generates cover letters for each job using the Application Agent.
    
    Returns summary of successful and failed applications.
    """
    try:
        db = get_db()
        user_email = current_user["email"]
        
        # Fetch user's artifact once
        artifact_doc = await db.student_artifacts.find_one(
            {"user_email": user_email},
            sort=[("created_at", -1)]
        )
        
        if not artifact_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User artifact not found. Please upload resume first."
            )
        
        student_artifact = artifact_doc.get("artifact_data", {})
        
        results = {
            "successful": [],
            "failed": [],
            "skipped": []
        }
        
        for queue_item_id in queue_item_ids:
            try:
                # Fetch queue item and verify ownership
                queue_item = await db.job_queue.find_one({"_id": ObjectId(queue_item_id)})
                
                if not queue_item:
                    results["failed"].append({
                        "queue_item_id": queue_item_id,
                        "error": "Queue item not found"
                    })
                    continue
                
                if queue_item["user_email"] != user_email:
                    results["failed"].append({
                        "queue_item_id": queue_item_id,
                        "error": "Cannot apply on behalf of another user"
                    })
                    continue
                
                # Skip already submitted jobs
                if queue_item.get("status") == JobStatus.SUBMITTED.value:
                    results["skipped"].append({
                        "queue_item_id": queue_item_id,
                        "job_title": queue_item.get("job_title", "Unknown"),
                        "reason": "Already applied"
                    })
                    continue
                
                # Fetch job listing from sandbox database
                job_id = queue_item["job_id"]
                job_doc = get_sandbox_job_by_id(job_id)
                
                if not job_doc:
                    await db.job_queue.update_one(
                        {"_id": ObjectId(queue_item_id)},
                        {"$set": {
                            "status": JobStatus.FAILED.value,
                            "error_message": "Job listing not found",
                            "updated_at": datetime.utcnow()
                        }}
                    )
                    results["failed"].append({
                        "queue_item_id": queue_item_id,
                        "error": "Job listing not found"
                    })
                    continue
                
                # Update status to APPLYING
                await db.job_queue.update_one(
                    {"_id": ObjectId(queue_item_id)},
                    {"$set": {"status": JobStatus.APPLYING.value, "updated_at": datetime.utcnow()}}
                )
                
                # Prepare job listing for agent
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
                
                results["successful"].append({
                    "queue_item_id": queue_item_id,
                    "job_id": job_id,
                    "job_title": job_listing["title"],
                    "company": job_listing["company"]
                })
                
                logger.info(f"Applied to job {job_id} for user {user_email}")
                
            except Exception as item_error:
                error_msg = str(item_error)
                logger.error(f"Failed to apply to queue item {queue_item_id}: {error_msg}")
                
                # Update status to FAILED
                await db.job_queue.update_one(
                    {"_id": ObjectId(queue_item_id)},
                    {"$set": {
                        "status": JobStatus.FAILED.value,
                        "error_message": error_msg,
                        "updated_at": datetime.utcnow()
                    }}
                )
                
                results["failed"].append({
                    "queue_item_id": queue_item_id,
                    "error": error_msg
                })
        
        return {
            "message": "Batch application completed",
            "total_processed": len(queue_item_ids),
            "successful_count": len(results["successful"]),
            "failed_count": len(results["failed"]),
            "skipped_count": len(results["skipped"]),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch application: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process batch application: {str(e)}"
        )
