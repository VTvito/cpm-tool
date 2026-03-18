"""
CPM – Grafici con Plotly.

Palette colori coerente con il tema dell'applicazione:
  Set A  = celeste (#2980B9)
  Set Ab = arancio (#E67E22)
  Set B  = verde   (#27AE60)
"""

from __future__ import annotations

import plotly.graph_objects as go

from core.answer_key import SETS, MAX_PER_SET
from core.scoring import ScoringResult

# Palette
COLOR_A  = "#2980B9"
COLOR_AB = "#E67E22"
COLOR_B  = "#27AE60"
COLOR_CORRECT = "#27AE60"
COLOR_WRONG   = "#E74C3C"
COLOR_BLANK   = "#BDC3C7"
COLOR_BG  = "rgba(0,0,0,0)"


def _layout(title: str = "", height: int = 350) -> dict:
    return dict(
        title=dict(text=title, font=dict(size=16, color="#1A252F")),
        paper_bgcolor=COLOR_BG,
        plot_bgcolor=COLOR_BG,
        margin=dict(l=40, r=40, t=50, b=40),
        height=height,
        font=dict(family="Calibri, sans-serif", size=13),
    )


# ─────────────────────────────────────────
#  Barre per set
# ─────────────────────────────────────────
def bar_chart_sets(result: ScoringResult) -> go.Figure:
    sets = ["Set A", "Set Ab", "Set B"]
    scores = [result.set_a_score, result.set_ab_score, result.set_b_score]
    colors = [COLOR_A, COLOR_AB, COLOR_B]

    fig = go.Figure(
        go.Bar(
            x=sets, y=scores,
            marker_color=colors,
            text=[f"{s}/12" for s in scores],
            textposition="outside",
            textfont=dict(size=15, color="#1A252F"),
        )
    )
    fig.update_layout(
        **_layout("Punteggio per Set"),
        yaxis=dict(range=[0, MAX_PER_SET + 1], dtick=2,
                   showgrid=True, gridcolor="#E5E8E8"),
        xaxis=dict(showgrid=False),
        showlegend=False,
    )
    return fig


# ─────────────────────────────────────────
#  Radar chart
# ─────────────────────────────────────────
def radar_chart(result: ScoringResult) -> go.Figure:
    categories = ["Set A", "Set Ab", "Set B", "Set A"]  # chiude il poligono
    values = [result.set_a_score, result.set_ab_score, result.set_b_score,
              result.set_a_score]

    fig = go.Figure(
        go.Scatterpolar(
            r=values, theta=categories,
            fill="toself",
            fillcolor="rgba(41,128,185,0.2)",
            line=dict(color=COLOR_A, width=2),
            marker=dict(size=8),
        )
    )
    fig.update_layout(
        **_layout("Profilo per Set", height=320),
        polar=dict(
            radialaxis=dict(visible=True, range=[0, MAX_PER_SET], dtick=3),
        ),
        showlegend=False,
    )
    return fig


# ─────────────────────────────────────────
#  Gauge percentile
# ─────────────────────────────────────────
_PCT_NUMERIC = {"<5": 2, "5": 5, "10": 10, "25": 25, "50": 50,
                "75": 75, "90": 90, "95": 95, ">95": 98}


def percentile_gauge(percentile: str) -> go.Figure:
    val = _PCT_NUMERIC.get(percentile, 0)

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=val,
            number=dict(suffix="°", font=dict(size=28)),
            title=dict(text=f"Percentile: {percentile}", font=dict(size=15)),
            gauge=dict(
                axis=dict(range=[0, 100], dtick=25),
                bar=dict(color="#1B3A6B"),
                steps=[
                    dict(range=[0, 10],  color="#FADBD8"),
                    dict(range=[10, 25], color="#FDEBD0"),
                    dict(range=[25, 75], color="#D5F5E3"),
                    dict(range=[75, 90], color="#D6EAF8"),
                    dict(range=[90, 100], color="#D2B4DE"),
                ],
            ),
        )
    )
    fig.update_layout(
        **_layout(height=280),
    )
    fig.update_layout(margin=dict(l=30, r=30, t=30, b=10))
    return fig


# ─────────────────────────────────────────
#  Heatmap item (corretti / errati)
# ─────────────────────────────────────────
def item_heatmap(result: ScoringResult) -> go.Figure:
    set_names = ["A", "Ab", "B"]
    z = []       # valori: 1=corretto, 0=errato, -1=vuoto
    text = []    # testo hover
    for set_name in set_names:
        row_z = []
        row_t = []
        for item in SETS[set_name]:
            r = result.item_results.get(item)
            if r is None:
                row_z.append(-1)
                row_t.append(f"{item}: –")
            elif r:
                row_z.append(1)
                row_t.append(f"{item}: ✓")
            else:
                row_z.append(0)
                row_t.append(f"{item}: ✗")
        z.append(row_z)
        text.append(row_t)

    colorscale = [
        [0.0,  COLOR_BLANK],    # -1 = nessuna risposta
        [0.45, COLOR_BLANK],
        [0.45, COLOR_WRONG],    #  0 = errato
        [0.55, COLOR_WRONG],
        [0.55, COLOR_CORRECT],  #  1 = corretto
        [1.0,  COLOR_CORRECT],
    ]

    fig = go.Figure(
        go.Heatmap(
            z=z, text=text, texttemplate="%{text}",
            x=[str(i) for i in range(1, 13)],
            y=["Set A", "Set Ab", "Set B"],
            colorscale=colorscale, zmin=-1, zmax=1,
            showscale=False,
            hoverinfo="text",
        )
    )
    fig.update_layout(
        **_layout("Dettaglio Item", height=220),
        xaxis=dict(title="Item", dtick=1, side="top"),
        yaxis=dict(autorange="reversed"),
    )
    return fig


# ─────────────────────────────────────────
#  Bar chart confronto con massimo
# ─────────────────────────────────────────
def total_bar(result: ScoringResult) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Punteggio Ottenuto"], y=[result.total_raw],
        marker_color="#0077B6", text=[str(result.total_raw)],
        textposition="outside", textfont=dict(size=18),
        name="Ottenuto",
    ))
    fig.add_trace(go.Bar(
        x=["Massimo Possibile"], y=[36],
        marker_color="#D5DBDB", text=["36"],
        textposition="outside", textfont=dict(size=18),
        name="Massimo",
    ))
    fig.update_layout(
        **_layout("Punteggio Totale", height=280),
        yaxis=dict(range=[0, 40], showgrid=True, gridcolor="#E5E8E8"),
        showlegend=False,
        barmode="group",
    )
    return fig
