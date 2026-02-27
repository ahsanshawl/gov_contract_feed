# gov contract feed

**Live intelligence feed for government contracts, awards & grants — with AI relevance scoring.**

Feed-first design: always-visible sidebar to tweak keywords live, infinite scroll feed, card-per-item layout that feels like a social feed not a search tool.



## How It Works

1. **On load** — feed pulls from SAM.gov + USASpending.gov + Grants.gov in parallel
2. **AI ranking** — GPT-4o-mini scores each item 0–100 for relevance to your profile and writes a one-line "why it matters" summary
3. **Fallback** — if no OpenAI key, keyword-match scoring is used automatically
4. **Mock data** — if live APIs are unreachable (no key, rate limit), realistic demo items are shown with a "DEMO" badge
5. **Sidebar** — tweak keywords live, hit "Apply & Refresh" to re-query and re-rank instantly


