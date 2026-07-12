from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# --- User Schemas ---
class UserRegister(BaseModel):
    email: str = Field(..., description="Unique email address for registration")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    full_name: str = Field(..., description="Full name of the customer")

class UserLogin(BaseModel):
    email: str = Field(..., description="Registered email address")
    password: str = Field(..., description="User password")

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- JWT Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None

# --- Chat Session Schemas ---
class SessionCreate(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the chat session")

class SessionResponse(BaseModel):
    id: str
    title: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Messaging Schemas ---
class ChatRequest(BaseModel):
    content: str = Field(..., description="The user's message query")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Synthesized agent response")
    agents: List[str] = Field(..., description="List of specialized agents triggered")
    session_id: str = Field(..., description="The active chat session ID")

class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str  # "user" or "assistant"
    content: str
    agents: Optional[List[str]] = None  # Populated only for assistant messages
    timestamp: datetime

    class Config:
        from_attributes = True