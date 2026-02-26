import httpx
import os
from datetime import datetime, timedelta

# Per GSA official docs: https://open.gsa.gov/api/get-opportunities-public-api/
SAM_BASE = "https://api.sam.gov/opportunities/v2/search"


def _rdate(days_ago: int) -> str:
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")



MOCK_SAM = [
    {
        "id": "sam-mock-001", "source": "SAM.gov", "source_type": "contract",
        "title": "Autonomous Counter-UAS Detection and Defeat System",
        "description": "The Department of the Air Force seeks proposals for a mobile, rapidly-deployable counter-drone system capable of detecting, tracking, and defeating Class I-III UAS threats. System must integrate with existing TCDL datalinks and support operations in GPS-denied environments. AESA radar and RF/EO fusion required.",
        "agency": "DEPT OF THE AIR FORCE", "posted_date": _rdate(2), "deadline": _rdate(-14),
        "naics": "541715", "set_aside": "Small Business", "contract_type": "Solicitation",
        "url": "https://sam.gov", "award_amount": None, "is_mock": True,
    },
    {
        "id": "sam-mock-002", "source": "SAM.gov", "source_type": "contract",
        "title": "Machine Learning-Based Predictive Maintenance for F-35 Fleet",
        "description": "NAVAIR is seeking an advanced ML platform to reduce F-35 maintenance burden through predictive failure analysis. The system shall ingest real-time sensor telemetry, historical maintenance records, and supply chain data to forecast component failures with 90% accuracy at 30-day horizons.",
        "agency": "DEPT OF NAVY / NAVAIR", "posted_date": _rdate(3), "deadline": _rdate(-21),
        "naics": "541512", "set_aside": "None", "contract_type": "Sources Sought",
        "url": "https://sam.gov", "award_amount": None, "is_mock": True,
    },
    {
        "id": "sam-mock-003", "source": "SAM.gov", "source_type": "contract",
        "title": "Tactical Edge AI Inference Hardware for Ground Vehicles",
        "description": "DEVCOM Ground Vehicle Systems Center requires ruggedized AI inference hardware for tactical wheeled vehicles. Must meet MIL-STD-810H, operate at -40C to +71C, and process 4K multi-spectral imagery at 30fps for real-time object detection and threat classification.",
        "agency": "DEPT OF ARMY / DEVCOM GVSC", "posted_date": _rdate(1), "deadline": _rdate(-10),
        "naics": "334413", "set_aside": "WOSB", "contract_type": "Solicitation",
        "url": "https://sam.gov", "award_amount": None, "is_mock": True,
    },
    {
        "id": "sam-mock-004", "source": "SAM.gov", "source_type": "contract",
        "title": "Zero Trust Architecture Implementation — DISA Enterprise",
        "description": "DISA requires a systems integrator to implement zero-trust network architecture across 47 data centers worldwide. Scope includes identity federation, micro-segmentation, continuous authorization, and integration with existing SIEM/SOAR platforms. 5-year IDIQ with $2.1B ceiling.",
        "agency": "DEFENSE INFORMATION SYSTEMS AGENCY", "posted_date": _rdate(5), "deadline": _rdate(-30),
        "naics": "541519", "set_aside": "None", "contract_type": "Solicitation",
        "url": "https://sam.gov", "award_amount": None, "is_mock": True,
    },
    {
        "id": "sam-mock-005", "source": "SAM.gov", "source_type": "contract",
        "title": "SOCOM Special Operations ISR Sensor Integration",
        "description": "US Special Operations Command seeks proposals for next-generation ISR payload integration onto MQ-9B platform. Requires EO/IR/SAR sensor fusion, onboard AI-assisted target recognition, and low-probability-of-intercept data exfiltration capability.",
        "agency": "US SPECIAL OPERATIONS COMMAND", "posted_date": _rdate(1), "deadline": _rdate(-18),
        "naics": "336411", "set_aside": "None", "contract_type": "Solicitation",
        "url": "https://sam.gov", "award_amount": None, "is_mock": True,
    },
    {
        "id": "sam-mock-006", "source": "SAM.gov", "source_type": "contract",
        "title": "Hypersonic Glide Vehicle Thermal Protection Materials R&D",
        "description": "AFRL Materials and Manufacturing Directorate solicits proposals for advanced ultra-high temperature ceramic composites capable of sustained operation above Mach 15.",
        "agency": "AIR FORCE RESEARCH LABORATORY", "posted_date": _rdate(4), "deadline": _rdate(-25),
        "naics": "541715", "set_aside": "Small Business", "contract_type": "BAA",
        "url": "https://sam.gov", "award_amount": None, "is_mock": True,
    },
    {
        "id": "sam-mock-007", "source": "SAM.gov", "source_type": "contract",
        "title": "Quantum Key Distribution Network for IC Facilities",
        "description": "The Intelligence Community seeks QKD solutions for point-to-point secure communications between cleared facilities in the NCR. System must achieve 1Mbps key generation rate over 50km fiber and meet NSA Type-1 standards.",
        "agency": "OFFICE OF THE DNI", "posted_date": _rdate(6), "deadline": _rdate(-35),
        "naics": "541519", "set_aside": "None", "contract_type": "Sources Sought",
        "url": "https://sam.gov", "award_amount": None, "is_mock": True,
    },
    {
        "id": "sam-mock-008", "source": "SAM.gov", "source_type": "contract",
        "title": "Autonomous Underwater Vehicle Fleet Management System",
        "description": "Naval Undersea Warfare Center requires a cloud-based fleet management and mission planning platform for a 50+ AUV fleet. Capabilities include mission deconfliction, acoustic communication relay, and post-mission data fusion from multi-static sonar arrays.",
        "agency": "NAVSEA / NUWC NEWPORT", "posted_date": _rdate(2), "deadline": _rdate(-12),
        "naics": "541512", "set_aside": "8(a)", "contract_type": "Solicitation",
        "url": "https://sam.gov", "award_amount": None, "is_mock": True,
    },
]


async def fetch_opportunities(keywords: str = "", limit: int = 15, page: int = 1) -> dict:
    api_key = os.getenv("SAM_API_KEY", "")
    if not api_key:
        mock = _mock_opportunities(keywords, limit, page)
        return {"items": mock, "total_on_page": len(mock), "has_more": page < 5}

    posted_from = (datetime.now() - timedelta(days=90)).strftime("%m/%d/%Y")
    posted_to = datetime.now().strftime("%m/%d/%Y")

    # SAM.gov uses 0-based offset
    offset = (page - 1) * min(limit, 25)

    # IMPORTANT: SAM.gov v2 has NO full-text keyword search param.
    # The `title` param does a "title contains" search but is very restrictive
    # — e.g. "artificial intelligence" won't match "AI" or "machine learning".
    # Strategy: fetch recent solicitations broadly (by date + ptype),
    # then let the AI ranker score relevance. On page 1 we try a title hint
    # for the first keyword; on later pages we fetch broadly to surface variety.
    params = {
        "api_key": api_key,
        "postedFrom": posted_from,
        "postedTo": posted_to,
        "limit": min(limit, 25),
        "offset": offset,
        # o=Solicitation, r=Sources Sought, p=Pre-solicitation, k=Combined Synopsis
        "ptype": "o,r,p,k",
    }

    # Only apply title filter on page 1 with the first keyword as a hint.
    # Subsequent pages fetch broadly so scroll surfaces different content.
    if keywords and page == 1:
        first_kw = keywords.split(",")[0].strip()
        if first_kw and len(first_kw) > 3:
            params["title"] = first_kw

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(SAM_BASE, params=params)

            if resp.status_code == 429:
                print("[SAM.gov] Rate limited — using mock data")
                mock = _mock_opportunities(keywords, limit, page)
                return {"items": mock, "total_on_page": len(mock), "has_more": False}

            if resp.status_code == 403:
                print(f"[SAM.gov] 403 Forbidden — check your API key. Body: {resp.text[:200]}")
                mock = _mock_opportunities(keywords, limit, page)
                return {"items": mock, "total_on_page": len(mock), "has_more": False}

            resp.raise_for_status()
            data = resp.json()
            items_raw = data.get("opportunitiesData", [])
            total_records = int(data.get("totalRecords", 0))
            has_more = (offset + limit) < total_records

            # If title-filtered page 1 returned nothing, retry without title filter
            if not items_raw and "title" in params:
                del params["title"]
                resp2 = await client.get(SAM_BASE, params=params)
                if resp2.status_code == 200:
                    data = resp2.json()
                    items_raw = data.get("opportunitiesData", [])
                    total_records = int(data.get("totalRecords", 0))
                    has_more = (offset + limit) < total_records

            if not items_raw:
                print("[SAM.gov] No results from live API — using mock data")
                mock = _mock_opportunities(keywords, limit, page)
                return {"items": mock, "total_on_page": len(mock), "has_more": False}

            items = [_parse(o) for o in items_raw]
            print(f"[SAM.gov] Fetched {len(items)} live opportunities (total available: {total_records})")
            return {"items": items, "total_on_page": len(items), "has_more": has_more}

    except Exception as e:
        print(f"[SAM.gov] {type(e).__name__}: {str(e)[:120]} — using mock data")
        mock = _mock_opportunities(keywords, limit, page)
        return {"items": mock, "total_on_page": len(mock), "has_more": page < 5}


def _parse(o: dict) -> dict:
    notice_id = o.get("noticeId", "")
    # GSA docs spell it "reponseDeadLine" (their typo) — handle both spellings
    deadline = o.get("reponseDeadLine") or o.get("responseDeadLine", "")
    return {
        "id": f"sam-{notice_id}",
        "source": "SAM.gov",
        "source_type": "contract",
        "title": o.get("title", "Untitled Opportunity"),
        "description": o.get("description", ""),
        "agency": o.get("fullParentPathName", o.get("organizationName", "")),
        "posted_date": o.get("postedDate", ""),
        "deadline": deadline,
        "naics": o.get("naicsCode", ""),
        "set_aside": o.get("typeOfSetAside", o.get("setAside", "")),
        "contract_type": o.get("type", ""),
        "url": f"https://sam.gov/opp/{notice_id}/view",
        "award_amount": None,
        "is_mock": False,
    }


def _mock_opportunities(keywords: str, limit: int, page: int = 1) -> list[dict]:
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
    start = ((page - 1) * limit) % len(items)
    rotated = items[start:] + items[:start]
    return rotated[:limit]
