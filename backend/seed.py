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
                ],
                "flashcards": [
                    {
                        "title": "Water Hardness",
                        "cards": [
                            {"question": "What is water hardness?", "answer": "Water hardness is the property of water that prevents lather formation with soap due to calcium and magnesium salts."},
                            {"question": "What is temporary hardness?", "answer": "Temporary hardness is caused by bicarbonates of calcium and magnesium and can be removed by boiling."},
                            {"question": "What is permanent hardness?", "answer": "Permanent hardness is caused by chlorides and sulphates of calcium and magnesium and cannot be removed by boiling."},
                            {"question": "How is hardness expressed?", "answer": "Hardness is expressed in CaCO3 equivalents."}
                        ]
                    },
                    {
                        "title": "Water Treatment",
                        "cards": [
                            {"question": "What is ion exchange method?", "answer": "Ion exchange removes dissolved ions using cation and anion exchange resins."},
                            {"question": "What is reverse osmosis?", "answer": "Reverse osmosis removes dissolved salts using pressure and semi permeable membrane."}
                        ]
                    },
                    {
                        "title": "Water Quality Assessment",
                        "cards": [
                            {"question": "What is Dissolved Oxygen?", "answer": "Dissolved Oxygen is the amount of oxygen present in water."},
                            {"question": "What is BOD?", "answer": "Biological Oxygen Demand is oxygen required by microorganisms to decompose organic matter."},
                            {"question": "What is COD?", "answer": "Chemical Oxygen Demand is oxygen required to oxidize organic and inorganic matter."}
                        ]
                    },
                    {
                        "title": "Sewage Treatment",
                        "cards": [
                            {"question": "What is primary treatment?", "answer": "Primary treatment removes large solids using screening and sedimentation."},
                            {"question": "What is secondary treatment?", "answer": "Secondary treatment uses microorganisms to remove organic matter."},
                            {"question": "What is tertiary treatment?", "answer": "Tertiary treatment removes nutrients and disinfects water."}
                        ]
                    },
                    {
                        "title": "Waste Management",
                        "cards": [
                            {"question": "What are the 4R principles?", "answer": "Reduce, Reuse, Recycle and Recovery."},
                            {"question": "What is e-waste?", "answer": "Discarded electronic devices containing toxic materials."}
                        ]
                    },
                    {
                        "title": "Environmental Chemistry",
                        "cards": [
                            {"question": "What is greenhouse effect?", "answer": "Greenhouse gases trap heat causing global warming."},
                            {"question": "What is ozone depletion?", "answer": "Destruction of ozone layer by CFC gases."},
                            {"question": "What are disinfection methods?", "answer": "Chlorination, Ozonation and UV disinfection."}
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
                ],
                "flashcards": [
                    {
                        "title": "Basics & Advantages",
                        "cards": [
                            {"question": "Define Photonics.", "answer": "The science of light (photon) generation, detection, and manipulation."},
                            {"question": "List two advantages of Photonics.", "answer": "High speed signal propagation and immunity to electromagnetic interference."}
                        ]
                    },
                    {
                        "title": "Photodetectors",
                        "cards": [
                            {"question": "What is a PIN Photodiode?", "answer": "A photodiode with an intrinsic (I) layer between P and N regions to increase depletion width."},
                            {"question": "Define Responsivity.", "answer": "The ratio of generated photocurrent to incident optical power."}
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
    print("Seed data updated successfully with Flashcards!")

if __name__ == "__main__":
    asyncio.run(seed())
