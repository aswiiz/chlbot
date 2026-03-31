import os
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import openai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Cognitive Learning Hub")

# For debugging purposes
print(f"Current working directory: {os.getcwd()}")
print(f"File path: {os.path.abspath(__file__)}")

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.clh_database
subjects_collection = db.subjects

# Mount Frontend static files
# Assuming the main.py is in /backend and index.html is in /frontend
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse(os.path.join(frontend_path, "index.html"))

# AI API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SAMBANOVA_API_KEY = os.getenv("SAMBANOVA_API_KEY")

openai.api_key = OPENAI_API_KEY

# Models
from backend.models import Topic, Subject, ChatRequest, MindMapResponse, Flashcard, FlashcardsResponse

# Helper Functions
def calculate_decay_and_score(last_reviewed: datetime, current_confidence: int):
    now = datetime.utcnow()
    delta = now - last_reviewed
    
    # 3 days -> Slight fade (decreases confidence by 1)
    # 7 days -> Yellow zone (decreases confidence by 2)
    # 14 days -> Red zone (decreases confidence by 3)
    
    decayed_confidence = current_confidence
    if delta.days >= 14:
        decayed_confidence = max(1, current_confidence - 3)
    elif delta.days >= 7:
        decayed_confidence = max(1, current_confidence - 2)
    elif delta.days >= 3:
        decayed_confidence = max(1, current_confidence - 1)
        
    # Status determination based on decayed score
    # 1: Red (Weak)
    # 2: Orange (Weak-Medium)
    # 3: Yellow (Medium)
    # 4: Light Green (Good)
    # 5: Green (Strong)
    
    status = "Strong"
    if decayed_confidence == 1:
        status = "Weak" # Red
    elif decayed_confidence == 2:
        status = "Medium-Weak" # Orange
    elif decayed_confidence == 3:
        status = "Medium" # Yellow
    elif decayed_confidence == 4:
        status = "Good" # Light Green
        
    return status, decayed_confidence

@app.post("/api/subjects/")
async def add_subject(subject: Subject):
    subject_dict = subject.dict()
    result = await subjects_collection.insert_one(subject_dict)
    return {"id": str(result.inserted_id), **subject_dict}

@app.get("/api/subjects/")
async def get_subjects():
    subjects = await subjects_collection.find().to_list(100)
    
    def process_node(node):
        last_rev = node.get("last_reviewed")
        if last_rev:
            if isinstance(last_rev, str):
                last_rev = datetime.fromisoformat(last_rev)
            status, score = calculate_decay_and_score(last_rev, node.get("confidence", 3))
            node["decay_status"] = status
            node["current_score"] = score
        
        for child in node.get("children", []):
            process_node(child)

    for s in subjects:
        s["id"] = str(s["_id"])
        del s["_id"]
        for topic in s.get("topics", []):
            process_node(topic)
    return subjects

@app.post("/api/subjects/{subject_name}/topics/")
async def add_topic(subject_name: str, topic: Topic):
    topic_dict = topic.dict()
    # Update subject by adding topic
    await subjects_collection.update_one(
        {"name": subject_name},
        {"$push": {"topics": topic_dict}}
    )
    return topic_dict

@app.patch("/api/subjects/{subject_name}/topics/{topic_name}")
async def update_topic_confidence(subject_name: str, topic_name: str, confidence: int = Body(..., embed=True)):
    await subjects_collection.update_one(
        {"name": subject_name, "topics.name": topic_name},
        {"$set": {"topics.$.confidence": confidence, "topics.$.last_reviewed": datetime.utcnow()}}
    )
    return {"message": "Confidence updated"}

# AI Endpoints
@app.post("/api/ai/mindmap", response_model=MindMapResponse)
async def generate_mindmap(topic: str, subject: str = ""):
    sys_prompt = "Generate a Mermaid.js mind map for the given topic. Only return the Mermaid code (graph LR or mindmap ...). Ensure it is structured hierarchically. Include nodes for: Introduction, Key Concepts, Examples, and Applications."
    prompt = f"Topic: {topic} (Subject: {subject})"
    
    try:
        # Check if we should use SambaNova
        if SAMBANOVA_API_KEY:
            client = openai.OpenAI(
                api_key=SAMBANOVA_API_KEY,
                base_url="https://api.sambanova.ai/v1",
            )
            response = client.chat.completions.create(
                model="DeepSeek-R1",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            mermaid_code = response.choices[0].message.content.strip()
        else:
            # Fallback to OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            mermaid_code = response.choices[0].message.content.strip()
        
        # Clean up code blocks if present
        if "```mermaid" in mermaid_code:
            mermaid_code = mermaid_code.split("```mermaid")[1].split("```")[0].strip()
        elif "```" in mermaid_code:
            mermaid_code = mermaid_code.split("```")[1].split("```")[0].strip()
        
        return MindMapResponse(mermaid_code=mermaid_code)
    except Exception as e:
        return MindMapResponse(mermaid_code=f"graph TD\n    A[{topic}] --> B[No AI response, try again]")

@app.post("/api/ai/flashcards")
async def generate_flashcards(topic: str):
    sys_prompt = "Generate 5 flashcards for the given topic. Return only a JSON array of objects with 'front' and 'back' fields. No other text."
    prompt = f"Topic: {topic}"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": prompt}]
        )
        import json
        flashcards = json.loads(response.choices[0].message.content.strip())
        return {"flashcards": flashcards}
    except Exception as e:
        return {"error": str(e), "flashcards": []}

@app.post("/api/ai/chat")
async def ai_chat(req: ChatRequest):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are CLH AI Assistant. Help the student with topic explanation, revision strategies, and generating study resources. Current Subject: {req.subject}. Current Topic: {req.topic}."},
                {"role": "user", "content": req.message}
            ]
        )
        return {"reply": response.choices[0].message.content}
    except Exception as e:
        return {"reply": f"Sorry, AI Assistant is currently offline. Error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
