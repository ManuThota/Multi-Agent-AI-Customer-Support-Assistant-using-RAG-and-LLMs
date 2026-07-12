import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

logger = logging.getLogger("uvicorn")

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    def connect(self):
        """Initializes the MongoDB connection client."""
        logger.info(f"Connecting to MongoDB at: {settings.MONGODB_URL}")
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB_NAME]
        logger.info("MongoDB client connected successfully.")

    def close(self):
        """Closes the MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB client connection closed.")

# Singleton instance
mongodb = MongoDB()

def get_db():
    """Dependency helper to get the active database object."""
    return mongodb.db

# Helper collections accessor functions
def get_users_collection():
    return mongodb.db["users"]

def get_sessions_collection():
    return mongodb.db["sessions"]

def get_messages_collection():
    return mongodb.db["messages"]

# Serialization utilities to convert MongoDB documents with ObjectId into JSON-friendly dicts
def serialize_doc(doc: dict) -> dict:
    """Converts MongoDB '_id' (ObjectId) into a string 'id' for JSON serialization."""
    if not doc:
        return {}
    serialized = {**doc}
    if "_id" in serialized:
        serialized["id"] = str(serialized["_id"])
        del serialized["_id"]
    return serialized

def serialize_list(docs: list) -> list[dict]:
    """Serializes a list of MongoDB documents."""
    return [serialize_doc(doc) for doc in docs]