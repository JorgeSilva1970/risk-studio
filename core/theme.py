"""Palette and Plotly template shared by the whole app (same family as Gestão Studio / PM Studio)."""
from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
PRIMARY = "#2a78d6"
NAVY = "#0f2a4a"
GOOD, WARN, SERIOUS, CRIT = "#1f9d55", "#eda100", "#eb6834", "#c62828"
TEXT, TEXT2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#ecebe8"
FONT = "Inter, 'Segoe UI', system-ui, -apple-system, sans-serif"

_tpl = go.layout.Template()
_tpl.layout = go.Layout(
    font=dict(family=FONT, size=13, color=TEXT2),
    title=dict(font=dict(size=15, color=TEXT), x=0, xanchor="left"),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=CAT,
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=TEXT2), automargin=True),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=TEXT2), automargin=True),
    hoverlabel=dict(bgcolor="white", font=dict(family=FONT, color=TEXT)),
    bargap=0.25,
)
pio.templates["risk"] = _tpl
pio.templates.default = "plotly_white+risk"

CSS = """
<style>
.block-container {padding-top: 1.8rem; padding-bottom: 3rem; max-width: 1380px;}
[data-testid="stSidebarNav"] span {font-size: 0.92rem;}
div[data-testid="stMetricValue"] {font-size: 1.45rem;}
.rs-hero {padding: 1.1rem 1.4rem; border-radius: 14px; margin-bottom: .9rem;
  background: linear-gradient(135deg,#0f2a4a 0%,#1d5aa6 60%,#2a78d6 100%); color:#fff;}
.rs-hero h1 {color:#fff; margin:0 0 .25rem 0; font-size:1.75rem;}
.rs-hero p {color:#e6eefb; margin:0;}
.rs-kpi {background:#fff; border:1px solid #e6e4df; border-left:5px solid #2a78d6; border-radius:12px; padding:10px 14px; min-height:92px;}
.rs-kpi .v {font-size:1.5rem; font-weight:700; color:#0f2a4a; line-height:1.15;}
.rs-kpi .l {color:#52514e; font-size:.76rem; text-transform:uppercase; letter-spacing:.04em;}
.rs-kpi .s {color:#8a8984; font-size:.78rem; margin-top:2px;}
.rs-chain {display:flex; gap:6px; flex-wrap:wrap; margin:6px 0 12px;}
.rs-step {flex:1 1 120px; background:#f6f9fd; border:1px solid #cfe0f5; border-radius:12px; padding:10px; text-align:center;}
.rs-step .n {display:inline-block; width:24px; height:24px; border-radius:50%; background:#2a78d6; color:#fff; font-weight:800; line-height:24px;}
.rs-step .t {font-weight:700; margin-top:4px; color:#0f2a4a;}
.rs-step .d {color:#52514e; font-size:.78rem;}
.rs-gap {border-radius:12px; padding:12px 14px; margin-bottom:8px;}
.rs-gap.red {background:#fdf2f2; border:1px solid #f3b4b4;}
.rs-gap.amber {background:#fdf8ee; border:1px solid #f0d28f;}
.rs-gap .sub {color:#52514e; font-size:.88rem;}
.rs-pill {display:inline-block; padding:2px 9px; border-radius:999px; font-size:.78rem; font-weight:600; margin:1px 2px;}
.rs-note {border-left:4px solid #2a78d6; background:#f6f9fd; padding:.55rem .8rem; border-radius:6px; color:#1d1d1b; font-size:.9rem;}
.rs-note.warn {border-left-color:#eb6834; background:#fdf6f2;}
.rs-note.good {border-left-color:#1f9d55; background:#f3faf6;}
</style>
"""
