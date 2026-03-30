# Cognitive Learning Hub (CLH)

An AI-driven retention and visual analytics learning platform.

## Features
- **Dashboard**: Confidence heatmap, weak topics, and recently studied.
- **Subject/Topic Management**: Add subjects and track memory decay.
- **Visual Learning**: AI-powered Mind Maps and Flowcharts (Mermaid.js).
- **Revision Tools**: Flashcard generator and AI summary.
- **AI Buddy**: Chat with an AI assistant to clarify topics.

## Setup & Hosting
1.  **Clone & Prepare**:
    - Project structure: `/backend` (API), `/frontend` (UI).
    - Create a `.env` in the root or `backend/` with `MONGODB_URI` and `OPENAI_API_KEY`.
2.  **Locally**:
    - Install: `pip install -r requirements.txt`
    - Run: `uvicorn backend.main:app --reload`
    - Open: `http://localhost:8000`
3.  **Hosting (Single Server)**:
    - This project is configured to serve the frontend from the FastAPI backend.
    - Simply deploy to Render, Heroku, or any server with Python support.
    - Use `Procfile` for platform-specific deployment commands.

## Tech Stack
- **Backend**: FastAPI, MongoDB (Motor), OpenAI API.
- **Frontend**: HTML5, Vanilla CSS (Glassmorphism), Vanilla JS.
- **Visualization**: Mermaid.js for Mind Maps/Flowcharts.
