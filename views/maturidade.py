import pandas as pd
import streamlit as st

from core import interpret as I
from core.ui import interpret_box
from core import charts, scoring
from core.catalogs import MATURITY_DIMENSIONS, MATURITY_LEVELS
from core.i18n import L, lang, tr
from core.ui import hero, kpi, note, proj, table_editor

p = proj()
hero(L("Maturidade da gestão de risco (ERM)", "Risk management (ERM) maturity"),
     L("Autoavaliação face à ISO 31000 (princípios e quadro) e COSO ERM (20 princípios em 5 componentes)",
       "Self-assessment against ISO 31000 (principles & framework) and COSO ERM (20 principles in 5 components)"), "🧩", help_key="maturity")

m = p["maturity"]
cur, tgt = scoring.maturity_index(p)
c = st.columns(3)
kpi(c[0], L("Índice atual", "Current index"), f"{cur:.1f} / 5", tr(MATURITY_LEVELS[max(1, min(5, round(cur)))]))
kpi(c[1], L("Índice alvo", "Target index"), f"{tgt:.1f} / 5", tr(MATURITY_LEVELS[max(1, min(5, round(tgt)))]), "#a78bfa")
kpi(c[2], L("Gap médio", "Average gap"), f"{tgt - cur:.1f}", colour="#f97316")
st.write("")
interpret_box(I.maturity(p))
from core.ui import ai_assist  # noqa: E402
ai_assist("maturity", I.maturity(p))

names = {c_: (en if lang() == "en" else pt) for c_, pt, en in MATURITY_DIMENSIONS}
c1, c2 = st.columns([1, 1])
with c1:
    st.plotly_chart(charts.radar(m, [names.get(d, d) for d in m["dim"]], title=L("Atual vs. alvo", "Current vs target")),
                    width="stretch")
with c2:
    st.markdown(f"**{L('Níveis', 'Levels')}**")
    for k_, v in MATURITY_LEVELS.items():
        st.markdown(f"- **{k_}** · {tr(v)}")
    gaps = m.assign(gap=m["target"] - m["current"], name=m["dim"].map(names)).sort_values("gap", ascending=False)
    st.markdown(f"**{L('Maiores gaps (prioridades de desenvolvimento)', 'Largest gaps (development priorities)')}**")
    for r in gaps.head(4).to_dict(orient="records"):
        st.markdown(f"- {r['name']}: {r['current']} → {r['target']} (gap {r['gap']})")

note(L("Classifique cada dimensão de 1 a 5 e registe a evidência que sustenta a classificação (políticas, atas, relatórios, ferramentas).",
       "Rate each dimension from 1 to 5 and record the evidence supporting the rating (policies, minutes, reports, tools)."))
st.write("")
disp = p["maturity"]
comp = pd.DataFrame({"dimname": disp["dim"].map(names)})
table_editor("maturity", ["current", "target", "evidence"], computed=comp, fixed=True, lead_computed=True,
             computed_cfg={"dimname": st.column_config.TextColumn(L("Dimensão", "Dimension"), disabled=True, width="large")})
