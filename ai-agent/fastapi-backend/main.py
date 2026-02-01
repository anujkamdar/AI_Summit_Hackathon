from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import connect_db, disconnect_db, get_db
from routers import auth, users

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

