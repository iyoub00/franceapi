import os
from fastapi import FastAPI
from app.api import router
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

REACT_HOST = os.getenv("REACT_HOST")

app = FastAPI(title="Silicon Shoring API - AI Agent")
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[REACT_HOST],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)