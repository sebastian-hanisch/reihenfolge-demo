"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import rei_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_progress(shots):
    """Spielstand nach jedem Schuss: Tore von Mannschaft A und B; senkrechte Linie vor dem ersten Schuss des Sudden Death."""
    xs = [0] + [s.number for s in shots]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[0] + [s.score_a for s in shots], mode="lines+markers", line=dict(color=C.COLOR_A, width=3, shape="hv"), name="Mannschaft A (erste)",
                             hovertemplate="nach Schuss %{x}: %{y} Tore<extra>A</extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[0] + [s.score_b for s in shots], mode="lines+markers", line=dict(color=C.COLOR_B, width=3, dash="dot", shape="hv"), name="Mannschaft B",
                             hovertemplate="nach Schuss %{x}: %{y} Tore<extra>B</extra>"))
    sd = [s.number for s in shots if s.phase == "Sudden Death"]
    if sd:
        fig.add_vline(x=sd[0] - 0.5, line_dash="dash", line_color="gray", annotation_text="Sudden Death", annotation_position="top left")
    fig.update_xaxes(title_text="Schuss Nr.", dtick=1, range=[-0.3, max(xs) + 0.5])
    fig.update_yaxes(title_text="Tore", dtick=1, rangemode="tozero")
    return _base(fig, height=300)


def build_stop_probs(stop_probs):
    """Wahrscheinlichkeit, dass die Entscheidung mit Schuss i fällt (nur Regelzeit; der Rest ist Gleichstand und führt in den Sudden Death)."""
    xs = list(range(1, len(stop_probs) + 1))
    fig = go.Figure(go.Bar(x=[str(x) for x in xs], y=[100.0 * p for p in stop_probs], marker_color=C.COLOR_LINE_A,
                           hovertemplate="mit Schuss %{x}: %{y:.1f} %<extra></extra>"))
    fig.update_xaxes(title_text="Entscheidung fällt mit Schuss Nr. (Regelzeit)", type="category")
    fig.update_yaxes(title_text="Wahrscheinlichkeit (%)", rangemode="tozero")
    return _base(fig, height=280)


def build_sweep_d(rows, d_now=None):
    """Gewinnwahrscheinlichkeit der ersten Mannschaft über d, beide Reihenfolgen (Prozent), 50 % als Linie."""
    xs = [r["d"] for r in rows]
    fig = go.Figure()
    fig.add_hline(y=50, line_dash="dash", line_color="gray")
    fig.add_trace(go.Scatter(x=xs, y=[100 * r["abab"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_LINE_B, width=3), name="ABAB",
                             hovertemplate="d = %{x:.2f}: %{y:.1f} %<extra>ABAB</extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[100 * r["abba"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_LINE_A, width=3), name="ABBA",
                             hovertemplate="d = %{x:.2f}: %{y:.1f} %<extra>ABBA</extra>"))
    if d_now is not None:
        fig.add_vline(x=d_now, line_dash="dot", line_color="gray", annotation_text="Einstellung", annotation_position="top left")
    fig.update_xaxes(title_text="Abschlag im Rückstand d")
    fig.update_yaxes(title_text="Erste Mannschaft gewinnt (%)")
    return _base(fig)


def build_sweep_r(rows, r_now=None):
    xs = [r["r"] for r in rows]
    fig = go.Figure()
    fig.add_hline(y=50, line_dash="dash", line_color="gray")
    fig.add_trace(go.Scatter(x=xs, y=[100 * r["abab"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_LINE_B, width=3), name="ABAB",
                             hovertemplate="%{x} Schüsse: %{y:.2f} %<extra>ABAB</extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[100 * r["abba"] for r in rows], mode="lines+markers", line=dict(color=C.COLOR_LINE_A, width=3), name="ABBA",
                             hovertemplate="%{x} Schüsse: %{y:.2f} %<extra>ABBA</extra>"))
    if r_now is not None:
        fig.add_vline(x=r_now, line_dash="dot", line_color="gray", annotation_text="Einstellung", annotation_position="top left")
    fig.update_xaxes(title_text="Schüsse je Mannschaft in der Regelzeit", dtick=1)
    fig.update_yaxes(title_text="Erste Mannschaft gewinnt (%)")
    return _base(fig)


def build_totals(totals: dict, k: int):
    """Gesamtwert je Person im gezeigten Beispiel, gruppiert nach Regel."""
    colors = [C.COLOR_LINE_A, C.COLOR_LINE_B, C.COLOR_LINE_C, "#b279a2"]
    fig = go.Figure()
    for i in range(k):
        fig.add_trace(go.Bar(x=list(totals), y=[totals[rule][i] for rule in totals], name=f"Person {i + 1}", marker_color=colors[i],
                             hovertemplate="%{x}: %{y:.2f}<extra>Person " + str(i + 1) + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Gesamtwert", rangemode="tozero")
    return _base(fig, height=300)


def build_choice_sweep(rows, xkey: str, xlabel: str):
    """Vorteil der ersten gegenüber der letzten Person je Regel über w oder m, mit ±2 Standardfehlern; 0 als Linie."""
    xs = [r[xkey] for r in rows]
    fig = go.Figure()
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    for rule, color in zip(C.RULES, (C.COLOR_LINE_B, C.COLOR_LINE_A, C.COLOR_LINE_C)):
        fig.add_trace(go.Scatter(x=xs, y=[r[rule] for r in rows], mode="lines+markers", line=dict(color=color, width=3), name=rule,
                                 error_y=dict(type="data", array=[2 * r[rule + "_se"] for r in rows], visible=True, thickness=1),
                                 hovertemplate=xlabel + " = %{x}: %{y:+.3f}<extra>" + rule + "</extra>"))
    fig.update_xaxes(title_text=xlabel)
    fig.update_yaxes(title_text="Erste minus letzte Person (Gesamtwert)")
    return _base(fig)
