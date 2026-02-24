from fastapi import APIRouter, Query
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services import sam_gov, usaspending, grants_gov, ai_ranker

router = APIRouter()

# Simple in-memory profile store
_profiles: dict = {}


def _get_profile(user_id: str) -> dict:
    return _profiles.get(user_id, {
        "keywords": "defense technology, AI, autonomous systems",
        "org_type": "",
        "focus": "Defense technology and government contracts",
        "agencies": [],
    })


def set_profile(user_id: str, profile: dict):
    _profiles[user_id] = profile


def get_profile_store(user_id: str) -> dict:
    return _get_profile(user_id)


@router.get("/")
async def get_feed(
    user_id: str = Query("default"),
    sources: str = Query("sam,usaspending,grants"),
    limit: int = Query(15, le=30),
    offset: int = Query(0),
    openai_key: str = Query(""),
):
    if openai_key:
        ai_ranker.set_api_key(openai_key)
    profile = _get_profile(user_id)
    keywords = profile.get("keywords", "defense")
    active = [s.strip() for s in sources.split(",")]

    tasks = []
    task_names = []

    if "sam" in active:
        tasks.append(sam_gov.fetch_opportunities(keywords, limit))
        task_names.append("sam")
    if "usaspending" in active:
        tasks.append(usaspending.fetch_awards(keywords, limit))
        task_names.append("usaspending")
    if "grants" in active:
        tasks.append(grants_gov.fetch_grants(keywords, limit))
        task_names.append("grants")

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_items = []
    source_counts = {}
    for name, result in zip(task_names, results):
        if isinstance(result, list):
            all_items.extend(result)
            source_counts[name] = len(result)
        else:
            print(f"[Feed] source {name} error: {result}")
            source_counts[name] = 0

    # AI rank + summarize
    ranked = await ai_ranker.rank_and_summarize(all_items, profile)

    # Apply offset for pagination
    paginated = ranked[offset:offset + limit * len(active)]
    has_more = len(ranked) > offset + limit * len(active)

    return {
        "items": paginated,
        "total": len(ranked),
        "has_more": has_more,
        "source_counts": source_counts,
        "profile": profile,
    }


@router.get("/sources")
def get_sources():
    return {
        "sources": [
            {"id": "sam",         "name": "SAM.gov",         "description": "Federal contract opportunities", "color": "#4A9EFF"},
            {"id": "usaspending", "name": "USASpending.gov",  "description": "Contract awards",               "color": "#4AFF91"},
            {"id": "grants",      "name": "Grants.gov",       "description": "Federal grant opportunities",   "color": "#C084FC"},
        ]
    }
