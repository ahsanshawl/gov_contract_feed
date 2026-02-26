from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
from routers import feed, profile

app = FastAPI(title="GovFeed API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://govcontractfeed.netlify.app","http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feed.router, prefix="/api/feed", tags=["feed"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])

@app.get("/health")
def health():
    return {"status": "ok"}
