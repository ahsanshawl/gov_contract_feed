import httpx
import os
from datetime import datetime, timedelta

USA_SPENDING_BASE = "https://api.usaspending.gov/api/v2/search/spending_by_award/"


def _rdate(days_ago: int) -> str:
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


MOCK_AWARDS = [
    {
        "id": "award-mock-001", "source": "USASpending.gov", "source_type": "award",
        "title": "Award to Palantir Technologies Inc.",
        "description": "Data integration and analytics platform for Army Enterprise Resource Planning. Scope includes deployment of Gotham and Foundry platforms across 15 brigade combat teams with full ATO.",
        "agency": "DEPT OF ARMY", "posted_date": _rdate(3), "deadline": _rdate(-365),
        "naics": "541512", "set_aside": "", "contract_type": "Definitive Contract",
        "url": "https://www.usaspending.gov", "award_amount": 229500000, "recipient": "Palantir Technologies Inc.", "is_mock": True,
    },
    {
        "id": "award-mock-002", "source": "USASpending.gov", "source_type": "award",
        "title": "Award to Anduril Industries",
        "description": "Autonomous surveillance tower (AST) production and sustainment contract. Lattice OS-enabled border security towers with EO/IR sensor fusion, radar, and autonomous threat alerting.",
        "agency": "DEPT OF HOMELAND SECURITY", "posted_date": _rdate(5), "deadline": _rdate(-730),
        "naics": "336414", "set_aside": "", "contract_type": "Definitive Contract",
        "url": "https://www.usaspending.gov", "award_amount": 120000000, "recipient": "Anduril Industries", "is_mock": True,
    },
    {
        "id": "award-mock-003", "source": "USASpending.gov", "source_type": "award",
        "title": "Award to Booz Allen Hamilton",
        "description": "Cyber operations support and threat intelligence services for CYBERCOM. Includes red team operations, vulnerability research, and adversary emulation across DoD networks.",
        "agency": "US CYBER COMMAND", "posted_date": _rdate(7), "deadline": _rdate(-365),
        "naics": "541513", "set_aside": "", "contract_type": "IDIQ Task Order",
        "url": "https://www.usaspending.gov", "award_amount": 342000000, "recipient": "Booz Allen Hamilton", "is_mock": True,
    },
    {
        "id": "award-mock-004", "source": "USASpending.gov", "source_type": "award",
        "title": "Award to Shield AI",
        "description": "Hivemind autonomous pilot software license and integration services for F-16 and MQ-20 Avenger platforms. Enables fully autonomous air combat maneuvering without GPS or comms.",
        "agency": "DEPT OF THE AIR FORCE", "posted_date": _rdate(4), "deadline": _rdate(-548),
        "naics": "541715", "set_aside": "", "contract_type": "Definitive Contract",
        "url": "https://www.usaspending.gov", "award_amount": 67800000, "recipient": "Shield AI", "is_mock": True,
    },
    {
        "id": "award-mock-005", "source": "USASpending.gov", "source_type": "award",
        "title": "Award to General Dynamics IT",
        "description": "DoD enterprise cloud migration and managed security services. Deployment of classified workloads to Impact Level 5/6 cloud environments with continuous monitoring.",
        "agency": "DEFENSE LOGISTICS AGENCY", "posted_date": _rdate(8), "deadline": _rdate(-1095),
        "naics": "541519", "set_aside": "", "contract_type": "IDIQ",
        "url": "https://www.usaspending.gov", "award_amount": 895000000, "recipient": "General Dynamics IT", "is_mock": True,
    },
    {
        "id": "award-mock-006", "source": "USASpending.gov", "source_type": "award",
        "title": "Award to Leidos",
        "description": "Navy Next Generation Enterprise Network (NGEN) support services. Full spectrum IT services including network operations, cybersecurity, and service desk for 400,000 Navy and Marine Corps users.",
        "agency": "DEPT OF NAVY", "posted_date": _rdate(2), "deadline": _rdate(-1825),
        "naics": "541519", "set_aside": "", "contract_type": "IDIQ",
        "url": "https://www.usaspending.gov", "award_amount": 7700000000, "recipient": "Leidos", "is_mock": True,
    },
    {
        "id": "award-mock-007", "source": "USASpending.gov", "source_type": "award",
        "title": "Award to Rebellion Defense",
        "description": "AI-enabled cyber threat detection and response platform (Nova) for classified DoD networks. Real-time adversarial behavior detection with automated playbook execution.",
        "agency": "DEPT OF DEFENSE / CIO", "posted_date": _rdate(6), "deadline": _rdate(-365),
        "naics": "541513", "set_aside": "", "contract_type": "Definitive Contract",
        "url": "https://www.usaspending.gov", "award_amount": 18400000, "recipient": "Rebellion Defense", "is_mock": True,
    },
]


async def fetch_awards(keywords: str = "", limit: int = 20) -> list[dict]:
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    payload = {
        "filters": {
            "time_period": [{"start_date": start_date, "end_date": end_date}],
            "award_type_codes": ["A", "B", "C", "D"],
        },
        "fields": ["Award ID", "Recipient Name", "Award Amount", "Awarding Agency",
                   "Award Type", "Description", "Period of Performance Start Date",
                   "Period of Performance Current End Date", "generated_internal_id"],
        "page": 1,
        "limit": min(limit, 25),
        "sort": "Award Amount",
        "order": "desc",
    }
    if keywords:
        payload["filters"]["keyword"] = keywords

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(USA_SPENDING_BASE, json=payload)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            if not results:
                return _mock_awards(keywords, limit)
            return [_parse(r) for r in results]
    except Exception as e:
        print(f"[USASpending] {e} — using mock data")
        return _mock_awards(keywords, limit)


def _parse(r: dict) -> dict:
    award_id = r.get("generated_internal_id", "")
    return {
        "id": f"award-{r.get('Award ID', '')}",
        "source": "USASpending.gov",
        "source_type": "award",
        "title": f"Award to {r.get('Recipient Name', 'Unknown')}",
        "description": r.get("Description", ""),
        "agency": r.get("Awarding Agency", ""),
        "posted_date": r.get("Period of Performance Start Date", ""),
        "deadline": r.get("Period of Performance Current End Date", ""),
        "naics": "",
        "set_aside": "",
        "contract_type": r.get("Award Type", ""),
        "url": f"https://www.usaspending.gov/award/{award_id}",
        "award_amount": r.get("Award Amount", 0),
        "recipient": r.get("Recipient Name", ""),
        "is_mock": False,
    }


def _mock_awards(keywords: str, limit: int) -> list[dict]:
    items = MOCK_AWARDS.copy()
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
