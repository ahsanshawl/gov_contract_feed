import httpx
import os
from datetime import datetime, timedelta

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
        "description": "AFRL Materials and Manufacturing Directorate solicits proposals for advanced ultra-high temperature ceramic composites capable of sustained operation above Mach 15. Research shall address oxidation resistance, structural integrity under thermal shock, and manufacturability at scale.",
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
