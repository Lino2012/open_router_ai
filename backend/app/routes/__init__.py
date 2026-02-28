"""Routes package initialization"""
from .auth import router as auth_router
from .chat import router as chat_router
from .memory import router as memory_router

__all__ = ["auth_router", "chat_router", "memory_router"]