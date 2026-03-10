"""
demo.py  —  v0.2.0
Dashboard now fetches LIVE data from the running API (localhost:8000)
instead of reading JSON files directly.

HOW TO USE:
    1. Start the API first:   uvicorn api.main:app --reload
    2. Then run this script:  python demo.py
       The script opens a self-contained HTML file that fetches from the API.

The generated HTML uses vanilla JS fetch() calls — no build step, no bundler.
"""

from __future__ import annotations
import os
import webbrowser

# ── Path to write the dashboard HTML ──────────────────────────────────────────
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "visualization", "dashboard.html")
API_BASE    = "http://localhost:8000"

DASHBOARD_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Open Intelligence Lab — Dashboard</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #0d1117;
      color: #c9d1d9;
      min-height: 100vh;
      padding: 2rem;
    }}
    h1 {{ color: #58a6ff; margin-bottom: 0.25rem; font-size: 1.6rem; }}
    .subtitle {{ color: #8b949e; font-size: 0.9rem; margin-bottom: 2rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
    .card {{
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 8px;
      padding: 1.25rem;
    }}
    .card .label {{ font-size: 0.75rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.05em; }}
    .card .value {{ font-size: 1.8rem; font-weight: 700; color: #58a6ff; margin-top: 0.25rem; }}
    .search-row {{
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
      margin-bottom: 1.5rem;
      align-items: flex-end;
    }}
    .search-row label {{ font-size: 0.8rem; color: #8b949e; display: block; margin-bottom: 0.3rem; }}
    input, select {{
      background: #161b22;
      border: 1px solid #30363d;
      color: #c9d1d9;
      border-radius: 6px;
      padding: 0.5rem 0.75rem;
      font-size: 0.9rem;
      outline: none;
    }}
    input:focus, select:focus {{ border-color: #58a6ff; }}
    button {{
      background: #238636;
      color: #fff;
      border: none;
      border-radius: 6px;
      padding: 0.55rem 1.25rem;
      font-size: 0.9rem;
      cursor: pointer;
    }}
    button:hover {{ background: #2ea043; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.88rem; }}
    th {{
      text-align: left;
      padding: 0.6rem 1rem;
      background: #161b22;
      border-bottom: 1px solid #30363d;
      color: #8b949e;
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.75rem;
      letter-spacing: 0.04em;
    }}
    td {{ padding: 0.6rem 1rem; border-bottom: 1px solid #21262d; }}
    tr:hover td {{ background: #161b22; }}
    .risk-badge {{
      display: inline-block;
      padding: 0.2rem 0.55rem;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 600;
    }}
    .risk-high   {{ background: #3d1a1a; color: #f85149; }}
    .risk-medium {{ background: #2d2208; color: #e3b341; }}
    .risk-low    {{ background: #0f2a1a; color: #3fb950; }}
    .detail-panel {{
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 8px;
      padding: 1.25rem;
      margin-top: 1.5rem;
      display: none;
    }}
    .detail-panel h3 {{ color: #58a6ff; margin-bottom: 0.75rem; }}
    .explanation {{ line-height: 1.7; color: #c9d1d9; }}
    .status {{ font-size: 0.82rem; color: #8b949e; margin-bottom: 1rem; }}
    .error {{ color: #f85149; }}
    .pagination {{ display: flex; gap: 0.5rem; align-items: center; margin-top: 1rem; font-size: 0.85rem; }}
    .page-btn {{ padding: 0.35rem 0.75rem; font-size: 0.82rem; background: #21262d; }}
    .page-btn:disabled {{ opacity: 0.4; cursor: default; }}
  </style>
</head>
<body>

  <h1>🔬 Open Intelligence Lab</h1>
  <p class="subtitle">v0.2.0 — Live data from <code>{API_BASE}</code></p>

  <!-- Summary cards -->
  <div class="grid" id="summary-cards">
    <div class="card"><div class="label">Nodes</div><div class="value" id="s-nodes">—</div></div>
    <div class="card"><div class="label">Edges</div><div class="value" id="s-edges">—</div></div>
    <div class="card"><div class="label">Avg Risk</div><div class="value" id="s-avg">—</div></div>
    <div class="card"><div class="label">Max Risk</div><div class="value" id="s-max">—</div></div>
  </div>

  <!-- Search / filter controls -->
  <div class="search-row">
    <div>
      <label>Search (id / label)</label>
      <input id="q-query" type="text" placeholder="e.g. apt28" style="width:180px"/>
    </div>
    <div>
      <label>Min Risk</label>
      <input id="q-min" type="number" min="0" max="1" step="0.05" placeholder="0.0" style="width:90px"/>
    </div>
    <div>
      <label>Max Risk</label>
      <input id="q-max" type="number" min="0" max="1" step="0.05" placeholder="1.0" style="width:90px"/>
    </div>
    <div>
      <label>Type</label>
      <input id="q-type" type="text" placeholder="threat_actor" style="width:140px"/>
    </div>
    <div style="align-self:flex-end">
      <button onclick="fetchEntities(0)">Search</button>
    </div>
  </div>

  <p class="status" id="status">Loading…</p>

  <!-- Results table -->
  <table>
    <thead>
      <tr>
        <th>Entity ID</th>
        <th>Label</th>
        <th>Type</th>
        <th>Risk Score</th>
        <th>Action</th>
      </tr>
    </thead>
    <tbody id="entity-table-body"></tbody>
  </table>

  <div class="pagination">
    <button class="page-btn" id="btn-prev" onclick="changePage(-1)" disabled>← Prev</button>
    <span id="page-info">—</span>
    <button class="page-btn" id="btn-next" onclick="changePage(1)">Next →</button>
  </div>

  <!-- Detail panel -->
  <div class="detail-panel" id="detail-panel">
    <h3 id="detail-title">Entity detail</h3>
    <p><strong>Risk score:</strong> <span id="detail-score">—</span></p>
    <p style="margin-top:0.75rem"><strong>Explanation:</strong></p>
    <p class="explanation" id="detail-explanation">—</p>
  </div>

<script>
  const API = "{API_BASE}";
  const LIMIT = 20;
  let currentOffset = 0;
  let totalEntities  = 0;

  // ── On load ─────────────────────────────────────────────────────────────────
  window.addEventListener("DOMContentLoaded", async () => {{
    await fetchSummary();
    await fetchEntities(0);
  }});

  // ── Summary cards ────────────────────────────────────────────────────────────
  async function fetchSummary() {{
    try {{
      const r = await fetch(`${{API}}/intelligence/graph/summary`);
      if (!r.ok) throw new Error(r.statusText);
      const d = await r.json();
      document.getElementById("s-nodes").textContent = d.node_count;
      document.getElementById("s-edges").textContent = d.edge_count;
      document.getElementById("s-avg").textContent   = d.avg_risk_score.toFixed(3);
      document.getElementById("s-max").textContent   = d.max_risk_score.toFixed(3);
    }} catch (e) {{
      document.getElementById("s-nodes").textContent = "ERR";
      console.error("Summary fetch failed:", e);
    }}
  }}

  // ── Entity list ──────────────────────────────────────────────────────────────
  async function fetchEntities(offset) {{
    currentOffset = offset;
    const params = new URLSearchParams({{ limit: LIMIT, offset }});
    const q    = document.getElementById("q-query").value.trim();
    const minR = document.getElementById("q-min").value.trim();
    const maxR = document.getElementById("q-max").value.trim();
    const type = document.getElementById("q-type").value.trim();
    if (q)    params.set("query", q);
    if (minR) params.set("min_risk", minR);
    if (maxR) params.set("max_risk", maxR);
    if (type) params.set("entity_type", type);

    document.getElementById("status").textContent = "Fetching…";
    try {{
      const r = await fetch(`${{API}}/intelligence/entities?${{params}}`);
      if (!r.ok) throw new Error(`HTTP ${{r.status}}: ${{r.statusText}}`);
      const data = await r.json();
      totalEntities = data.total;
      renderTable(data.entities);
      document.getElementById("status").textContent =
        `Showing ${{offset + 1}}–${{Math.min(offset + LIMIT, totalEntities)}} of ${{totalEntities}} entities`;
      updatePagination();
    }} catch (e) {{
      document.getElementById("status").innerHTML =
        `<span class="error">⚠ API unreachable — is <code>uvicorn api.main:app</code> running? (${{e.message}})</span>`;
      document.getElementById("entity-table-body").innerHTML = "";
    }}
  }}

  function renderTable(entities) {{
    const tbody = document.getElementById("entity-table-body");
    if (!entities.length) {{
      tbody.innerHTML = `<tr><td colspan="5" style="color:#8b949e;padding:1rem">No entities match the current filters.</td></tr>`;
      return;
    }}
    tbody.innerHTML = entities.map(e => {{
      const score = typeof e.risk_score === "number" ? e.risk_score : 0;
      const cls   = score >= 0.7 ? "risk-high" : score >= 0.4 ? "risk-medium" : "risk-low";
      return `
        <tr>
          <td><code>${{e.entity_id}}</code></td>
          <td>${{e.label || e.entity_id}}</td>
          <td>${{e.type || "—"}}</td>
          <td><span class="risk-badge ${{cls}}">${{score.toFixed(3)}}</span></td>
          <td><button style="padding:0.25rem 0.6rem;font-size:0.78rem;background:#1f6feb"
                onclick="showDetail('${{e.entity_id}}')">Analyze</button></td>
        </tr>`;
    }}).join("");
  }}

  // ── Detail panel ─────────────────────────────────────────────────────────────
  async function showDetail(entityId) {{
    const panel = document.getElementById("detail-panel");
    panel.style.display = "block";
    document.getElementById("detail-title").textContent = entityId;
    document.getElementById("detail-score").textContent = "Loading…";
    document.getElementById("detail-explanation").textContent = "Loading…";
    panel.scrollIntoView({{ behavior: "smooth" }});

    try {{
      const r = await fetch(`${{API}}/intelligence/analyze/${{encodeURIComponent(entityId)}}`);
      if (!r.ok) throw new Error(`HTTP ${{r.status}}`);
      const d = await r.json();
      document.getElementById("detail-score").textContent = d.risk_score;
      document.getElementById("detail-explanation").textContent =
        typeof d.explanation === "string" ? d.explanation : JSON.stringify(d.explanation, null, 2);
    }} catch (e) {{
      document.getElementById("detail-explanation").textContent = `Error: ${{e.message}}`;
    }}
  }}

  // ── Pagination ───────────────────────────────────────────────────────────────
  function changePage(direction) {{
    const next = currentOffset + direction * LIMIT;
    if (next < 0 || next >= totalEntities) return;
    fetchEntities(next);
  }}

  function updatePagination() {{
    const prev = document.getElementById("btn-prev");
    const next = document.getElementById("btn-next");
    const info = document.getElementById("page-info");
    const page  = Math.floor(currentOffset / LIMIT) + 1;
    const pages = Math.ceil(totalEntities / LIMIT);
    info.textContent   = `Page ${{page}} / ${{pages}}`;
    prev.disabled      = currentOffset === 0;
    next.disabled      = currentOffset + LIMIT >= totalEntities;
  }}
</script>
</body>
</html>
"""

def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(DASHBOARD_HTML)
    print(f"✅  Dashboard written to: {OUTPUT_PATH}")
    print(f"📡  Make sure the API is running:  uvicorn api.main:app --reload")
    print(f"🌐  Opening dashboard in browser…")
    webbrowser.open(f"file://{os.path.abspath(OUTPUT_PATH)}")


if __name__ == "__main__":
    main()
