<div align="center">

# Agent Stories

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)](https://python.langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**Transform your stories into cinematic visual experiences using AI.**

<p align="center">
  <a href="#features">Features</a> •
  <a href="#demo">Demo</a> •
  <a href="#setup">Setup</a> •
  <a href="#project-structure">Structure</a> •
  <a href="#api-endpoints">API</a> •
  <a href="#tech-stack">Tech Stack</a>
</p>

</div>

---

## Overview

Agent Stories takes a story prompt or uploaded document and uses Google Gemini to break it into cinematic scenes — each with a generated image. Visual consistency is maintained across all scenes so characters, lighting, and environments stay coherent throughout the storyboard.

---

## Features

- **Story Generation** — Converts prompts or uploaded files (`.pdf`, `.docx`, `.txt`) into detailed multi-scene cinematic scripts
- **AI Image Generation** — Powered by Google Gemini with visual continuity across scenes
- **5 Visual Styles** — Cinematic, Anime, Watercolor, Noir, Cyberpunk
- **User Accounts** — Register, login, manage your story history
- **Story Management** — Rename, archive, delete, and share stories via public links
- **Agent Memory** — Remembers user preferences and story context across sessions
- **Analytics** — Built-in summarization, genre classification, and narrative pattern detection
- **File Upload** — Drag and drop PDF, DOCX, or TXT files as story input
- **Search & Filter** — Find past stories by keyword, genre, or style

---

## Demo

The `suggestion/` folder contains sample stories and their generated scene images so you can see what the app produces before running it yourself.

---

## Screenshots

**Landing Screen**
![landing_screen](https://github.com/hassanayoub409/agent-stories/blob/c0541cb5cb042d54f049971ec5a69c5611c30e90/landing_screen.png)


**Given a story like:**

The wind in the coastal town never stopped moving, as if it were afraid that stillness might make it forget. On the morning the boy 
decided to leave, he stood on the rooftop of his house and held a paper glider between his fingers, feeling the air test its wings. 
He had folded it years ago with someone whose face he could no longer recall clearly, only the sound of her laughter and the way she 
always leaned into the wind instead of away from it. People said memories faded because time demanded space for new ones, but the boy 
believed they faded because they were afraid of being carried too far. He had stayed longer than he meant to, returning each day to the 
same rooftop, releasing the same fragile gliders, watching them rise and fall like thoughts that refused to settle. The town below 
continued its quiet routines—fishermen mending nets, windmills creaking, waves pressing themselves against the shore as if asking to be 
let in. On his final morning, the wind grew stronger than usual. The glider tore at one edge, yet instead of falling, it rose higher 
than any before it. The boy ran down the stairs and through the streets, chasing the white flicker against the blue sky, until he reached 
the cliffs where the land finally gave up and became air. There, the wind caught the glider fully and carried it out over the sea, 
where it dissolved into distance. For the first time, the boy did not feel loss. He felt answered. He turned away from the ocean,
shouldered his bag, and walked toward the road leading out of town. Behind him, the wind kept moving—not to hold him, but to remember 
him.

The following story-book is generated:
![page1](https://github.com/hassanayoub409/agent-stories/blob/c0541cb5cb042d54f049971ec5a69c5611c30e90/page1.png)
![page2](https://github.com/hassanayoub409/agent-stories/blob/c0541cb5cb042d54f049971ec5a69c5611c30e90/page2.png)
![page3](https://github.com/hassanayoub409/agent-stories/blob/c0541cb5cb042d54f049971ec5a69c5611c30e90/page3.png)
![page4](https://github.com/hassanayoub409/agent-stories/blob/c0541cb5cb042d54f049971ec5a69c5611c30e90/page4.png)
![page5](https://github.com/hassanayoub409/agent-stories/blob/c0541cb5cb042d54f049971ec5a69c5611c30e90/page5.png)
---

## Setup

### Prerequisites

- Python 3.10 or higher
- A Google Gemini API key — get one free at [aistudio.google.com](https://aistudio.google.com/app/apikey)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/agent-stories.git
cd agent-stories
```

### 2. Create a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and add your Gemini API key:

```env
GOOGLE_API_KEY=your_actual_gemini_api_key_here
DATABASE_URL=sqlite:///./database/story_scenes.db
```

### 5. Initialize the database

```bash
python init_database.py
```

### 6. Start the backend server

**macOS / Linux:**
```bash
chmod +x run_server.sh
./run_server.sh
```

**Windows:**
```bash
run_server.bat
```

**Or manually:**
```bash
python main.py
```

The API will be available at `http://localhost:8000`  
Interactive API docs at `http://localhost:8000/docs`

### 7. Open the frontend

Open `index.html` directly in your browser, or serve it locally:

```bash
python -m http.server 8080
```

Then visit `http://localhost:8080`

---

## Usage

1. **Sign up** — Create a free account
2. **Input** — Type a story prompt or drag and drop a file (PDF, DOCX, TXT)
3. **Style** — Choose a visual style (Cinematic, Anime, Watercolor, Noir, Cyberpunk)
4. **Generate Scenes** — The AI breaks your story into cinematic scenes
5. **Generate Images** — Bring each scene to life with AI-generated visuals
6. **Share** — Use the share button to get a public link to your story

---

## Project Structure

```
Agent-Stories/
├── main.py                    # Entry point — starts the FastAPI server
├── init_database.py           # Database initialization script
├── run_server.sh              # Launch script (macOS/Linux)
├── run_server.bat             # Launch script (Windows)
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
│
├── src/
│   ├── api.py                 # FastAPI routes and endpoints
│   ├── scene_generator.py     # Story-to-scene logic (LangChain + Gemini)
│   ├── image_generator.py     # Image generation with visual continuity
│   ├── analytics.py           # Summarization, classification, pattern detection
│   ├── memory.py              # Agent memory and user preferences
│   ├── database.py            # SQLite database operations
│   └── models.py              # Pydantic request/response models
│
├── database/
│   └── schema.sql             # Database schema
│
├── data/
│   └── story_templates.json   # Story template data
│
├── suggestion/                # Sample stories and pre-generated scene images
│
├── scene_images/              # Runtime generated scene images
│
├── index.html                 # Frontend entry point
├── js/
│   └── app.js                 # Frontend logic and API integration
└── styles/
    ├── main.css
    ├── components.css
    ├── layout.css
    └── animations.css
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Register a new user |
| `POST` | `/api/auth/login` | Login and receive token |

### Story Generation
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/generate-scenes` | Generate scenes from a story prompt |
| `POST` | `/api/generate-images/{story_id}` | Generate images for all scenes |
| `GET` | `/api/story/{story_id}` | Get full story details |
| `GET` | `/api/story/{story_id}/public` | Get story without auth (for sharing) |
| `PUT` | `/api/story/{story_id}` | Rename a story |
| `DELETE` | `/api/story/{story_id}` | Delete a story |
| `POST` | `/api/story/{story_id}/archive` | Archive a story |
| `POST` | `/api/story/{story_id}/unarchive` | Unarchive a story |

### History & Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/history` | Get all user stories |
| `GET` | `/api/history/archived` | Get archived stories |
| `POST` | `/api/search` | Search stories by keyword |
| `POST` | `/api/filter` | Filter stories by genre or style |
| `POST` | `/api/categorize` | Classify a story's genre and style |

### Other
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload-file` | Upload and extract text from a file |
| `GET` | `/api/health` | Health check |

Full interactive docs available at `http://localhost:8000/docs` when the server is running.

---

## Troubleshooting

**Database errors** — Re-run `python init_database.py`

**CORS errors** — Make sure the backend is running on port 8000 before opening the frontend

**API quota errors** — The app handles Gemini rate limits gracefully. If image generation is interrupted, your story is saved and you can retry image generation later from your history

**Import errors** — Make sure you're running commands from the project root, not from inside `src/`

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI, Python |
| AI — Text | Google Gemini 2.5 Flash via LangChain |
| AI — Images | Google Gemini 2.5 Flash Image |
| Database | SQLite |
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Validation | Pydantic |

---

## Important Notes

- **Authentication** — The current token system uses a simplified user ID token. This is suitable for local use and demos. For production deployment, replace with proper JWT authentication.
- **API Keys** — Never commit your `.env` file. It is already excluded via `.gitignore`.
- **Rate Limits** — Gemini API has free tier rate limits. Image generation may slow down for longer stories.

---

## Authors

**Hassan Ayoub** — 2025

**Shahram Munsaf** — 2025

**Own Mustafvi** — 2025

**Abdul Basit** — 2025


---

## License
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

**This project was developed as a part of Artificial Intelligence course requirement at Punjab University College of Information Technology.**
