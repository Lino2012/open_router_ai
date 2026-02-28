from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import Field
from beanie import Document, Indexed, before_event, Insert, Replace

class User(Document):  # type: ignore
    email: str = Indexed(str, unique=True)  # type: ignore
    username: str = Indexed(str, unique=True)  # type: ignore
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Settings:
        name = "users"
        use_state_management = True
    
    @before_event(Insert, Replace)  # type: ignore
    def update_timestamps(self):
        self.updated_at = datetime.utcnow()

class Session(Document):  # type: ignore
    user_id: str
    title: str = "New Chat"
    memory_enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Settings:
        name = "sessions"
        use_state_management = True
    
    @before_event(Insert, Replace)  # type: ignore
    def update_timestamps(self):
        self.updated_at = datetime.utcnow()

class Message(Document):  # type: ignore
    session_id: str
    role: str
    content: str
    tokens: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "messages"
        use_state_management = True

class MemoryEntry(Document):  # type: ignore
    user_id: str
    content: str
    type: str = "general"
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "memory_entries"
        use_state_management = True

class UserPreferences(Document):  # type: ignore
    user_id: str = Indexed(str, unique=True)  # type: ignore
    preferences: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "user_preferences"
        use_state_management = True