# main.py
# This file is the main entry point for the FastAPI application.
# Author: Yassine Amounane
from fastapi import FastAPI
from app.api import router

app = FastAPI(title="Silicon Shoring API - AI Agent")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)