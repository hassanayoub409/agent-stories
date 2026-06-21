import os
import json
import re
from typing import List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import threading
import queue

load_dotenv()

OUTPUT_DIR = "output_scenes"
SCENES_FILE = "scenes.json"
MAX_SCENES = 8

def ensure_output_dir(path: str):
    os.makedirs(path, exist_ok=True)

def clean_json_response(response_text: str) -> str:
    """Clean JSON response from LLM (remove markdown code blocks)"""
    response_text = response_text.strip()
    # Remove markdown code blocks
    if response_text.startswith("```"):
        response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)
    return response_text.strip()

class SceneGenerator:
    def __init__(self, model_name: str = "gemini-2.5-flash", max_scenes: int = MAX_SCENES):
        # Configure LLM with no retries on rate limits - stop immediately on 429 errors
        # max_retries=0 means no automatic retries, but langchain still retries internally
        # We'll handle timeouts manually to prevent infinite retries
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            max_retries=0,  # Disable automatic retries
            temperature=0.7
        )
        self.max_scenes = max_scenes

        self.template = PromptTemplate(
            input_variables=["story", "max_scenes"],
            template=(
                "You are a cinematic scene generator. "
                "Split the following story into numbered scenes with short descriptions but do not disrupt the context of story, "
                "then generate cinematic prompts for each scene suitable for image generation. "
                "Return JSON list with keys: scene_number, scene_text, cinematic_prompt. "
                "Do not include any explanation or code fences.\n\n"
                "Generate at least 4 and at most {max_scenes} scenes.\n\n"
                "Story:\n\"\"\"\n{story}\n\"\"\""
            )
        )

    def generate_scenes(self, story: str) -> List[Dict]:
        prompt = self.template.format(story=story, max_scenes=self.max_scenes)

        # Use threading with timeout to prevent infinite retries on rate limits
        result_queue = queue.Queue()
        exception_queue = queue.Queue()
        max_wait_time = 30  # 30 second timeout for scene generation
        
        def run_llm():
            try:
                response_text = self.llm.predict(prompt)
                result_queue.put(response_text)
            except Exception as e:
                exception_queue.put(e)
        
        # Start LLM call in a thread
        thread = threading.Thread(target=run_llm, daemon=True)
        thread.start()
        thread.join(timeout=max_wait_time)
        
        # Check if thread is still running (timeout occurred)
        if thread.is_alive():
            raise Exception(f"Scene generation timed out after {max_wait_time} seconds. API quota may be exceeded.")
        
        # Check for exceptions
        if not exception_queue.empty():
            e = exception_queue.get()
            error_msg = str(e)
            # Check for rate limit/quota errors
            if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower() or "ResourceExhausted" in error_msg:
                raise Exception(f"API quota exceeded: {error_msg}")
            raise e
        
        # Get result
        if result_queue.empty():
            raise Exception("Scene generation failed - no result returned")
        
        response_text = result_queue.get()
        
        # Clean the response
        response_text = clean_json_response(response_text)
        
        try:
            scenes = json.loads(response_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                scenes = json.loads(json_match.group())
            else:
                # Fallback: create a simple scene structure
                scenes = [{
                    "scene_number": 1,
                    "scene_text": story[:200] + "..." if len(story) > 200 else story,
                    "cinematic_prompt": f"Cinematic scene: {story[:150]}"
                }]

        # Ensure scenes is a list
        if not isinstance(scenes, list):
            scenes = [scenes]

        if len(scenes) > self.max_scenes:
            scenes = scenes[:self.max_scenes]

        return scenes

    def save_scenes(self, scenes: List[Dict], output_dir: str = OUTPUT_DIR):
        ensure_output_dir(output_dir)
        path = os.path.join(output_dir, SCENES_FILE)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(scenes, f, indent=2)
        print(f"Saved {len(scenes)} scenes to {path}")
