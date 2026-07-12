import os
import sys
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
from jose import jwt, JWTError
from bson import ObjectId

# Add backend root to sys.path to resolve imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.config import settings
from app.database import (
    mongodb, 
    get_users_collection, 
    get_sessions_collection, 
    get_messages_collection,
    serialize_doc,
    serialize_list
)
from app.models.schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    Token,
    SessionCreate,
    SessionResponse,
    ChatRequest,
    ChatResponse,
    MessageResponse
)
from app.agents.router import process_customer_query
from app.rag.retriever import retriever

# --- Lifespan for Startup and Shutdown ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB and initialize the RAG vector index
    mongodb.connect()
    retriever.initialize()
    yield
    # Shutdown: Cleanly close MongoDB sockets
    mongodb.close()

app = FastAPI(
    title="Multi-Agent Customer Support Assistant API",
    version="1.0.0",
    lifespan=lifespan
)

# --- CORS Middleware ---
# Allows Next.js frontend running on port 3000 to interact with port 8000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Direct Bcrypt Hashing ---
security = HTTPBearer()

def hash_password(password: str) -> str:
    """Hashes passwords directly using bcrypt."""
    pw_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pw_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies passwords directly using bcrypt."""
    pw_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pw_bytes, hash_bytes)

def create_access_token(data: dict) -> str:
    """Generates a secure JSON Web Token for the user session."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """FastAPI Dependency injection to extract and validate user credentials from header."""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    users_col = get_users_collection()
    user = await users_col.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_exception
    
    return serialize_doc(user)

# --- Standard Status Routes ---

@app.get("/")
async def root_status():
    """Welcome endpoint to quickly verify the API server is online."""
    return {
        "status": "online",
        "service": "Multi-Agent Customer Support Assistant API",
        "documentation": "/docs"
    }

# --- Authentication Endpoints ---

@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    users_col = get_users_collection()
    
    # Check if email is already registered
    existing_user = await users_col.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
        
    new_user = {
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "full_name": user_data.full_name,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await users_col.insert_one(new_user)
    new_user["_id"] = result.inserted_id
    return serialize_doc(new_user)

@app.post("/api/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    users_col = get_users_collection()
    
    user = await users_col.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
        
    access_token = create_access_token(data={"sub": str(user["_id"]), "email": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Session Management Endpoints ---

@app.post("/api/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(session_data: SessionCreate, current_user: dict = Depends(get_current_user)):
    sessions_col = get_sessions_collection()
    
    title = session_data.title if session_data.title else f"Chat Session ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
    new_session = {
        "title": title,
        "user_id": current_user["id"],
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await sessions_col.insert_one(new_session)
    new_session["_id"] = result.inserted_id
    return serialize_doc(new_session)

@app.get("/api/sessions", response_model=List[SessionResponse])
async def list_sessions(current_user: dict = Depends(get_current_user)):
    sessions_col = get_sessions_collection()
    cursor = sessions_col.find({"user_id": current_user["id"]}).sort("created_at", -1)
    sessions = await cursor.to_list(length=100)
    return serialize_list(sessions)

@app.get("/api/sessions/{session_id}/history", response_model=List[MessageResponse])
async def get_session_history(session_id: str, current_user: dict = Depends(get_current_user)):
    sessions_col = get_sessions_collection()
    messages_col = get_messages_collection()
    
    # Verify session belongs to requesting user
    session = await sessions_col.find_one({"_id": ObjectId(session_id), "user_id": current_user["id"]})
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
    cursor = messages_col.find({"session_id": session_id}).sort("timestamp", 1)
    messages = await cursor.to_list(length=200)
    return serialize_list(messages)

# --- Chat Routing & Orchestrator Endpoint ---

@app.post("/api/sessions/{session_id}/chat", response_model=ChatResponse)
async def send_chat_message(
    session_id: str, 
    chat_req: ChatRequest, 
    current_user: dict = Depends(get_current_user)
):
    sessions_col = get_sessions_collection()
    messages_col = get_messages_collection()
    
    # 1. Verify session exists and belongs to current user
    session = await sessions_col.find_one({"_id": ObjectId(session_id), "user_id": current_user["id"]})
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
    # 2. Retrieve last 15 messages of conversation history for memory
    cursor = messages_col.find({"session_id": session_id}).sort("timestamp", -1).limit(15)
    db_history = await cursor.to_list(length=15)
    db_history.reverse()  # Restore chronological order
    
    # Format memory for the agent orchestrator
    memory_history = [
        {"role": msg["role"], "content": msg["content"]} 
        for msg in db_history
    ]
    
    # 3. Call multi-agent orchestrator
    try:
        agent_result = process_customer_query(chat_req.content, memory_history)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent orchestrator failed: {str(e)}"
        )
        
    # 4. Save user message to database
    user_msg = {
        "session_id": session_id,
        "role": "user",
        "content": chat_req.content,
        "timestamp": datetime.now(timezone.utc)
    }
    await messages_col.insert_one(user_msg)
    
    # 5. Save assistant response + metadata to database
    assistant_msg = {
        "session_id": session_id,
        "role": "assistant",
        "content": agent_result["response"],
        "agents": agent_result["agents"],
        "timestamp": datetime.now(timezone.utc)
    }
    await messages_col.insert_one(assistant_msg)
    
    # If the session has the default timestamp title, update the title to match first query
    if session["title"].startswith("Chat Session ("):
        new_title = chat_req.content[:35] + ("..." if len(chat_req.content) > 35 else "")
        await sessions_col.update_one({"_id": ObjectId(session_id)}, {"$set": {"title": new_title}})
        
    return {
        "response": agent_result["response"],
        "agents": agent_result["agents"],
        "session_id": session_id
    }

# --- Analytics Dashboard Endpoint ---

@app.get("/api/analytics")
async def get_analytics(current_user: dict = Depends(get_current_user)):
    sessions_col = get_sessions_collection()
    messages_col = get_messages_collection()
    
    # Retrieve user's sessions
    user_sessions_cursor = sessions_col.find({"user_id": current_user["id"]})
    user_sessions = await user_sessions_cursor.to_list(length=1000)
    session_ids = [str(s["_id"]) for s in user_sessions]
    
    total_sessions = len(session_ids)
    
    # Count messages associated with these sessions
    total_messages = 0
    agent_usage = {"billing": 0, "technical": 0, "product": 0, "complaint": 0, "faq": 0}
    
    if total_sessions > 0:
        total_messages = await messages_col.count_documents({"session_id": {"$in": session_ids}})
        
        # Count agent trigger distributions
        cursor = messages_col.find({"session_id": {"$in": session_ids}, "role": "assistant"})
        async for msg in cursor:
            agents = msg.get("agents") or []
            for agent in agents:
                if agent in agent_usage:
                    agent_usage[agent] += 1
                    
    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "agent_usage": agent_usage,
        "customer_name": current_user["full_name"]
    }