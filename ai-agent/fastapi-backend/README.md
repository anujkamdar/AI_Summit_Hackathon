# FastAPI Backend - Modular Structure

## 📁 Project Structure

```
fastapi-backend/
├── main.py              # Main application entry point with FastAPI app initialization
├── models.py            # Pydantic models and data schemas
├── auth.py              # Authentication utilities (JWT, password hashing)
├── database.py          # MongoDB connection and database lifecycle
├── agent.py             # Background job agent simulation
├── requirements.txt     # Python dependencies
└── routers/             # API route handlers
    ├── __init__.py
    ├── auth.py          # Authentication endpoints (signup, signin)
    ├── users.py         # User-related endpoints (profile, metrics, jobs, logs)
    └── jobs.py          # Job-related endpoints (queue, stats, control, logs)
```

## 📄 File Descriptions

### **main.py**
Clean entry point that:
- Initializes FastAPI app
- Configures CORS middleware
- Includes routers from the `routers/` directory
- Manages database lifecycle (startup/shutdown)
- Starts background agent on startup
- Provides root and health check endpoints

### **models.py**
Centralized Pydantic models:
- `JobStatus`, `LogType` - Enums
- `Job`, `Log`, `Policy` - Data models
- `User`, `UserCreate`, `UserLogin`, `Token` - Authentication models
- `UserMetrics` - User statistics model

### **auth.py**
Authentication utilities:
- Password hashing with bcrypt
- JWT token creation and validation
- `get_current_user()` dependency for protected routes

### **database.py**
MongoDB configuration:
- Database connection management
- `connect_db()` - Initialize MongoDB connection
- `disconnect_db()` - Close connection
- `get_db()` - Get database instance

### **agent.py**
Background agent logic:
- `run_agent_loop()` - Simulates AI job hunting agent
- Creates new job opportunities every 5 seconds
- Processes queued jobs every 7 seconds

### **routers/auth.py**
Authentication endpoints:
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/signin` - Sign in existing user

### **routers/users.py**
User-related endpoints (all require authentication):
- `GET /api/user/me` - Get current user info
- `GET /api/user/metrics` - Get user job application metrics
- `GET /api/user/jobs` - Get all jobs for user
- `GET /api/user/logs` - Get logs for user

### **routers/jobs.py**
Job and control endpoints:
- `GET /api/jobs/queue` - Get all jobs
- `GET /api/logs` - Get system logs
- `GET /api/stats` - Get application statistics
- `POST /api/control` - Start/stop the agent

## 🚀 Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload
```

The server will run on `http://127.0.0.1:8000`

## 🔧 Environment Variables

Create a `.env` file with:
```
MONGO_URI=your_mongodb_connection_string
SECRET_KEY=your_secret_key_for_jwt
```

## 📡 API Documentation

Once the server is running, visit:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## ✨ Benefits of This Structure

1. **Separation of Concerns**: Each file has a specific responsibility
2. **Easy Maintenance**: Authentication logic is isolated in separate files
3. **Scalability**: Easy to add new routers or modify existing ones
4. **Clean main.py**: Only ~60 lines compared to 598 lines before
5. **Testability**: Individual modules can be tested in isolation
6. **Readability**: Clear organization makes it easy to find specific functionality
