import numpy as np
import json
import faiss  # type: ignore
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib

from .models import MemoryEntry, UserPreferences
from .config import get_settings
from .utils.logging import logger
from .openrouter import client

settings = get_settings()

class VectorMemory:
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)  # type: ignore
        self.id_to_entry = {}
        self.next_id = 0
    
    def add_embeddings(self, entries: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Add memory entries and their embeddings to FAISS index"""
        if not entries or not embeddings:
            return
        
        embeddings_array = np.array(embeddings).astype('float32')
        start_id = self.next_id
        self.index.add(embeddings_array)  # type: ignore
        
        for i, entry in enumerate(entries):
            self.id_to_entry[start_id + i] = entry
        
        self.next_id += len(entries)
    
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar memory entries"""
        if self.index.ntotal == 0:  # type: ignore
            return []
        
        query_array = np.array([query_embedding]).astype('float32')
        distances, indices = self.index.search(query_array, k)  # type: ignore
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx in self.id_to_entry:
                entry = self.id_to_entry[idx].copy()
                entry['similarity'] = float(1 - distances[0][i] / 2)
                entry['distance'] = float(distances[0][i])
                results.append(entry)
        
        return results

# Global vector memory instances
user_vector_memories: Dict[str, VectorMemory] = {}

async def get_embedding(text: str) -> List[float]:
    """Get embedding using deterministic hash-based method"""
    try:
        # Create a deterministic pseudo-embedding based on text hash
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to list of floats between -1 and 1
        base_floats = []
        for i in range(0, 16, 4):
            chunk = hash_bytes[i:i+4]
            if len(chunk) == 4:
                val = int.from_bytes(chunk, byteorder='big') / (2**32 - 1) * 2 - 1
                base_floats.append(val)
        
        # Repeat to reach 1536 dimensions
        embedding = []
        while len(embedding) < 1536:
            embedding.extend(base_floats)
        
        return embedding[:1536]
        
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return [0.0] * 1536

async def get_user_vector_memory(user_id: str) -> VectorMemory:
    """Get or create vector memory for user"""
    if user_id not in user_vector_memories:
        user_vector_memories[user_id] = VectorMemory()
        
        # Load existing memories
        memories = await MemoryEntry.find(
            MemoryEntry.user_id == user_id,
            MemoryEntry.embedding != None
        ).limit(100).to_list()
        
        if memories:
            entries = []
            embeddings = []
            for memory in memories:
                entries.append({
                    'id': str(memory.id),
                    'content': memory.content,
                    'type': memory.type,
                    'metadata': memory.metadata,
                    'created_at': memory.created_at
                })
                if memory.embedding:
                    embeddings.append(memory.embedding)
            
            if embeddings:
                user_vector_memories[user_id].add_embeddings(entries, embeddings)
    
    return user_vector_memories[user_id]

async def store_memory(
    user_id: str,
    content: str,
    memory_type: str = "general",
    metadata: Optional[Dict[str, Any]] = None
) -> MemoryEntry:
    """Store a memory entry with embedding"""
    if not content:
        raise ValueError("Content cannot be empty")
    
    embedding = await get_embedding(content)
    
    memory_entry = MemoryEntry(
        user_id=user_id,
        content=content,
        type=memory_type,
        embedding=embedding,
        metadata=metadata or {}
    )
    
    await memory_entry.insert()
    
    vector_memory = await get_user_vector_memory(user_id)
    vector_memory.add_embeddings(
        [{
            'id': str(memory_entry.id),
            'content': content,
            'type': memory_type,
            'metadata': metadata or {},
            'created_at': memory_entry.created_at
        }],
        [embedding]
    )
    
    return memory_entry

async def retrieve_relevant_memories(
    user_id: str,
    query: str,
    memory_type: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Retrieve relevant memories using vector search"""
    if not query:
        return []
    
    query_embedding = await get_embedding(query)
    
    vector_memory = await get_user_vector_memory(user_id)
    vector_results = vector_memory.search(query_embedding, limit)
    
    if memory_type and vector_results:
        vector_results = [r for r in vector_results if r.get('type') == memory_type]
    
    if len(vector_results) < limit:
        query_filter = {"user_id": user_id}
        if memory_type:
            query_filter["type"] = memory_type
        
        recent_memories = await MemoryEntry.find(query_filter).sort(
            "-created_at"
        ).limit(limit).to_list()
        
        for memory in recent_memories:
            if not any(r.get('id') == str(memory.id) for r in vector_results):
                vector_results.append({
                    'id': str(memory.id),
                    'content': memory.content,
                    'type': memory.type,
                    'metadata': memory.metadata,
                    'created_at': memory.created_at,
                    'recent': True
                })
    
    return vector_results[:limit]

async def extract_and_store_preferences(
    user_id: str,
    messages: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Extract user preferences from conversation and store them"""
    preferences = {
        "likes": [],
        "interests": [],
        "topics": []
    }
    
    preference_keywords = {
        'like': 'likes',
        'love': 'likes',
        'enjoy': 'likes',
        'interested in': 'interests',
        'passionate about': 'interests',
        'topic': 'topics',
        'about': 'topics'
    }
    
    for msg in messages:
        if msg.get('role') == 'user':
            content = msg.get('content', '').lower()
            for keyword, category in preference_keywords.items():
                if keyword in content:
                    sentences = content.split('.')
                    for sentence in sentences:
                        if keyword in sentence:
                            value = sentence.strip()
                            if value and value not in preferences[category]:
                                preferences[category].append(value)
    
    # Store each preference
    for category, values in preferences.items():
        for value in values:
            if value:
                try:
                    await store_memory(
                        user_id,
                        f"{category}: {value}",
                        memory_type="preference",
                        metadata={"category": category, "value": value}
                    )
                except Exception as e:
                    logger.error(f"Error storing preference: {e}")
    
    # Update user preferences document
    try:
        user_prefs = await UserPreferences.find_one({"user_id": user_id})
        if user_prefs:
            user_prefs.preferences.update(preferences)
            user_prefs.updated_at = datetime.utcnow()
            await user_prefs.save()
        else:
            user_prefs = UserPreferences(
                user_id=user_id,
                preferences=preferences
            )
            await user_prefs.insert()
    except Exception as e:
        logger.error(f"Error saving user preferences: {e}")
    
    return preferences

async def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """Get stored user preferences"""
    try:
        user_prefs = await UserPreferences.find_one({"user_id": user_id})
        return user_prefs.preferences if user_prefs else {}
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        return {}

async def consolidate_memories(user_id: str, days: int = 7):
    """Consolidate and summarize old memories"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_memories = await MemoryEntry.find(
            MemoryEntry.user_id == user_id,
            MemoryEntry.created_at < cutoff_date,
            MemoryEntry.type != "summary"
        ).to_list()
        
        if len(old_memories) < 10:
            return
        
        # Group by type
        memories_by_type = {}
        for memory in old_memories:
            if memory.type not in memories_by_type:
                memories_by_type[memory.type] = []
            memories_by_type[memory.type].append(memory.content)
        
        # Create summaries using Grok
        for memory_type, contents in memories_by_type.items():
            if len(contents) < 5:
                continue
                
            try:
                response = client.chat.completions.create(
                    model=settings.OPENROUTER_MODEL,
                    messages=[
                        {"role": "system", "content": f"Summarize these {memory_type} into key points:"},
                        {"role": "user", "content": "\n".join(contents[:20])}
                    ],
                    temperature=0.3,
                    max_tokens=300
                )
                
                summary = response.choices[0].message.content
                if summary:
                    await store_memory(
                        user_id,
                        summary,
                        memory_type="summary",
                        metadata={"original_type": memory_type, "count": len(contents)}
                    )
                    
                    for memory in old_memories:
                        if memory.type == memory_type:
                            memory.metadata['archived'] = True
                            await memory.save()
                            
            except Exception as e:
                logger.error(f"Error creating summary: {e}")
    except Exception as e:
        logger.error(f"Error in consolidate_memories: {e}")

async def clear_user_vector_memory(user_id: str):
    """Clear vector memory cache for a user"""
    if user_id in user_vector_memories:
        del user_vector_memories[user_id]
        logger.info(f"Cleared vector memory cache for user {user_id}")