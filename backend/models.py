from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Any

class Topic(BaseModel):
    title: str
    note: Optional[str] = None
    confidence: int = Field(3, ge=1, le=5)  # 1: Red, 3: Yellow, 5: Green
    last_reviewed: datetime = Field(default_factory=datetime.utcnow)
    decay_status: str = "Strong"
    children: List['Topic'] = []

# For Pydantic V2 compatibility
if hasattr(Topic, "model_rebuild"):
    Topic.model_rebuild()
else:
    Topic.update_forward_refs()

class Subject(BaseModel):
    name: str
    topics: List[Topic] = []

class User(BaseModel):
    username: str
    subjects: List[Subject] = []

class ChatRequest(BaseModel):
    message: str
    topic: Optional[str] = None
    subject: Optional[str] = None

class MindMapResponse(BaseModel):
    mermaid_code: str

class Flashcard(BaseModel):
    front: str
    back: str

class FlashcardsResponse(BaseModel):
    flashcards: List[Flashcard]
