const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

export interface FeedItem {
  id: string;
  source: string;
  source_type: "contract" | "award" | "grant";
  title: string;
  description: string;
  agency: string;
  posted_date: string;
  deadline: string;
  naics: string;
  set_aside: string;
  contract_type: string;
  url: string;
  award_amount: number | null;
  relevance_score?: number;
  ai_summary?: string;
  recipient?: string;
  is_mock?: boolean;
}

export interface UserProfile {
  keywords: string;
  org_type: string;
  focus: string;
  agencies?: string[];
  raw_input?: string;
}

export interface FeedResponse {
  items: FeedItem[];
  total: number;
  has_more: boolean;
  source_counts: Record<string, number>;
  profile: UserProfile;
}

export async function fetchFeed(
  userId = "default",
  sources = "sam,usaspending,grants",
  limit = 15,
  page = 1,
  openaiKey = ""
): Promise<FeedResponse> {
  const keyParam = openaiKey ? `&openai_key=${encodeURIComponent(openaiKey)}` : "";
  const res = await fetch(
    `${API_BASE}/api/feed/?user_id=${userId}&sources=${sources}&limit=${limit}&page=${page}${keyParam}`
  );
  if (!res.ok) throw new Error(`Feed error: ${res.status}`);
  return res.json();
}

export async function updateProfileFromText(
  rawInput: string,
  openaiKey: string,
  userId = "default"
): Promise<UserProfile> {
  const res = await fetch(`${API_BASE}/api/profile/from-text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, raw_input: rawInput, openai_api_key: openaiKey }),
  });
  const data = await res.json();
  return data.profile;
}

export async function updateProfileDirect(
  keywords: string,
  focus: string,
  openaiKey: string,
  userId = "default"
): Promise<UserProfile> {
  const res = await fetch(`${API_BASE}/api/profile/update`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, keywords, focus, openai_api_key: openaiKey }),
  });
  const data = await res.json();
  return data.profile;
}
