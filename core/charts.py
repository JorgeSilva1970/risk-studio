"""Plotly figures. Every function accepts `dark` (app) vs light (HTML report)."""
from __future__ import annotations

import textwrap

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from core.catalogs import IMPACT_SCALE, LEVELS, OPP_LEVELS, PROB_SCALE, label
from core.i18n import L, lang
from core.model import ids_list

from core.theme import GOOD as _GOOD, NAVY, PRIMARY

TEAL = PRIMARY  # residual / primary series
GREY = "#64748b"
CONCL_COL = {"effective": "#22c55e", "partial": "#eab308", "ineffective": "#ef4444", "not_tested": "#94a3b8"}


def _layout(fig: go.Figure, dark: bool = False, title: str | None = None, height: int = 420) -> go.Figure:
    fg = "#e6f1f5" if dark else "#1d1d1b"
    grid = "rgba(148,163,184,0.18)" if dark else "#ecebe8"
    fig.update_layout(
        title=dict(text=title, x=0.01, font=dict(size=15)) if title else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Segoe UI, sans-serif", color=fg, size=12),
        margin=dict(l=10, r=10, t=45 if title else 15, b=10),
        height=height,
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor=grid, zerolinecolor=grid, automargin=True)
    fig.update_yaxes(gridcolor=grid, zerolinecolor=grid, automargin=True)
    return fig


def _lvl_colour(score: int, opp=False) -> str:
    for lo, hi, _, _, _, col in (OPP_LEVELS if opp else LEVELS):
        if lo <= score <= hi:
            return col
    return GREY


def heatmap(ra: pd.DataFrame, which: str = "res", opportunity: bool = False, dark=False,
            title: str | None = None, height=460) -> go.Figure:
    """5×5 probability-impact matrix with risk IDs placed in their cells."""
    pcol, icol = {"inh": ("p_inh", "i_inh"), "res": ("p_res", "i_res"), "tgt": ("p_tgt_f", "i_tgt_f")}[which]
    df = ra[ra["type"] == ("opportunity" if opportunity else "threat")] if not ra.empty else ra
    z = np.zeros((5, 5))
    txt = [["" for _ in range(5)] for _ in range(5)]
    colours = []
    for p in range(1, 6):
        for i in range(1, 6):
            z[p - 1][i - 1] = p * i
    for row in df.to_dict(orient="records"):
        p, i = int(row[pcol]), int(row[icol])
        txt[p - 1][i - 1] += (" " if txt[p - 1][i - 1] else "") + str(row["id"])
    # discrete colour scale built from levels
    table = OPP_LEVELS if opportunity else LEVELS
    for lo, hi, _, _, _, col in table:
        colours += [[(lo - 1) / 24, col], [(hi - 1) / 24 if hi < 25 else 1.0, col]]
    wrapped = [["<br>".join(textwrap.wrap(t, 8)) for t in r] for r in txt]
    xl = [f"{k}<br>{IMPACT_SCALE[k][1 if lang() == 'en' else 0]}" for k in range(1, 6)]
    yl = [f"{PROB_SCALE[k][0][1 if lang() == 'en' else 0]} ({k})" for k in range(1, 6)]
    fig = go.Figure(go.Heatmap(
        z=z, x=xl, y=yl, text=wrapped, texttemplate="<b>%{text}</b>", textfont=dict(size=12, color="#0b1b2b"),
        colorscale=colours, zmin=1, zmax=25, showscale=False, xgap=3, ygap=3,
        hovertemplate=L("Prob.: %{y}<br>Impacto: %{x}<br>Score: %{z}<br>Riscos: %{text}<extra></extra>",
                        "Prob.: %{y}<br>Impact: %{x}<br>Score: %{z}<br>Risks: %{text}<extra></extra>"),
    ))
    fig.update_xaxes(title=L("Impacto", "Impact") if not opportunity else L("Benefício", "Benefit"), side="bottom")
    fig.update_yaxes(title=L("Probabilidade", "Probability"))
    return _layout(fig, dark, title, height)


def movement(ra: pd.DataFrame, dark=False, title=None, height=480) -> go.Figure:
    """Inherent → residual → target movement for threats."""
    df = ra[ra["type"] == "threat"] if not ra.empty else ra
    fig = go.Figure()
    for lo, hi, _, pt, en, col in LEVELS:
        pass
    # background score bands
    for p in range(1, 6):
        for i in range(1, 6):
            fig.add_shape(type="rect", x0=i - 0.5, x1=i + 0.5, y0=p - 0.5, y1=p + 0.5, line=dict(width=1, color="rgba(255,255,255,0.6)" if dark else "white"),
                          fillcolor=_lvl_colour(p * i), opacity=0.28 if dark else 0.35, layer="below")
    rng = np.random.default_rng(1)
    for r in df.to_dict(orient="records"):
        jx, jy = rng.uniform(-0.22, 0.22, 2)
        x0, y0 = r["i_inh"] + jx, r["p_inh"] + jy
        x1, y1 = r["i_res"] + jx, r["p_res"] + jy
        fig.add_annotation(x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=3, arrowsize=1.2, arrowwidth=1.6,
                           arrowcolor="#e2e8f0" if dark else "#334155", opacity=0.85)
        fig.add_trace(go.Scatter(x=[x0], y=[y0], mode="markers", marker=dict(size=9, color="#f8fafc" if dark else "#334155", symbol="circle-open", line=dict(width=2)),
                                 showlegend=False, hovertemplate=f"{r['id']} — {L('inerente','inherent')} {r['score_inh']}<extra></extra>"))
        fig.add_trace(go.Scatter(x=[x1], y=[y1], mode="markers+text", text=[r["id"]], textposition="top center",
                                 marker=dict(size=13, color=r["colour_res"], line=dict(width=1.5, color=NAVY)),
                                 showlegend=False,
                                 hovertemplate=f"<b>{r['id']}</b> {r.get('title','')}<br>{L('Residual','Residual')}: {r['score_res']}<extra></extra>"))
    fig.update_xaxes(range=[0.5, 5.5], dtick=1, title=L("Impacto", "Impact"))
    fig.update_yaxes(range=[0.5, 5.5], dtick=1, title=L("Probabilidade", "Probability"))
    return _layout(fig, dark, title, height)


def priority_bubble(ra: pd.DataFrame, dark=False, title=None, height=420) -> go.Figure:
    df = ra[ra["type"] == "threat"] if not ra.empty else ra
    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Scatter(
            x=df["velocity"], y=df["score_res"], mode="markers+text", text=df["id"], textposition="middle center",
            textfont=dict(size=10, color=NAVY),
            marker=dict(size=np.clip(df["priority"].astype(float) * 2.2, 14, 70), color=df["colour_res"], opacity=0.85,
                        line=dict(width=1, color="white")),
            customdata=np.stack([df["title"], df["priority"], df["proximity"].map(lambda x: label("proximity", x))], axis=-1),
            hovertemplate="<b>%{text}</b> %{customdata[0]}<br>Score: %{y}<br>" + L("Velocidade", "Velocity") +
                          ": %{x}<br>" + L("Proximidade", "Proximity") + ": %{customdata[2]}<br>" +
                          L("Prioridade", "Priority") + ": %{customdata[1]}<extra></extra>"))
    fig.update_xaxes(range=[0.5, 5.5], dtick=1, title=L("Velocidade (1 lenta → 5 imediata)", "Velocity (1 slow → 5 immediate)"))
    fig.update_yaxes(range=[0, 26], title=L("Score residual", "Residual score"))
    return _layout(fig, dark, title, height)


def appetite_bars(ra: pd.DataFrame, dark=False, title=None, height=None) -> go.Figure:
    df = ra[ra["type"] == "threat"].sort_values("score_res") if not ra.empty else ra
    h = height or max(300, 26 * len(df) + 90)
    fig = go.Figure()
    if not df.empty:
        ylab = [f"{i} · {textwrap.shorten(str(t), 38)}" for i, t in zip(df["id"], df["title"])]
        fig.add_trace(go.Bar(y=ylab, x=df["score_inh"], orientation="h", name=L("Inerente", "Inherent"),
                             marker_color="rgba(148,163,184,0.45)"))
        fig.add_trace(go.Bar(y=ylab, x=df["score_res"], orientation="h", name=L("Residual", "Residual"),
                             marker_color=list(df["colour_res"])))
        fig.add_trace(go.Scatter(y=ylab, x=df["appetite"], mode="markers", name=L("Apetite", "Appetite"),
                                 marker=dict(symbol="line-ns", size=18, line=dict(width=3, color=_GOOD))))
        fig.add_trace(go.Scatter(y=ylab, x=df["tolerance"], mode="markers", name=L("Tolerância", "Tolerance"),
                                 marker=dict(symbol="line-ns", size=18, line=dict(width=3, color="#f43f5e"))))
        fig.update_layout(barmode="overlay", legend=dict(orientation="h", y=1.06, x=0))
    fig.update_xaxes(range=[0, 25.5], title="Score (P×I)")
    return _layout(fig, dark, title, h)


def category_bars(ra: pd.DataFrame, dark=False, title=None, height=360) -> go.Figure:
    df = ra[ra["type"] == "threat"] if not ra.empty else ra
    fig = go.Figure()
    if not df.empty:
        g = df.groupby("category").agg(inh=("score_inh", "sum"), res=("score_res", "sum"), n=("id", "count")).reset_index()
        g["lab"] = g["category"].map(lambda c: label("category", c))
        g = g.sort_values("inh", ascending=True)
        fig.add_trace(go.Bar(y=g["lab"], x=g["inh"], orientation="h", name=L("Inerente", "Inherent"), marker_color="#94a3b8"))
        fig.add_trace(go.Bar(y=g["lab"], x=g["res"], orientation="h", name=L("Residual", "Residual"), marker_color=TEAL))
        fig.update_layout(barmode="group", legend=dict(orientation="h", y=1.1, x=0))
    fig.update_xaxes(title=L("Exposição agregada (Σ scores)", "Aggregate exposure (Σ scores)"))
    return _layout(fig, dark, title, height)


def donut(values: dict, colours: dict, dark=False, title=None, height=300, centre: str = "") -> go.Figure:
    labs = [k for k, v in values.items() if v]
    vals = [values[k] for k in labs]
    fig = go.Figure(go.Pie(labels=labs, values=vals, hole=0.62, marker=dict(colors=[colours.get(k, GREY) for k in labs]),
                           textinfo="value", sort=False))
    if centre:
        fig.add_annotation(text=centre, x=0.5, y=0.5, showarrow=False, font=dict(size=18))
    fig.update_layout(legend=dict(orientation="h", y=-0.1))
    return _layout(fig, dark, title, height)


def bowtie(risk: dict, controls: pd.DataFrame, dark=False, height=560) -> go.Figure:
    """Bow-tie: causes → preventive barriers → EVENT → mitigating barriers → consequences."""
    fg = "#e6f1f5" if dark else "#0f172a"
    causes = [c.strip() for c in str(risk.get("cause") or "").split(";") if c.strip()] or [L("(causa não definida)", "(cause not defined)")]
    cons = [c.strip() for c in str(risk.get("effect") or "").split(";") if c.strip()] or [L("(consequência não definida)", "(consequence not defined)")]
    rid = str(risk.get("id")).upper()
    linked = controls[controls["risk_ids"].apply(lambda s: rid in ids_list(s))] if not controls.empty else controls
    prev = linked[linked["control_type"].isin(["preventive", "directive"])].to_dict(orient="records") if not linked.empty else []
    mit = linked[linked["control_type"].isin(["detective", "corrective"])].to_dict(orient="records") if not linked.empty else []

    fig = go.Figure()

    def ys(n):
        return [0.5] if n == 1 else list(np.linspace(0.92, 0.08, n))

    def box(x, y, text, fill, w=0.15, h=0.07, font_col=NAVY, size=11):
        fig.add_shape(type="rect", x0=x - w / 2, x1=x + w / 2, y0=y - h / 2, y1=y + h / 2,
                      line=dict(color="rgba(255,255,255,0.5)", width=1), fillcolor=fill, layer="above")
        fig.add_annotation(x=x, y=y, text="<br>".join(textwrap.wrap(text, 24, break_long_words=False)[:3]), showarrow=False,
                           font=dict(size=size, color=font_col))

    def line(x0, y0, x1, y1):
        fig.add_shape(type="line", x0=x0, y0=y0, x1=x1, y1=y1, line=dict(color="#94a3b8", width=1.5), layer="below")

    # barrier "walls"
    for x0, x1 in ((0.195, 0.345), (0.655, 0.805)):
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=0.02, y1=0.98, fillcolor="rgba(42,120,214,0.06)",
                      line=dict(color="rgba(42,120,214,0.35)", width=1, dash="dot"), layer="below")
    # knot
    fig.add_shape(type="path", path="M 0.395 0.5 L 0.5 0.66 L 0.605 0.5 L 0.5 0.34 Z", fillcolor="#f97316",
                  line=dict(color="white", width=1.5))
    ev = textwrap.wrap(str(risk.get("event") or risk.get("title") or rid), 18, break_long_words=False)
    fig.add_annotation(x=0.5, y=0.5, text="<b>" + "<br>".join(ev[:4]) + ("…" if len(ev) > 4 else "") + "</b>",
                       showarrow=False, font=dict(size=11, color=NAVY))
    fig.add_annotation(x=0.5, y=0.71, text=f"<b>{rid}</b> · {L('Evento de risco', 'Risk event')}", showarrow=False, font=dict(color=fg, size=12))

    for x, t in [(0.08, L("CAUSAS / AMEAÇAS", "CAUSES / THREATS")), (0.27, L("BARREIRAS PREVENTIVAS", "PREVENTIVE BARRIERS")),
                 (0.73, L("BARREIRAS DE MITIGAÇÃO", "MITIGATING BARRIERS")), (0.92, L("CONSEQUÊNCIAS", "CONSEQUENCES"))]:
        fig.add_annotation(x=x, y=1.03, text=f"<b>{t}</b>", showarrow=False, font=dict(color=TEAL, size=11))

    for y in ys(len(causes)):
        line(0.15, y, 0.395, 0.5)
    for y in ys(len(cons)):
        line(0.605, 0.5, 0.85, y)
    for c, y in zip(causes, ys(len(causes))):
        box(0.08, y, c, "#fde68a")
    for c, y in zip(cons, ys(len(cons))):
        box(0.92, y, c, "#fecaca")
    if prev:
        for c, y in zip(prev, ys(len(prev))):
            box(0.27, y, f"{c['id']} {c.get('name','')}", CONCL_COL.get(c.get("conclusion", "not_tested"), GREY), w=0.14, size=10)
    else:
        box(0.27, 0.5, L("⚠ Sem barreiras preventivas", "⚠ No preventive barriers"), "#334155" if dark else "#e2e8f0", w=0.14,
            font_col=fg, size=10)
    if mit:
        for c, y in zip(mit, ys(len(mit))):
            box(0.73, y, f"{c['id']} {c.get('name','')}", CONCL_COL.get(c.get("conclusion", "not_tested"), GREY), w=0.14, size=10)
    else:
        box(0.73, 0.5, L("⚠ Sem barreiras de mitigação", "⚠ No mitigating barriers"), "#334155" if dark else "#e2e8f0", w=0.14,
            font_col=fg, size=10)
    fig.update_xaxes(visible=False, range=[0, 1])
    fig.update_yaxes(visible=False, range=[0, 1.07])
    return _layout(fig, dark, None, height)


def gantt(acts: pd.DataFrame, dark=False, title=None) -> go.Figure:
    df = acts.dropna(subset=["start", "due"]) if not acts.empty else acts
    fig = go.Figure()
    col = {"not_started": "#94a3b8", "in_progress": "#3b82f6", "done": "#22c55e", "cancelled": "#475569"}
    if not df.empty:
        df = df.sort_values("start", ascending=False)
        for r in df.to_dict(orient="records"):
            s, e = pd.to_datetime(r["start"]), pd.to_datetime(r["due"])
            c = "#ef4444" if r.get("overdue") else col.get(r.get("status"), GREY)
            lab = f"{r['id']} · {textwrap.shorten(str(r.get('description','')), 40)}"
            fig.add_trace(go.Bar(y=[lab], x=[(e - s).days or 1], base=[s], orientation="h", marker_color=c,
                                 showlegend=False, text=[f"{r.get('progress', 0)}%"], textposition="inside",
                                 hovertemplate=f"<b>{r['id']}</b> ({r.get('risk_id','')})<br>{r.get('description','')}<br>"
                                               f"{r['start']} → {r['due']}<br>{label('action_status', r.get('status'))}<extra></extra>"))
        today = pd.Timestamp.today().normalize()
        fig.add_shape(type="line", x0=today, x1=today, y0=0, y1=1, yref="paper", line=dict(color=TEAL, dash="dot", width=2))
        fig.add_annotation(x=today, y=1.02, yref="paper", text=L("Hoje", "Today"), showarrow=False, font=dict(color=TEAL))
        fig.update_xaxes(type="date")
    h = max(260, 30 * (len(df) if not df.empty else 1) + 90)
    return _layout(fig, dark, title, h)


def kri_bullet(row: dict, dark=False) -> go.Figure:
    cur = row.get("current")
    amber, red = row.get("amber"), row.get("red")
    lw = row.get("direction") == "lower_worse"
    vals = [v for v in (cur, amber, red, row.get("previous")) if v is not None and not pd.isna(v)]
    mx = max(vals) * 1.3 if vals else 1
    if lw:
        steps = [dict(range=[0, red], color="#ef4444"), dict(range=[red, amber], color="#eab308"), dict(range=[amber, mx], color="#22c55e")]
    else:
        steps = [dict(range=[0, amber], color="#22c55e"), dict(range=[amber, red], color="#eab308"), dict(range=[red, mx], color="#ef4444")]
    fig = go.Figure(go.Indicator(
        mode="number+gauge+delta", value=cur if cur is not None else 0,
        delta=dict(reference=row.get("previous"), increasing=dict(color="#ef4444" if not lw else "#22c55e"),
                   decreasing=dict(color="#22c55e" if not lw else "#ef4444")) if row.get("previous") is not None and not pd.isna(row.get("previous")) else None,
        number=dict(suffix=f" {row.get('unit') or ''}", font=dict(size=22)),
        gauge=dict(shape="bullet", axis=dict(range=[0, mx]), steps=steps, bar=dict(color=NAVY if not dark else "#f8fafc", thickness=0.35)),
        domain=dict(x=[0.25, 1], y=[0, 1]),
        title=dict(text=f"<b>{row.get('id')}</b><br><span style='font-size:11px'>{textwrap.shorten(str(row.get('name','')), 34)}</span>",
                   font=dict(size=13)),
    ))
    return _layout(fig, dark, None, 110)


def histogram(total_inh: np.ndarray, total_res: np.ndarray | None, st: dict, dark=False, cur="€", title=None) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=total_inh, nbinsx=70, name=L("Inerente", "Inherent"), marker_color="rgba(148,163,184,0.65)"))
    if total_res is not None:
        fig.add_trace(go.Histogram(x=total_res, nbinsx=70, name=L("Residual", "Residual"), marker_color="rgba(42,120,214,0.6)"))
    fig.update_layout(barmode="overlay", legend=dict(orientation="v", y=0.98, x=0.98, xanchor="right", yanchor="top"))
    for k, c, n in [("p50", "#eab308", "P50"), ("p80", "#f97316", "P80"), ("p95", "#ef4444", "VaR95")]:
        if k in st:
            fig.add_vline(x=st[k], line=dict(color=c, dash="dash", width=2), annotation_text=f"{n}", annotation_position="top")
    fig.update_xaxes(title=L(f"Perda líquida anual ({cur})", f"Net annual loss ({cur})"))
    fig.update_yaxes(title=L("Frequência", "Frequency"))
    return _layout(fig, dark, title, 400)


def s_curve(total_inh: np.ndarray, total_res: np.ndarray | None, dark=False, cur="€", title=None) -> go.Figure:
    fig = go.Figure()
    for arr, name, col in [(total_inh, L("Inerente", "Inherent"), "#94a3b8"), (total_res, L("Residual", "Residual"), TEAL)]:
        if arr is None:
            continue
        xs = np.sort(arr)
        ys = np.arange(1, len(xs) + 1) / len(xs)
        step = max(1, len(xs) // 400)
        fig.add_trace(go.Scatter(x=xs[::step], y=ys[::step], mode="lines", name=name, line=dict(color=col, width=3)))
    fig.add_hline(y=0.8, line=dict(dash="dot", color="#f97316"), annotation_text="P80")
    fig.update_yaxes(tickformat=".0%", title=L("Probabilidade acumulada", "Cumulative probability"))
    fig.update_xaxes(title=cur)
    fig.update_layout(legend=dict(orientation="h", y=1.08, x=0))
    return _layout(fig, dark, title, 380)


def tornado(sens: pd.DataFrame, dark=False, title=None, top=12) -> go.Figure:
    df = sens.head(top).iloc[::-1]
    fig = go.Figure(go.Bar(y=[f"{i} · {textwrap.shorten(str(t), 34)}" for i, t in zip(df["id"], df["title"])], x=df["corr"],
                           orientation="h", marker_color=[("#ef4444" if v > 0 else "#3b82f6") for v in df["corr"]],
                           text=[f"{v:.2f}" for v in df["corr"]], textposition="outside"))
    fig.update_xaxes(range=[-1, 1], title=L("Correlação de Spearman com o total", "Spearman correlation with total"))
    return _layout(fig, dark, title, max(300, 30 * len(df) + 80))


def exceedance(curves: dict[str, pd.DataFrame], dark=False, cur="€", title=None, capacity=None) -> go.Figure:
    fig = go.Figure()
    cols = ["#f97316", TEAL, "#a78bfa", "#f43f5e", "#22c55e"]
    for (name, df), c in zip(curves.items(), cols):
        fig.add_trace(go.Scatter(x=df["loss"], y=df["prob"], mode="lines", name=name, line=dict(width=3, color=c)))
    if capacity:
        fig.add_vline(x=capacity, line=dict(color="#ef4444", dash="dash"), annotation_text=L("Capacidade", "Capacity"))
    fig.update_yaxes(tickformat=".0%", title=L("P(perda > x)", "P(loss > x)"))
    fig.update_xaxes(title=cur)
    fig.update_layout(legend=dict(orientation="h", y=1.08, x=0))
    return _layout(fig, dark, title, 380)


def radar(m: pd.DataFrame, names: list[str], dark=False, title=None) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=list(m["target"]) + [m["target"].iloc[0]], theta=names + [names[0]], name=L("Alvo", "Target"),
                                  line=dict(color="#a78bfa", dash="dash")))
    fig.add_trace(go.Scatterpolar(r=list(m["current"]) + [m["current"].iloc[0]], theta=names + [names[0]], name=L("Atual", "Current"),
                                  fill="toself", line=dict(color=TEAL), fillcolor="rgba(42,120,214,0.22)"))
    fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(range=[0, 5], dtick=1)),
                      legend=dict(orientation="h", y=-0.08))
    return _layout(fig, dark, title, 480)


def pareto(f: pd.DataFrame, dark=False, title=None) -> go.Figure:
    df = f.sort_values("rpn", ascending=False)
    cum = df["rpn"].cumsum() / df["rpn"].sum() if df["rpn"].sum() else df["rpn"] * 0
    col = {"H": "#ef4444", "M": "#eab308", "L": "#22c55e"}
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["id"], y=df["rpn"], marker_color=[col.get(a, GREY) for a in df["ap"]], name="RPN",
                         customdata=df["failure_mode"], hovertemplate="%{x}: %{customdata}<br>RPN %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=df["id"], y=cum, yaxis="y2", name=L("% acumulada", "Cumulative %"), line=dict(color=TEAL, width=3)))
    fig.update_layout(yaxis2=dict(overlaying="y", side="right", tickformat=".0%", range=[0, 1.05], showgrid=False),
                      legend=dict(orientation="h", y=1.1, x=0))
    return _layout(fig, dark, title, 380)


def chain_bar(ca: pd.DataFrame, dark=False, title=None) -> go.Figure:
    steps = ["risk", "objective", "control", "evidence", "testing", "conclusion", "action"]
    names = {
        "risk": L("1 Risco", "1 Risk"), "objective": L("2 Objetivo", "2 Objective"), "control": L("3 Controlo", "3 Control"),
        "evidence": L("4 Evidência", "4 Evidence"), "testing": L("5 Teste", "5 Testing"),
        "conclusion": L("6 Conclusão", "6 Conclusion"), "action": L("7 Ação", "7 Action"),
    }
    vals = [float(np.mean([s[k] for s in ca["chain_steps"]])) if not ca.empty else 0 for k in steps]
    fig = go.Figure(go.Bar(x=[names[k] for k in steps], y=vals, marker_color=[TEAL if v >= 0.8 else ("#eab308" if v >= 0.5 else "#ef4444") for v in vals],
                           text=[f"{v:.0%}" for v in vals], textposition="outside"))
    fig.update_yaxes(range=[0, 1.15], tickformat=".0%")
    return _layout(fig, dark, title, 320)
