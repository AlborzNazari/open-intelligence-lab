"""
demo.py — Open Intelligence Lab
========================================================
Full intelligence pipeline:
  1. Loads all 5 real datasets
  2. Builds the threat knowledge graph
  3. Computes risk scores + explanations
  4. Opens a gorgeous interactive dashboard in browser
========================================================
"""

import json, os, math, webbrowser, tempfile

BASE = os.path.dirname(os.path.abspath(__file__))

def load(filename):
    with open(os.path.join(BASE, "datasets", filename), encoding="utf-8") as f:
        return json.load(f)

def risk_band(score):
    if score >= 0.90: return "CRITICAL", "#ff2d55"
    if score >= 0.70: return "HIGH",     "#ff6b35"
    if score >= 0.40: return "MEDIUM",   "#f5a623"
    return "LOW", "#39ff8f"

def explain(entity, relations, all_entities):
    eid   = entity["entity_id"]
    score = entity.get("risk_score", 0.5)
    conf  = entity.get("confidence", entity.get("confidence_level", 0.7))
    band, _ = risk_band(score)
    connected = [r for r in relations if r["source_id"] == eid or r["target_id"] == eid]
    lines = [
        f"Risk score {score:.2f} · confidence {conf:.2f} · band {band}",
        f"Appears in {len(connected)} documented relation(s) in the knowledge graph",
    ]
    targets = [r["target_id"] for r in connected if r["source_id"] == eid]
    sources = [r["source_id"] for r in connected if r["target_id"] == eid]
    if targets:
        names = [next((e["name"] for e in all_entities if e["entity_id"] == t), t) for t in targets[:3]]
        lines.append(f"Outbound links: {', '.join(names)}")
    if sources:
        names = [next((e["name"] for e in all_entities if e["entity_id"] == s), s) for s in sources[:3]]
        lines.append(f"Referenced by: {', '.join(names)}")
    if entity.get("motivation"):
        lines.append(f"Motivation: {', '.join(entity['motivation'])}")
    if entity.get("target_sectors"):
        lines.append(f"Target sectors: {', '.join(entity['target_sectors'][:3])}")
    if entity.get("tags"):
        lines.append(f"Tags: {', '.join(entity['tags'][:5])}")
    return lines

ENTITY_COLOR = {
    "threat_actor":   "#ff2d55",
    "malware":        "#c084fc",
    "infrastructure": "#f5a623",
    "vulnerability":  "#ff6b35",
    "target_sector":  "#4a9eff",
    "attack_pattern": "#fbbf24",
}
DEFAULT_COLOR = "#4a6278"

def ecolor(t): return ENTITY_COLOR.get(t, DEFAULT_COLOR)

def spring_layout(node_ids, edge_pairs, iterations=140, k=2.8, seed=42):
    import random
    random.seed(seed)
    n = len(node_ids)
    pos = {nid: [random.uniform(-2, 2), random.uniform(-2, 2)] for nid in node_ids}
    id_set = set(node_ids)
    nl = list(node_ids)
    for it in range(iterations):
        disp = {nid: [0.0, 0.0] for nid in node_ids}
        for i in range(n):
            for j in range(i + 1, n):
                u, v = nl[i], nl[j]
                dx = pos[u][0] - pos[v][0]
                dy = pos[u][1] - pos[v][1]
                dist = max(math.sqrt(dx * dx + dy * dy), 0.01)
                f = k * k / dist
                disp[u][0] += dx / dist * f; disp[u][1] += dy / dist * f
                disp[v][0] -= dx / dist * f; disp[v][1] -= dy / dist * f
        for s, t in edge_pairs:
            if s in pos and t in pos:
                dx = pos[s][0] - pos[t][0]
                dy = pos[s][1] - pos[t][1]
                dist = max(math.sqrt(dx * dx + dy * dy), 0.01)
                f = dist * dist / k
                disp[s][0] -= dx / dist * f; disp[s][1] -= dy / dist * f
                disp[t][0] += dx / dist * f; disp[t][1] += dy / dist * f
        temp = max(0.02, 0.15 * (1 - it / iterations))
        for nid in node_ids:
            mag = max(math.sqrt(disp[nid][0] ** 2 + disp[nid][1] ** 2), 0.01)
            pos[nid][0] += disp[nid][0] / mag * min(mag, temp)
            pos[nid][1] += disp[nid][1] / mag * min(mag, temp)
    return pos


def main():
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║   OPEN INTELLIGENCE LAB  ·  Threat Knowledge Graph  v0.1 ║")
    print("║   Ethical OSINT · Graph-Based · MITRE ATT&CK Aligned      ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    print("[1/4] Loading datasets...")
    entities  = load("threat_entities.json")
    patterns  = load("attack_patterns.json")
    relations = load("relations.json")
    campaigns = load("campaigns.json")
    mitre     = load("mitre_mapping.json")

    all_ents = list(entities)
    for i, p in enumerate(patterns):
        all_ents.append({
            **p,
            "entity_id":   p.get("pattern_id", p.get("id", f"AP-{i}")),
            "entity_type": "attack_pattern",
            "risk_score":  p.get("severity_score", p.get("risk_score", 0.6)),
            "confidence":  p.get("confidence", 0.7),
        })

    print(f"      ✓ {len(entities)} entities  ·  {len(patterns)} attack patterns  ·  {len(relations)} relations  ·  {len(campaigns)} campaigns")

    print("[2/4] Computing risk & explanations...")
    for e in all_ents:
        e["_band"], e["_bcolor"] = risk_band(e.get("risk_score", 0.5))
        e["_explain"] = explain(e, relations, all_ents)

    print(f"\n  {'ENTITY':<28} {'TYPE':<18} {'RISK':>6}  BAND")
    print(f"  {'─' * 64}")
    for e in sorted(all_ents, key=lambda x: -x.get("risk_score", 0)):
        s = e.get("risk_score", 0)
        print(f"  {e['name']:<28} {e['entity_type']:<18} {s:>6.2f}  {e['_band']}")

    print("\n[3/4] Computing graph layout...")
    nids = [e["entity_id"] for e in all_ents]
    nset = set(nids)
    epairs = [(r["source_id"], r["target_id"]) for r in relations if r["source_id"] in nset and r["target_id"] in nset]
    pos = spring_layout(nids, epairs)

    print("[4/4] Rendering dashboard...")

    nodes_js, edges_js, camps_js = [], [], []

    for e in all_ents:
        nid   = e["entity_id"]
        x, y  = pos.get(nid, [0, 0])
        score = e.get("risk_score", 0.5)
        color = ecolor(e["entity_type"])
        band, bcolor = e["_band"], e["_bcolor"]
        expl  = "<br>".join(e["_explain"])
        tags  = ", ".join(e.get("tags", [])[:5])
        nodes_js.append({
            "id":     nid,
            "x":      round(x, 4),
            "y":      round(y, 4),
            "name":   e["name"],
            "type":   e["entity_type"].replace("_", " ").title(),
            "score":  round(score, 3),
            "band":   band,
            "bcolor": bcolor,
            "color":  color,
            "tags":   tags,
            "expl":   expl,
            "size":   round(14 + score * 30),
        })

    for r in relations:
        if r["source_id"] in nset and r["target_id"] in nset:
            src = next((e for e in all_ents if e["entity_id"] == r["source_id"]), None)
            edges_js.append({
                "s":    r["source_id"],
                "t":    r["target_id"],
                "rel":  r["relation_type"],
                "conf": round(r.get("confidence", 0.7), 2),
                "color": ecolor(src["entity_type"]) if src else DEFAULT_COLOR,
            })

    for c in campaigns:
        camps_js.append({
            "name":      c.get("campaign_name", c.get("name", "Unknown")),
            "adversary": c.get("adversary", c.get("attributed_to", "Unknown")),
            "objective": c.get("objective", c.get("motivation", "")),
            "year":      str(c.get("year", c.get("date", ""))),
        })

    NJ = json.dumps(nodes_js)
    EJ = json.dumps(edges_js)
    CJ = json.dumps(camps_js)

    n_critical = sum(1 for e in all_ents if e.get("risk_score", 0) >= 0.9)

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Open Intelligence Lab — Threat Knowledge Graph</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --void:#020408;--surface:#080d14;--panel:#0c1420;--border:#1a2535;
  --accent:#00d4ff;--text:#e8f4fd;--muted:#4a6278;--subtle:#111d2b;
  --critical:#ff2d55;--high:#ff6b35;--medium:#f5a623;--low:#39ff8f;
}
body{background:var(--void);color:var(--text);font-family:'JetBrains Mono',monospace;height:100vh;overflow:hidden;display:flex;flex-direction:column}
body::before{content:'';position:fixed;inset:0;
  background-image:linear-gradient(rgba(0,212,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(0,212,255,.025) 1px,transparent 1px);
  background-size:44px 44px;pointer-events:none;z-index:0}

header{height:56px;background:rgba(8,13,20,.97);border-bottom:1px solid var(--border);
  display:flex;align-items:center;justify-content:space-between;padding:0 20px;
  flex-shrink:0;position:relative;z-index:10}
.logo{display:flex;align-items:center;gap:10px}
.logo-hex{width:32px;height:32px}
.logo-title{font-family:'Syne',sans-serif;font-weight:800;font-size:15px;letter-spacing:.1em}
.logo-title span{color:var(--accent)}
.logo-sub{font-size:8px;color:var(--muted);letter-spacing:.18em;text-transform:uppercase;display:block;margin-top:1px}
.hstats{display:flex;gap:7px}
.hstat{background:var(--subtle);border:1px solid var(--border);padding:4px 11px;border-radius:3px;font-size:10px;color:var(--muted)}
.hstat b{color:var(--text)}
.live{display:flex;align-items:center;gap:6px;font-size:10px;color:var(--muted)}
.dot{width:6px;height:6px;border-radius:50%;background:var(--low);animation:blink 2s infinite}
@keyframes blink{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(57,255,143,.5)}50%{opacity:.6;box-shadow:0 0 0 5px rgba(57,255,143,0)}}

.workspace{display:flex;flex:1;overflow:hidden;position:relative;z-index:1}

.left-panel{width:236px;background:var(--panel);border-right:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden;flex-shrink:0}
.panel-head{padding:11px 13px 8px;border-bottom:1px solid var(--border);flex-shrink:0}
.panel-label{font-size:8px;letter-spacing:.25em;text-transform:uppercase;color:var(--muted)}
.elist{overflow-y:auto;flex:1;padding:6px}
.eitem{display:flex;align-items:center;gap:7px;padding:6px 8px;border-radius:5px;
  cursor:pointer;border:1px solid transparent;margin-bottom:3px;transition:all .15s}
.eitem:hover{background:var(--subtle);border-color:var(--border)}
.eitem.sel{background:rgba(0,212,255,.07);border-color:rgba(0,212,255,.3)}
.edot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.einfo{flex:1;min-width:0}
.ename{font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--text)}
.etype{font-size:8px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;margin-top:1px}
.escore{font-size:9px;padding:1px 5px;border-radius:2px;flex-shrink:0;font-weight:500}

.canvas-wrap{flex:1;position:relative;overflow:hidden}
canvas{position:absolute;inset:0;cursor:grab;display:block}
canvas:active{cursor:grabbing}
.toolbar{position:absolute;top:12px;left:12px;display:flex;gap:5px;z-index:5}
.tbtn{width:30px;height:30px;background:rgba(8,13,20,.92);border:1px solid var(--border);
  color:var(--muted);border-radius:5px;cursor:pointer;font-size:14px;
  display:flex;align-items:center;justify-content:center;transition:all .18s}
.tbtn:hover{border-color:var(--accent);color:var(--accent)}
.hints{position:absolute;bottom:12px;left:12px;display:flex;gap:8px;z-index:5}
.chip{background:rgba(8,13,20,.88);border:1px solid var(--border);padding:4px 9px;border-radius:3px;font-size:9px;color:var(--muted)}
.chip b{color:var(--accent)}
.tooltip{position:absolute;background:rgba(8,13,20,.97);border:1px solid var(--border);
  border-radius:6px;padding:10px 13px;pointer-events:none;z-index:20;min-width:160px;
  display:none;box-shadow:0 6px 24px rgba(0,0,0,.6)}
.tt-name{font-family:'Syne',sans-serif;font-size:12px;font-weight:700;margin-bottom:5px}
.tt-row{display:flex;justify-content:space-between;font-size:9px;color:var(--muted);padding:1px 0}
.tt-row span:last-child{color:var(--text)}

.right-panel{width:258px;background:var(--panel);border-left:1px solid var(--border);
  display:flex;flex-direction:column;overflow:hidden;flex-shrink:0}
.rsec{padding:13px;border-bottom:1px solid var(--border);flex-shrink:0}
.rsec-title{font-size:8px;letter-spacing:.25em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
.gauge-row{display:flex;align-items:center;gap:11px;margin-bottom:10px}
.gauge-svg{width:70px;height:70px;flex-shrink:0}
.gauge-info{flex:1}
.g-name{font-family:'Syne',sans-serif;font-size:12px;font-weight:700;line-height:1.2;margin-bottom:3px}
.g-type{font-size:8px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em}
.metrics{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:2px}
.metric{background:var(--subtle);border:1px solid var(--border);border-radius:4px;padding:7px 9px}
.mv{font-family:'Syne',sans-serif;font-size:17px;font-weight:700;line-height:1}
.ml{font-size:8px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;margin-top:2px}
.expl-list{display:flex;flex-direction:column;gap:3px}
.expl-item{font-size:9px;color:var(--muted);line-height:1.5;padding:3px 0;
  border-bottom:1px solid rgba(26,37,53,.4);display:flex;gap:5px}
.expl-item::before{content:'›';color:var(--accent);flex-shrink:0;font-size:12px;line-height:1.2}
.camp-wrap{flex-shrink:0;max-height:170px;overflow-y:auto}
.camp-item{padding:7px 13px;border-bottom:1px solid rgba(26,37,53,.3)}
.camp-name{font-size:10px;color:var(--text);margin-bottom:2px}
.camp-meta{font-size:8px;color:var(--muted)}
.legend{padding:8px 13px;border-top:1px solid var(--border);display:flex;flex-wrap:wrap;gap:5px;flex-shrink:0}
.li{display:flex;align-items:center;gap:4px;font-size:8px;color:var(--muted)}
.ld{width:7px;height:7px;border-radius:50%}
::-webkit-scrollbar{width:3px}
::-webkit-scrollbar-track{background:var(--panel)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
</style>
</head>
<body>
<header>
  <div class="logo">
    <svg class="logo-hex" viewBox="0 0 32 32" fill="none">
      <polygon points="16,2 28,9 28,23 16,30 4,23 4,9" stroke="#00d4ff" stroke-width="1.2" fill="rgba(0,212,255,.06)"/>
      <circle cx="16" cy="16" r="4" fill="#00d4ff" opacity=".9"/>
      <circle cx="16" cy="5"  r="1.8" fill="#ff2d55"/>
      <circle cx="26" cy="11" r="1.8" fill="#f5a623"/>
      <circle cx="26" cy="21" r="1.8" fill="#39ff8f"/>
      <circle cx="16" cy="27" r="1.8" fill="#00d4ff"/>
      <circle cx="6"  cy="21" r="1.8" fill="#c084fc"/>
      <circle cx="6"  cy="11" r="1.8" fill="#ff6b35"/>
    </svg>
    <div>
      <div class="logo-title">OPEN <span>INTELLIGENCE</span> LAB</div>
      <span class="logo-sub">Graph-Based Threat Intelligence · Ethical OSINT · MITRE ATT&CK Aligned</span>
    </div>
  </div>
  <div class="hstats">
    <div class="hstat">Entities <b id="h-n">0</b></div>
    <div class="hstat">Relations <b id="h-e">0</b></div>
    <div class="hstat">Campaigns <b id="h-c">0</b></div>
    <div class="hstat">Critical <b id="h-k" style="color:#ff2d55">0</b></div>
  </div>
  <div class="live"><div class="dot"></div>GRAPH ENGINE ACTIVE</div>
</header>

<div class="workspace">
  <div class="left-panel">
    <div class="panel-head"><div class="panel-label">Entity Registry — sorted by risk</div></div>
    <div class="elist" id="elist"></div>
  </div>

  <div class="canvas-wrap">
    <div class="toolbar">
      <div class="tbtn" onclick="zoomIn()">+</div>
      <div class="tbtn" onclick="zoomOut()">−</div>
      <div class="tbtn" onclick="resetView()">⊙</div>
      <div class="tbtn" onclick="toggleLabels()" id="lbtn">⊞</div>
    </div>
    <canvas id="gc"></canvas>
    <div class="hints">
      <div class="chip">Scroll <b>zoom</b></div>
      <div class="chip">Drag <b>pan</b></div>
      <div class="chip">Click <b>inspect</b></div>
    </div>
    <div class="tooltip" id="tooltip">
      <div class="tt-name" id="tt-name"></div>
      <div class="tt-row"><span>Type</span><span id="tt-type"></span></div>
      <div class="tt-row"><span>Risk</span><span id="tt-risk"></span></div>
      <div class="tt-row"><span>Connections</span><span id="tt-conn"></span></div>
    </div>
  </div>

  <div class="right-panel">
    <div class="rsec">
      <div class="rsec-title">Entity Intelligence</div>
      <div class="gauge-row">
        <svg class="gauge-svg" viewBox="0 0 70 70">
          <circle cx="35" cy="35" r="27" fill="none" stroke="#1a2535" stroke-width="5.5"/>
          <circle id="garc" cx="35" cy="35" r="27" fill="none" stroke="#ff2d55" stroke-width="5.5"
            stroke-dasharray="170" stroke-dashoffset="17" stroke-linecap="round"
            transform="rotate(-90 35 35)" style="transition:all .4s"/>
          <text id="gscore" x="35" y="32" text-anchor="middle" fill="#e8f4fd"
            font-family="Syne,sans-serif" font-size="13" font-weight="800">—</text>
          <text id="gband" x="35" y="43" text-anchor="middle" fill="#4a6278"
            font-family="JetBrains Mono,monospace" font-size="5.5" letter-spacing="1.5">SELECT NODE</text>
        </svg>
        <div class="gauge-info">
          <div class="g-name" id="dname">—</div>
          <div class="g-type" id="dtype">click any node</div>
        </div>
      </div>
      <div class="metrics">
        <div class="metric"><div class="mv" id="m1" style="color:#ff2d55">—</div><div class="ml">Risk Score</div></div>
        <div class="metric"><div class="mv" id="m2" style="color:#f5a623">—</div><div class="ml">Confidence</div></div>
        <div class="metric"><div class="mv" id="m3" style="color:#00d4ff">—</div><div class="ml">Connections</div></div>
        <div class="metric"><div class="mv" id="m4" style="color:#39ff8f">—</div><div class="ml">Risk Band</div></div>
      </div>
    </div>
    <div class="rsec" style="flex:1;overflow-y:auto;min-height:0">
      <div class="rsec-title">Explainability Rationale</div>
      <div class="expl-list" id="expl"></div>
    </div>
    <div style="flex-shrink:0;border-top:1px solid var(--border)">
      <div style="padding:8px 13px 4px;font-size:8px;letter-spacing:.25em;text-transform:uppercase;color:var(--muted)">Active Campaigns</div>
      <div class="camp-wrap" id="camps"></div>
    </div>
    <div class="legend" id="leg"></div>
  </div>
</div>

<script>
const NODES=NODE_DATA_PLACEHOLDER;
const EDGES=EDGE_DATA_PLACEHOLDER;
const CAMPS=CAMP_DATA_PLACEHOLDER;

document.getElementById('h-n').textContent=NODES.length;
document.getElementById('h-e').textContent=EDGES.length;
document.getElementById('h-c').textContent=CAMPS.length;
document.getElementById('h-k').textContent=NODES.filter(n=>n.score>=0.9).length;

// entity list
const elist=document.getElementById('elist');
[...NODES].sort((a,b)=>b.score-a.score).forEach(n=>{
  const d=document.createElement('div');
  d.className='eitem';d.dataset.id=n.id;
  d.innerHTML=`<div class="edot" style="background:${n.color};box-shadow:0 0 5px ${n.color}88"></div>
    <div class="einfo"><div class="ename">${n.name}</div><div class="etype">${n.type}</div></div>
    <div class="escore" style="background:${n.bcolor}22;color:${n.bcolor};border:1px solid ${n.bcolor}44">${n.score.toFixed(2)}</div>`;
  d.onclick=()=>selectNode(n.id);
  elist.appendChild(d);
});

// campaigns
const campsEl=document.getElementById('camps');
CAMPS.forEach(c=>{
  const d=document.createElement('div');d.className='camp-item';
  d.innerHTML=`<div class="camp-name">${c.name}</div><div class="camp-meta">${c.adversary}${c.year?' · '+c.year:''} · ${c.objective||''}</div>`;
  campsEl.appendChild(d);
});

// legend
const LCOLS={'Threat Actor':'#ff2d55','Malware':'#c084fc','Infrastructure':'#f5a623','Vulnerability':'#ff6b35','Target Sector':'#4a9eff','Attack Pattern':'#fbbf24'};
const legEl=document.getElementById('leg');
Object.entries(LCOLS).forEach(([k,c])=>{
  const d=document.createElement('div');d.className='li';
  d.innerHTML=`<div class="ld" style="background:${c}"></div>${k}`;
  legEl.appendChild(d);
});

// canvas
const canvas=document.getElementById('gc');
const ctx=canvas.getContext('2d');
let W,H,ox=0,oy=0,scale=1,showLabels=true,selId=null,hovId=null;
let drag=false,dx=0,dy=0;

const nmap={};
NODES.forEach(n=>nmap[n.id]=n);
const deg={};
NODES.forEach(n=>deg[n.id]=0);
EDGES.forEach(e=>{deg[e.s]=(deg[e.s]||0)+1;deg[e.t]=(deg[e.t]||0)+1;});

function resize(){
  const w=canvas.parentElement;
  W=canvas.width=w.clientWidth;
  H=canvas.height=w.clientHeight;
  draw();
}

function ws(wx,wy){return[wx*scale+ox+W/2,wy*scale+oy+H/2];}
function sw(sx,sy){return[(sx-W/2-ox)/scale,(sy-H/2-oy)/scale];}

function hexA(h,a){
  const c=h.replace('#','');
  return `rgba(${parseInt(c.slice(0,2),16)},${parseInt(c.slice(2,4),16)},${parseInt(c.slice(4,6),16)},${a})`;
}

function connectedTo(id){
  const s=new Set([id]);
  EDGES.forEach(e=>{if(e.s===id)s.add(e.t);if(e.t===id)s.add(e.s);});
  return s;
}

function draw(){
  ctx.clearRect(0,0,W,H);
  ctx.fillStyle='#080d14';ctx.fillRect(0,0,W,H);
  const conn=selId?connectedTo(selId):null;

  // edges
  EDGES.forEach(e=>{
    const s=nmap[e.s],t=nmap[e.t];if(!s||!t)return;
    const[sx,sy]=ws(s.x,s.y),[tx,ty]=ws(t.x,t.y);
    const active=!selId||(e.s===selId||e.t===selId);
    const alpha=active?(0.2+e.conf*0.55):0.04;
    ctx.beginPath();ctx.moveTo(sx,sy);ctx.lineTo(tx,ty);
    ctx.strokeStyle=hexA(e.color,alpha);
    ctx.lineWidth=active?(0.7+e.conf*1.6)*Math.min(scale,1.5):0.5;
    ctx.stroke();
    // arrow on active
    if(active&&selId){
      const ang=Math.atan2(ty-sy,tx-sx);
      const mx=(sx+tx)/2,my=(sy+ty)/2,al=9;
      ctx.beginPath();ctx.moveTo(mx,my);
      ctx.lineTo(mx-al*Math.cos(ang-Math.PI/7),my-al*Math.sin(ang-Math.PI/7));
      ctx.lineTo(mx-al*Math.cos(ang+Math.PI/7),my-al*Math.sin(ang+Math.PI/7));
      ctx.closePath();ctx.fillStyle=hexA(e.color,0.75);ctx.fill();
      if(showLabels){
        ctx.font=`${Math.max(8,9*Math.min(scale,1.2))}px JetBrains Mono`;
        ctx.fillStyle='#4a6278';ctx.textAlign='center';
        ctx.shadowColor='#020408';ctx.shadowBlur=4;
        ctx.fillText(e.rel,mx,my-7);ctx.shadowBlur=0;
      }
    }
  });

  // nodes
  NODES.forEach(n=>{
    const[sx,sy]=ws(n.x,n.y);
    const r=Math.max(7,n.size*scale*0.36);
    const isSel=n.id===selId,isHov=n.id===hovId;
    const dim=selId&&!conn.has(n.id);

    if(isSel||isHov){
      const g=ctx.createRadialGradient(sx,sy,r*.4,sx,sy,r*2.6);
      g.addColorStop(0,hexA(n.color,.22));g.addColorStop(1,hexA(n.color,0));
      ctx.beginPath();ctx.arc(sx,sy,r*2.6,0,Math.PI*2);
      ctx.fillStyle=g;ctx.fill();
    }
    ctx.beginPath();ctx.arc(sx,sy,r,0,Math.PI*2);
    ctx.fillStyle=hexA(n.color,dim?.03:.13);ctx.fill();
    ctx.strokeStyle=dim?hexA(n.bcolor,.12):n.bcolor;
    ctx.lineWidth=isSel?2.4:1.4;ctx.stroke();
    ctx.beginPath();ctx.arc(sx,sy,r*.3,0,Math.PI*2);
    ctx.fillStyle=dim?hexA(n.color,.15):n.color;ctx.fill();

    if(showLabels&&!dim){
      const fs=Math.max(8,Math.min(11,9.5*Math.min(scale*.6,1)));
      ctx.font=`${fs}px JetBrains Mono`;ctx.textAlign='center';
      ctx.shadowColor='#020408';ctx.shadowBlur=5;
      ctx.fillStyle=isSel?'#e8f4fd':'#9bb8cc';
      ctx.fillText(n.name,sx,sy+r+fs+1);
      if(isSel||isHov){
        ctx.font=`bold ${Math.max(7,fs-1)}px JetBrains Mono`;
        ctx.fillStyle=n.bcolor;
        ctx.fillText(n.score.toFixed(2),sx,sy+r+fs*2+2);
      }
      ctx.shadowBlur=0;
    }
  });
}

function nodeAt(sx,sy){
  for(const n of NODES){
    const[nx,ny]=ws(n.x,n.y);
    const r=Math.max(9,n.size*scale*0.36);
    if((sx-nx)**2+(sy-ny)**2<r*r)return n;
  }return null;
}

const tt=document.getElementById('tooltip');
canvas.addEventListener('mousedown',e=>{
  const n=nodeAt(e.offsetX,e.offsetY);
  if(n){selectNode(n.id);return;}
  drag=true;dx=e.offsetX;dy=e.offsetY;
});
canvas.addEventListener('mousemove',e=>{
  if(drag){ox+=e.offsetX-dx;oy+=e.offsetY-dy;dx=e.offsetX;dy=e.offsetY;draw();return;}
  const n=nodeAt(e.offsetX,e.offsetY);
  const nh=n?n.id:null;
  if(nh!==hovId){hovId=nh;canvas.style.cursor=n?'pointer':'grab';draw();}
  if(n){
    tt.style.display='block';
    tt.style.left=(e.offsetX+14)+'px';tt.style.top=(e.offsetY-20)+'px';
    document.getElementById('tt-name').textContent=n.name;
    document.getElementById('tt-name').style.color=n.color;
    document.getElementById('tt-type').textContent=n.type;
    document.getElementById('tt-risk').textContent=n.score.toFixed(2)+' ('+n.band+')';
    document.getElementById('tt-risk').style.color=n.bcolor;
    document.getElementById('tt-conn').textContent=deg[n.id]||0;
  } else {tt.style.display='none';}
});
canvas.addEventListener('mouseup',()=>drag=false);
canvas.addEventListener('mouseleave',()=>{drag=false;tt.style.display='none';});
canvas.addEventListener('wheel',e=>{
  e.preventDefault();
  const f=e.deltaY<0?1.13:.88;
  const wx=(e.offsetX-W/2-ox)/scale,wy=(e.offsetY-H/2-oy)/scale;
  scale=Math.min(8,Math.max(.15,scale*f));
  ox=e.offsetX-W/2-wx*scale;oy=e.offsetY-H/2-wy*scale;draw();
},{passive:false});

function selectNode(id){
  selId=id;
  document.querySelectorAll('.eitem').forEach(el=>el.classList.toggle('sel',el.dataset.id===id));
  const n=nmap[id];if(!n)return;
  const circ=2*Math.PI*27;
  const off=circ*(1-n.score)+circ*.05;
  const arc=document.getElementById('garc');
  arc.style.stroke=n.bcolor;
  arc.style.filter=`drop-shadow(0 0 5px ${n.bcolor})`;
  arc.setAttribute('stroke-dashoffset',off.toFixed(1));
  document.getElementById('gscore').textContent=n.score.toFixed(2);
  document.getElementById('gscore').setAttribute('fill',n.bcolor);
  document.getElementById('gband').textContent=n.band;
  document.getElementById('dname').textContent=n.name;
  document.getElementById('dtype').textContent=n.type;
  document.getElementById('m1').textContent=n.score.toFixed(2);
  document.getElementById('m1').style.color=n.bcolor;
  document.getElementById('m2').textContent='—';
  document.getElementById('m3').textContent=deg[id]||0;
  document.getElementById('m4').textContent=n.band;
  document.getElementById('m4').style.color=n.bcolor;
  const ex=document.getElementById('expl');ex.innerHTML='';
  n.expl.split('<br>').filter(l=>l.trim()).forEach(line=>{
    const d=document.createElement('div');d.className='expl-item';d.textContent=line;ex.appendChild(d);
  });
  if(n.tags){const d=document.createElement('div');d.className='expl-item';d.textContent='Tags: '+n.tags;ex.appendChild(d);}
  draw();
}

function zoomIn(){scale=Math.min(8,scale*1.25);draw();}
function zoomOut(){scale=Math.max(.15,scale*.8);draw();}
function resetView(){
  let x0=Infinity,x1=-Infinity,y0=Infinity,y1=-Infinity;
  NODES.forEach(n=>{x0=Math.min(x0,n.x);x1=Math.max(x1,n.x);y0=Math.min(y0,n.y);y1=Math.max(y1,n.y);});
  const pw=x1-x0||1,ph=y1-y0||1;
  scale=Math.min(W/(pw*1.35),H/(ph*1.35))*.82;
  ox=-(x0+x1)/2*scale;oy=-(y0+y1)/2*scale;draw();
}
function toggleLabels(){showLabels=!showLabels;draw();}
window.addEventListener('resize',resize);
resize();setTimeout(resetView,60);
</script>
</body>
</html>"""

    html = (html
        .replace("NODE_DATA_PLACEHOLDER", NJ)
        .replace("EDGE_DATA_PLACEHOLDER", EJ)
        .replace("CAMP_DATA_PLACEHOLDER", CJ))

    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, prefix="oi_lab_")
    tmp.write(html.encode("utf-8"))
    tmp.close()
    webbrowser.open(f"file:///{tmp.name.replace(os.sep, '/')}")
    print(f"\n[✓] Dashboard opened in browser")
    print(f"    Scroll = zoom  ·  Drag = pan  ·  Click node = full intelligence report\n")


if __name__ == "__main__":
    main()
