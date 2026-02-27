# gov contract feed

**Live intelligence feed for government contracts, awards & grants — with AI relevance scoring.**

Feed-first design: always-visible sidebar to tweak keywords live, infinite scroll feed, card-per-item layout that feels like a social feed not a search tool.

---

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt

# Copy and fill in your keys
cp .env.example .env

uvicorn main:app --reload --port 8000
```

**.env keys:**
- `OPENAI_API_KEY` — for AI ranking (optional; falls back to keyword scoring)
- `SAM_API_KEY` — free from sam.gov/content/dapi (optional; uses demo data without it)


### Frontend
```bash
cd frontend
npm install
npm start       # runs on :3000, proxies /api → :8000
```

---

## How It Works

1. **On load** — feed pulls from SAM.gov + USASpending.gov + Grants.gov in parallel
2. **AI ranking** — GPT-4o-mini scores each item 0–100 for relevance to your profile and writes a one-line "why it matters" summary
3. **Fallback** — if no OpenAI key, keyword-match scoring is used automatically
4. **Mock data** — if live APIs are unreachable (no key, rate limit), realistic demo items are shown with a "DEMO" badge
5. **Sidebar** — tweak keywords live, hit "Apply & Refresh" to re-query and re-rank instantly

---

## Deployment

**Backend → Railway**
- Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Add env vars: `OPENAI_API_KEY`, `SAM_API_KEY`

**Frontend → Vercel**
- Set env var: `REACT_APP_API_URL=https://your-railway-url.up.railway.app`

---

## Adding a New Data Source

1. Create `backend/services/new_source.py` with `async def fetch_X(keywords, limit) -> list[dict]`
2. Each dict must include: `id, source, source_type, title, description, agency, posted_date, deadline, url, award_amount`
3. Add to `tasks` in `routers/feed.py`
4. Add source entry in the frontend sidebar `SOURCES` array in `App.tsx`
