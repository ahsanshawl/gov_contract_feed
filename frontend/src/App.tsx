import React, { useState, useEffect, useCallback, useRef } from "react";
import "./styles.css";
import { fetchFeed, updateProfileDirect, FeedItem, UserProfile } from "./services/api";

// ─── CONSTANTS ───────────────────────────────────────────────────────────────
const SOURCE_META: Record<string, { color: string; label: string; icon: string }> = {
  "SAM.gov":          { color: "#4A9EFF", label: "CONTRACT OPP", icon: "◈" },
  "USASpending.gov":  { color: "#4AFF91", label: "AWARD",        icon: "◉" },
  "Grants.gov":       { color: "#C084FC", label: "GRANT",        icon: "◇" },
};

const QUICK_PROFILES = [
  { label: "Counter-drone / C-UAS", keywords: "counter-UAS, drone defeat, C-UAS, RF detection, UAS", focus: "Counter-drone and UAS defeat systems" },
  { label: "AI / ML for DoD",       keywords: "artificial intelligence, machine learning, autonomy, AI", focus: "AI and ML applications for defense" },
  { label: "Cybersecurity",         keywords: "cybersecurity, zero trust, SIEM, vulnerability, network defense", focus: "DoD and IC cybersecurity contracts" },
  { label: "Space / SDA",           keywords: "space domain awareness, satellite, SDA, launch, space systems", focus: "Space systems and domain awareness" },
  { label: "Hypersonics",           keywords: "hypersonic, glide vehicle, propulsion, thermal protection", focus: "Hypersonic weapons and propulsion R&D" },
  { label: "ISR / Sensors",         keywords: "ISR, intelligence surveillance, sensor fusion, EO/IR, radar", focus: "ISR platforms and sensor systems" },
];

// ─── HELPERS ─────────────────────────────────────────────────────────────────
function fmtMoney(n: number | null | undefined): string {
  if (!n) return "";
  if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`;
  return `$${n.toLocaleString()}`;
}

function fmtRelDate(d: string): string {
  if (!d) return "";
  try {
    let date: Date;
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(d)) {
      const [m, day, y] = d.split("/");
      date = new Date(`${y}-${m}-${day}`);
    } else {
      date = new Date(d);
    }
    if (isNaN(date.getTime())) return d;
    const diff = Math.round((Date.now() - date.getTime()) / 86400000);
    if (diff === 0) return "today";
    if (diff > 0 && diff < 365) return `${diff}d ago`;
    if (diff < 0 && diff > -365) return `in ${Math.abs(diff)}d`;
    return date.toLocaleDateString("en-US", { month: "short", year: "numeric" });
  } catch { return d; }
}

function daysUntil(d: string): number | null {
  if (!d) return null;
  try {
    const date = new Date(d);
    if (isNaN(date.getTime())) return null;
    return Math.round((date.getTime() - Date.now()) / 86400000);
  } catch { return null; }
}

// ─── FEED CARD ───────────────────────────────────────────────────────────────
const FeedCard: React.FC<{ item: FeedItem; index: number; isNew?: boolean }> = ({ item, index, isNew }) => {
  const [expanded, setExpanded] = useState(false);
  const meta = SOURCE_META[item.source] || { color: "#888", label: "SOURCE", icon: "◆" };
  const score = item.relevance_score ?? 0;
  const hasAI = !!item.ai_summary;
  const days = daysUntil(item.deadline);
  const urgentDeadline = days !== null && days >= 0 && days <= 14;
  const scoreColor = score >= 80 ? "#4AFF91" : score >= 55 ? "#FFD84A" : "#768390";

  return (
    <article
      className={`card${isNew ? " card-new" : ""}`}
      style={{ "--accent": meta.color, "--score-color": scoreColor, animationDelay: `${Math.min(index, 10) * 0.04}s` } as React.CSSProperties}
    >
      {/* Top row */}
      <div className="card-top">
        <span className="badge" style={{ color: meta.color, borderColor: `${meta.color}55`, background: `${meta.color}0D` }}>
          <span className="badge-icon">{meta.icon}</span>
          {meta.label}
        </span>
        <div className="card-top-right">
          {item.is_mock && <span className="demo-tag">DEMO DATA</span>}
          {score > 0 && (
            <span className="score" style={{ color: scoreColor, borderColor: `${scoreColor}44` }}>
              <span className="score-label">MATCH</span>
              <span className="score-num">{score}</span>
            </span>
          )}
        </div>
      </div>

      {/* Title */}
      <h3 className="card-title">{item.title}</h3>

      {/* AI Summary */}
      {hasAI && (
        <div className="ai-row">
          <span className="ai-pill">AI</span>
          <span className="ai-text">{item.ai_summary}</span>
        </div>
      )}
      {!hasAI && score > 0 && (
        <div className="ai-row ai-row-fallback">
          <span className="ai-pill ai-pill-kw">KW</span>
          <span className="ai-text">Keyword match — add OpenAI key in sidebar for AI summaries</span>
        </div>
      )}

      {/* Meta chips */}
      <div className="chips">
        {item.agency && <span className="chip chip-agency">{item.agency}</span>}
        {item.award_amount != null && item.award_amount > 0 && (
          <span className="chip chip-money">{fmtMoney(item.award_amount)}</span>
        )}
        {item.naics && <span className="chip">NAICS {item.naics}</span>}
        {item.set_aside && item.set_aside !== "None" && item.set_aside !== "" && (
          <span className="chip chip-setaside">{item.set_aside}</span>
        )}
        {item.contract_type && <span className="chip">{item.contract_type}</span>}
        {item.recipient && item.source === "USASpending.gov" && (
          <span className="chip chip-recipient">→ {item.recipient}</span>
        )}
      </div>

      {/* Dates */}
      <div className="dates">
        {item.posted_date && (
          <span className="date-item">
            <span className="date-key">POSTED</span>
            <span>{fmtRelDate(item.posted_date)}</span>
          </span>
        )}
        {item.deadline && (
          <span className={`date-item${urgentDeadline ? " date-urgent" : ""}`}>
            <span className="date-key">DUE</span>
            <span>{fmtRelDate(item.deadline)}{urgentDeadline ? ` ⚡ ${days}d` : ""}</span>
          </span>
        )}
      </div>

      {/* Expanded description */}
      {expanded && item.description && (
        <div className="card-desc">
          <p>{item.description.slice(0, 800)}{item.description.length > 800 ? "…" : ""}</p>
        </div>
      )}

      {/* Actions */}
      <div className="card-actions">
        {item.description && (
          <button className="act" onClick={() => setExpanded(e => !e)}>
            {expanded ? "collapse ↑" : "details ↓"}
          </button>
        )}
        <a
          href={item.url}
          target="_blank"
          rel="noreferrer"
          className="act act-ext"
          style={{ color: meta.color, borderColor: `${meta.color}44` }}
        >
          view on {item.source.split(".")[0].toLowerCase()} →
        </a>
      </div>
    </article>
  );
};

// ─── SIDEBAR ─────────────────────────────────────────────────────────────────
interface SidebarProps {
  profile: UserProfile;
  openaiKey: string;
  activeSources: string[];
  sortBy: string;
  sourceCounts: Record<string, number>;
  loading: boolean;
  onApply: (profile: UserProfile, key: string, sources: string[], sort: string) => void;
}

const SOURCES_CONFIG = [
  { id: "sam",         label: "SAM.gov",     color: "#4A9EFF", icon: "◈", desc: "Contract opportunities" },
  { id: "usaspending", label: "USASpending",  color: "#4AFF91", icon: "◉", desc: "Contract awards" },
  { id: "grants",      label: "Grants.gov",   color: "#C084FC", icon: "◇", desc: "Grant opportunities" },
];

const Sidebar: React.FC<SidebarProps> = ({
  profile, openaiKey, activeSources, sortBy, sourceCounts, loading, onApply
}) => {
  const [keywords, setKeywords] = useState(profile.keywords);
  const [focus, setFocus] = useState(profile.focus);
  const [localKey, setLocalKey] = useState(openaiKey);
  const [localSources, setLocalSources] = useState(activeSources);
  const [localSort, setLocalSort] = useState(sortBy);
  const [applying, setApplying] = useState(false);
  const [dirty, setDirty] = useState(false);

  useEffect(() => { setKeywords(profile.keywords); setFocus(profile.focus); }, [profile]);
  useEffect(() => { setLocalKey(openaiKey); }, [openaiKey]);
  useEffect(() => { setLocalSources(activeSources); }, [activeSources]);

  const markDirty = () => setDirty(true);

  const handleApply = async () => {
    setApplying(true);
    try {
      const updated = await updateProfileDirect(keywords, focus, localKey);
      onApply(updated, localKey, localSources, localSort);
    } catch {
      onApply({ keywords, focus, org_type: "" }, localKey, localSources, localSort);
    } finally {
      setApplying(false);
      setDirty(false);
    }
  };

  const toggleSource = (id: string) => {
    setLocalSources(prev =>
      prev.includes(id) ? (prev.length > 1 ? prev.filter(s => s !== id) : prev) : [...prev, id]
    );
    markDirty();
  };

  return (
    <aside className="sidebar">
      <div className="sb-brand">
        <span className="sb-logo">⬡</span>
        <div>
          <div className="sb-name">GOVFEED</div>
          <div className="sb-sub">Defense &amp; Gov Intelligence</div>
        </div>
      </div>

      <div className="sb-section">
        <div className="sb-label">YOUR FOCUS</div>
        <textarea
          className="sb-textarea"
          rows={2}
          value={focus}
          placeholder="e.g. AI-enabled ISR and targeting systems"
          onChange={e => { setFocus(e.target.value); markDirty(); }}
        />
      </div>

      <div className="sb-section">
        <div className="sb-label">SEARCH KEYWORDS</div>
        <input
          className="sb-input"
          value={keywords}
          placeholder="counter-UAS, autonomy, cyber..."
          onChange={e => { setKeywords(e.target.value); markDirty(); }}
          onKeyDown={e => e.key === "Enter" && handleApply()}
        />
        <div className="quick-chips">
          {QUICK_PROFILES.map(qp => (
            <button
              key={qp.label}
              className="quick-chip"
              onClick={() => { setKeywords(qp.keywords); setFocus(qp.focus); markDirty(); }}
            >
              {qp.label}
            </button>
          ))}
        </div>
      </div>

      <div className="sb-section">
        <div className="sb-label">SOURCES</div>
        {SOURCES_CONFIG.map(s => (
          <label key={s.id} className={`source-row${localSources.includes(s.id) ? " source-row-on" : ""}`}>
            <input type="checkbox" checked={localSources.includes(s.id)} onChange={() => toggleSource(s.id)} />
            <span className="source-icon" style={{ color: s.color }}>{s.icon}</span>
            <div className="source-info">
              <span className="source-name">{s.label}</span>
              <span className="source-desc">{s.desc}</span>
            </div>
            <span className="source-ct" style={{ color: s.color }}>
              {sourceCounts[s.id] !== undefined ? sourceCounts[s.id] : "—"}
            </span>
          </label>
        ))}
      </div>

      <div className="sb-section">
        <div className="sb-label">SORT BY</div>
        <div className="sort-row">
          {[
            { id: "relevance", label: "AI MATCH" },
            { id: "date",      label: "NEWEST" },
            { id: "amount",    label: "VALUE $" },
          ].map(s => (
            <button
              key={s.id}
              className={`sort-btn${localSort === s.id ? " sort-on" : ""}`}
              onClick={() => { setLocalSort(s.id); markDirty(); }}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="sb-section">
        <div className="sb-label">
          OPENAI KEY <span className="sb-optional">— enables AI ranking + summaries</span>
        </div>
        <input
          className="sb-input sb-key"
          type="password"
          value={localKey}
          placeholder="sk-..."
          onChange={e => { setLocalKey(e.target.value); markDirty(); }}
        />
        <p className="sb-hint">
          {localKey
            ? "✓ Key set — AI summaries active on next refresh"
            : "Without a key, keyword scoring is used instead"}
        </p>
      </div>

      <button
        className={`apply-btn${dirty ? " apply-dirty" : ""}`}
        onClick={handleApply}
        disabled={applying || loading}
      >
        {applying ? "Updating…" : dirty ? "↻ Apply Changes" : "↻ Refresh Feed"}
      </button>
    </aside>
  );
};

// ─── MAIN APP ─────────────────────────────────────────────────────────────────
export default function App() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [newItemIds, setNewItemIds] = useState<Set<string>>(new Set());
  const [profile, setProfile] = useState<UserProfile>({
    keywords: "defense technology, AI, autonomous systems",
    focus: "Defense technology and government contracts",
    org_type: "",
  });
  const [openaiKey, setOpenaiKey] = useState("");
  const [activeSources, setActiveSources] = useState(["sam", "usaspending", "grants"]);
  const [sortBy, setSortBy] = useState("relevance");
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState("");
  const [sourceCounts, setSourceCounts] = useState<Record<string, number>>({});
  const [offset, setOffset] = useState(0);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const PAGE = 15;

  const loadFeed = useCallback(async (
    reset = true,
    overrideKey?: string,
    overrideSources?: string[]
  ) => {
    const key = overrideKey !== undefined ? overrideKey : openaiKey;
    const sources = overrideSources !== undefined ? overrideSources : activeSources;
    const currentOffset = reset ? 0 : offset;

    if (reset) { setLoading(true); }
    else { setLoadingMore(true); }
    setError("");

    try {
      const data = await fetchFeed("default", sources.join(","), PAGE, currentOffset, key);

      if (reset) {
        const incomingIds = new Set(data.items.map((i: FeedItem) => i.id));
        setNewItemIds(incomingIds);
        setItems(data.items);
        setOffset(PAGE);
        setTimeout(() => setNewItemIds(new Set()), 4000);
      } else {
        setItems(prev => [...prev, ...data.items]);
        setOffset(o => o + PAGE);
      }

      setHasMore(data.has_more);
      setSourceCounts(data.source_counts || {});
      if (data.profile) setProfile(data.profile);
      setLastUpdated(new Date());
    } catch {
      setError("Cannot reach the backend. Make sure FastAPI is running on port 8000.");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [activeSources, openaiKey, offset]);

  useEffect(() => {
    loadFeed(true);
  }, []); // eslint-disable-line

  const sortedItems = [...items].sort((a, b) => {
    if (sortBy === "relevance") return (b.relevance_score ?? 0) - (a.relevance_score ?? 0);
    if (sortBy === "amount")    return (b.award_amount ?? 0) - (a.award_amount ?? 0);
    if (sortBy === "date") {
      return new Date(b.posted_date || 0).getTime() - new Date(a.posted_date || 0).getTime();
    }
    return 0;
  });

  const handleSidebarApply = (newProfile: UserProfile, newKey: string, newSources: string[], newSort: string) => {
    setProfile(newProfile);
    setOpenaiKey(newKey);
    setActiveSources(newSources);
    setSortBy(newSort);
    loadFeed(true, newKey, newSources);
  };

  return (
    <div className="layout">
      <Sidebar
        profile={profile}
        openaiKey={openaiKey}
        activeSources={activeSources}
        sortBy={sortBy}
        sourceCounts={sourceCounts}
        loading={loading}
        onApply={handleSidebarApply}
      />

      <main className="feed-main">
        {/* Topbar */}
        <div className="feed-topbar">
          <div className="topbar-left">
            <span className="topbar-count">
              {loading
                ? <span className="topbar-spin">⟳ Loading…</span>
                : `${sortedItems.length} items`}
            </span>
            {lastUpdated && !loading && (
              <span className="topbar-time">updated {fmtRelDate(lastUpdated.toISOString())}</span>
            )}
          </div>
          <button className="topbar-refresh" onClick={() => loadFeed(true)} disabled={loading}>
            ⟳ refresh
          </button>
        </div>

        {error && (
          <div className="error-bar">
            <strong>⚠ Backend offline.</strong> {error}
          </div>
        )}

        {loading ? (
          <div className="skeletons">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="skeleton" style={{ animationDelay: `${i * 0.06}s` }} />
            ))}
          </div>
        ) : sortedItems.length === 0 ? (
          <div className="empty">
            <div className="empty-glyph">◈</div>
            <p className="empty-msg">No items found for your current filters.</p>
            <p className="empty-sub">Adjust keywords or enable more sources in the sidebar.</p>
          </div>
        ) : (
          <>
            <div className="feed-list">
              {sortedItems.map((item, i) => (
                <FeedCard
                  key={item.id}
                  item={item}
                  index={i}
                  isNew={newItemIds.has(item.id)}
                />
              ))}
            </div>

            <div className="load-more-area">
              {hasMore ? (
                <button
                  className="load-more"
                  onClick={() => loadFeed(false)}
                  disabled={loadingMore}
                >
                  {loadingMore ? <><span className="topbar-spin">⟳</span> Loading…</> : "Load more ↓"}
                </button>
              ) : (
                <p className="feed-end">— end of feed —</p>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
