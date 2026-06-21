"""
Pydantic Models for Validation
"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List

# Authentication Models
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum() and '_' not in v:
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v.strip()


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    plan: str
    created_at: str


# Story Models
class StoryInput(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=5000)
    style: Optional[str] = Field(None, pattern="^(Cinematic|Anime|Watercolor|Noir|Cyberpunk)$")
    max_scenes: int = Field(8, ge=3, le=15)
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Prompt must be at least 10 characters')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "A detective standing in the rain, heavy noir atmosphere...",
                "style": "Cinematic",
                "max_scenes": 8
            }
        }


class SceneOutput(BaseModel):
    scene_number: int = Field(..., ge=1)
    scene_text: str = Field(..., min_length=10)
    cinematic_prompt: str = Field(..., min_length=20)
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    completeness_score: float = Field(0.0, ge=0.0, le=1.0)
    
    @validator('cinematic_prompt')
    def validate_prompt_length(cls, v):
        if len(v) < 20:
            raise ValueError('Cinematic prompt too short')
        return v


class StoryResponse(BaseModel):
    story_id: int
    title: str
    genre: Optional[str]
    style: Optional[str]
    scenes: List[SceneOutput]
    summary: Optional[str]
    total_scenes: int
    status: str
    created_at: str
    user_prompt: Optional[str] = None
    original_title: Optional[str] = None  # Original generated title (for book canvas)
    archived: Optional[int] = 0  # Archive status (0 = not archived, 1 = archived)


# Query Models
class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)


class FilterQuery(BaseModel):
    genre: Optional[str] = None
    style: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class CategorizeRequest(BaseModel):
    story_text: str = Field(..., min_length=10)

