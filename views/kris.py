import datetime as dt

import pandas as pd
import streamlit as st

from core import interpret as I
from core.ui import interpret_box
from core import ai, charts, scoring
from core.catalogs import label
from core.i18n import L
from core.ui import hero, kpi, note, proj, table_editor

p = proj()
hero(L("KRIs & monitorização", "KRIs & monitoring"),
     L("Indicadores-chave de risco com limiares âmbar/vermelho · sinais de alerta precoce (leading indicators)",
       "Key risk indicators with amber/red thresholds · early-warning (leading) indicators"), "📈", help_key="kris")

kr = scoring.analyse_kris(p)
c = st.columns(4)
kpi(c[0], "KRIs", str(len(kr)))
kpi(c[1], L("Vermelho", "Red"), str(int((kr["rag"] == "red").sum())) if not kr.empty else "0", colour="#ef4444")
kpi(c[2], L("Âmbar", "Amber"), str(int((kr["rag"] == "amber").sum())) if not kr.empty else "0", colour="#eab308")
kpi(c[3], L("Verde", "Green"), str(int((kr["rag"] == "green").sum())) if not kr.empty else "0", colour="#22c55e")
st.write("")
interpret_box(I.kris(p))
from core.ui import ai_assist  # noqa: E402
ai_assist("kris", I.kris(p))

t1, t2 = st.tabs([L("Painel de KRIs", "KRI dashboard"), L("Definir / atualizar KRIs", "Define / update KRIs")])
with t1:
    if kr.empty:
        st.info(L("Sem KRIs definidos.", "No KRIs defined."))
    else:
        cols = st.columns(2)
        for i, row in enumerate(kr.to_dict(orient="records")):
            with cols[i % 2]:
                st.plotly_chart(charts.kri_bullet(row), width="stretch", key=f"kri_{row['id']}")
        tbl = kr.copy()
        tbl["RAG"] = tbl["rag"].map({"red": "🔴", "amber": "🟡", "green": "🟢", "na": "⚪"})
        tbl["trend"] = tbl["trend_calc"].map(lambda v: label("trend", v))
        st.dataframe(tbl[["RAG", "id", "risk_id", "name", "previous", "current", "amber", "red", "unit", "trend", "owner"]].rename(columns={
            "id": "ID", "risk_id": L("Risco", "Risk"), "name": "KRI", "previous": L("Anterior", "Previous"), "current": L("Atual", "Current"),
            "amber": L("Âmbar", "Amber"), "red": L("Vermelho", "Red"), "unit": L("Unidade", "Unit"), "trend": L("Tendência", "Trend"),
            "owner": L("Responsável", "Owner")}), hide_index=True, width="stretch")
with t2:
    note(L("Para cada KRI defina o <b>sentido</b> (maior = pior, ex.: n.º de incidentes; menor = pior, ex.: disponibilidade), o limiar "
           "<b>âmbar</b> (alerta) e o <b>vermelho</b> (ação imediata). Atualize o valor atual a cada período — o anterior serve para a tendência.",
           "For each KRI set the <b>direction</b> (higher = worse, e.g. incidents; lower = worse, e.g. availability), the <b>amber</b> "
           "(warning) and <b>red</b> (immediate action) thresholds. Update the current value each period — the previous one drives the trend."))
    st.write("")
    comp = None
    if not kr.empty:
        comp = pd.DataFrame({"rag_i": kr["rag"].map({"red": "🔴", "amber": "🟡", "green": "🟢", "na": "⚪"})})
    table_editor("kris", ["id", "risk_id", "name", "unit", "direction", "amber", "red", "previous", "current", "frequency", "owner"],
                 computed=comp, computed_cfg={"rag_i": st.column_config.TextColumn("RAG", disabled=True, width="small")})
    if ai.available():
        ra = scoring.analyse_risks(p)
        no_kri = [r for r in ra[ra["type"] == "threat"].sort_values("priority", ascending=False)["id"] if r not in set(p["kris"]["risk_id"])][:5] if not ra.empty else []
        if no_kri and st.button(L(f"🤖 Propor KRIs para riscos prioritários sem KRI ({', '.join(no_kri)})",
                                  f"🤖 Propose KRIs for priority risks without KRIs ({', '.join(no_kri)})")):
            with st.spinner(L("A propor KRIs…", "Proposing KRIs…")):
                items, err = ai.structured(p, "kris", ai.prompt_kris(no_kri))
            if err:
                st.error(err)
            else:
                st.session_state["ai_preview"] = {"kind": "kris", "items": items}
                st.switch_page("views/agente.py")

st.caption(L("📈 As revisões periódicas e a comparação passado vs. atual estão em «Evolução & comparação».",
             "📈 Periodic reviews and past-vs-current comparison are in 'Evolution & comparison'."))
