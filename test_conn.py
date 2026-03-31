import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def test():
    uri = os.getenv("MONGODB_URI")
    print(f"Testing URI: {uri[:40]}...")
    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
    try:
        await client.server_info()
        print("Success: MongoDB connection verified!")
    except Exception as e:
        print(f"Error: Connection failed. {e}")

if __name__ == "__main__":
    asyncio.run(test())
