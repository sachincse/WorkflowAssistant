from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from api import upload, onboarding

app = FastAPI(title="HR Onboarding Automation")

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)

# Mount uploads directory to serve files (optional, but useful for verification)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(upload.router, prefix="/api")
app.include_router(onboarding.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "HR Onboarding Automation Agent System is Running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
