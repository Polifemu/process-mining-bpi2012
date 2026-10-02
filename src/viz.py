import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


def _fmt_count(v):
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v/1_000:.0f}k"
    return f"{v:.0f}"


def render_dfg(dfg, start_activities, end_activities, out_path, title, value_fmt=None):
    value_fmt = value_fmt or _fmt_count
    activities = set()
    for a, b in dfg:
        activities.add(a)
        activities.add(b)
    activities.update(start_activities)
    activities.update(end_activities)

    freq = {a: 0 for a in activities}
    for (a, b), c in dfg.items():
        freq[a] += c
        freq[b] += c
    for a, c in start_activities.items():
        freq[a] += c
    for a, c in end_activities.items():
        freq[a] += c

    G = nx.DiGraph()
    for a in activities:
        G.add_node(a)
    for (a, b), c in dfg.items():
        G.add_edge(a, b, weight=c)

    pos = nx.spring_layout(G, seed=42, k=1.2 / np.sqrt(max(len(activities), 1)))
    counts = np.array([freq.get(n, 0) for n in G.nodes])
    sizes = 300 + 3500 * counts / counts.max()
    weights = np.array([G[u][v]["weight"] for u, v in G.edges])
    widths = 0.6 + 4.0 * weights / weights.max()

    fig, ax = plt.subplots(figsize=(16, 11))
    nx.draw_networkx_edges(G, pos, ax=ax, width=widths, alpha=0.45,
                           arrows=True, arrowsize=14, edge_color="#37474f",
                           connectionstyle="arc3,rad=0.08")
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=sizes, node_color="#ffe082",
                           edgecolors="#4e342e", linewidths=1.2)
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=8)

    if len(G.edges) > 0:
        cutoff = np.quantile(weights, 0.55)
        labels = {(u, v): value_fmt(d["weight"]) for u, v, d in G.edges(data=True)
                  if d["weight"] >= cutoff}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, ax=ax, font_size=7,
                                     bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.7))
    ax.set_title(title, fontsize=14)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def render_petri_net(net, im, fm, out_path, title):
    G = nx.DiGraph()
    place_names = {p.name for p in net.places}
    trans_names = {t.name for t in net.transitions}
    for p in place_names:
        G.add_node(("p", p))
    for t in trans_names:
        G.add_node(("t", t))
    for arc in net.arcs:
        s = arc.source
        t = arc.target
        sn = ("p", s.name) if s.name in place_names else ("t", s.name)
        tn = ("p", t.name) if t.name in place_names else ("t", t.name)
        G.add_edge(sn, tn)

    pos = nx.spring_layout(G, seed=7, k=2.0 / np.sqrt(max(len(G.nodes), 1)))
    node_list = list(G.nodes)
    is_place = [n[0] == "p" for n in node_list]
    colors = ["#90caf9" if n[0] == "t" else "#ffffff" for n in node_list]
    shapes = ["s" if n[0] == "t" else "o" for n in node_list]

    initial = {f"p_{n}" for n in im}
    final = {f"p_{n}" for n in fm}
    for i, n in enumerate(node_list):
        if n[0] == "p":
            label = f"p_{n[1]}"
            if label in initial:
                colors[i] = "#a5d6a7"
            elif label in final:
                colors[i] = "#ffcc80"

    fig, ax = plt.subplots(figsize=(16, 12))
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.5, arrows=True, arrowsize=12,
                           edge_color="#455a64")
    for shape in ("o", "s"):
        idx = [i for i, s in enumerate(shapes) if s == shape]
        if not idx:
            continue
        nodes = [node_list[i] for i in idx]
        nx.draw_networkx_nodes(G, pos, nodelist=nodes, ax=ax,
                               node_shape=shape,
                               node_color=[colors[i] for i in idx],
                               node_size=700 if shape == "o" else 1400,
                               edgecolors="#263238", linewidths=1.2)
    labels = {n: n[1] for n in node_list}
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax, font_size=8)
    ax.set_title(title, fontsize=14)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_variants(variant_counts, out_path, top=10):
    items = variant_counts[:top]
    labels = [" → ".join(v[:6]) + (" …" if len(v) > 6 else "") for v, _ in items]
    values = [c for _, c in items]
    fig, ax = plt.subplots(figsize=(12, 6))
    y = np.arange(len(values))[::-1]
    ax.barh(y, values, color="#5c6bc0")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("casi")
    ax.set_title(f"Top {top} varianti")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_case_durations(durations_days, out_path):
    arr = np.asarray(durations_days, dtype=float)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(arr, bins=60, color="#26a69a", alpha=0.85)
    ax.axvline(np.mean(arr), color="#c62828", linestyle="--", label=f"media {np.mean(arr):.1f} gg")
    ax.axvline(np.median(arr), color="#4527a0", linestyle=":", label=f"mediana {np.median(arr):.1f} gg")
    ax.set_xlabel("durata del caso (giorni)")
    ax.set_ylabel("casi")
    ax.set_title("Distribuzione durata dei casi")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
