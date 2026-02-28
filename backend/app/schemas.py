from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

# Custom ObjectId type for Pydantic v2
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return str(v)

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: str = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[str] = None

# Session schemas
class SessionBase(BaseModel):
    title: str = "New Chat"
    memory_enabled: bool = True

class SessionCreate(SessionBase):
    pass

class SessionResponse(SessionBase):
    id: str = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

# Message schemas
class MessageBase(BaseModel):
    role: str
    content: str

class MessageCreate(MessageBase):
    session_id: str

class MessageResponse(MessageBase):
    id: str = Field(default_factory=PyObjectId, alias="_id")
    session_id: str
    tokens: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

# Chat schemas
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    memory_enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatResponse(BaseModel):
    message: str
    session_id: str
    tokens_used: int

# Memory schemas
class MemoryEntryBase(BaseModel):
    content: str
    type: str = "general"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MemoryEntryResponse(MemoryEntryBase):
    id: str = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    created_at: datetime
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class MemorySearchRequest(BaseModel):
    query: str
    limit: int = 5
    memory_type: Optional[str] = None

class PreferenceExtractionRequest(BaseModel):
    messages: List[Dict[str, str]]