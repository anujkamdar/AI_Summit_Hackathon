from fastapi import APIRouter, HTTPException, status, File, UploadFile, Form
from typing import Optional, Annotated
from datetime import datetime
import base64
import os
import sys
import json
import tempfile
from models import Token, UserLogin
from auth import verify_password, get_password_hash, create_access_token
from database import get_db

# Add parent directory to path to import agent module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from agent import Generate_artifact
except ImportError:
    Generate_artifact = None

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=Token)
async def signup(
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    resume: UploadFile = File(...),
    work_authorization: Optional[str] = Form(None),
    location_preference: Optional[str] = Form(None),
    remote_preference: Optional[str] = Form(None),
    start_date: Optional[str] = Form(None),
    relocation: Optional[str] = Form(None),
    salary_expectation: Optional[str] = Form(None)
):
    """Register a new user with email, password, resume (required), and optional FAQ answers"""
    db = get_db()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password length
    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Validate resume is provided
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume is required for signup"
        )
    
    # Process resume
    resume_content = await resume.read()
    resume_base64 = base64.b64encode(resume_content).decode('utf-8')
    
    # Save resume temporarily for agent processing
    artifact_data = None
    artifact_id = None
    
    try:
        # Create temp file with proper extension
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(resume_content)
            temp_pdf_path = temp_file.name
        
        # Generate artifact using agent if available
        if Generate_artifact:
            try:
                artifact_json = Generate_artifact(temp_pdf_path)
                artifact_dict = json.loads(artifact_json) if isinstance(artifact_json, str) else artifact_json
                
                # Store artifact in separate collection
                artifact_doc = {
                    "user_email": email,
                    "artifact_data": artifact_dict,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                artifact_result = await db.student_artifacts.insert_one(artifact_doc)
                artifact_id = str(artifact_result.inserted_id)
                artifact_data = artifact_dict
                
            except Exception as e:
                # Log error but continue with signup
                await db.logs.insert_one({
                    "time": datetime.utcnow(),
                    "type": "error",
                    "msg": f"Failed to generate artifact for {email}: {str(e)}",
                    "user_email": email
                })
        
    finally:
        # Clean up temp file
        if 'temp_pdf_path' in locals():
            try:
                os.unlink(temp_pdf_path)
            except:
                pass
    
    # Collect FAQ answers
    faq_answers = {
        "work_authorization": work_authorization,
        "location_preference": location_preference,
        "remote_preference": remote_preference,
        "start_date": start_date,
        "relocation": relocation,
        "salary_expectation": salary_expectation
    }
    
    # Create user with FAQ answers and artifact reference
    user_data = {
        "email": email,
        "password": get_password_hash(password),
        "resume": resume_base64,
        "artifact_id": artifact_id,
        "faq_answers": faq_answers,
        "created_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_data)
    user_id = str(result.inserted_id)
    
    # Create access token
    access_token = create_access_token(data={"sub": email})
    
    # Log user registration
    await db.logs.insert_one({
        "time": datetime.utcnow(),
        "type": "success",
        "msg": f"New user registered: {email}" + (" with artifact" if artifact_id else ""),
        "user_email": email
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": email,
            "artifact_id": artifact_id,
            "has_artifact": artifact_id is not None,
            "created_at": user_data["created_at"].isoformat()
        }
    }


@router.post("/signin", response_model=Token)
async def signin(user_login: UserLogin):
    """Sign in an existing user"""
    db = get_db()
    
    # Find user
    user = await db.users.find_one({"email": user_login.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(user_login.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user["email"]})
    
    # Log successful sign in
    await db.logs.insert_one({
        "time": datetime.utcnow(),
        "type": "info",
        "msg": f"User signed in: {user['email']}",
        "user_email": user["email"]
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "email": user["email"],
            "created_at": user["created_at"].isoformat()
        }
    }


@router.get("/artifact/{user_email}")
async def get_student_artifact(user_email: str):
    """Retrieve the student artifact for a given user email"""
    db = get_db()   
    
    # Find the artifact
    artifact = await db.student_artifacts.find_one({"user_email": user_email})
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No artifact found for this user"
        )
    
    return {
        "user_email": artifact["user_email"],
        "artifact": artifact["artifact_data"],
        "created_at": artifact["created_at"].isoformat(),
        "updated_at": artifact["updated_at"].isoformat()
    }
