"""
FastAPI Backend Server
"""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import os
import json
from datetime import datetime

from src.models import (
    UserRegister, UserLogin, UserResponse, StoryInput, StoryResponse, SceneOutput,
    SearchQuery, FilterQuery, CategorizeRequest
)
from pydantic import BaseModel as PydanticBaseModel, Field
from src.database import (
    init_db, create_user, get_user_by_email, get_user_by_id, verify_password,
    create_story, get_story, get_user_stories, create_scene, get_story_scenes,
    log_agent_decision, log_user_query, create_report, set_metadata,
    update_story, delete_story, archive_story, update_user_username, update_user_password
)
from src.scene_generator import SceneGenerator
from src.image_generator import ImageGenerator
from src.analytics import AnalyticsEngine
from src.memory import AgentMemory
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Story-to-Scene Generator API")

# Force CORS headers on all responses (including StaticFiles)
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


# CORS Configuration - Explicitly allow all methods including DELETE and PUT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Dependency to get current user (simplified - in production use JWT)
def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> int:
    """Get current user ID from token (simplified for now)"""
    # In production, decode JWT token here
    # For now, we'll use a simple user_id in the token
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        user_id = int(credentials.credentials)
        # Verify user exists by checking database
        from src.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=401, detail="User not found")
        conn.close()
        return user_id
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token format")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


# Authentication Endpoints
@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    user_id = create_user(user_data.username, user_data.email, user_data.password)
    if not user_id:
        raise HTTPException(status_code=400, detail="Email or username already exists")
    
    user = get_user_by_email(user_data.email)
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        plan=user["plan"],
        created_at=user["created_at"]
    )


@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    """Login user"""
    user = get_user_by_email(credentials.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # In production, return JWT token
    return {
        "access_token": str(user["id"]),
        "token_type": "bearer",
        "user": UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            plan=user["plan"],
            created_at=user["created_at"]
        )
    }


# Story Generation Endpoints
@app.post("/api/generate-scenes", response_model=StoryResponse)
async def generate_scenes(story_input: StoryInput, user_id: int = Depends(get_current_user)):
    """Generate scenes from story prompt"""
    story_id = None
    try:
        # Limit max_scenes to 8
        max_scenes = min(story_input.max_scenes, 8)
        # Initialize generators
        analytics = AnalyticsEngine()
        memory = AgentMemory(user_id)
        
        # Get user preferences from memory
        preferences = memory.get_user_preferences()
        if preferences.get("preferred_style") and not story_input.style:
            story_input.style = preferences.get("preferred_style")
        
        # Classify the story
        classification = analytics.classify(story_input.prompt)
        genre = classification.get("genre", "Drama")
        # Determine style (from input, preferences, or classification)
        style = story_input.style or preferences.get("preferred_style") or classification.get("style", "Cinematic")
        
        # Initialize scene generator (style is not used in scene generation, only in image generation)
        scene_gen = SceneGenerator(max_scenes=max_scenes)
        
        # Generate title from prompt using LLM 
        try:
            title = analytics.generate_title(story_input.prompt)
        except Exception as title_error:
            print(f"Title generation failed: {title_error}")
            # Fallback to a better default title
            words = story_input.prompt.split()[:6]
            title = " ".join(words) + ("..." if len(story_input.prompt.split()) > 6 else "")
            if len(title) > 50:
                title = title[:47] + "..."
        
        # Store original_title separately - this will never change, even when user renames
        original_title = title
        
        # Create story record FIRST - ensure it's saved even if generation fails
        story_id = create_story(user_id, title, story_input.prompt, genre, style, original_title)
        
        # Update memory
        memory.story_id = story_id
        memory.add_message("user", story_input.prompt)
        
        # Log agent decision
        log_agent_decision(story_id, "genre_classification", json.dumps(classification), 0.8)
        
        # Generate scenes (with error handling for rate limits)
        try:
            scenes_data = scene_gen.generate_scenes(story_input.prompt)
        except Exception as scene_error:
            error_msg = str(scene_error)
            # If scene generation fails due to quota, create a basic scene from prompt
            if "quota" in error_msg.lower() or "429" in error_msg or "rate limit" in error_msg.lower() or "ResourceExhausted" in error_msg:
                print(f"Scene generation failed due to quota: {scene_error}")
                # Create a basic scene structure so story can still be saved
                scenes_data = [{
                    "scene_number": 1,
                    "scene_text": story_input.prompt[:200] + "..." if len(story_input.prompt) > 200 else story_input.prompt,
                    "cinematic_prompt": f"Cinematic scene: {story_input.prompt[:150]}"
                }]
            else:
                raise
        
        try:
            patterns = analytics.detect_patterns(scenes_data)
            log_agent_decision(story_id, "pattern_detection", json.dumps(patterns), patterns.get("visual_consistency_score", 0.7))
        except Exception as pattern_error:
            print(f"Pattern detection failed: {pattern_error}")
        
        try:
            summary = analytics.summarize(story_input.prompt, "story")
            set_metadata(story_id, "summary", summary)
        except Exception as summary_error:
            print(f"Summary generation failed: {summary_error}")
            summary = "Story summary unavailable"
        
        # Save scenes to database
        scene_outputs = []
        for scene_data in scenes_data:
            scene_id = create_scene(
                story_id,
                scene_data["scene_number"],
                scene_data["scene_text"],
                scene_data["cinematic_prompt"]
            )
            
            # Calculate scores
            confidence = 0.8  # Can be improved with actual scoring
            completeness = min(1.0, len(scene_data["scene_text"]) / 100)
            
            scene_outputs.append(SceneOutput(
                scene_number=scene_data["scene_number"],
                scene_text=scene_data["scene_text"],
                cinematic_prompt=scene_data["cinematic_prompt"],
                confidence_score=confidence,
                completeness_score=completeness
            ))
        
        # Update story status to completed
        from src.database import get_db_connection
        conn = get_db_connection()
        conn.execute("UPDATE stories SET status = 'completed' WHERE id = ?", (story_id,))
        conn.commit()
        conn.close()
        
        # Add assistant message to memory
        memory.add_message("assistant", f"Generated {len(scene_outputs)} scenes")
        
        return StoryResponse(
            story_id=story_id,
            title=title,
            genre=genre,
            style=style,
            scenes=scene_outputs,
            summary=summary,
            total_scenes=len(scene_outputs),
            status="completed",
            created_at=datetime.now().isoformat(),
            original_title=original_title  # Include original_title in response
        )
    
    except Exception as e:
        if story_id:
            try:
                from src.database import get_db_connection
                conn = get_db_connection()
                conn.execute("UPDATE stories SET status = 'failed' WHERE id = ?", (story_id,))
                conn.commit()
                conn.close()
            except:
                pass
        
        raise HTTPException(status_code=500, detail=f"Error generating scenes: {str(e)}")


@app.post("/api/generate-images/{story_id}")
async def generate_images(story_id: int, user_id: int = Depends(get_current_user)):
    """Generate images for scenes - handles rate limits gracefully"""
    # Verify story belongs to user
    story = get_story(story_id, user_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    scenes = get_story_scenes(story_id)
    if not scenes:
        raise HTTPException(status_code=404, detail="No scenes found")
    
    try:
        # Get style from story for image generation
        story_style = story.get("style", "Cinematic")
        # Initialize ImageGenerator with story_id and style for unique filenames and style-appropriate images
        image_gen = ImageGenerator(story_id=story_id, style=story_style)
        image_paths = []
        image_urls = []
        failed_scenes = []
        rate_limit_hit = False
        
        for scene in scenes:
            try:
                scene_dict = {
                    "scene_number": scene["scene_number"],
                    "scene_text": scene["scene_text"],
                    "cinematic_prompt": scene["cinematic_prompt"]
                }
                
                # Add timeout wrapper to prevent hanging
                import concurrent.futures
                
                # Run image generation with timeout
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(image_gen.generate_image_for_scene, scene_dict)
                    try:
                        # Increased timeout to allow for retries (3 attempts * 120s = up to 6 minutes)
                        # But we'll use 5 minutes to be safe
                        path = future.result(timeout=300)
                    except concurrent.futures.TimeoutError:
                        raise Exception("Image generation timed out after 5 minutes (including retries)")
                    except Exception as e:
                        raise e
                
                image_paths.append(path)
                
                # Convert path to URL - get just the filename
                filename = os.path.basename(path)
                image_url = f"/scene_images/{filename}"
                image_urls.append(image_url)
                
                # Update scene with image path and URL
                from src.database import get_db_connection
                conn = get_db_connection()
                conn.execute("UPDATE scenes SET image_path = ?, image_url = ? WHERE id = ?", 
                            (path, image_url, scene["id"]))
                conn.commit()
                conn.close()
                
            except Exception as scene_error:
                error_msg = str(scene_error)
                print(f"Error generating image for scene {scene['scene_number']}: {error_msg}")
                
                # Check if it's a rate limit error
                if "429" in error_msg or "rate limit" in error_msg.lower() or "throttled" in error_msg.lower() or "quota" in error_msg.lower():
                    rate_limit_hit = True
                    break
                else:
                    failed_scenes.append(scene["scene_number"])
                    continue
        
        # If rate limit was hit, return immediately with partial results
        if rate_limit_hit:
            return {
                "message": f"Rate limit reached. Generated {len(image_paths)}/{len(scenes)} images. Please wait and try again later.",
                "image_paths": image_paths,
                "image_urls": image_urls,
                "partial": True,
                "rate_limited": True,
                "completed": len(image_paths),
                "total": len(scenes)
            }
        
        # Return success (even if some scenes failed)
        if failed_scenes:
            return {
                "message": f"Generated {len(image_paths)}/{len(scenes)} images. Some scenes failed.",
                "image_paths": image_paths,
                "image_urls": image_urls,
                "partial": True,
                "failed_scenes": failed_scenes
            }
        
        return {
            "message": "Images generated successfully",
            "image_paths": image_paths,
            "image_urls": image_urls,
            "partial": False
        }
    
    except Exception as e:
        error_msg = str(e)
        # Check if it's a rate limit error
        if "429" in error_msg or "rate limit" in error_msg.lower() or "throttled" in error_msg.lower():
            raise HTTPException(
                status_code=429,
                detail="Rate limit reached. Please wait a moment and try again. Your story is saved and you can generate images later."
            )
        raise HTTPException(status_code=500, detail=f"Error generating images: {str(e)}")


# History Endpoints
@app.get("/api/history")
async def get_history(user_id: int = Depends(get_current_user)):
    """Get user's story history"""
    stories = get_user_stories(user_id)
    return [{
        "id": s["id"],
        "title": s["title"],
        "genre": s["genre"],
        "style": s["style"],
        "status": s["status"],
        "created_at": s["created_at"]
    } for s in stories]


# Request Models
class UpdateStoryRequest(PydanticBaseModel):
    title: str


class UpdateUsernameRequest(PydanticBaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class UpdatePasswordRequest(PydanticBaseModel):
    password: str = Field(..., min_length=6, max_length=100)


@app.get("/api/history/archived")
async def get_archived_history(user_id: int = Depends(get_current_user)):
    """Get user's archived story history"""
    from src.database import get_db_connection
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Get only archived stories
        cursor.execute(
            "SELECT * FROM stories WHERE user_id = ? AND archived = 1 ORDER BY created_at DESC",
            (user_id,)
        )
        stories = [dict(row) for row in cursor.fetchall()]
        return [{
            "id": s["id"],
            "title": s["title"],
            "genre": s["genre"],
            "style": s["style"],
            "status": s["status"],
            "created_at": s["created_at"]
        } for s in stories]
    finally:
        conn.close()


@app.put("/api/user/username")
async def update_username_endpoint(request: UpdateUsernameRequest, user_id: int = Depends(get_current_user)):
    """Update user's username"""
    if not request.username or len(request.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    
    success = update_user_username(user_id, request.username.strip())
    if not success:
        raise HTTPException(status_code=400, detail="Username already exists or update failed")
    
    # Get updated user data
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        plan=user["plan"],
        created_at=user["created_at"]
    )

@app.put("/api/user/password")
async def update_password_endpoint(request: UpdatePasswordRequest, user_id: int = Depends(get_current_user)):
    """Update user's password"""
    if not request.password or len(request.password.strip()) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    success = update_user_password(user_id, request.password.strip())
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password")
    
    return {"message": "Password updated successfully"}

# Story CRUD endpoints - Order matters: PUT and DELETE before GET to ensure proper registration
@app.put("/api/story/{story_id}")
async def update_story_title_endpoint(
    story_id: int, 
    request: UpdateStoryRequest, 
    user_id: int = Depends(get_current_user)
):
    """Update story title"""
    if not request or not hasattr(request, 'title') or not request.title:
        raise HTTPException(status_code=400, detail="Title is required")
    
    success = update_story(story_id, user_id, request.title.strip())
    if not success:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return {"message": "Story updated successfully", "story_id": story_id}


@app.delete("/api/story/{story_id}")
async def delete_story_endpoint(
    story_id: int, 
    user_id: int = Depends(get_current_user)
):
    """Delete a story"""
    # Verify story exists
    story = get_story(story_id, user_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Delete the story
    success = delete_story(story_id, user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete story")
    
    return {"message": "Story deleted successfully", "story_id": story_id}


@app.post("/api/story/{story_id}/archive")
async def archive_story_endpoint(
    story_id: int,
    user_id: int = Depends(get_current_user)
):
    """Archive a story"""
    # Verify story exists
    story = get_story(story_id, user_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Archive the story
    success = archive_story(story_id, user_id, archived=True)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to archive story")
    
    return {"message": "Story archived successfully", "story_id": story_id}


@app.post("/api/story/{story_id}/unarchive")
async def unarchive_story_endpoint(
    story_id: int,
    user_id: int = Depends(get_current_user)
):
    """Unarchive a story"""
    # Verify story exists
    story = get_story(story_id, user_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Unarchive the story
    success = archive_story(story_id, user_id, archived=False)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to unarchive story")
    
    return {"message": "Story unarchived successfully", "story_id": story_id}


@app.get("/api/story/{story_id}/public")
async def get_story_public(story_id: int):
    """Get story details for sharing (public, no auth required)"""
    from src.database import get_db_connection
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Get story without user_id check (for sharing)
        cursor.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Story not found")
        story = dict(row)
    finally:
        conn.close()
    
    scenes_data = get_story_scenes(story_id)
    scenes = [SceneOutput(
        scene_number=s["scene_number"],
        scene_text=s["scene_text"],
        cinematic_prompt=s["cinematic_prompt"],
        image_path=s.get("image_path"),
        image_url=s.get("image_url"),
        confidence_score=0.8,
        completeness_score=0.8
    ) for s in scenes_data]
    
    from src.database import get_metadata
    summary = get_metadata(story_id, "summary")
    
    original_title = story.get("original_title") or story["title"]
    archived_status = story.get("archived", 0)
    if archived_status is None:
        archived_status = 0
    
    return StoryResponse(
        story_id=story["id"],
        title=story["title"],
        genre=story["genre"],
        style=story["style"],
        scenes=scenes,
        summary=summary,
        user_prompt=story.get("user_prompt", ""),
        total_scenes=len(scenes),
        status=story["status"],
        created_at=story["created_at"],
        original_title=original_title,
        archived=archived_status
    )


@app.get("/api/story/{story_id}", response_model=StoryResponse)
async def get_story_details(story_id: int, user_id: int = Depends(get_current_user)):
    """Get full story details (requires authentication)"""
    story = get_story(story_id, user_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    scenes_data = get_story_scenes(story_id)
    scenes = [SceneOutput(
        scene_number=s["scene_number"],
        scene_text=s["scene_text"],
        cinematic_prompt=s["cinematic_prompt"],
        image_path=s.get("image_path"),
        image_url=s.get("image_url"),
        confidence_score=0.8,
        completeness_score=0.8
    ) for s in scenes_data]
    
    from src.database import get_metadata
    summary = get_metadata(story_id, "summary")
    
    # Get original_title from database, fallback to title if not set (for old stories)
    original_title = story.get("original_title") or story["title"]
    
    # Get archived status
    archived_status = story.get("archived", 0)
    if archived_status is None:
        archived_status = 0
    
    return StoryResponse(
        story_id=story["id"],
        title=story["title"],
        genre=story["genre"],
        style=story["style"],
        scenes=scenes,
        summary=summary,
        user_prompt=story.get("user_prompt", ""),
        total_scenes=len(scenes),
        status=story["status"],
        created_at=story["created_at"],
        original_title=original_title,  # Include original_title in response
        archived=archived_status  # Include archived status
    )


# Query Endpoints
@app.post("/api/search")
async def search_stories(query: SearchQuery, user_id: int = Depends(get_current_user)):
    """Search stories by keywords"""
    stories = get_user_stories(user_id)
    # Simple keyword search (can be improved with full-text search)
    results = [s for s in stories if query.query.lower() in s["title"].lower() or query.query.lower() in s.get("user_prompt", "").lower()]
    
    log_user_query(user_id, query.query, "search", len(results))
    
    return results


@app.post("/api/filter")
async def filter_stories(filter_query: FilterQuery, user_id: int = Depends(get_current_user)):
    """Filter stories by genre, style, date"""
    stories = get_user_stories(user_id)
    results = stories
    
    if filter_query.genre:
        results = [s for s in results if s.get("genre") == filter_query.genre]
    if filter_query.style:
        results = [s for s in results if s.get("style") == filter_query.style]
    
    log_user_query(user_id, json.dumps(filter_query.dict()), "filter", len(results))
    
    return results


@app.post("/api/categorize")
async def categorize_story(request: CategorizeRequest, user_id: int = Depends(get_current_user)):
    """Categorize a story"""
    analytics = AnalyticsEngine()
    classification = analytics.classify(request.story_text)
    
    log_user_query(user_id, request.story_text, "categorize", 1)
    
    return classification


# File Upload Endpoint
@app.post("/api/upload-file")
async def upload_file(file: UploadFile = File(...), user_id: int = Depends(get_current_user)):
    """Upload and extract text from file (PDF, DOCX, TXT, or Images)"""
    import tempfile
    import os
    from pathlib import Path
    
    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.txt', '.jpg', '.jpeg', '.png'}
    file_ext = Path(file.filename).suffix.lower() if file.filename else ''
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: PDF, DOCX, TXT, JPG, PNG"
        )
    
    extracted_text = ""
    file_type = file_ext[1:] if file_ext else "unknown"
    
    try:
        # Read file content
        contents = await file.read()
        
        if file_ext == '.pdf':
            # Extract text from PDF
            import PyPDF2
            from io import BytesIO
            pdf_file = BytesIO(contents)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            extracted_text = "\n".join([page.extract_text() for page in pdf_reader.pages])
            
        elif file_ext == '.docx':
            # Extract text from DOCX
            from docx import Document
            from io import BytesIO
            docx_file = BytesIO(contents)
            doc = Document(docx_file)
            extracted_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
        elif file_ext == '.txt':
            # Extract text from TXT
            extracted_text = contents.decode('utf-8', errors='ignore')
            
        elif file_ext in {'.jpg', '.jpeg', '.png'}:
            # For images, we'll use Google Vision API or return a message
            # For now, return a message that image analysis is not yet implemented
            # In the future, could use Google Vision API to extract text from images
            extracted_text = f"[Image file: {file.filename}] Image analysis not yet implemented. Please provide a text description."
        
        # Clean extracted text
        extracted_text = extracted_text.strip()
        
        if not extracted_text:
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the file. Please ensure the file contains readable text."
            )
        
        # Limit text length (first 5000 characters for prompt)
        if len(extracted_text) > 5000:
            extracted_text = extracted_text[:5000] + "... [truncated]"
        
        return {
            "filename": file.filename,
            "file_type": file_type,
            "extracted_text": extracted_text,
            "text_length": len(extracted_text),
            "message": f"File uploaded and processed successfully. Extracted {len(extracted_text)} characters."
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"File upload error: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {error_msg}"
        )


# Health Check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Serve static files (images) - Mount AFTER API routes to avoid conflicts
if os.path.exists("scene_images"):
    app.mount("/scene_images", StaticFiles(directory="scene_images"), name="scene_images")
if os.path.exists("output_scenes"):
    app.mount("/output_scenes", StaticFiles(directory="output_scenes"), name="output_scenes")
if os.path.exists("suggestion"):
    app.mount("/suggestion", StaticFiles(directory="suggestion"), name="suggestion")

