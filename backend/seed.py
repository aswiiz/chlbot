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
    
    subjects_data = [
        {
            "name": "Engineering Physics",
            "topics": [
                {
                    "title": "Photonics",
                    "confidence": 3,
                    "children": [
                        {
                            "title": "Introduction",
                            "note": "Photonics is the physical science of light (photon) generation, detection, and manipulation through emission, transmission, modulation, signal processing, switching, amplification, and sensing.",
                            "confidence": 5,
                            "children": [
                                {"title": "Definition", "note": "The study of photons, the fundamental particles of light.", "confidence": 5},
                                {"title": "Optics", "note": "The branch of physics that studies the behavior and properties of light.", "confidence": 4}
                            ]
                        },
                        {
                            "title": "Photodetectors",
                            "note": "Devices that sense light or other electromagnetic radiation.",
                            "confidence": 2,
                            "children": [
                                {"title": "PIN Photodiode", "note": "Structure: p-region, intrinsic region, n-region. High speed and sensitivity.", "confidence": 2},
                                {"title": "Avalanche Photodiode", "note": "Uses the photoelectric effect to convert light to electricity with internal gain.", "confidence": 1}
                            ]
                        }
                    ]
                },
                {"title": "Lasers", "confidence": 4, "children": []},
                {"title": "Fiber Optics", "confidence": 5, "children": []},
                {"title": "Semiconductor", "confidence": 2, "children": []}
            ]
        },
        {
            "name": "Programming",
            "topics": [
                {"title": "Python", "confidence": 5, "children": []},
                {"title": "Data Structures", "confidence": 3, "children": []},
                {"title": "Web Development", "confidence": 4, "children": []}
            ]
        },
        {
            "name": "Mathematics",
            "topics": [
                {"title": "Calculus", "confidence": 2, "children": []},
                {"title": "Linear Algebra", "confidence": 4, "children": []}
            ]
        },
        {
            "name": "Electronics",
            "topics": [
                {"title": "Digital Circuits", "confidence": 5, "children": []},
                {"title": "Analog Design", "confidence": 3, "children": []}
            ]
        }
    ]
    
    await subjects_collection.insert_many(subjects_data)
    print("Seed data inserted successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
