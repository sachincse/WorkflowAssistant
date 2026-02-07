from fastapi import FastAPI
import os


app = FastAPI()


@app.get("/")
def health():
    return {"status": "WorkflowAssistant running"}


port = int(os.environ.get("PORT", 8000))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=port)
