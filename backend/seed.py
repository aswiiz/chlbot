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
                        "note": "Caused by the presence of multivalent cations in water.",
                        "confidence": 4,
                        "children": [
                            {"title": "Temporary Hardness", "note": "Caused by bicarbonates. Removed by boiling. Forms white scum.", "confidence": 5},
                            {"title": "Permanent Hardness", "note": "Caused by chlorides, sulfates, and nitrates of calcium and magnesium. Boiling won't remove it; processes like ion-exchange are needed.", "confidence": 3},
                            {"title": "Measurement", "note": "Usually measured in terms of CaCO3 equivalents in parts per million (ppm).", "confidence": 4},
                            {"title": "Disadvantages", "note": "Scale formation in boilers, excessive soap consumption, and reduced pipe efficiency.", "confidence": 3}
                        ]
                    },
                    {
                        "title": "Water Treatment",
                        "note": "Strategies to make water suitable for industrial or potable use.",
                        "confidence": 3,
                        "children": [
                            {"title": "Demineralization", "note": "The process of removing all dissolved salts using ion-exchange resins.", "confidence": 4},
                            {"title": "Reverse Osmosis", "note": "Applying external pressure against the osmotic pressure to purify water through a semi-permeable membrane.", "confidence": 5},
                            {"title": "Disinfection", "note": "Killing pathogenic microorganisms using chlorination, UV treatment, or ozonization.", "confidence": 4}
                        ]
                    },
                    {
                        "title": "Sewage Treatment",
                        "note": "Treatment of municipal wastewater to remove organic and inorganic pollutants.",
                        "confidence": 2,
                        "children": [
                            {"title": "Primary Treatment", "note": "Physical processes like screening and sedimentation to remove floating and large settleable solids.", "confidence": 3},
                            {"title": "Secondary Treatment", "note": "Biological processes where microbes decompose organic matter (e.g., Activated Sludge Process).", "confidence": 2},
                            {"title": "Tertiary Treatment", "note": "Advanced treatment to remove nutrients, chemicals, and leftover pathogens.", "confidence": 4}
                        ]
                    },
                    {
                        "title": "Water Quality Parameters",
                        "note": "Indicators used to assess the health of water bodies.",
                        "confidence": 4,
                        "children": [
                            {"title": "BOD", "note": "Biochemical Oxygen Demand (BOD) is the amount of oxygen needed by microbes to decompose organic matter.", "confidence": 4},
                            {"title": "COD", "note": "Chemical Oxygen Demand (COD) measures the amount of oxygen required for chemical oxidation of pollutants.", "confidence": 3},
                            {"title": "Dissolved Oxygen", "note": "Levels of oxygen present in water, critical for aquatic life survival.", "confidence": 5}
                        ]
                    },
                    {
                        "title": "Waste Management",
                        "note": "Techniques for handling and reducing waste generated from human activities.",
                        "confidence": 5,
                        "children": [
                            {"title": "E-Waste", "note": "Electronics that have reached the end of their useful life. Contains hazardous materials like lead and mercury.", "confidence": 5},
                            {"title": "4R Concept", "note": "Reduce, Reuse, Recycle, and Recover. The cornerstone of modern sustainability.", "confidence": 5},
                            {"title": "Sustainable Development", "note": "Development that meets present needs without compromising future generations.", "confidence": 5}
                        ]
                    },
                    {
                        "title": "Environmental Issues",
                        "note": "Global challenges affecting the biosphere.",
                        "confidence": 1,
                        "children": [
                            {"title": "Greenhouse Effect", "note": "Trapping of heat by gases like CO2 and Methane, leading to global temperature rise.", "confidence": 1},
                            {"title": "Ozone Depletion", "note": "Breakdown of the ozone layer by CFCs, letting in harmful UV rays.", "confidence": 2},
                            {"title": "Global Warming", "note": "The long-term heating of Earth's climate system observed since the pre-industrial period.", "confidence": 1}
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
                "confidence": 4,
                "children": [
                    {"title": "Introduction", "note": "Photonics is the science of light particles (photons) generation and control. It bridges physics and electrical engineering.", "confidence": 5},
                    {"title": "Advantages", "note": "High speed signal propagation, immunity to electromagnetic interference (EMI), and low power loss during transmission.", "confidence": 4},
                    {
                        "title": "Photodetectors",
                        "note": "Sensors that convert light into electrical currents.",
                        "confidence": 3,
                        "children": [
                            {"title": "Types", "note": "Common types: Photodiodes (PIN, APD), Phototransistors, and Photoconductors.", "confidence": 3},
                            {"title": "Requirements", "note": "Key requirements: High sensitivity, fast response time, low noise, and wavelength selectively.", "confidence": 4}
                        ]
                    },
                    {"title": "Solar Cells", "note": "Photovoltaic cells that convert light energy directly into electrical energy through the PV effect.", "confidence": 5},
                    {"title": "LED", "note": "Light Emitting Diodes that emit light when current flows through a p-n junction. Highly efficient.", "confidence": 5},
                    {"title": "Applications", "note": "Used in fiber-optic communications, medical lasers, optical storage (CD/DVD), and barcode scanning.", "confidence": 4}
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
    print("Seed data inserted successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
