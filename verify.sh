#!/bin/bash
echo "Creating dummy file..."
echo "This is a test document." > test_doc.txt

echo "Uploading file..."
UPLOAD_RESP=$(curl -s -X POST -F "file=@test_doc.txt" http://localhost:8000/api/upload/)
echo "Upload Response: $UPLOAD_RESP"

# Extract file path using python for reliability (avoiding jq dependency issues if not present)
FILE_PATH=$(echo $UPLOAD_RESP | python3 -c "import sys, json; print(json.load(sys.stdin)['location'])")
echo "File Path: $FILE_PATH"

if [ -z "$FILE_PATH" ]; then
    echo "Error: Could not extract file path from upload response."
    exit 1
fi

echo "Triggering Onboarding..."
curl -X POST http://localhost:8000/api/onboard/ \
     -H "Content-Type: application/json" \
     -d "{\"employee_name\": \"Alice Smith\", \"role\": \"Senior Developer\", \"document_path\": \"$FILE_PATH\"}"
