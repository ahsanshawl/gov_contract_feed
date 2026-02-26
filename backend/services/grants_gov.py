import httpx
import os
from datetime import datetime, timedelta

GRANTS_BASE = "https://apply07.grants.gov/grantsws/rest/opportunities/search/"


def _rdate(days_ago: int) -> str:
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def _fdate(days_ahead: int) -> str:
    return (datetime.now() + timedelta(days=days_ahead)).strftime("%m/%d/%Y")


MOCK_GRANTS = [
    {
        "id": "grant-mock-001", "source": "Grants.gov", "source_type": "grant",
        "title": "DARPA Young Faculty Award — Autonomous Systems",
        "description": "The Defense Advanced Research Projects Agency Young Faculty Award (YFA) program aims to identify and engage rising research stars in junior faculty positions and expose them to DoD needs. This cycle focuses on autonomous multi-agent coordination, adversarial machine learning, and edge computing for contested environments.",
        "agency": "DEFENSE ADVANCED RESEARCH PROJECTS AGENCY", "posted_date": _rdate(4), "deadline": _fdate(45),
        "naics": "", "set_aside": "", "contract_type": "Grant",
        "url": "https://www.grants.gov", "award_amount": 500000, "is_mock": True,
    },
    {
        "id": "grant-mock-002", "source": "Grants.gov", "source_type": "grant",
        "title": "SBIR Phase II — Electronic Warfare Cognitive Radio",
        "description": "This SBIR Phase II opportunity funds development of software-defined cognitive radio systems for electronic warfare applications. Technology must demonstrate real-time spectrum sensing, adaptive waveform generation, and AI-driven interference avoidance in congested/contested spectrum environments.",
        "agency": "DEPT OF THE AIR FORCE / AFWERX", "posted_date": _rdate(2), "deadline": _fdate(30),
        "naics": "", "set_aside": "Small Business", "contract_type": "SBIR Phase II",
        "url": "https://www.grants.gov", "award_amount": 1750000, "is_mock": True,
    },
    {
        "id": "grant-mock-003", "source": "Grants.gov", "source_type": "grant",
        "title": "ONR University Research Initiative — Undersea Acoustics",
        "description": "The Office of Naval Research Multidisciplinary University Research Initiative (MURI) award solicits proposals in next-generation undersea acoustic sensing and communications. Focus areas include deep water propagation modeling, bio-inspired sonar, and ML-based signal classification.",
        "agency": "OFFICE OF NAVAL RESEARCH", "posted_date": _rdate(6), "deadline": _fdate(60),
        "naics": "", "set_aside": "", "contract_type": "MURI Grant",
        "url": "https://www.grants.gov", "award_amount": 7500000, "is_mock": True,
    },
    {
        "id": "grant-mock-004", "source": "Grants.gov", "source_type": "grant",
        "title": "DHS S&T — Critical Infrastructure Cyber Resilience",
        "description": "DHS Science and Technology Directorate funds research into automated cyber resilience for industrial control systems in critical infrastructure. Topics include anomaly detection in OT networks, automated patch management, and supply chain risk assessment for SCADA systems.",
        "agency": "DEPT OF HOMELAND SECURITY / S&T", "posted_date": _rdate(3), "deadline": _fdate(90),
        "naics": "", "set_aside": "", "contract_type": "Grant",
        "url": "https://www.grants.gov", "award_amount": 2000000, "is_mock": True,
    },
    {
        "id": "grant-mock-005", "source": "Grants.gov", "source_type": "grant",
        "title": "STTR Phase I — Directed Energy Beam Control",
        "description": "Army STTR Phase I solicitation for novel adaptive optics approaches to high-energy laser beam control in turbulent atmospheric conditions. Proposals must demonstrate theoretical basis for wavefront correction achieving Strehl ratios above 0.8 at 5km range.",
        "agency": "DEPT OF ARMY / RDECOM", "posted_date": _rdate(1), "deadline": _fdate(21),
        "naics": "", "set_aside": "Small Business", "contract_type": "STTR Phase I",
        "url": "https://www.grants.gov", "award_amount": 250000, "is_mock": True,
    },
    {
        "id": "grant-mock-006", "source": "Grants.gov", "source_type": "grant",
        "title": "NSF-DoD Joint Program — Trusted AI for National Security",
        "description": "Joint NSF/DoD program funding foundational research in trustworthy AI systems for national security applications. Priority areas include formal verification of neural networks, robustness to distribution shift, and interpretability in high-stakes decision systems.",
        "agency": "NATIONAL SCIENCE FOUNDATION / DoD", "posted_date": _rdate(8), "deadline": _fdate(120),
        "naics": "", "set_aside": "", "contract_type": "Cooperative Agreement",
        "url": "https://www.grants.gov", "award_amount": 4000000, "is_mock": True,
    },
    {
        "id": "grant-mock-007", "source": "Grants.gov", "source_type": "grant",
        "title": "AFRL SBIR Phase I — Space Domain Awareness AI",
        "description": "Air Force Research Laboratory seeks SBIR Phase I proposals for AI-enabled space domain awareness tools. Scope includes conjunction analysis, maneuver detection, intent prediction for non-cooperative space objects, and data fusion from ground-based and space-based sensor networks.",
        "agency": "AIR FORCE RESEARCH LABORATORY / AFWERX", "posted_date": _rdate(5), "deadline": _fdate(35),
        "naics": "", "set_aside": "Small Business", "contract_type": "SBIR Phase I",
        "url": "https://www.grants.gov", "award_amount": 150000, "is_mock": True,
    },
]


async def fetch_grants(keywords: str = "", limit: int = 15, page: int = 1) -> dict:
    start_record = (page - 1) * min(limit, 25)
    payload = {
        "keyword": keywords or "defense technology",
        "oppStatuses": "forecasted|posted",
        "rows": min(limit, 25),
        "startRecordNum": start_record,
        "sortBy": "openDate|desc",
        "eligibilities": "",
        "agencyCode": "",
        "fundingCategories": "",
        "fundingInstruments": "",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(GRANTS_BASE, json=payload)
            resp.raise_for_status()
            data = resp.json()
            hits = data.get("oppHits", [])
            total = data.get("oppCount", 0)
            has_more = (start_record + limit) < total

            if not hits:
                mock = _mock_grants(keywords, limit, page)
                return {"items": mock, "total_on_page": len(mock), "has_more": False}

            items = [_parse(g) for g in hits]
            return {"items": items, "total_on_page": len(items), "has_more": has_more}

    except Exception as e:
        print(f"[Grants.gov] {e} — using mock data")
        mock = _mock_grants(keywords, limit, page)
        return {"items": mock, "total_on_page": len(mock), "has_more": page < 5}


def _parse(g: dict) -> dict:
    opp_id = g.get("id", "")
    return {
        "id": f"grant-{opp_id}",
        "source": "Grants.gov",
        "source_type": "grant",
        "title": g.get("title", "Untitled Grant"),
        "description": g.get("synopsis", ""),
        "agency": g.get("agencyName", ""),
        "posted_date": g.get("openDate", ""),
        "deadline": g.get("closeDate", ""),
        "naics": "",
        "set_aside": "",
        "contract_type": g.get("instrumentTypes", ""),
        "url": f"https://www.grants.gov/search-results-detail/{opp_id}",
        "award_amount": g.get("awardCeiling"),
        "is_mock": False,
    }


def _mock_grants(keywords: str, limit: int, page: int = 1) -> list[dict]:
    items = MOCK_GRANTS.copy()
    if keywords:
        kw = keywords.lower()
        scored = []
        for item in items:
            text = (item["title"] + " " + item["description"] + " " + item["agency"]).lower()
            score = sum(1 for k in kw.split(",") for word in k.strip().split() if word in text)
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        items = [i for _, i in scored]
    start = ((page - 1) * limit) % len(items)
    rotated = items[start:] + items[:start]
    return rotated[:limit]
