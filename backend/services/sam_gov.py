import httpx
import os
from datetime import datetime, timedelta

SAM_BASE = "https://api.sam.gov/opportunities/v2/search"


def _rdate(days_ago: int) -> str:
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


MOCK_SAM = [
]


async def fetch_opportunities(keywords: str = "", limit: int = 20) -> list[dict]:
    api_key = os.getenv("SAM_API_KEY", "")
    # if not api_key:
    #     return _mock_opportunities(keywords, limit)

    posted_from = (datetime.now() - timedelta(days=30)).strftime("%m/%d/%Y")
    posted_to = datetime.now().strftime("%m/%d/%Y")
    params = {
        "api_key": api_key,
        "postedFrom": posted_from,
        "postedTo": posted_to,
        "limit": min(limit, 25),
        "offset": 0,
    }
    if keywords:
        params["q"] = keywords

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(SAM_BASE, params=params)
            if resp.status_code == 429:
                return _mock_opportunities(keywords, limit)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("opportunitiesData", [])
            if not items:
                return _mock_opportunities(keywords, limit)
            return [_parse(o) for o in items]
    except Exception as e:
        print(f"[SAM.gov] {e} — using mock data")
        return _mock_opportunities(keywords, limit)


def _parse(o: dict) -> dict:
    return {
        "id": f"sam-{o.get('noticeId', '')}",
        "source": "SAM.gov",
        "source_type": "contract",
        "title": o.get("title", "Untitled Opportunity"),
        "description": o.get("description", ""),
        "agency": o.get("fullParentPathName", o.get("organizationName", "")),
        "posted_date": o.get("postedDate", ""),
        "deadline": o.get("responseDeadLine", ""),
        "naics": o.get("naicsCode", ""),
        "set_aside": o.get("typeOfSetAside", ""),
        "contract_type": o.get("type", ""),
        "url": f"https://sam.gov/opp/{o.get('noticeId', '')}/view",
        "award_amount": None,
        "is_mock": False,
    }


def _mock_opportunities(keywords: str, limit: int) -> list[dict]:
    items = MOCK_SAM.copy()
    if keywords:
        kw = keywords.lower()
        scored = []
        for item in items:
            text = (item["title"] + " " + item["description"] + " " + item["agency"]).lower()
            score = sum(1 for k in kw.split(",") for word in k.strip().split() if word in text)
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        items = [i for _, i in scored]
    return items[:limit]
