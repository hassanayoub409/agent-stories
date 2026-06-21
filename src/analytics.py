"""
Analytics Features: Summarization, Classification, Pattern Detection
"""
import json
from typing import Dict, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

class AnalyticsEngine:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        # Configure LLM with no retries on rate limits
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            max_retries=0,  # Disable automatic retries
            temperature=0.7
        )
        
        # Summarization Template
        self.summarize_template = PromptTemplate(
            input_variables=["text", "type"],
            template=(
                "You are a professional story analyst. "
                "Create a concise {type} summary of the following text. "
                "Keep it brief (2-3 sentences for story, 1 sentence for scene).\n\n"
                "Text:\n\"\"\"\n{text}\n\"\"\"\n\n"
                "Summary:"
            )
        )
        
        # Classification Template
        self.classify_template = PromptTemplate(
            input_variables=["text"],
            template=(
                "You are a story classifier. Analyze the following story and classify it. "
                "Return ONLY a JSON object with these keys: "
                "genre (one of: Mystery, Sci-Fi, Fantasy, Romance, Thriller, Horror, Drama, Comedy, Action, Adventure), "
                "style (one of: Cinematic, Anime, Watercolor, Noir, Cyberpunk, Realistic, Abstract), "
                "scene_type (one of: Action, Dialogue, Setting, Transition, Climax, Resolution). "
                "Do not include any explanation or code fences.\n\n"
                "Story:\n\"\"\"\n{text}\n\"\"\""
            )
        )
        
        # Pattern Detection Template
        self.pattern_template = PromptTemplate(
            input_variables=["scenes"],
            template=(
                "You are a narrative pattern analyst. Analyze the following scenes and detect patterns. "
                "Return ONLY a JSON object with these keys: "
                "narrative_structure (one of: Three-Act, Hero's Journey, Linear, Non-Linear, Episodic), "
                "themes (array of recurring themes), "
                "character_arcs (array of character development patterns), "
                "visual_consistency_score (0-1, how consistent the visual style is), "
                "pacing (one of: Fast, Medium, Slow). "
                "Do not include any explanation or code fences.\n\n"
                "Scenes:\n\"\"\"\n{scenes}\n\"\"\""
            )
        )
        
        # Title Generation Template
        self.title_template = PromptTemplate(
            input_variables=["prompt"],
            template=(
                "You are a creative story title generator. Based on the following story prompt, "
                "generate a compelling, concise title (2-6 words maximum). "
                "The title should be engaging and capture the essence of the story. "
                "Return ONLY the title text, nothing else. No quotes, no explanation, just the title.\n\n"
                "Story Prompt:\n\"\"\"\n{prompt}\n\"\"\"\n\n"
                "Title:"
            )
        )
    
    def summarize(self, text: str, summary_type: str = "story") -> str:
        """Generate a summary of the text"""
        try:
            prompt = self.summarize_template.format(text=text, type=summary_type)
            response = self.llm.predict(prompt)
            return response.strip()
        except Exception as e:
            print(f"Summarization error: {e}")
            return f"Summary: {text[:100]}..." if len(text) > 100 else text
    
    def classify(self, text: str) -> Dict:
        """Classify story by genre, style, and scene type"""
        try:
            prompt = self.classify_template.format(text=text)
            response = self.llm.predict(prompt)
            # Clean response (remove markdown code blocks if present)
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            classification = json.loads(response)
            return classification
        except Exception as e:
            print(f"Classification error: {e}")
            return {
                "genre": "Drama",
                "style": "Cinematic",
                "scene_type": "Setting"
            }
    
    def detect_patterns(self, scenes: List[Dict]) -> Dict:
        """Detect narrative patterns in scenes"""
        try:
            scenes_text = "\n".join([
                f"Scene {s.get('scene_number', i+1)}: {s.get('scene_text', '')}"
                for i, s in enumerate(scenes)
            ])
            prompt = self.pattern_template.format(scenes=scenes_text)
            response = self.llm.predict(prompt)
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            patterns = json.loads(response)
            return patterns
        except Exception as e:
            print(f"Pattern detection error: {e}")
            return {
                "narrative_structure": "Linear",
                "themes": [],
                "character_arcs": [],
                "visual_consistency_score": 0.7,
                "pacing": "Medium"
            }
    
    def generate_title(self, prompt: str) -> str:
        """Generate a compelling title from story prompt"""
        try:
            prompt_text = self.title_template.format(prompt=prompt)
            response = self.llm.predict(prompt_text)
            # Clean response - remove quotes, extra whitespace, etc.
            title = response.strip()
            # Remove surrounding quotes if present
            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1]
            elif title.startswith("'") and title.endswith("'"):
                title = title[1:-1]
            # Limit to reasonable length (50 chars max)
            if len(title) > 50:
                title = title[:47] + "..."
            return title.strip()
        except Exception as e:
            print(f"Title generation error: {e}")
            # Fallback: create a title from first few words
            words = prompt.split()[:6]
            return " ".join(words) + ("..." if len(prompt.split()) > 6 else "")