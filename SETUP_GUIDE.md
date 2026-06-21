# Setup Guide - Story-to-Scene Generator

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
REPLICATE_API_TOKEN=your_replicate_token_here
DATABASE_URL=sqlite:///./database/story_scenes.db
```

### 3. Initialize Database
```bash
python init_database.py
```

### 4. Start Backend Server
```bash
python main.py
```
Or use:
- Windows: `run_server.bat`
- Linux/Mac: `chmod +x run_server.sh && ./run_server.sh`

The API will be available at: `http://localhost:8000`

### 5. Open Frontend
Open `index.html` in your browser, or serve it:
```bash
# Using Python
cd ui  # if you moved index.html to ui folder
python -m http.server 8080
```

Then open: `http://localhost:8080`

## Project Structure

```
Front 2 - Copy (2)/
├── src/                    # Backend code
│   ├── api.py             # FastAPI server
│   ├── scene_generator.py # Scene generation
│   ├── image_generator.py # Image generation
│   ├── analytics.py       # Analytics features
│   ├── memory.py          # Agent memory
│   ├── database.py        # Database operations
│   └── models.py          # Pydantic models
├── ui/                     # Frontend (if moved)
│   ├── index.html
│   ├── js/app.js
│   └── styles/
├── data/                   # Datasets
│   └── story_templates.json
├── database/               # Database files
│   ├── schema.sql
│   └── story_scenes.db
├── index.html             # Main HTML file
├── js/app.js              # Frontend JavaScript
├── styles/                # CSS files
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
└── README.md
```

## Features Implemented

✅ **Authentication System**
- User registration and login
- Session management with localStorage
- Protected routes

✅ **Story Generation**
- Convert prompts to scenes
- Multiple visual styles
- Scene-by-scene breakdown

✅ **Image Generation**
- Generate images for scenes
- Visual consistency across scenes

✅ **Agent Memory**
- Conversation history
- Long-term user preferences
- Story context

✅ **Analytics**
- Story summarization
- Genre/style classification
- Pattern detection

✅ **Database**
- User management
- Story storage
- Scene storage
- Conversation logs
- Agent decisions
- Query logs

✅ **UI/UX**
- Beautiful, modern design
- Login/Signup modals
- Responsive layout
- Real-time updates

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register
- `POST /api/auth/login` - Login

### Stories
- `POST /api/generate-scenes` - Generate scenes
- `POST /api/generate-images/{story_id}` - Generate images
- `GET /api/history` - Get history
- `GET /api/story/{story_id}` - Get story

### Queries
- `POST /api/search` - Search stories
- `POST /api/filter` - Filter stories
- `POST /api/categorize` - Categorize

## Troubleshooting

### Database Errors
If you get database errors, run:
```bash
python init_database.py
```

### CORS Errors
Make sure the frontend URL matches the CORS settings in `src/api.py`

### API Connection Errors
1. Check if backend is running on port 8000
2. Update `API_BASE_URL` in `js/app.js` if needed
3. Check browser console for errors

### Import Errors
Make sure you're running from the project root:
```bash
python -m src.api
```

## Next Steps

1. **Test the Application**
   - Sign up a new user
   - Create a story
   - Generate scenes
   - Generate images

2. **Customize**
   - Update API_BASE_URL in `js/app.js` for production
   - Add JWT authentication (currently using simple token)
   - Implement file upload extraction (PDF/DOCX)

3. **Deploy**
   - Backend: Deploy to Render/Railway
   - Frontend: Deploy to Vercel/Netlify
   - Update CORS settings for production

## Notes

- Authentication uses simple user_id tokens (not secure for production)
- For production, implement JWT tokens
- File upload extraction is placeholder (needs implementation)
- Image generation may take time (10s delay between images)

