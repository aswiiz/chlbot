import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.clh_database
subjects_collection = db.subjects

async def seed():
    # Clear existing
    await subjects_collection.delete_many({})
    
    # Add Engineering Mathematics (Strong)
    await subjects_collection.insert_one({
        "name": "Engineering Mathematics",
        "topics": [
            {"name": "Linear Algebra", "confidence": 5, "last_reviewed": datetime.utcnow(), "decay_status": "Strong"},
            {"name": "Calculus", "confidence": 4, "last_reviewed": datetime.utcnow() - timedelta(days=2), "decay_status": "Strong"}
        ]
    })
    
    # Add Physics (Weak/Decaying)
    await subjects_collection.insert_one({
        "name": "Physics II",
        "topics": [
            {"name": "Electromagnetism", "confidence": 2, "last_reviewed": datetime.utcnow() - timedelta(days=15), "decay_status": "Weak"},
            {"name": "Quantum Mechanics", "confidence": 1, "last_reviewed": datetime.utcnow() - timedelta(days=8), "decay_status": "Medium"}
        ]
    })
    
    # Add C Programming
    await subjects_collection.insert_one({
        "name": "C Programming",
        "topics": [
            {"name": "Pointers", "confidence": 3, "last_reviewed": datetime.utcnow() - timedelta(days=4), "decay_status": "Slightly Faded"},
            {"name": "Structs", "confidence": 5, "last_reviewed": datetime.utcnow(), "decay_status": "Strong"}
        ]
    })
    
    print("Seed data inserted!")

if __name__ == "__main__":
    asyncio.run(seed())
