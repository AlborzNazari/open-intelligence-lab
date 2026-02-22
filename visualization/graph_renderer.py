import matplotlib.pyplot as plt
import networkx as nx


def draw_threat_graph(graph: nx.DiGraph) -> None:
    pos = nx.spring_layout(graph, seed=42)

    node_colors = []
    for n in graph.nodes:
        etype = graph.nodes[n].get("entity_type")
        if etype == "organization":
            node_colors.append("skyblue")
        elif etype == "domain":
            node_colors.append("lightgreen")
        elif etype == "incident_category":
            node_colors.append("salmon")
        else:
            node_colors.append("gray")

    nx.draw(
        graph,
        pos,
        with_labels=True,
        node_color=node_colors,
        node_size=800,
        font_size=8,
    )
    plt.title("Open Intelligence Lab — Threat Knowledge Graph")
    plt.show()
