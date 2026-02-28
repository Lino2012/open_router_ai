from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import datetime

from app import schemas, models, auth
from app.memory import (
    store_memory, retrieve_relevant_memories, get_user_preferences,
    extract_and_store_preferences, consolidate_memories
)
from app.utils.logging import logger

router = APIRouter(tags=["memory"], prefix="/memory")

@router.post("/store", response_model=Dict[str, str])
async def store_memory_endpoint(
    memory_data: schemas.MemoryEntryBase,
    current_user: models.User = Depends(auth.get_current_user)
):
    """Store a new memory entry"""
    try:
        entry = await store_memory(
            user_id=str(current_user.id),
            content=memory_data.content,
            memory_type=memory_data.type,
            metadata=memory_data.metadata
        )
        
        return {
            "id": str(entry.id),
            "message": "Memory stored successfully"
        }
    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store memory"
        )

@router.post("/search")
async def search_memories(
    request: Dict[str, Any],
    current_user: models.User = Depends(auth.get_current_user)
):
    """Search memories by similarity"""
    try:
        query = request.get("query", "")
        memory_type = request.get("memory_type")
        limit = request.get("limit", 5)
        
        results = await retrieve_relevant_memories(
            user_id=str(current_user.id),
            query=query,
            memory_type=memory_type,
            limit=limit
        )
        
        return {"results": results}
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search memories"
        )

@router.get("/preferences")
async def get_preferences(
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get user preferences"""
    try:
        preferences = await get_user_preferences(str(current_user.id))
        return {"preferences": preferences}
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get preferences"
        )

@router.get("/recent")
async def get_recent_memories(
    limit: int = 10,
    memory_type: Optional[str] = None,
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get recent memories"""
    try:
        query_filter = {"user_id": str(current_user.id)}
        if memory_type:
            query_filter["type"] = memory_type
        
        memories = await models.MemoryEntry.find(query_filter).sort(
            "-created_at"
        ).limit(limit).to_list()
        
        return {
            "memories": [
                {
                    "id": str(m.id),
                    "content": m.content,
                    "type": m.type,
                    "metadata": m.metadata,
                    "created_at": m.created_at
                }
                for m in memories
            ]
        }
    except Exception as e:
        logger.error(f"Error getting recent memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recent memories"
        )

@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    current_user: models.User = Depends(auth.get_current_user)
):
    """Delete a specific memory entry"""
    try:
        memory = await models.MemoryEntry.get(memory_id)
        
        if not memory or memory.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )
        
        await memory.delete()
        
        return {"message": "Memory deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete memory"
        )

@router.post("/consolidate")
async def consolidate_memories_endpoint(
    request: Dict[str, Any] = {},
    current_user: models.User = Depends(auth.get_current_user)
):
    """Consolidate old memories"""
    try:
        days = request.get("days", 7)
        await consolidate_memories(str(current_user.id), days)
        return {"message": f"Memories older than {days} days consolidated"}
    except Exception as e:
        logger.error(f"Error consolidating memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to consolidate memories"
        )