import os
import json
import re

# Module-level key store — survives across requests in the same process
_openai_key: str = ""


def set_api_key(key: str):
    global _openai_key
    if key:
        _openai_key = key
        os.environ["OPENAI_API_KEY"] = key


def get_openai_client():
    try:
        from openai import AsyncOpenAI
        api_key = _openai_key or os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return None
        return AsyncOpenAI(api_key=api_key)
    except ImportError:
        return None


async def rank_and_summarize(items: list[dict], user_profile: dict) -> list[dict]:
    """Use OpenAI to rank items by relevance and generate summaries.
    Always falls back to keyword ranking — never raises, never crashes the feed.
    """
    if not items:
        return items

    oai = get_openai_client()
    if not oai:
        return _keyword_rank(items, user_profile)

    interests = user_profile.get("keywords", "")
    focus = user_profile.get("focus", interests)

    item_summaries = []
    for i, item in enumerate(items[:40]):
        item_summaries.append({
            "idx": i,
            "title": item.get("title", ""),
            "agency": item.get("agency", ""),
            "type": item.get("source_type", ""),
            "amount": item.get("award_amount"),
            "snippet": (item.get("description") or "")[:300],
        })

    prompt = f"""You are a government contracting intelligence analyst.

User focus: "{focus}"
User keywords: "{interests}"

Score each item 0-100 for relevance to this user. Write a sharp, specific 1-sentence summary (max 18 words) explaining WHY it's relevant — not just what it is.

Return ONLY a JSON array, no markdown:
[{{"idx": 0, "score": 85, "summary": "Directly targets your AI/ISR work — $120M NAVAIR award with sensor fusion scope"}}]

Items:
{json.dumps(item_summaries)}"""

    try:
        response = await oai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2500,
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        rankings = json.loads(raw.strip())

        score_map = {r["idx"]: r for r in rankings}
        for i, item in enumerate(items[:40]):
            r = score_map.get(i, {})
            item["relevance_score"] = r.get("score", 50)
            item["ai_summary"] = r.get("summary", "")

        items[:40] = sorted(items[:40], key=lambda x: x.get("relevance_score", 0), reverse=True)
        return items

    except Exception as e:
        # Catch everything including RateLimitError, AuthenticationError,
        # APIConnectionError, JSONDecodeError — never crash the feed request
        err_type = type(e).__name__
        err_msg = str(e)[:120]

        if "insufficient_quota" in err_msg or "RateLimit" in err_type:
            print(f"[AI Ranker] OpenAI quota exceeded — falling back to keyword ranking. Add credits at platform.openai.com")
        elif "AuthenticationError" in err_type or "invalid_api_key" in err_msg:
            print(f"[AI Ranker] OpenAI key invalid — falling back to keyword ranking")
            # Clear the bad key so we stop trying
            global _openai_key
            _openai_key = ""
        else:
            print(f"[AI Ranker] {err_type}: {err_msg} — falling back to keyword ranking")

        return _keyword_rank(items, user_profile)


def _keyword_rank(items: list[dict], profile: dict) -> list[dict]:
    """Keyword-based relevance scoring used when OpenAI is unavailable."""
    keywords = profile.get("keywords", "").lower()
    words = [w.strip() for w in re.split(r"[,\s]+", keywords) if len(w.strip()) > 2]

    for item in items:
        text = " ".join([
            item.get("title", ""),
            item.get("description", ""),
            item.get("agency", ""),
        ]).lower()
        title_text = item.get("title", "").lower()
        score = sum(3 if w in title_text else 1 for w in words if w in text)
        item["relevance_score"] = min(95, 30 + score * 8)
        item["ai_summary"] = ""

    return sorted(items, key=lambda x: x.get("relevance_score", 0), reverse=True)


async def parse_profile_from_text(raw_input: str) -> dict:
    """Extract structured keywords and focus from free-text description."""
    oai = get_openai_client()
    if not oai:
        return {
            "keywords": raw_input,
            "org_type": "",
            "focus": raw_input[:100],
            "agencies": [],
        }

    prompt = f"""Extract a search profile from this user description for a government contracts/grants feed:

"{raw_input}"

Return ONLY JSON (no markdown):
{{
  "keywords": "3-8 comma-separated search terms optimized for SAM.gov, e.g.: counter-UAS, autonomous systems, C2",
  "org_type": "small business / large prime / research university / nonprofit / etc",
  "focus": "One crisp sentence describing their focus area",
  "agencies": ["list", "of", "relevant", "DoD/IC agencies"]
}}"""

    try:
        response = await oai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400,
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        return json.loads(raw.strip())
    except Exception as e:
        print(f"[AI Profile] {type(e).__name__}: {str(e)[:120]}")
        return {"keywords": raw_input, "org_type": "", "focus": raw_input[:100], "agencies": []}
