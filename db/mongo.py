import os
import pymongo
from datetime import datetime
from pymongo import MongoClient

# Default to localhost if not set
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "hr_onboarding"
COLLECTION_NAME = "onboarding_history"

class MongoDBHandler:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]
        print(f"DEBUG: Connected to MongoDB at {MONGO_URI} (DB: {DB_NAME})")

    def save_conversation(self, employee_name, role, conversation_history, status="completed"):
        """
        Saves the workflow execution history to MongoDB.
        """
        try:
            document = {
                "employee_name": employee_name,
                "role": role,
                "timestamp": datetime.utcnow(),
                "status": status,
                "conversation": conversation_history
            }
            result = self.collection.insert_one(document)
            print(f"DEBUG: Saved conversation history with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"ERROR: Failed to save to MongoDB: {e}")
            return None

# Global instance
db_handler = MongoDBHandler()
