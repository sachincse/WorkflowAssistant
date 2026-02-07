import requests
import json
import sys
from pymongo import MongoClient

# 1. Upload File
print("Uploading file...")
with open("test_doc.txt", "w") as f:
    f.write("This is a test document for MongoDB verification.")

url = "http://localhost:8000/api/upload/"
files = {'file': open('test_doc.txt', 'rb')}
response = requests.post(url, files=files)
if response.status_code != 200:
    print(f"Upload failed: {response.text}")
    sys.exit(1)

file_path = response.json()['location']
print(f"File uploaded to: {file_path}")

# 2. Trigger Onboarding
print("Triggering onboarding...")
headers = {'Content-Type': 'application/json'}
payload = {
    "employee_name": "Mongo Test User",
    "role": "Database Admin",
    "document_path": file_path
}
response = requests.post("http://localhost:8000/api/onboard/", headers=headers, json=payload)
if response.status_code != 200:
    print(f"Onboarding failed: {response.text}")
    sys.exit(1)

data = response.json()
db_id = data.get("db_id")
print(f"Onboarding complete. DB ID from API: {db_id}")

if not db_id:
    print("Error: No DB ID returned from API.")
    sys.exit(1)

# 3. Verify in MongoDB
print("Verifying in MongoDB...")
client = MongoClient("mongodb://localhost:27017/")
db = client["hr_onboarding"]
collection = db["onboarding_history"]

# Convert string ID to ObjectId if necessary, or just search by string if that's how it was inserted (it returns ObjectId usually)
from bson.objectid import ObjectId
record = collection.find_one({"_id": ObjectId(db_id)})

if record:
    print("SUCCESS: Record found in MongoDB!")
    print(f"Employee: {record['employee_name']}")
    print(f"Status: {record['status']}")
else:
    print("FAILURE: Record NOT found in MongoDB.")
    sys.exit(1)
