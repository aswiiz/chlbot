import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def test():
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    print(f"Connecting to: {uri.split('@')[-1]}") # Hide credentials
    client = AsyncIOMotorClient(uri)
    db = client.clh_database
    coll = db.subjects
    try:
        count = await coll.count_documents({})
        print(f"Found {count} subjects")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
