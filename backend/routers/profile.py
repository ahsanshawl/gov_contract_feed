from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services import ai_ranker
from routers.feed import set_profile, get_profile_store

router = APIRouter()


class ProfileFromText(BaseModel):
    user_id: str = "default"
    raw_input: str
    openai_api_key: Optional[str] = None


class ProfileDirect(BaseModel):
    user_id: str = "default"
    keywords: str
    focus: Optional[str] = ""
    org_type: Optional[str] = ""
    openai_api_key: Optional[str] = None


@router.post("/from-text")
async def create_from_text(data: ProfileFromText):
    if data.openai_api_key:
        ai_ranker.set_api_key(data.openai_api_key)
    profile = await ai_ranker.parse_profile_from_text(data.raw_input)
    profile["raw_input"] = data.raw_input
    set_profile(data.user_id, profile)
    return {"profile": profile}


@router.post("/update")
async def update_profile(data: ProfileDirect):
    if data.openai_api_key:
        ai_ranker.set_api_key(data.openai_api_key)
    profile = {
        "keywords": data.keywords,
        "focus": data.focus or data.keywords,
        "org_type": data.org_type or "",
        "agencies": [],
    }
    set_profile(data.user_id, profile)
    return {"profile": profile}


@router.get("/{user_id}")
def read_profile(user_id: str):
    return {"profile": get_profile_store(user_id)}
