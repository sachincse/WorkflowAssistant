from fastapi import APIRouter, File, UploadFile, HTTPException
import shutil
import os
from pathlib import Path

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload/")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document to the server.
    """
    try:
        # Sanitize filename if needed, for now just use the provided filename
        file_location = UPLOAD_DIR / file.filename
        
        # Save the file
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "filename": file.filename, 
            "location": str(file_location.absolute()), 
            "message": "File uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not upload file: {str(e)}")
