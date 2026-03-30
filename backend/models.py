from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class Topic(BaseModel):
    name: str
    confidence: int = Field(1, ge=1, le=5)
    last_reviewed: datetime = Field(default_factory=datetime.utcnow)
    decay_status: str = "Strong"
    score: float = 5.0 # normalized score?

class Subject(BaseModel):
    name: str
    syllabus: List[str] = []
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
