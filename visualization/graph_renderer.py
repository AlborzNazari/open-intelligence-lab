"""
graph_renderer.py — Open Intelligence Lab
Interactive threat knowledge graph powered by Plotly.
Opens in your browser: fully zoomable, pannable, clickable.
"""

import math
import webbrowser
import tempfile
import networkx as nx
import plotly.graph_objects as go


# ── PALETTE ───────────────────────────────────────────────────────────────────
BG_VOID   = "#020408"
BG_PANEL  = "#080d14"
BORDER    = "#1a2535"
TEXT_PRI  = "#e8f4fd"
TEXT_MUT  = "#4a6278"
ACCENT    = "#00d4ff"

ENTITY_COLOR = {
    "organization":      "#00d4ff",
    "domain":            "#39ff8f",
    "incident_category": "#ff4d6d",
    "threat_actor":      "#ff2d55",
    "malware":           "#c084fc",
    "infrastructure":    "#f5a623",
    "cve":               "#ff6b35",
    "sector":            "#4a9eff",
}
DEFAULT_COLOR = "#4a6278"

RISK_COLOR = {
    "critical": "#ff2d55",
    "high":     "#ff6b35",
    "medium":   "#f5a623",
    "low":      "#39ff8f",
}

def _risk_band(score: float) -> str:
    if score >= 0.90: return "critical"
    if score >= 0.70: return "high"
    if score >= 0.40: return "medium"
    return "low"

def _node_size(risk: float) -> int:
    return int(22 + risk * 32)

def _hex_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ── MAIN ──────────────────────────────────────────────────────────────────────
def draw_threat_graph(graph: nx.DiGraph) -> None:

    if graph.number_of_nodes() == 0:
        print("[graph_renderer] Empty graph — nothing to render.")
        return

    pos = nx.spring_layout(graph, seed=42, k=2.2)

    # ── EDGE ARROWS ──────────────────────────────────────────────────────────
    annotations = []
    edge_hover_xs, edge_hover_ys, edge_hover_texts = [], [], []

    for u, v, data in graph.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        rel   = data.get("relation_type", "related_to")
        conf  = data.get("confidence", 0.7)
        color = ENTITY_COLOR.get(graph.nodes[u].get("entity_type", ""), DEFAULT_COLOR)
        rgba  = _hex_rgba(color, 0.2 + conf * 0.5)

        # arrow
        annotations.append(dict(
            ax=x0, ay=y0, x=x1, y=y1,
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True,
            arrowhead=2, arrowsize=1.2,
            arrowwidth=0.8 + conf * 1.8,
            arrowcolor=rgba,
        ))

        # edge label at midpoint
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        annotations.append(dict(
            x=mx, y=my, xref="x", yref="y",
            text=f"<span style='font-size:9px;color:{TEXT_MUT};font-family:monospace'>{rel}</span>",
            showarrow=False,
            bgcolor=BG_VOID,
            bordercolor=BORDER,
            borderwidth=0.5,
            borderpad=2,
            opacity=0.85,
        ))

        edge_hover_xs.append(mx)
        edge_hover_ys.append(my)
        edge_hover_texts.append(f"<b>{rel}</b><br>confidence: {conf:.2f}")

    # invisible edge hover trace
    edge_trace = go.Scatter(
        x=edge_hover_xs, y=edge_hover_ys,
        mode="markers",
        marker=dict(size=10, color="rgba(0,0,0,0)"),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=edge_hover_texts,
        showlegend=False,
    )

    # ── GLOW HALOS ────────────────────────────────────────────────────────────
    glow_xs, glow_ys, glow_sizes, glow_colors = [], [], [], []
    for n in graph.nodes:
        x, y  = pos[n]
        risk  = graph.nodes[n].get("risk_score", 0.5)
        etype = graph.nodes[n].get("entity_type", "unknown")
        color = ENTITY_COLOR.get(etype, DEFAULT_COLOR)
        glow_xs.append(x)
        glow_ys.append(y)
        glow_sizes.append(_node_size(risk) * 2.6)
        glow_colors.append(_hex_rgba(color, 0.09))

    glow_trace = go.Scatter(
        x=glow_xs, y=glow_ys,
        mode="markers",
        marker=dict(size=glow_sizes, color=glow_colors, line=dict(width=0)),
        hoverinfo="skip",
        showlegend=False,
    )

    # ── NODE TRACES (grouped by entity type for legend) ───────────────────────
    types_map: dict = {}
    for n in graph.nodes:
        etype = graph.nodes[n].get("entity_type", "unknown")
        types_map.setdefault(etype, []).append(n)

    node_traces = []
    for etype, node_ids in types_map.items():
        color = ENTITY_COLOR.get(etype, DEFAULT_COLOR)
        xs, ys, sizes, texts, hovers, borders = [], [], [], [], [], []

        for n in node_ids:
            attrs = graph.nodes[n]
            x, y  = pos[n]
            name  = attrs.get("name", n)
            risk  = attrs.get("risk_score", 0.5)
            band  = _risk_band(risk)
            rc    = RISK_COLOR[band]
            conf  = attrs.get("confidence_level", 0.8)
            deg   = graph.degree(n)

            xs.append(x)
            ys.append(y)
            sizes.append(_node_size(risk))
            borders.append(rc)
            texts.append(
                f"<span style='font-family:monospace;font-size:10px;color:{TEXT_PRI}'>{name}</span>"
                f"<br><span style='font-family:monospace;font-size:8px;color:{rc}'>{risk:.2f} · {band.upper()}</span>"
            )
            hovers.append(
                f"<b style='color:{color};font-family:monospace'>{name}</b><br>"
                f"<span style='color:{TEXT_MUT}'>type · </span>{etype}<br>"
                f"<span style='color:{TEXT_MUT}'>risk · </span><span style='color:{rc}'>{risk:.2f} ({band.upper()})</span><br>"
                f"<span style='color:{TEXT_MUT}'>confidence · </span>{conf:.2f}<br>"
                f"<span style='color:{TEXT_MUT}'>connections · </span>{deg}"
            )

        node_traces.append(go.Scatter(
            x=xs, y=ys,
            mode="markers+text",
            name=etype.replace("_", " ").title(),
            text=texts,
            textposition="bottom center",
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hovers,
            marker=dict(
                size=sizes,
                color=_hex_rgba(color, 0.15),
                line=dict(color=borders, width=2.2),
                symbol="circle",
            ),
        ))

    # ── FIGURE ────────────────────────────────────────────────────────────────
    n_nodes = graph.number_of_nodes()
    n_edges = graph.number_of_edges()

    fig = go.Figure(data=[glow_trace, edge_trace] + node_traces)

    fig.update_layout(
        title=dict(
            text=(
                f"<span style='font-family:monospace;font-size:18px;color:{TEXT_PRI};letter-spacing:4px'>"
                f"OPEN INTELLIGENCE LAB</span>"
                f"<span style='font-family:monospace;font-size:14px;color:{ACCENT}'>  —  Threat Knowledge Graph</span><br>"
                f"<span style='font-family:monospace;font-size:10px;color:{TEXT_MUT}'>"
                f"Nodes: {n_nodes}  ·  Edges: {n_edges}  ·  Ethical OSINT  ·  MITRE ATT&CK Aligned  ·  v0.1"
                f"</span>"
            ),
            x=0.5, xanchor="center",
            y=0.97, yanchor="top",
        ),
        paper_bgcolor=BG_VOID,
        plot_bgcolor=BG_PANEL,
        font=dict(family="monospace", color=TEXT_PRI),
        showlegend=True,
        legend=dict(
            bgcolor=BG_PANEL,
            bordercolor=BORDER,
            borderwidth=1,
            font=dict(family="monospace", size=10, color=TEXT_PRI),
            title=dict(text="<b>ENTITY TYPES</b>", font=dict(size=9, color=TEXT_MUT)),
            x=0.01, y=0.01,
            xanchor="left", yanchor="bottom",
        ),
        xaxis=dict(showgrid=True, gridcolor=BORDER, gridwidth=0.4,
                   zeroline=False, showticklabels=False, showline=True, linecolor=BORDER),
        yaxis=dict(showgrid=True, gridcolor=BORDER, gridwidth=0.4,
                   zeroline=False, showticklabels=False, showline=True, linecolor=BORDER),
        annotations=annotations,
        margin=dict(l=20, r=20, t=110, b=20),
        hovermode="closest",
        hoverlabel=dict(
            bgcolor=BG_PANEL, bordercolor=BORDER,
            font=dict(family="monospace", size=11, color=TEXT_PRI),
        ),
        dragmode="pan",
    )

    # risk band legend (bottom right)
    fig.add_annotation(
        x=0.99, y=0.01, xref="paper", yref="paper",
        xanchor="right", yanchor="bottom",
        text=(
            f"<span style='font-family:monospace;font-size:9px;color:{TEXT_MUT}'>RISK BANDS<br></span>"
            + "".join([
                f"<span style='font-family:monospace;font-size:9px;color:{RISK_COLOR[b]}'>{b.upper():<9}</span>"
                f"<span style='font-family:monospace;font-size:9px;color:{TEXT_MUT}'>{t}<br></span>"
                for b, t in [("critical","≥ 0.90"),("high","≥ 0.70"),("medium","≥ 0.40"),("low","< 0.40")]
            ])
        ),
        showarrow=False, align="left",
        bgcolor=BG_PANEL, bordercolor=BORDER,
        borderwidth=1, borderpad=8, opacity=0.92,
    )

    # ── OPEN IN BROWSER ───────────────────────────────────────────────────────
    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False, prefix="oi_lab_")
    fig.write_html(
        tmp.name,
        include_plotlyjs="cdn",
        config={
            "scrollZoom": True,
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["select2d", "lasso2d"],
            "toImageButtonOptions": {
                "format": "png",
                "filename": "open_intelligence_lab",
                "width": 1920, "height": 1080,
            },
        },
    )
    webbrowser.open(f"file://{tmp.name}")
    print(f"\n[Open Intelligence Lab] ✓ Graph opened in browser")
    print(f"  → Zoom with scroll wheel")
    print(f"  → Pan by dragging")
    print(f"  → Hover nodes & edges for details")
    print(f"  → Click legend items to filter entity types")
    print(f"  → Save as PNG via the camera icon\n")
