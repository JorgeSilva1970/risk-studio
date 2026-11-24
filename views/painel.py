import streamlit as st

from core import charts, scoring
from core.catalogs import INDUSTRIES, label
from core.i18n import L, tr
from core.report import narrative
from core.ui import hero, kpi, note, pct, proj

p = proj()
m = p["meta"]
hero(m.get("name", "Risk Studio"),
     f"{m.get('organisation') or ''} · {tr(INDUSTRIES.get(m.get('industry'), ('', '')))} · {m.get('scope') or ''}", "🛡️", help_key="dashboard")

if st.session_state.get("example_loaded"):
    st.info(L("Está a ver um **projeto-exemplo (Seguros)**. Explore livremente; para começar o seu, vá a **Dados & templates** "
              "(projeto em branco, template Excel ou outros exemplos por indústria).",
              "You are viewing an **example project (Insurance)**. Explore freely; to start your own go to **Data & templates** "
              "(blank project, Excel template or other industry examples)."), icon="💡")

k = scoring.kpis(p)
ra = scoring.analyse_risks(p)
ca = scoring.analyse_controls(p)

c = st.columns(6)
kpi(c[0], L("Riscos", "Risks"), f"{k['n_risks']}", L(f"{k['n_threats']} ameaças · {k['n_opps']} oportunidades", f"{k['n_threats']} threats · {k['n_opps']} opportunities"))
kpi(c[1], L("Críticos", "Critical"), f"{k['critical_inh']} → {k['critical_res']}", L("inerente → residual", "inherent → residual"), "#ef4444")
kpi(c[2], L("Fora da tolerância", "Outside tolerance"), f"{k['outside']}", L(f"{k['above_appetite']} acima do apetite", f"{k['above_appetite']} above appetite"),
    "#ef4444" if k["outside"] else "#22c55e")
kpi(c[3], L("Redução pelos controlos", "Reduction by controls"), pct(k["reduction"]), L(f"média {k['avg_inh']:.1f} → {k['avg_res']:.1f}".replace(".", ","), f"avg {k['avg_inh']:.1f} → {k['avg_res']:.1f}"))
kpi(c[4], L("Cobertura de controlos", "Control coverage"), pct(k["coverage"]), L(f"{k['no_controls']} riscos sem controlo", f"{k['no_controls']} risks uncovered"),
    "#eab308" if k["no_controls"] else "#22c55e")
kpi(c[5], L("Ações / KRIs", "Actions / KRIs"), f"{k['overdue']} ⏰ · {k['kri_red']} 🔴", L(f"{k['n_actions']} ações · {k['n_kris']} KRIs", f"{k['n_actions']} actions · {k['n_kris']} KRIs"),
    "#ef4444" if (k["overdue"] or k["kri_red"]) else "#2a78d6")

st.write("")
left, right = st.columns([1.05, 1])
with left:
    st.subheader(L("Matriz residual", "Residual matrix"))
    if ra.empty:
        st.caption(L("Sem riscos.", "No risks."))
    else:
        st.plotly_chart(charts.heatmap(ra, "res", height=430), width="stretch")
with right:
    st.subheader(L("Leitura interpretativa", "Interpretation"))
    for t in narrative(p):
        st.markdown(f"- {t}")

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.subheader(L("Top riscos por prioridade", "Top risks by priority"))
    if not ra.empty:
        top = ra[ra["type"] == "threat"].sort_values("priority", ascending=False).head(8).copy()
        top["Nível"] = top["level_res"]
        top["Apetite"] = top["appetite_status"].map(scoring.appetite_label)
        st.dataframe(top[["id", "title", "owner", "score_inh", "score_res", "priority", "Apetite"]].rename(columns={
            "id": "ID", "title": L("Risco", "Risk"), "owner": L("Responsável", "Owner"), "score_inh": L("Inerente", "Inherent"),
            "score_res": L("Residual", "Residual"), "priority": L("Prioridade", "Priority"), "Apetite": L("Apetite", "Appetite")}),
            hide_index=True, width="stretch",
            column_config={L("Residual", "Residual"): st.column_config.ProgressColumn(min_value=0, max_value=25, format="%d")})
with c2:
    st.subheader(L("Exposição por categoria", "Exposure by category"))
    if not ra.empty:
        st.plotly_chart(charts.category_bars(ra, height=340), width="stretch")

c1, c2, c3 = st.columns(3)
with c1:
    vals = {L("Eficaz", "Effective"): int((ca["conclusion"] == "effective").sum()) if not ca.empty else 0,
            L("Parcial", "Partial"): int((ca["conclusion"] == "partial").sum()) if not ca.empty else 0,
            L("Ineficaz", "Ineffective"): int((ca["conclusion"] == "ineffective").sum()) if not ca.empty else 0,
            L("Não testado", "Not tested"): int((ca["conclusion"] == "not_tested").sum()) if not ca.empty else 0}
    cols = dict(zip(vals, ["#22c55e", "#eab308", "#ef4444", "#94a3b8"]))
    st.plotly_chart(charts.donut(vals, cols, title=L("Eficácia dos controlos", "Control effectiveness"), centre=f"{len(ca)}"),
                    width="stretch")
with c2:
    thr = ra[ra["type"] == "threat"] if not ra.empty else ra
    vals = {scoring.appetite_label(s): int((thr["appetite_status"] == s).sum()) if not thr.empty else 0 for s in ["within", "tolerance", "outside"]}
    cols = dict(zip(vals, ["#22c55e", "#eab308", "#ef4444"]))
    st.plotly_chart(charts.donut(vals, cols, title=L("Posição face ao apetite", "Position vs appetite"), centre=f"{len(thr)}"),
                    width="stretch")
with c3:
    st.markdown(f"**{L('Cadeia Risco → Ação', 'Risk → Action chain')}**")
    if not ca.empty:
        st.plotly_chart(charts.chain_bar(ca), width="stretch")

from core.ui import ai_assist  # noqa: E402

ai_assist("dashboard", narrative(p))
note(L("Próximo passo sugerido: reveja os riscos <b>fora da tolerância</b> e os <b>riscos sem controlo</b> em <i>Controlos & RCM</i>; "
       "peça ao <i>Agente IA</i> um sumário executivo ou propostas de controlos.",
       "Suggested next step: review risks <b>outside tolerance</b> and <b>uncovered risks</b> in <i>Controls & RCM</i>; "
       "ask the <i>AI Agent</i> for an executive summary or control proposals."))
