from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime

from app import schemas, models, auth
from app.memory import store_memory, retrieve_relevant_memories, extract_and_store_preferences
from app.config import get_settings
from app.utils.logging import logger
from app.openrouter import client

router = APIRouter(tags=["chat"])
settings = get_settings()

@router.post("/chat", response_model=schemas.ChatResponse)
async def chat(
    request: schemas.ChatRequest,
    current_user: models.User = Depends(auth.get_current_user)
):
    """Send a message and get AI response"""
    try:
        user_id = str(current_user.id)
        
        # Get model from metadata or use default
        model = request.metadata.get('model', settings.OPENROUTER_MODEL) if request.metadata else settings.OPENROUTER_MODEL
        
        # Create or get session
        if request.session_id:
            session = await models.Session.get(request.session_id)
            if not session or session.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found"
                )
        else:
            session = models.Session(
                user_id=user_id,
                memory_enabled=request.memory_enabled
            )
            await session.insert()
        
        # Save user message
        user_message = models.Message(
            session_id=str(session.id),
            role="user",
            content=request.message
        )
        await user_message.insert()
        
        # Get recent messages
        recent_messages = await models.Message.find(
            models.Message.session_id == str(session.id)
        ).sort("-created_at").limit(10).to_list()
        recent_messages.reverse()
        
        # Prepare conversation context
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant with memory capabilities."}
        ]
        
        # Add recent messages
        for msg in recent_messages:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Retrieve long-term memories if enabled
        memory_context = ""
        if session.memory_enabled:
            relevant_memories = await retrieve_relevant_memories(
                user_id, request.message, limit=3
            )
            
            if relevant_memories:
                memory_context = "Relevant information from past conversations:\n"
                for mem in relevant_memories:
                    memory_context += f"- {mem['content']}\n"
                
                messages.insert(1, {"role": "system", "content": memory_context})
        
        # Call OpenRouter API
        response = client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore
            temperature=0.7,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content or ""
        tokens_used = response.usage.total_tokens if response.usage else 0
        
        # Save AI response
        ai_message = models.Message(
            session_id=str(session.id),
            role="assistant",
            content=ai_response,
            tokens=tokens_used,
            metadata={
                "model": model,
                "provider": "openrouter",
                "temperature": 0.7,
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "memory_context": memory_context if memory_context else None
            }
        )
        await ai_message.insert()
        
        # Store in long-term memory if enabled
        if session.memory_enabled:
            if request.message:
                await store_memory(
                    user_id,
                    request.message,
                    memory_type="conversation",
                    metadata={"session_id": str(session.id), "role": "user"}
                )
            
            if ai_response:
                await store_memory(
                    user_id,
                    ai_response,
                    memory_type="conversation",
                    metadata={"session_id": str(session.id), "role": "assistant"}
                )
            
            # Extract preferences periodically
            message_count = len(recent_messages) + 1
            if message_count % 5 == 0:
                all_messages = recent_messages + [user_message, ai_message]
                message_dicts = []
                for m in all_messages:
                    if m and hasattr(m, 'role') and hasattr(m, 'content'):
                        message_dicts.append({
                            "role": m.role,
                            "content": m.content or ""
                        })
                
                await extract_and_store_preferences(
                    user_id,
                    message_dicts
                )
        
        # Update session title if it's the first message
        if len(recent_messages) <= 1 and request.message:
            try:
                title_response = client.chat.completions.create(
                    model="x-ai/grok-3-mini-beta",
                    messages=[
                        {"role": "system", "content": "Generate a short title (max 6 words) for this conversation based on the user's first message. Return only the title, no quotes."},
                        {"role": "user", "content": request.message}
                    ],
                    max_tokens=20
                )
                title = title_response.choices[0].message.content
                if title:
                    session.title = title.strip()
                    await session.save()
            except Exception as e:
                logger.error(f"Title generation error: {e}")
        
        return schemas.ChatResponse(
            message=ai_response,
            session_id=str(session.id),
            tokens_used=tokens_used
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your message: {str(e)}"
        )

@router.get("/sessions", response_model=List[schemas.SessionResponse])
async def get_sessions(
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get all sessions for the current user"""
    try:
        sessions = await models.Session.find(
            models.Session.user_id == str(current_user.id)
        ).sort("-updated_at").to_list()
        
        # Convert ObjectId to string
        result = []
        for session in sessions:
            result.append({
                "id": str(session.id),
                "user_id": session.user_id,
                "title": session.title,
                "memory_enabled": session.memory_enabled,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            })
        
        return result
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sessions"
        )

@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    current_user: models.User = Depends(auth.get_current_user)
):
    """Delete a session and all its messages"""
    try:
        session = await models.Session.get(session_id)
        
        if not session or session.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Delete all messages in the session
        await models.Message.find(
            models.Message.session_id == session_id
        ).delete()
        
        # Delete the session
        await session.delete()
        
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )

@router.get("/session/{session_id}/messages", response_model=List[schemas.MessageResponse])
async def get_session_messages(
    session_id: str,
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get all messages for a specific session"""
    try:
        session = await models.Session.get(session_id)
        if not session or session.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        messages = await models.Message.find(
            models.Message.session_id == session_id
        ).sort("created_at").to_list()
        
        # Convert ObjectId to string
        result = []
        for msg in messages:
            result.append({
                "id": str(msg.id),
                "session_id": msg.session_id,
                "role": msg.role,
                "content": msg.content,
                "tokens": msg.tokens,
                "metadata": msg.metadata,
                "created_at": msg.created_at
            })
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session messages"
        )

@router.put("/session/{session_id}/title")
async def update_session_title(
    session_id: str,
    title_data: Dict[str, str],
    current_user: models.User = Depends(auth.get_current_user)
):
    """Update session title"""
    try:
        session = await models.Session.get(session_id)
        
        if not session or session.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        new_title = title_data.get("title", "")
        if new_title:
            session.title = new_title
            await session.save()
        
        return {"message": "Session title updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session title: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session title"
        )