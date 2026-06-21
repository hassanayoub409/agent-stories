"""
Agent Memory: Conversation and Long-term Memory
"""
from typing import List, Dict, Optional
from src.database import (
    add_conversation, set_metadata,
    get_user_stories, get_story_scenes
)

class AgentMemory:
    def __init__(self, user_id: int, story_id: Optional[int] = None):
        self.user_id = user_id
        self.story_id = story_id
        self.conversation_history: List[Dict] = []
    
    def add_message(self, role: str, message: str):
        """Add a message to conversation memory"""
        self.conversation_history.append({"role": role, "message": message})
        # Also save to database
        add_conversation(self.story_id, self.user_id, role, message)
    
    def get_conversation_context(self, limit: int = 10) -> str:
        """Get recent conversation context as string"""
        recent = self.conversation_history[-limit:] if len(self.conversation_history) > limit else self.conversation_history
        context = "\n".join([f"{msg['role']}: {msg['message']}" for msg in recent])
        return context
    
    def get_user_preferences(self) -> Dict:
        """Get user preferences from long-term memory"""
        # Get from metadata or user's past stories
        past_stories = get_user_stories(self.user_id, limit=5)
        preferences = {
            "preferred_style": None,
            "preferred_genre": None,
            "average_scenes": 8
        }
        
        if past_stories:
            styles = [s.get("style") for s in past_stories if s.get("style")]
            genres = [s.get("genre") for s in past_stories if s.get("genre")]
            
            if styles:
                preferences["preferred_style"] = max(set(styles), key=styles.count)
            if genres:
                preferences["preferred_genre"] = max(set(genres), key=genres.count)
        
        return preferences
    
    def save_preference(self, key: str, value: str):
        """Save a user preference"""
        if self.story_id:
            set_metadata(self.story_id, f"user_pref_{key}", value)
    
    def get_story_context(self) -> Optional[str]:
        """Get context from current story"""
        if not self.story_id:
            return None
        
        scenes = get_story_scenes(self.story_id)
        if scenes:
            context = "\n".join([f"Scene {s['scene_number']}: {s['scene_text']}" for s in scenes])
            return context
        return None