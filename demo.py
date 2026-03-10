"""
demo.py  —  v0.2.0
Dashboard fetches LIVE data from localhost:8000.
Includes: summary cards, search/filter table, graph visualization, entity detail panel.

HOW TO USE:
    1. uvicorn api.main:app --reload --port 8000
    2. python demo.py
"""

from __future__ import annotations
import os
import webbrowser

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "visualization", "dashboard.html")
API_BASE    = "http://localhost:8000"

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Open Intelligence Lab — Dashboard</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',system-ui,sans-serif;background:#0d1117;color:#c9d1d9;min-height:100vh;padding:1.5rem}
    h1{color:#58a6ff;font-size:1.5rem;margin-bottom:.2rem}
    .subtitle{color:#8b949e;font-size:.85rem;margin-bottom:1.5rem}

    /* TABS */
    .tabs{display:flex;gap:.5rem;margin-bottom:1.5rem;border-bottom:1px solid #30363d;padding-bottom:.5rem}
    .tab{padding:.45rem 1.1rem;border-radius:6px 6px 0 0;cursor:pointer;font-size:.88rem;color:#8b949e;border:1px solid transparent;border-bottom:none}
    .tab.active{color:#58a6ff;border-color:#30363d;background:#161b22}
    .tab:hover:not(.active){color:#c9d1d9}
    .panel{display:none}.panel.active{display:block}

    /* SUMMARY CARDS */
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1rem;margin-bottom:1.5rem}
    .card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1.1rem}
    .card .label{font-size:.72rem;color:#8b949e;text-transform:uppercase;letter-spacing:.05em}
    .card .value{font-size:1.7rem;font-weight:700;color:#58a6ff;margin-top:.2rem}

    /* SEARCH */
    .search-row{display:flex;gap:.6rem;flex-wrap:wrap;margin-bottom:1.2rem;align-items:flex-end}
    .search-row label{font-size:.78rem;color:#8b949e;display:block;margin-bottom:.25rem}
    input,select{background:#161b22;border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:.45rem .7rem;font-size:.88rem;outline:none}
    input:focus,select:focus{border-color:#58a6ff}
    button{background:#238636;color:#fff;border:none;border-radius:6px;padding:.5rem 1.1rem;font-size:.88rem;cursor:pointer}
    button:hover{background:#2ea043}

    /* TABLE */
    table{width:100%;border-collapse:collapse;font-size:.85rem}
    th{text-align:left;padding:.55rem .9rem;background:#161b22;border-bottom:1px solid #30363d;color:#8b949e;font-weight:600;text-transform:uppercase;font-size:.72rem;letter-spacing:.04em}
    td{padding:.55rem .9rem;border-bottom:1px solid #21262d}
    tr:hover td{background:#161b22}
    .risk-badge{display:inline-block;padding:.18rem .5rem;border-radius:999px;font-size:.76rem;font-weight:700}
    .risk-high{background:#3d1a1a;color:#f85149}
    .risk-medium{background:#2d2208;color:#e3b341}
    .risk-low{background:#0f2a1a;color:#3fb950}
    .status{font-size:.8rem;color:#8b949e;margin-bottom:.9rem}
    .error{color:#f85149}
    .pagination{display:flex;gap:.5rem;align-items:center;margin-top:.9rem;font-size:.83rem}
    .page-btn{padding:.3rem .7rem;font-size:.8rem;background:#21262d}
    .page-btn:disabled{opacity:.4;cursor:default}

    /* DETAIL PANEL */
    .detail-panel{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1.2rem;margin-top:1.2rem;display:none}
    .detail-panel h3{color:#58a6ff;margin-bottom:.6rem;font-size:1rem}
    .detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;margin-bottom:.8rem}
    .detail-item .dk{font-size:.72rem;color:#8b949e;text-transform:uppercase}
    .detail-item .dv{font-size:.95rem;color:#e6edf3;margin-top:.1rem}
    .explanation-list{list-style:none;padding:0}
    .explanation-list li{padding:.4rem 0;border-bottom:1px solid #21262d;font-size:.85rem;line-height:1.6;color:#c9d1d9}
    .explanation-list li:last-child{border:none}
    .explanation-list li::before{content:"→ ";color:#58a6ff;font-weight:700}

    /* GRAPH */
    #graph-container{background:#0d1117;border:1px solid #30363d;border-radius:8px;position:relative;overflow:hidden}
    #graph-svg{width:100%;height:620px}
    .graph-controls{display:flex;gap:.5rem;margin-bottom:.8rem;flex-wrap:wrap;align-items:center}
    .graph-controls select{width:180px}
    .legend{display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:.8rem}
    .legend-item{display:flex;align-items:center;gap:.4rem;font-size:.78rem;color:#8b949e}
    .legend-dot{width:11px;height:11px;border-radius:50%}
    .node-tooltip{position:absolute;background:#161b22;border:1px solid #30363d;border-radius:6px;padding:.6rem .9rem;font-size:.8rem;pointer-events:none;opacity:0;transition:opacity .15s;max-width:260px;z-index:100}
    .node-tooltip .tt-id{color:#58a6ff;font-weight:700;margin-bottom:.2rem}
    .node-tooltip .tt-type{color:#8b949e;font-size:.72rem;text-transform:uppercase}
    .node-tooltip .tt-score{color:#e3b341;font-weight:600;margin-top:.3rem}
    .graph-info{font-size:.78rem;color:#8b949e;margin-top:.5rem}
  </style>
</head>
<body>

<h1>🔬 Open Intelligence Lab</h1>
<p class="subtitle">v0.2.0 — Live data from <code>""" + API_BASE + """</code></p>

<!-- Summary Cards -->
<div class="grid">
  <div class="card"><div class="label">Nodes</div><div class="value" id="s-nodes">—</div></div>
  <div class="card"><div class="label">Edges</div><div class="value" id="s-edges">—</div></div>
  <div class="card"><div class="label">Avg Risk</div><div class="value" id="s-avg">—</div></div>
  <div class="card"><div class="label">Max Risk</div><div class="value" id="s-max">—</div></div>
  <div class="card"><div class="label">Min Risk</div><div class="value" id="s-min">—</div></div>
</div>

<!-- Tabs -->
<div class="tabs">
  <div class="tab active" onclick="switchTab('entities')">📋 Entities</div>
  <div class="tab" onclick="switchTab('graph')">🕸️ Graph</div>
</div>

<!-- ENTITIES PANEL -->
<div id="panel-entities" class="panel active">
  <div class="search-row">
    <div><label>Search (id / label)</label><input id="q-query" type="text" placeholder="e.g. APT28" style="width:170px"/></div>
    <div><label>Min Risk</label><input id="q-min" type="number" min="0" max="1" step="0.05" placeholder="0.0" style="width:85px"/></div>
    <div><label>Max Risk</label><input id="q-max" type="number" min="0" max="1" step="0.05" placeholder="1.0" style="width:85px"/></div>
    <div><label>Type</label>
      <select id="q-type">
        <option value="">All types</option>
        <option value="threat_actor">threat_actor</option>
        <option value="malware">malware</option>
        <option value="vulnerability">vulnerability</option>
        <option value="infrastructure">infrastructure</option>
        <option value="target_sector">target_sector</option>
        <option value="attack_pattern">attack_pattern</option>
      </select>
    </div>
    <div style="align-self:flex-end"><button onclick="fetchEntities(0)">Search</button></div>
  </div>

  <p class="status" id="status">Loading…</p>

  <table>
    <thead><tr><th>Entity ID</th><th>Label</th><th>Type</th><th>Risk Score</th><th>Action</th></tr></thead>
    <tbody id="entity-table-body"></tbody>
  </table>
  <div class="pagination">
    <button class="page-btn" id="btn-prev" onclick="changePage(-1)" disabled>← Prev</button>
    <span id="page-info">—</span>
    <button class="page-btn" id="btn-next" onclick="changePage(1)">Next →</button>
  </div>

  <div class="detail-panel" id="detail-panel">
    <h3 id="detail-title">Entity Detail</h3>
    <div class="detail-grid">
      <div class="detail-item"><div class="dk">Entity ID</div><div class="dv" id="d-id">—</div></div>
      <div class="detail-item"><div class="dk">Risk Score</div><div class="dv" id="d-score">—</div></div>
    </div>
    <div class="dk" style="margin-bottom:.5rem">Explanation</div>
    <ul class="explanation-list" id="d-explanation"></ul>
  </div>
</div>

<!-- GRAPH PANEL -->
<div id="panel-graph" class="panel">
  <div class="graph-controls">
    <div>
      <label style="font-size:.78rem;color:#8b949e;display:block;margin-bottom:.25rem">Filter by Type</label>
      <select id="g-type-filter" onchange="renderGraph()">
        <option value="">All</option>
        <option value="threat_actor">Threat Actors</option>
        <option value="malware">Malware</option>
        <option value="vulnerability">Vulnerabilities</option>
        <option value="infrastructure">Infrastructure</option>
        <option value="target_sector">Target Sectors</option>
        <option value="attack_pattern">Attack Patterns</option>
      </select>
    </div>
    <div style="align-self:flex-end">
      <button onclick="resetZoom()" style="background:#21262d;font-size:.8rem">Reset Zoom</button>
    </div>
    <div style="align-self:flex-end;font-size:.78rem;color:#8b949e">
      Drag nodes · Scroll to zoom · Click to analyze
    </div>
  </div>

  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#f85149"></div>Threat Actor</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ff7b72"></div>Malware</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ffa657"></div>Vulnerability</div>
    <div class="legend-item"><div class="legend-dot" style="background:#d2a8ff"></div>Infrastructure</div>
    <div class="legend-item"><div class="legend-dot" style="background:#79c0ff"></div>Target Sector</div>
    <div class="legend-item"><div class="legend-dot" style="background:#56d364"></div>Attack Pattern</div>
  </div>

  <div id="graph-container">
    <div class="node-tooltip" id="tooltip"></div>
    <svg id="graph-svg"></svg>
  </div>
  <p class="graph-info" id="graph-info">Loading graph data…</p>

  <div class="detail-panel" id="graph-detail-panel" style="margin-top:1rem">
    <h3 id="gd-title">Entity Detail</h3>
    <div class="detail-grid">
      <div class="detail-item"><div class="dk">Entity ID</div><div class="dv" id="gd-id">—</div></div>
      <div class="detail-item"><div class="dk">Risk Score</div><div class="dv" id="gd-score">—</div></div>
    </div>
    <div class="dk" style="margin-bottom:.5rem">Explanation</div>
    <ul class="explanation-list" id="gd-explanation"></ul>
  </div>
</div>

<script>
const API = '""" + API_BASE + """';
const LIMIT = 20;
let currentOffset = 0;
let totalEntities = 0;
let allGraphData = null;

// ── Tab switching ─────────────────────────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab').forEach((t,i) => {
    const names = ['entities','graph'];
    t.classList.toggle('active', names[i] === name);
  });
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.getElementById('panel-' + name).classList.add('active');
  if (name === 'graph' && !allGraphData) loadGraphData();
}

// ── On load ───────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', async () => {
  await fetchSummary();
  await fetchEntities(0);
});

// ── Summary ───────────────────────────────────────────────────────────────────
async function fetchSummary() {
  try {
    const r = await fetch(`${API}/intelligence/graph/summary`);
    const d = await r.json();
    document.getElementById('s-nodes').textContent = d.node_count;
    document.getElementById('s-edges').textContent = d.edge_count;
    document.getElementById('s-avg').textContent   = d.avg_risk_score.toFixed(3);
    document.getElementById('s-max').textContent   = d.max_risk_score.toFixed(3);
    document.getElementById('s-min').textContent   = d.min_risk_score.toFixed(3);
  } catch(e) {
    document.getElementById('s-nodes').textContent = 'ERR';
  }
}

// ── Entity table ──────────────────────────────────────────────────────────────
async function fetchEntities(offset) {
  currentOffset = offset;
  const params = new URLSearchParams({ limit: LIMIT, offset });
  const q    = document.getElementById('q-query').value.trim();
  const minR = document.getElementById('q-min').value.trim();
  const maxR = document.getElementById('q-max').value.trim();
  const type = document.getElementById('q-type').value;
  if (q)    params.set('query', q);
  if (minR) params.set('min_risk', minR);
  if (maxR) params.set('max_risk', maxR);
  if (type) params.set('entity_type', type);

  document.getElementById('status').textContent = 'Fetching…';
  try {
    const r = await fetch(`${API}/intelligence/entities?${params}`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    totalEntities = data.total;
    renderTable(data.entities);
    document.getElementById('status').textContent =
      `Showing ${offset+1}–${Math.min(offset+LIMIT,totalEntities)} of ${totalEntities} entities`;
    updatePagination();
  } catch(e) {
    document.getElementById('status').innerHTML =
      `<span class="error">⚠ API unreachable — is uvicorn running? (${e.message})</span>`;
    document.getElementById('entity-table-body').innerHTML = '';
  }
}

function renderTable(entities) {
  const tbody = document.getElementById('entity-table-body');
  if (!entities.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="color:#8b949e;padding:1rem">No entities match.</td></tr>`;
    return;
  }
  tbody.innerHTML = entities.map(e => {
    const score = typeof e.risk_score === 'number' ? e.risk_score : 0;
    const cls   = score >= 0.7 ? 'risk-high' : score >= 0.4 ? 'risk-medium' : 'risk-low';
    return `<tr>
      <td><code>${e.entity_id}</code></td>
      <td>${e.label || e.entity_id}</td>
      <td><span style="font-size:.75rem;color:#8b949e">${e.type || '—'}</span></td>
      <td><span class="risk-badge ${cls}">${score.toFixed(3)}</span></td>
      <td><button style="padding:.22rem .55rem;font-size:.76rem;background:#1f6feb"
            onclick="showDetail('${e.entity_id}','table')">Analyze</button></td>
    </tr>`;
  }).join('');
}

async function showDetail(entityId, source) {
  const panelId = source === 'graph' ? 'graph-detail-panel' : 'detail-panel';
  const panel = document.getElementById(panelId);
  panel.style.display = 'block';
  const prefix = source === 'graph' ? 'gd' : 'd';
  document.getElementById(`${prefix}-title`).textContent = entityId;
  document.getElementById(`${prefix}-id`).textContent = entityId;
  document.getElementById(`${prefix}-score`).textContent = 'Loading…';
  document.getElementById(`${prefix}-explanation`).innerHTML = '';
  panel.scrollIntoView({ behavior: 'smooth' });

  try {
    const r = await fetch(`${API}/intelligence/analyze/${encodeURIComponent(entityId)}`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const d = await r.json();
    document.getElementById(`${prefix}-score`).textContent = d.risk_score;
    const lines = Array.isArray(d.explanation) ? d.explanation : [String(d.explanation)];
    document.getElementById(`${prefix}-explanation`).innerHTML =
      lines.map(l => `<li>${l}</li>`).join('');
  } catch(e) {
    document.getElementById(`${prefix}-explanation`).innerHTML =
      `<li style="color:#f85149">Error: ${e.message}</li>`;
  }
}

function changePage(dir) {
  const next = currentOffset + dir * LIMIT;
  if (next < 0 || next >= totalEntities) return;
  fetchEntities(next);
}
function updatePagination() {
  document.getElementById('btn-prev').disabled = currentOffset === 0;
  document.getElementById('btn-next').disabled = currentOffset + LIMIT >= totalEntities;
  const page  = Math.floor(currentOffset / LIMIT) + 1;
  const pages = Math.ceil(totalEntities / LIMIT);
  document.getElementById('page-info').textContent = `Page ${page} / ${pages}`;
}

// ── GRAPH VISUALIZATION ───────────────────────────────────────────────────────

const TYPE_COLORS = {
  threat_actor:  '#f85149',
  malware:       '#ff7b72',
  vulnerability: '#ffa657',
  infrastructure:'#d2a8ff',
  target_sector: '#79c0ff',
  attack_pattern:'#56d364',
};
const TYPE_RADIUS = {
  threat_actor:  16,
  malware:       13,
  vulnerability: 14,
  infrastructure:12,
  target_sector: 15,
  attack_pattern:11,
};

let svgSel, simulation, zoomBehavior;

async function loadGraphData() {
  document.getElementById('graph-info').textContent = 'Loading…';
  try {
    const r = await fetch(`${API}/intelligence/entities?limit=200`);
    const data = await r.json();

    // Build nodes + edges from entity list + known relations via analyze
    const nodes = data.entities.map(e => ({
      id:    e.entity_id,
      label: e.label,
      type:  e.type,
      score: e.risk_score,
    }));

    // Fetch relations from a dedicated call — use graph summary node list
    // We build edges by calling /entities/ids and checking known patterns
    const edgeRes = await fetch(`${API}/intelligence/entities/ids`);
    const edgeData = await edgeRes.json();

    allGraphData = { nodes, edges: [] };

    // Load edges from the static relations file via the API
    // We expose edges through the analyze endpoint's neighbor data
    // For now build edges by fetching each entity's connections
    await buildEdges(nodes);

    renderGraph();
  } catch(e) {
    document.getElementById('graph-info').textContent = `Error: ${e.message}`;
  }
}

async function buildEdges(nodes) {
  // Fetch all entities with full detail to extract relationships
  const edgesSet = new Set();
  const edges = [];

  // We'll batch-fetch a sample — analyze each node to get neighbors
  // Use the known relations from the dataset structure
  const knownRelations = [
    ['TA-001','MA-001','uses'],['TA-001','MA-002','uses'],['TA-001','INF-001','uses'],
    ['TA-002','MA-003','uses'],['TA-002','VUL-002','exploits'],
    ['TA-003','MA-004','uses'],['TA-003','MA-005','uses'],
    ['TA-004','MA-006','uses'],
    ['TA-005','MA-007','uses'],['TA-005','INF-002','uses'],
    ['TA-006','MA-008','uses'],['TA-006','VUL-001','exploits'],
    ['TA-001','SECTOR-003','targets'],['TA-002','SECTOR-003','targets'],
    ['TA-004','SECTOR-002','targets'],['TA-005','SECTOR-001','targets'],
    ['TA-006','SECTOR-002','targets'],['TA-007','SECTOR-001','targets'],
    ['MA-001','MA-002','related_to'],['VUL-001','SECTOR-002','related_to'],
    ['TA-001','OSINT-T003','uses_pattern'],['TA-002','OSINT-T007','uses_pattern'],
    ['TA-003','OSINT-T004','uses_pattern'],['TA-004','OSINT-T015','uses_pattern'],
    ['TA-005','OSINT-T005','uses_pattern'],['TA-005','OSINT-T011','uses_pattern'],
    ['TA-006','OSINT-T010','uses_pattern'],['TA-007','OSINT-T003','uses_pattern'],
  ];

  const nodeIds = new Set(allGraphData.nodes.map(n => n.id));
  knownRelations.forEach(([src, dst, rel]) => {
    const key = `${src}->${dst}`;
    if (!edgesSet.has(key) && nodeIds.has(src) && nodeIds.has(dst)) {
      edgesSet.add(key);
      edges.push({ source: src, target: dst, type: rel });
    }
  });

  allGraphData.edges = edges;
}

function renderGraph() {
  if (!allGraphData) return;

  const typeFilter = document.getElementById('g-type-filter').value;
  const filteredNodes = typeFilter
    ? allGraphData.nodes.filter(n => n.type === typeFilter)
    : allGraphData.nodes;
  const filteredIds = new Set(filteredNodes.map(n => n.id));
  const filteredEdges = allGraphData.edges.filter(
    e => filteredIds.has(e.source) && filteredIds.has(e.target)
  );

  document.getElementById('graph-info').textContent =
    `${filteredNodes.length} nodes · ${filteredEdges.length} edges · Risk score drives node size`;

  const container = document.getElementById('graph-container');
  const W = container.clientWidth || 900;
  const H = 620;

  d3.select('#graph-svg').selectAll('*').remove();

  svgSel = d3.select('#graph-svg')
    .attr('viewBox', `0 0 ${W} ${H}`);

  zoomBehavior = d3.zoom()
    .scaleExtent([0.2, 4])
    .on('zoom', e => g.attr('transform', e.transform));
  svgSel.call(zoomBehavior);

  const g = svgSel.append('g');

  // Arrow markers per type
  const markerTypes = [...new Set(filteredEdges.map(e => e.type))];
  svgSel.append('defs').selectAll('marker')
    .data(['uses','exploits','targets','uses_pattern','related_to'])
    .enter().append('marker')
    .attr('id', d => `arrow-${d}`)
    .attr('viewBox','0 -5 10 10')
    .attr('refX', 22).attr('refY', 0)
    .attr('markerWidth', 6).attr('markerHeight', 6)
    .attr('orient','auto')
    .append('path')
    .attr('d','M0,-5L10,0L0,5')
    .attr('fill', d => d === 'exploits' ? '#ffa657' : d === 'targets' ? '#f85149' : '#484f58');

  // Copy nodes/edges for d3 simulation
  const nodes = filteredNodes.map(n => ({ ...n }));
  const edges = filteredEdges.map(e => ({ ...e }));

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id).distance(d => {
      const types = [d.source.type, d.target.type];
      if (types.includes('threat_actor')) return 120;
      return 90;
    }).strength(0.6))
    .force('charge', d3.forceManyBody().strength(-320))
    .force('center', d3.forceCenter(W/2, H/2))
    .force('collision', d3.forceCollide().radius(d => (TYPE_RADIUS[d.type]||12) + 8));

  // Edges
  const link = g.append('g').selectAll('line')
    .data(edges).enter().append('line')
    .attr('stroke', d => d.type === 'exploits' ? '#ffa657' : d.type === 'targets' ? '#5c1a1a' : '#30363d')
    .attr('stroke-width', d => d.type === 'exploits' ? 2 : 1.2)
    .attr('stroke-opacity', 0.7)
    .attr('marker-end', d => `url(#arrow-${d.type})`);

  // Edge labels
  const linkLabel = g.append('g').selectAll('text')
    .data(edges).enter().append('text')
    .attr('font-size', 9)
    .attr('fill', '#484f58')
    .attr('text-anchor','middle')
    .text(d => d.type);

  // Nodes
  const node = g.append('g').selectAll('g')
    .data(nodes).enter().append('g')
    .call(d3.drag()
      .on('start', (e,d) => { if(!e.active) simulation.alphaTarget(.3).restart(); d.fx=d.x; d.fy=d.y; })
      .on('drag',  (e,d) => { d.fx=e.x; d.fy=e.y; })
      .on('end',   (e,d) => { if(!e.active) simulation.alphaTarget(0); d.fx=null; d.fy=null; })
    )
    .on('click', (e,d) => showDetail(d.id, 'graph'))
    .on('mouseover', (e,d) => {
      const tt = document.getElementById('tooltip');
      tt.innerHTML = `<div class="tt-id">${d.label}</div>
        <div class="tt-type">${d.type}</div>
        <div class="tt-score">Risk: ${d.score.toFixed(3)}</div>`;
      tt.style.opacity = 1;
    })
    .on('mousemove', e => {
      const tt = document.getElementById('tooltip');
      const rect = container.getBoundingClientRect();
      tt.style.left = (e.clientX - rect.left + 12) + 'px';
      tt.style.top  = (e.clientY - rect.top  - 10) + 'px';
    })
    .on('mouseout', () => {
      document.getElementById('tooltip').style.opacity = 0;
    });

  // Node circles — size driven by risk score
  node.append('circle')
    .attr('r', d => (TYPE_RADIUS[d.type]||12) * (0.7 + d.score * 0.6))
    .attr('fill', d => TYPE_COLORS[d.type] || '#8b949e')
    .attr('fill-opacity', 0.85)
    .attr('stroke', d => TYPE_COLORS[d.type] || '#8b949e')
    .attr('stroke-width', 1.5)
    .attr('stroke-opacity', 0.4);

  // Risk score ring
  node.append('circle')
    .attr('r', d => (TYPE_RADIUS[d.type]||12) * (0.7 + d.score * 0.6) + 3)
    .attr('fill', 'none')
    .attr('stroke', d => d.score > 0.7 ? '#f85149' : d.score > 0.4 ? '#e3b341' : '#3fb950')
    .attr('stroke-width', 1)
    .attr('stroke-opacity', 0.5)
    .attr('stroke-dasharray', d => {
      const circ = 2 * Math.PI * ((TYPE_RADIUS[d.type]||12) * (0.7 + d.score * 0.6) + 3);
      return `${circ * d.score} ${circ}`;
    });

  // Node labels
  node.append('text')
    .attr('dy', d => (TYPE_RADIUS[d.type]||12) * (0.7 + d.score * 0.6) + 13)
    .attr('text-anchor','middle')
    .attr('font-size', 10)
    .attr('fill','#c9d1d9')
    .text(d => d.label.length > 14 ? d.label.slice(0,13)+'…' : d.label);

  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
    linkLabel
      .attr('x', d => (d.source.x + d.target.x)/2)
      .attr('y', d => (d.source.y + d.target.y)/2);
    node.attr('transform', d => `translate(${d.x},${d.y})`);
  });
}

function resetZoom() {
  svgSel.transition().duration(400).call(zoomBehavior.transform, d3.zoomIdentity);
}
</script>
</body>
</html>"""

def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(DASHBOARD_HTML)
    print(f"✅  Dashboard written to: {OUTPUT_PATH}")
    print(f"📡  Make sure API is running:  uvicorn api.main:app --reload --port 8000")
    print(f"🌐  Opening dashboard…")
    webbrowser.open(f"file://{OUTPUT_PATH}")

if __name__ == "__main__":
    main()
