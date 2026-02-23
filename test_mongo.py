from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["fitgen_db"]

    result = await db.test.insert_one({"name": "Avinash"})
    print("Inserted:", result.inserted_id)

asyncio.run(test())
