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
    
    # Add Photonics
    photonics_data = {
        "name": "PHOTONICS",
        "topics": [
            {
                "title": "Introduction",
                "confidence": 5,
                "decay_status": "Strong",
                "children": [
                    {"title": "Definition", "note": "Photonics is the science of producing, detecting, and manipulating photons (particles of light) through emission, transmission, modulation, signal processing, switching, amplification, and sensing.", "confidence": 5, "children": []},
                    {"title": "Optics", "note": "Traditional optics deals with the behavior and properties of light and its interaction with matter, whereas photonics is more focused on the manipulation of light in solid-state materials.", "confidence": 4, "children": []},
                    {"title": "Quantum Mechanics", "note": "Understand light-matter interaction at the quantum level – photons are quantized electromagnetic waves.", "confidence": 3, "children": []},
                    {"title": "Electromagnetism", "note": "Light is an electromagnetic wave governed by Maxwell's equations.", "confidence": 5, "children": []}
                ]
            },
            {
                "title": "Advantages over Electronics",
                "confidence": 4,
                "decay_status": "Good",
                "children": [
                    {"title": "High Bandwidth", "note": "Light can carry vastly more data than electrical signals over copper wires.", "confidence": 5, "children": []},
                    {"title": "Low Power Consumption", "note": "Photonics signals lose less energy through heat compared to electrical resistance.", "confidence": 4, "children": []},
                    {"title": "Increased Security", "note": "Optical fiber is harder to tap into without being detected compared to copper wires.", "confidence": 3, "children": []},
                    {"title": "Higher Reliability", "note": "Immune to electromagnetic interference (EMI).", "confidence": 5, "children": []}
                ]
            },
            {
                "title": "Photodetectors",
                "confidence": 1,
                "decay_status": "Weak",
                "children": [
                    {
                        "title": "Types",
                        "confidence": 1,
                        "children": [
                            {"title": "Junction Photodiode", "note": "A p-n junction operating under reverse bias to detect light and create a photocurrent.", "confidence": 2, "children": []},
                            {"title": "PIN Photodiode", "note": "Structure: p-region, intrinsic region, n-region. Working: Intrinsic layer absorbs photons. Advantages: Better efficiency, Higher speed, Better sensitivity. Applications: Fiber optics, Microwave switches, X-ray detection.", "confidence": 1, "children": []},
                            {"title": "Avalanche Photodiode", "note": "Internal gain mechanism – one photon results in many electrons via carrier multiplication.", "confidence": 1, "children": []},
                            {"title": "Schottky Photodiode", "note": "Metal-semiconductor junction, used for ultrafast applications.", "confidence": 3, "children": []},
                            {"title": "Phototransistors", "note": "A transistor used to amplify light-induced currents.", "confidence": 2, "children": []}
                        ]
                    },
                    {
                        "title": "Requirements",
                        "confidence": 2,
                        "children": [
                            {"title": "High Sensitivity", "note": "Ability to respond to very low light levels.", "confidence": 3, "children": []},
                            {"title": "Short Response Time", "note": "Critical for high-speed data communications.", "confidence": 2, "children": []},
                            {"title": "Low Bias Voltage", "note": "Ensures minimal power consumption and simpler circuitry.", "confidence": 4, "children": []}
                        ]
                    }
                ]
            },
            {
                "title": "Solar Cells",
                "confidence": 3,
                "decay_status": "Medium",
                "children": [
                    {"title": "Photovoltaic Effect", "note": "Conversion of light energy directly into electricity via semiconductor materials.", "confidence": 4, "children": []},
                    {"title": "I-V Characteristics", "note": "Describes current vs. voltage behavior in different lighting conditions.", "confidence": 2, "children": []},
                    {"title": "Configuration", "note": "Single junction vs multi-junction designs for maximum efficiency.", "confidence": 3, "children": []},
                    {"title": "Pros and Cons", "note": "Renewable but currently high initial cost and dependency on sunlight availability.", "confidence": 5, "children": []}
                ]
            },
            {
                "title": "Light Emitting Diodes",
                "confidence": 5,
                "decay_status": "Strong",
                "children": [
                    {"title": "Electron-hole Recombination", "note": "P-N junction process where light is emitted when electrons jump into holes.", "confidence": 5, "children": []},
                    {"title": "Materials and Color", "note": "Bandgap determines the color of light emitted (e.g. InGaN for Blue).", "confidence": 4, "children": []},
                    {"title": "Features", "note": "Energy efficient, long lifespan, and fast switching speed.", "confidence": 5, "children": []}
                ]
            },
            {
                "title": "Applications",
                "confidence": 5,
                "decay_status": "Strong",
                "children": [
                    {"title": "Communication", "note": "Fiber optics – backbone of the modern internet.", "confidence": 5, "children": []},
                    {"title": "Medicine", "note": "Laser surgery, non-invasive imaging, and biosensors.", "confidence": 5, "children": []},
                    {"title": "Consumer Electronics", "note": "Barcode scanners, laser printers, and display backlighting.", "confidence": 4, "children": []},
                    {"title": "Satellites", "note": "Optical inter-satellite links for high data rates in space.", "confidence": 3, "children": []},
                    {"title": "Automotive Lighting", "note": "LED headlights and HUD displays.", "confidence": 5, "children": []}
                ]
            }
        ]
    }
    
    await subjects_collection.insert_one(photonics_data)
    print("Seed data for PHOTONICS inserted!")

if __name__ == "__main__":
    asyncio.run(seed())
