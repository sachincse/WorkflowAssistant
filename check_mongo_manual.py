from pymongo import MongoClient
from pprint import pprint

client = MongoClient("mongodb://localhost:27017/")
db = client["hr_onboarding"]
collection = db["onboarding_history"]

print(f"Total documents: {collection.count_documents({})}")
print("Latest document:")
latest = collection.find_one(sort=[("_id", -1)])
if latest:
    pprint(latest)
else:
    print("No documents found.")
