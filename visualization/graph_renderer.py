import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import networkx as nx


# ── THEME ──────────────────────────────────────────────────────────────────────
BG_VOID      = "#020408"
BG_PANEL     = "#080d14"
BORDER       = "#1a2535"
TEXT_PRIMARY = "#e8f4fd"
TEXT_MUTED   = "#4a6278"
ACCENT       = "#00d4ff"

ENTITY_STYLES = {
    "organization":     {"color": "#00d4ff", "glow": "#00d4ff66", "marker": "●"},
    "domain":           {"color": "#39ff8f", "glow": "#39ff8f66", "marker": "◆"},
    "incident_category":{"color": "#ff4d6d", "glow": "#ff4d6d66", "marker": "▲"},
    "threat_actor":     {"color": "#ff2d55", "glow": "#ff2d5566", "marker": "★"},
    "malware":          {"color": "#c084fc", "glow": "#c084fc66", "marker": "■"},
    "infrastructure":   {"color": "#f5a623", "glow": "#f5a62366", "marker": "⬟"},
    "cve":              {"color": "#ff6b35", "glow": "#ff6b3566", "marker": "◉"},
    "sector":           {"color": "#4a9eff", "glow": "#4a9eff66", "marker": "⬡"},
}
DEFAULT_STYLE = {"color": "#4a6278", "glow": "#4a627866", "marker": "●"}

RISK_COLORS = {
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


# ── MAIN DRAW FUNCTION ─────────────────────────────────────────────────────────
def draw_threat_graph(graph: nx.DiGraph) -> None:

    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor(BG_VOID)
    ax.set_facecolor(BG_PANEL)

    # subtle grid
    ax.grid(True, color=BORDER, linewidth=0.4, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
        spine.set_linewidth(1)

    # ── LAYOUT ────────────────────────────────────────────────────────────────
    pos = nx.spring_layout(graph, seed=42, k=2.8)

    # ── COLLECT NODE PROPERTIES ───────────────────────────────────────────────
    node_colors, node_sizes, node_edge_colors = [], [], []
    for n in graph.nodes:
        attrs = graph.nodes[n]
        etype = attrs.get("entity_type", "unknown")
        style = ENTITY_STYLES.get(etype, DEFAULT_STYLE)
        risk  = attrs.get("risk_score", 0.5)
        node_colors.append(style["color"] + "33")      # translucent fill
        node_sizes.append(1800 + risk * 2200)           # size scales with risk
        node_edge_colors.append(style["color"])

    # ── DRAW GLOW HALOS ────────────────────────────────────────────────────────
    for n, (x, y) in pos.items():
        attrs  = graph.nodes[n]
        etype  = attrs.get("entity_type", "unknown")
        style  = ENTITY_STYLES.get(etype, DEFAULT_STYLE)
        risk   = attrs.get("risk_score", 0.5)
        radius = (1800 + risk * 2200) / 28000
        circle = plt.Circle(
            (x, y), radius * 2.8,
            color=style["glow"], linewidth=0, alpha=0.25, zorder=1
        )
        ax.add_patch(circle)

    # ── DRAW EDGES ────────────────────────────────────────────────────────────
    edge_styles = []
    for u, v, data in graph.edges(data=True):
        rel  = data.get("relation_type", "related_to")
        conf = data.get("confidence", 0.7)
        src_style = ENTITY_STYLES.get(
            graph.nodes[u].get("entity_type", ""), DEFAULT_STYLE
        )
        edge_styles.append((u, v, src_style["color"], conf))

    for u, v, color, conf in edge_styles:
        nx.draw_networkx_edges(
            graph, pos, edgelist=[(u, v)], ax=ax,
            edge_color=color,
            alpha=0.25 + conf * 0.45,
            width=0.6 + conf * 1.6,
            arrows=True,
            arrowsize=16,
            arrowstyle="-|>",
            node_size=2800,
            connectionstyle="arc3,rad=0.08",
            min_source_margin=18,
            min_target_margin=18,
        )

    # ── DRAW NODES ────────────────────────────────────────────────────────────
    nx.draw_networkx_nodes(
        graph, pos, ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        linewidths=1.8,
    )
    # coloured borders drawn separately for full control
    for i, n in enumerate(graph.nodes):
        nx.draw_networkx_nodes(
            graph, pos, ax=ax,
            nodelist=[n],
            node_color="none",
            node_size=node_sizes[i],
            linewidths=1.8,
            edgecolors=node_edge_colors[i],
        )

    # ── DRAW LABELS ───────────────────────────────────────────────────────────
    for n, (x, y) in pos.items():
        attrs = graph.nodes[n]
        name  = attrs.get("name", n)
        risk  = attrs.get("risk_score", None)
        label = name if len(name) <= 18 else name[:16] + "…"

        # main label
        ax.text(
            x, y + 0.01, label,
            fontsize=8.5, fontweight="600",
            color=TEXT_PRIMARY, ha="center", va="center",
            fontfamily="monospace",
            zorder=10,
            path_effects=[
                pe.withStroke(linewidth=3, foreground=BG_PANEL)
            ],
        )

        # risk badge below node
        if risk is not None:
            band  = _risk_band(risk)
            rcolor = RISK_COLORS[band]
            ax.text(
                x, y - 0.095,
                f"{risk:.2f}",
                fontsize=7, fontweight="bold",
                color=rcolor, ha="center", va="center",
                fontfamily="monospace",
                zorder=10,
                path_effects=[
                    pe.withStroke(linewidth=2.5, foreground=BG_PANEL)
                ],
            )

    # ── EDGE RELATION LABELS (mid-edge) ──────────────────────────────────────
    edge_labels = {
        (u, v): data.get("relation_type", "")
        for u, v, data in graph.edges(data=True)
        if data.get("relation_type")
    }
    if edge_labels:
        nx.draw_networkx_edge_labels(
            graph, pos, edge_labels=edge_labels, ax=ax,
            font_size=6.5,
            font_color=TEXT_MUTED,
            font_family="monospace",
            bbox=dict(
                boxstyle="round,pad=0.2",
                facecolor=BG_VOID, edgecolor=BORDER,
                alpha=0.75, linewidth=0.6,
            ),
            rotate=False,
            label_pos=0.5,
        )

    # ── LEGEND ────────────────────────────────────────────────────────────────
    present_types = {
        graph.nodes[n].get("entity_type", "unknown")
        for n in graph.nodes
    }
    legend_handles = []
    for etype, style in ENTITY_STYLES.items():
        if etype in present_types:
            legend_handles.append(
                mpatches.Patch(
                    facecolor=style["color"] + "33",
                    edgecolor=style["color"],
                    linewidth=1.5,
                    label=etype.replace("_", " ").title(),
                )
            )

    if legend_handles:
        legend = ax.legend(
            handles=legend_handles,
            loc="lower left",
            frameon=True,
            framealpha=0.85,
            facecolor=BG_PANEL,
            edgecolor=BORDER,
            fontsize=8,
            title="ENTITY TYPES",
            title_fontsize=7,
            labelcolor=TEXT_PRIMARY,
            handlelength=1.2,
            handleheight=1.0,
            borderpad=0.8,
            labelspacing=0.55,
        )
        legend.get_title().set_color(TEXT_MUTED)
        legend.get_title().set_fontfamily("monospace")

    # ── RISK SCALE (top-right) ────────────────────────────────────────────────
    risk_handles = [
        mpatches.Patch(facecolor=RISK_COLORS["critical"] + "33",
                       edgecolor=RISK_COLORS["critical"], linewidth=1.5,
                       label="Critical  ≥ 0.90"),
        mpatches.Patch(facecolor=RISK_COLORS["high"] + "33",
                       edgecolor=RISK_COLORS["high"], linewidth=1.5,
                       label="High      ≥ 0.70"),
        mpatches.Patch(facecolor=RISK_COLORS["medium"] + "33",
                       edgecolor=RISK_COLORS["medium"], linewidth=1.5,
                       label="Medium    ≥ 0.40"),
        mpatches.Patch(facecolor=RISK_COLORS["low"] + "33",
                       edgecolor=RISK_COLORS["low"], linewidth=1.5,
                       label="Low       < 0.40"),
    ]
    risk_legend = ax.legend(
        handles=risk_handles,
        loc="lower right",
        frameon=True,
        framealpha=0.85,
        facecolor=BG_PANEL,
        edgecolor=BORDER,
        fontsize=8,
        title="RISK BANDS",
        title_fontsize=7,
        labelcolor=TEXT_PRIMARY,
        handlelength=1.2,
        handleheight=1.0,
        borderpad=0.8,
        labelspacing=0.55,
    )
    risk_legend.get_title().set_color(TEXT_MUTED)
    risk_legend.get_title().set_fontfamily("monospace")
    ax.add_artist(legend)   # re-add first legend (matplotlib replaces it)

    # ── TITLE & STATS BAR ─────────────────────────────────────────────────────
    node_count = graph.number_of_nodes()
    edge_count = graph.number_of_edges()

    fig.text(
        0.5, 0.965,
        "OPEN INTELLIGENCE LAB  —  Threat Knowledge Graph",
        ha="center", va="top",
        fontsize=14, fontweight="bold",
        color=TEXT_PRIMARY, fontfamily="monospace",
    )
    fig.text(
        0.5, 0.942,
        f"Nodes: {node_count}   ·   Edges: {edge_count}   ·   "
        "Ethical OSINT  ·  MITRE ATT&CK Aligned  ·  v0.1",
        ha="center", va="top",
        fontsize=8, color=TEXT_MUTED, fontfamily="monospace",
    )

    # top accent line
    fig.add_artist(
        plt.Line2D(
            [0.04, 0.96], [0.935, 0.935],
            transform=fig.transFigure,
            color=ACCENT, linewidth=0.6, alpha=0.5,
        )
    )

    ax.set_xlim(ax.get_xlim()[0] - 0.15, ax.get_xlim()[1] + 0.15)
    ax.set_ylim(ax.get_ylim()[0] - 0.18, ax.get_ylim()[1] + 0.10)
    ax.tick_params(colors=BORDER)
    ax.set_xticks([])
    ax.set_yticks([])

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.show()
