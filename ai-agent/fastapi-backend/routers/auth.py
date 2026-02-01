from fastapi import APIRouter, HTTPException, status, File, UploadFile, Form
from typing import Optional, Annotated
from datetime import datetime
import base64
from models import Token, UserLogin
from auth import verify_password, get_password_hash, create_access_token
from database import get_db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=Token)
async def signup(
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    resume: Optional[UploadFile] = File(None)
):
    """Register a new user with email, password, and optional resume"""
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
    
    # Process resume if provided
    resume_data = None
    if resume:
        # Read and encode resume as base64
        resume_content = await resume.read()
        resume_data = base64.b64encode(resume_content).decode('utf-8')
    
    # Create user
    user_data = {
        "email": email,
        "password": get_password_hash(password),
        "resume": resume_data,
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
        "msg": f"New user registered: {email}",
        "user_email": email
    })
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_id,
            "email": email,
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
