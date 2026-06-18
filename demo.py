"""
demo.py - v0.2.0
Run AFTER: uvicorn api.main:app --reload --port 8000
"""
import os, webbrowser

API = "http://localhost:8000"
HERE = os.path.dirname(os.path.abspath(__file__))
HTML_OUT = os.path.join(HERE, "visualization", "dashboard.html")

def main():
    os.makedirs(os.path.dirname(HTML_OUT), exist_ok=True)
    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(get_html())
    print("Dashboard written to:", HTML_OUT)
    print("API must be running at:", API)
    webbrowser.open("file:///" + HTML_OUT.replace("\\", "/"))

def get_html():
    return (
        '<!DOCTYPE html><html lang="en"><head>'
        '<meta charset="UTF-8"/>'
        '<meta name="viewport" content="width=device-width,initial-scale=1"/>'
        '<title>Open Intelligence Lab</title>'
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>'
        '<style>' + CSS + '</style>'
        '</head><body>'
        '<h1>Open Intelligence Lab</h1>'
        '<p class="sub">v0.2.0 &mdash; Live data from <code>' + API + '</code></p>'
        + BODY +
        '<script>const API="' + API + '";' + JS + '</script>'
        '</body></html>'
    )

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',sans-serif;background:#0d1117;color:#c9d1d9;padding:1.5rem}
h1{color:#58a6ff;font-size:1.5rem;margin-bottom:.2rem}
.sub{color:#8b949e;font-size:.85rem;margin-bottom:1.5rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:1rem;margin-bottom:1.5rem}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1rem}
.lbl{font-size:.7rem;color:#8b949e;text-transform:uppercase;letter-spacing:.05em}
.val{font-size:1.7rem;font-weight:700;color:#58a6ff;margin-top:.2rem}
.tabs{display:flex;gap:.5rem;margin-bottom:1.5rem;border-bottom:1px solid #30363d;padding-bottom:.5rem}
.tab{padding:.4rem 1rem;border-radius:6px 6px 0 0;cursor:pointer;font-size:.88rem;color:#8b949e;border:1px solid transparent;border-bottom:none}
.tab.active{color:#58a6ff;border-color:#30363d;background:#161b22}
.panel{display:none}.panel.active{display:block}
.row{display:flex;gap:.6rem;flex-wrap:wrap;margin-bottom:1.2rem;align-items:flex-end}
.row label{font-size:.75rem;color:#8b949e;display:block;margin-bottom:.2rem}
input,select{background:#161b22;border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:.4rem .65rem;font-size:.87rem;outline:none}
input:focus,select:focus{border-color:#58a6ff}
button{background:#238636;color:#fff;border:none;border-radius:6px;padding:.45rem 1rem;font-size:.87rem;cursor:pointer}
button:hover{background:#2ea043}
table{width:100%;border-collapse:collapse;font-size:.84rem}
th{text-align:left;padding:.5rem .85rem;background:#161b22;border-bottom:1px solid #30363d;color:#8b949e;font-weight:600;text-transform:uppercase;font-size:.7rem;letter-spacing:.04em}
td{padding:.5rem .85rem;border-bottom:1px solid #21262d}
tr:hover td{background:#161b22}
.badge{display:inline-block;padding:.15rem .45rem;border-radius:999px;font-size:.75rem;font-weight:700}
.hi{background:#3d1a1a;color:#f85149}.md{background:#2d2208;color:#e3b341}.lo{background:#0f2a1a;color:#3fb950}
.status{font-size:.78rem;color:#8b949e;margin-bottom:.8rem}
.errt{color:#f85149}
.pages{display:flex;gap:.5rem;align-items:center;margin-top:.8rem;font-size:.82rem}
.pbtn{padding:.28rem .65rem;font-size:.79rem;background:#21262d}
.pbtn:disabled{opacity:.4;cursor:default}
.dpanel{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1.2rem;margin-top:1.2rem;display:none}
.dpanel h3{color:#58a6ff;margin-bottom:.6rem;font-size:1rem}
.dgrid{display:grid;grid-template-columns:1fr 1fr;gap:.5rem;margin-bottom:.8rem}
.dk{font-size:.7rem;color:#8b949e;text-transform:uppercase;margin-bottom:.1rem}
.dv{font-size:.93rem;color:#e6edf3}
ul.expl{list-style:none;padding:0}
ul.expl li{padding:.35rem 0;border-bottom:1px solid #21262d;font-size:.84rem;line-height:1.6;color:#c9d1d9}
ul.expl li:last-child{border:none}
ul.expl li::before{content:">> ";color:#58a6ff;font-weight:700}
#gc{background:#0d1117;border:1px solid #30363d;border-radius:8px;position:relative;overflow:hidden}
#gsvg{width:100%;height:640px}
.gctrl{display:flex;gap:.6rem;flex-wrap:wrap;margin-bottom:.8rem;align-items:flex-end}
.legend{display:flex;gap:.8rem;flex-wrap:wrap;margin-bottom:.8rem}
.li{display:flex;align-items:center;gap:.35rem;font-size:.76rem;color:#8b949e}
.ld{width:11px;height:11px;border-radius:50%}
.tip{position:absolute;background:#161b22;border:1px solid #58a6ff;border-radius:6px;padding:.6rem .9rem;font-size:.79rem;pointer-events:none;opacity:0;transition:opacity .15s;max-width:260px;z-index:100;line-height:1.5}
.tid{color:#58a6ff;font-weight:700;font-size:.88rem}
.ttype{color:#8b949e;font-size:.7rem;text-transform:uppercase;margin-top:.1rem}
.tscore{font-weight:700;margin-top:.25rem}
.ginfo{font-size:.76rem;color:#8b949e;margin-top:.5rem}
"""

BODY = """
<div class="grid">
  <div class="card"><div class="lbl">Nodes</div><div class="val" id="sn">-</div></div>
  <div class="card"><div class="lbl">Edges</div><div class="val" id="se">-</div></div>
  <div class="card"><div class="lbl">Avg Risk</div><div class="val" id="sa">-</div></div>
  <div class="card"><div class="lbl">Max Risk</div><div class="val" id="sm">-</div></div>
  <div class="card"><div class="lbl">Min Risk</div><div class="val" id="si">-</div></div>
</div>

<div class="tabs">
  <div class="tab active" onclick="switchTab('entities')">Entities Table</div>
  <div class="tab" onclick="switchTab('graph')">Graph View</div>
</div>

<div id="panel-entities" class="panel active">
  <div class="row">
    <div><label>Search</label><input id="qq" type="text" placeholder="APT28, TA-001..." style="width:155px"/></div>
    <div><label>Min Risk</label><input id="qn" type="number" min="0" max="1" step="0.05" placeholder="0.0" style="width:78px"/></div>
    <div><label>Max Risk</label><input id="qx" type="number" min="0" max="1" step="0.05" placeholder="1.0" style="width:78px"/></div>
    <div><label>Type</label>
      <select id="qt">
        <option value="">All types</option>
        <option value="threat_actor">threat_actor</option>
        <option value="malware">malware</option>
        <option value="vulnerability">vulnerability</option>
        <option value="infrastructure">infrastructure</option>
        <option value="target_sector">target_sector</option>
        <option value="attack_pattern">attack_pattern</option>
      </select>
    </div>
    <div style="align-self:flex-end"><button onclick="loadEntities(0)">Search</button></div>
  </div>
  <p class="status" id="st">Loading...</p>
  <table>
    <thead><tr><th>Entity ID</th><th>Label</th><th>Type</th><th>Risk Score</th><th></th></tr></thead>
    <tbody id="tb"></tbody>
  </table>
  <div class="pages">
    <button class="pbtn" id="pp" onclick="changePage(-1)" disabled>&lt; Prev</button>
    <span id="pi">-</span>
    <button class="pbtn" id="pn" onclick="changePage(1)">Next &gt;</button>
  </div>
  <div class="dpanel" id="dp">
    <h3 id="dt">-</h3>
    <div class="dgrid">
      <div><div class="dk">Entity ID</div><div class="dv" id="did">-</div></div>
      <div><div class="dk">Type</div><div class="dv" id="dtp">-</div></div>
      <div><div class="dk">Risk Score</div><div class="dv" id="dsc">-</div></div>
    </div>
    <div class="dk">Explanation</div>
    <ul class="expl" id="dex"></ul>
  </div>
</div>

<div id="panel-graph" class="panel">
  <div class="gctrl">
    <div>
      <label style="font-size:.75rem;color:#8b949e;display:block;margin-bottom:.2rem">Filter by Type</label>
      <select id="gf" onchange="applyFilter()">
        <option value="">All entities</option>
        <option value="threat_actor">Threat Actors only</option>
        <option value="malware">Malware only</option>
        <option value="vulnerability">Vulnerabilities only</option>
        <option value="infrastructure">Infrastructure only</option>
        <option value="target_sector">Target Sectors only</option>
        <option value="attack_pattern">Attack Patterns only</option>
      </select>
    </div>
    <div style="align-self:flex-end">
      <button onclick="resetZoom()" style="background:#21262d;font-size:.78rem">Reset Zoom</button>
    </div>
    <div style="align-self:flex-end;font-size:.75rem;color:#8b949e">
      Drag nodes &middot; Scroll to zoom &middot; Click node to analyze
    </div>
  </div>
  <div class="legend">
    <div class="li"><div class="ld" style="background:#f85149"></div>Threat Actor</div>
    <div class="li"><div class="ld" style="background:#ff7b72"></div>Malware</div>
    <div class="li"><div class="ld" style="background:#ffa657"></div>Vulnerability</div>
    <div class="li"><div class="ld" style="background:#d2a8ff"></div>Infrastructure</div>
    <div class="li"><div class="ld" style="background:#79c0ff"></div>Target Sector</div>
    <div class="li"><div class="ld" style="background:#56d364"></div>Attack Pattern</div>
  </div>
  <div id="gc"><div class="tip" id="tip"></div><svg id="gsvg"></svg></div>
  <p class="ginfo" id="gi">Loading graph data from API...</p>
  <div class="dpanel" id="gdp" style="margin-top:1rem">
    <h3 id="gdt">-</h3>
    <div class="dgrid">
      <div><div class="dk">Entity ID</div><div class="dv" id="gdid">-</div></div>
      <div><div class="dk">Type</div><div class="dv" id="gdtp">-</div></div>
      <div><div class="dk">Risk Score</div><div class="dv" id="gdsc">-</div></div>
    </div>
    <div class="dk">Explanation</div>
    <ul class="expl" id="gdex"></ul>
  </div>
</div>
"""

JS = """
const LIMIT=20;
let offset=0,total=0,graphData=null,svgEl,sim,zoom;

const COLORS={threat_actor:"#f85149",malware:"#ff7b72",vulnerability:"#ffa657",infrastructure:"#d2a8ff",target_sector:"#79c0ff",attack_pattern:"#56d364"};
const RADIUS={threat_actor:18,malware:14,vulnerability:15,infrastructure:13,target_sector:16,attack_pattern:12};

function switchTab(name){
  document.querySelectorAll(".tab").forEach((t,i)=>t.classList.toggle("active",["entities","graph"][i]===name));
  document.querySelectorAll(".panel").forEach(p=>p.classList.remove("active"));
  document.getElementById("panel-"+name).classList.add("active");
  if(name==="graph"&&!graphData)loadGraph();
}

window.addEventListener("DOMContentLoaded",()=>{fetchSummary();loadEntities(0);});

async function fetchSummary(){
  try{
    const d=await fetch(API+"/intelligence/graph/summary").then(r=>r.json());
    document.getElementById("sn").textContent=d.node_count;
    document.getElementById("se").textContent=d.edge_count;
    document.getElementById("sa").textContent=d.avg_risk_score.toFixed(3);
    document.getElementById("sm").textContent=d.max_risk_score.toFixed(3);
    document.getElementById("si").textContent=d.min_risk_score.toFixed(3);
  }catch(e){document.getElementById("sn").textContent="ERR";}
}

async function loadEntities(off){
  offset=off;
  const p=new URLSearchParams({limit:LIMIT,offset:off});
  const q=document.getElementById("qq").value.trim();
  const mn=document.getElementById("qn").value.trim();
  const mx=document.getElementById("qx").value.trim();
  const tp=document.getElementById("qt").value;
  if(q)p.set("query",q);if(mn)p.set("min_risk",mn);if(mx)p.set("max_risk",mx);if(tp)p.set("entity_type",tp);
  document.getElementById("st").textContent="Fetching...";
  try{
    const d=await fetch(API+"/intelligence/entities?"+p).then(r=>r.json());
    total=d.total;renderTable(d.entities);
    document.getElementById("st").textContent="Showing "+(off+1)+"-"+Math.min(off+LIMIT,total)+" of "+total+" entities";
    updatePages();
  }catch(e){
    document.getElementById("st").innerHTML="<span class=\\"errt\\">API unreachable - is uvicorn running? ("+e.message+")</span>";
    document.getElementById("tb").innerHTML="";
  }
}

function renderTable(rows){
  const tb=document.getElementById("tb");
  if(!rows.length){tb.innerHTML="<tr><td colspan=\\"5\\" style=\\"color:#8b949e;padding:1rem\\">No results.</td></tr>";return;}
  tb.innerHTML=rows.map(e=>{
    const s=+e.risk_score||0;
    const c=s>=.7?"hi":s>=.4?"md":"lo";
    return "<tr><td><code style=\\"color:#58a6ff\\">"+e.entity_id+"</code></td>"
      +"<td>"+e.label+"</td>"
      +"<td><span style=\\"font-size:.73rem;color:#8b949e\\">"+(e.type||"-")+"</span></td>"
      +"<td><span class=\\"badge "+c+"\\">"+s.toFixed(3)+"</span></td>"
      +"<td><button style=\\"padding:.2rem .5rem;font-size:.75rem;background:#1f6feb\\" onclick=\\"analyze('"+e.entity_id+"','e')\\">Analyze</button></td></tr>";
  }).join("");
}

async function analyze(id,src){
  const pre=src==="g"?"gd":"d";
  const panel=document.getElementById(src==="g"?"gdp":"dp");
  panel.style.display="block";
  document.getElementById(pre+"t").textContent=id;
  document.getElementById(pre+"id").textContent=id;
  document.getElementById(pre+"sc").textContent="Loading...";
  document.getElementById(pre+"ex").innerHTML="";
  panel.scrollIntoView({behavior:"smooth"});
  try{
    const d=await fetch(API+"/intelligence/analyze/"+encodeURIComponent(id)).then(r=>r.json());
    document.getElementById(pre+"t").textContent=d.name||id;
    document.getElementById(pre+"id").textContent=d.entity_id;
    document.getElementById(pre+"tp").textContent=d.type||"-";
    document.getElementById(pre+"sc").innerHTML="<span style=\\"color:"+(d.risk_score>=.7?"#f85149":d.risk_score>=.4?"#e3b341":"#3fb950")+";font-weight:700\\">"+d.risk_score+"</span>";
    const lines=Array.isArray(d.explanation)?d.explanation:[String(d.explanation)];
    document.getElementById(pre+"ex").innerHTML=lines.map(l=>"<li>"+l+"</li>").join("");
  }catch(e){
    document.getElementById(pre+"ex").innerHTML="<li style=\\"color:#f85149\\">Error: "+e.message+"</li>";
  }
}

function changePage(dir){const n=offset+dir*LIMIT;if(n<0||n>=total)return;loadEntities(n);}
function updatePages(){
  document.getElementById("pp").disabled=offset===0;
  document.getElementById("pn").disabled=offset+LIMIT>=total;
  document.getElementById("pi").textContent="Page "+(Math.floor(offset/LIMIT)+1)+" / "+Math.ceil(total/LIMIT);
}

async function loadGraph(){
  document.getElementById("gi").textContent="Fetching graph data from API...";
  try{
    const [entRes,edgeRes]=await Promise.all([
      fetch(API+"/intelligence/entities?limit=200").then(r=>r.json()),
      fetch(API+"/intelligence/graph/edges").then(r=>r.json())
    ]);
    const nodes=entRes.entities.map(e=>({id:e.entity_id,label:e.label,type:e.type,score:e.risk_score}));
    const ids=new Set(nodes.map(n=>n.id));
    const edges=edgeRes.edges
      .filter(e=>ids.has(e.source)&&ids.has(e.target))
      .map(e=>({source:e.source,target:e.target,type:e.relation_type}));
    graphData={nodes,edges};
    renderGraph();
  }catch(e){document.getElementById("gi").textContent="Graph load error: "+e.message;}
}

function applyFilter(){if(graphData)renderGraph();}

function renderGraph(){
  if(!graphData)return;
  const tf=document.getElementById("gf").value;
  const nodes=tf?graphData.nodes.filter(n=>n.type===tf):graphData.nodes;
  const ids=new Set(nodes.map(n=>n.id));
  const edges=graphData.edges.filter(e=>ids.has(e.source)&&ids.has(e.target));
  document.getElementById("gi").textContent=nodes.length+" nodes | "+edges.length+" edges | node size = risk score | click any node to analyze";

  const cont=document.getElementById("gc");
  const W=cont.clientWidth||960,H=640;
  d3.select("#gsvg").selectAll("*").remove();
  svgEl=d3.select("#gsvg").attr("viewBox","0 0 "+W+" "+H);
  zoom=d3.zoom().scaleExtent([.15,5]).on("zoom",ev=>g.attr("transform",ev.transform));
  svgEl.call(zoom);
  const g=svgEl.append("g");

  svgEl.append("defs").selectAll("marker")
    .data(["uses","exploits","targets","uses_pattern","related_to"]).enter()
    .append("marker").attr("id",d=>"arr-"+d)
    .attr("viewBox","0 -5 10 10").attr("refX",26).attr("refY",0)
    .attr("markerWidth",7).attr("markerHeight",7).attr("orient","auto")
    .append("path").attr("d","M0,-5L10,0L0,5")
    .attr("fill",d=>d==="exploits"?"#ffa657":d==="targets"?"#f85149":"#484f58");

  const ns=nodes.map(n=>({...n}));
  const es=edges.map(e=>({...e}));

  sim=d3.forceSimulation(ns)
    .force("link",d3.forceLink(es).id(d=>d.id).distance(d=>{
      const types=[d.source.type,d.target.type];
      if(types.includes("threat_actor")&&types.includes("malware"))return 100;
      if(types.includes("threat_actor"))return 130;
      return 90;
    }).strength(.6))
    .force("charge",d3.forceManyBody().strength(-350))
    .force("center",d3.forceCenter(W/2,H/2))
    .force("collide",d3.forceCollide().radius(d=>(RADIUS[d.type]||12)*(0.6+d.score*.7)+12));

  const link=g.append("g").selectAll("line").data(es).enter().append("line")
    .attr("stroke",d=>d.type==="exploits"?"#ffa657":d.type==="targets"?"#8b1a1a":"#30363d")
    .attr("stroke-width",d=>d.type==="exploits"?2.5:d.type==="targets"?1.5:1)
    .attr("stroke-opacity",.85)
    .attr("marker-end",d=>"url(#arr-"+d.type+")");

  const linkLbl=g.append("g").selectAll("text").data(es).enter().append("text")
    .attr("font-size",8).attr("fill","#484f58").attr("text-anchor","middle")
    .text(d=>d.type==="uses_pattern"?"uses pattern":d.type);

  const node=g.append("g").selectAll("g").data(ns).enter().append("g")
    .style("cursor","pointer")
    .call(d3.drag()
      .on("start",(ev,d)=>{if(!ev.active)sim.alphaTarget(.3).restart();d.fx=d.x;d.fy=d.y;})
      .on("drag",(ev,d)=>{d.fx=ev.x;d.fy=ev.y;})
      .on("end",(ev,d)=>{if(!ev.active)sim.alphaTarget(0);d.fx=null;d.fy=null;}))
    .on("click",(ev,d)=>analyze(d.id,"g"))
    .on("mouseover",(ev,d)=>{
      const tt=document.getElementById("tip");
      const scoreColor=d.score>=.7?"#f85149":d.score>=.4?"#e3b341":"#3fb950";
      tt.innerHTML="<div class=\\"tid\\">"+d.label+"</div><div class=\\"ttype\\">"+d.type.replace(/_/g," ")+"</div><div class=\\"tscore\\" style=\\"color:"+scoreColor+"\\">Risk: "+d.score.toFixed(3)+"</div><div style=\\"font-size:.7rem;color:#8b949e;margin-top:.2rem\\">Click to analyze</div>";
      tt.style.opacity=1;
    })
    .on("mousemove",ev=>{
      const tt=document.getElementById("tip");
      const r=cont.getBoundingClientRect();
      tt.style.left=(ev.clientX-r.left+14)+"px";
      tt.style.top=(ev.clientY-r.top-10)+"px";
    })
    .on("mouseout",()=>{document.getElementById("tip").style.opacity=0;});

  const r=d=>Math.max(8,(RADIUS[d.type]||12)*(0.55+d.score*.75));

  node.append("circle").attr("r",r)
    .attr("fill",d=>COLORS[d.type]||"#8b949e").attr("fill-opacity",.88)
    .attr("stroke",d=>COLORS[d.type]||"#8b949e").attr("stroke-width",2).attr("stroke-opacity",.35);

  node.append("circle").attr("r",d=>r(d)+4).attr("fill","none")
    .attr("stroke",d=>d.score>=.7?"#f85149":d.score>=.4?"#e3b341":"#3fb950")
    .attr("stroke-width",1.8).attr("stroke-opacity",.55)
    .attr("stroke-dasharray",d=>{const c=2*Math.PI*(r(d)+4);return (c*d.score)+" "+c;});

  node.append("text")
    .attr("dy",d=>r(d)+14)
    .attr("text-anchor","middle").attr("font-size",10).attr("fill","#c9d1d9")
    .text(d=>d.label.length>16?d.label.slice(0,15)+"...":d.label);

  sim.on("tick",()=>{
    link.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y)
        .attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);
    linkLbl.attr("x",d=>(d.source.x+d.target.x)/2).attr("y",d=>(d.source.y+d.target.y)/2);
    node.attr("transform",d=>"translate("+d.x+","+d.y+")");
  });
}

function resetZoom(){svgEl.transition().duration(400).call(zoom.transform,d3.zoomIdentity);}
"""

if __name__ == "__main__":
    main()
