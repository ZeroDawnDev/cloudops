"""
main.py
-------
CloudOps AI backend entrypoint.

Run with:  uvicorn main:app --reload --port 8000
(from inside the backend/ directory, with your virtualenv activated)
"""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # reads backend/.env

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

from api.routes import router as api_router  # noqa: E402 (after load_dotenv/logging setup)

app = FastAPI(
    title="CloudOps AI",
    description="An autonomous AI Cloud Operations Engineer.",
    version="0.1.0",
)

# Allow the Next.js dev server (and any origin configured in .env) to call the API.
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {"service": "CloudOps AI", "status": "running", "docs": "/docs"}
