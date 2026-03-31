import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

subjects_data = [
    {
        "name": "Chemistry",
        "topics": [
            {
                "title": "Water Characteristics and Waste Management",
                "confidence": 3,
                "children": [
                    {
                        "title": "Water Hardness",
                        "confidence": 3,
                        "children": [
                            {"title": "Temporary Hardness", "confidence": 3},
                            {"title": "Permanent Hardness", "confidence": 3},
                            {"title": "Measurement", "confidence": 3},
                            {"title": "Disadvantages", "confidence": 3}
                        ]
                    },
                    {
                        "title": "Water Treatment",
                        "confidence": 3,
                        "children": [
                            {"title": "Boiling Method", "confidence": 3},
                            {"title": "Ion Exchange", "confidence": 3},
                            {"title": "Reverse Osmosis", "confidence": 3},
                            {"title": "Demineralization", "confidence": 3}
                        ]
                    },
                    {
                        "title": "Water Quality Parameters",
                        "confidence": 3,
                        "children": [
                            {"title": "Dissolved Oxygen", "confidence": 3},
                            {"title": "BOD", "confidence": 3},
                            {"title": "COD", "confidence": 3}
                        ]
                    },
                    {
                        "title": "Sewage Treatment",
                        "confidence": 3,
                        "children": [
                            {"title": "Primary Treatment", "confidence": 3},
                            {"title": "Secondary Treatment", "confidence": 3},
                            {"title": "Tertiary Treatment", "confidence": 3}
                        ]
                    },
                    {
                        "title": "Waste Management",
                        "confidence": 3,
                        "children": [
                            {"title": "E-Waste", "confidence": 3},
                            {"title": "4R Concept", "confidence": 3},
                            {"title": "Sustainable Development", "confidence": 3}
                        ]
                    },
                    {
                        "title": "Environmental Issues",
                        "confidence": 3,
                        "children": [
                            {"title": "Greenhouse Effect", "confidence": 3},
                            {"title": "Ozone Layer Depletion", "confidence": 3},
                            {"title": "Global Warming", "confidence": 3}
                        ]
                    }
                ]
            }
        ]
    },
    {
        "name": "Engineering Physics",
        "topics": [
            {
                "title": "Photonics",
                "confidence": 3,
                "children": [
                    {
                        "title": "Introduction",
                        "confidence": 3,
                        "children": [
                            {"title": "Definition", "confidence": 3},
                            {"title": "Optics", "confidence": 3},
                            {"title": "Quantum Mechanics", "confidence": 3},
                            {"title": "Electromagnetism", "confidence": 3}
                        ]
                    },
                    {
                        "title": "Advantages",
                        "confidence": 3,
                        "children": [
                            {"title": "High Bandwidth", "confidence": 3},
                            {"title": "Low Power Consumption", "confidence": 3},
                            {"title": "Increased Security", "confidence": 3},
                            {"title": "Higher Reliability", "confidence": 3}
                        ]
                    },
                    {
                        "title": "Photodetectors",
                        "confidence": 3,
                        "children": [
                            {
                                "title": "Types",
                                "confidence": 3,
                                "children": [
                                    {"title": "Junction Photodiode", "confidence": 3},
                                    {"title": "PIN Photodiode", "confidence": 3},
                                    {"title": "Avalanche Photodiode", "confidence": 3},
                                    {"title": "Schottky Photodiode", "confidence": 3}
                                ]
                            },
                            {
                                "title": "Requirements",
                                "confidence": 3,
                                "children": [
                                    {"title": "High Sensitivity", "confidence": 3},
                                    {"title": "Short Response Time", "confidence": 3},
                                    {"title": "Low Bias Voltage", "confidence": 3}
                                ]
                            }
                        ]
                    },
                    {
                        "title": "Solar Cells",
                        "confidence": 3,
                        "children": [
                            {"title": "Photovoltaic Effect", "confidence": 3},
                            {"title": "I-V Characteristics", "confidence": 3},
                            {"title": "Configuration", "confidence": 3},
                            {"title": "Advantages and Disadvantages", "confidence": 3}
                        ]
                    },
                    {
                        "title": "LED",
                        "confidence": 3,
                        "children": [
                            {"title": "Working Principle", "confidence": 3},
                            {"title": "Materials and Colors", "confidence": 3},
                            {"title": "Features", "confidence": 3},
                            {"title": "Applications", "confidence": 3}
                        ]
                    },
                    {
                        "title": "Applications",
                        "confidence": 3,
                        "children": [
                            {"title": "Communication", "confidence": 3},
                            {"title": "Medicine", "confidence": 3},
                            {"title": "Consumer Electronics", "confidence": 3},
                            {"title": "Satellites", "confidence": 3},
                            {"title": "Automotive Lighting", "confidence": 3}
                        ]
                    }
                ]
            }
        ]
    }
]

async def seed():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.clh_database
    subjects_collection = db.subjects
    
    # Clear existing
    await subjects_collection.delete_many({})
    await subjects_collection.insert_many(subjects_data)
    print("Seed data updated successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
