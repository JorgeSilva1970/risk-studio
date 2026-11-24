import streamlit as st

from core import interpret as I
from core.ui import interpret_box
from core import ai, charts, scoring
from core.i18n import L
from core.ui import hero, note, proj

p = proj()
hero(L("Matrizes de risco & priorização", "Risk matrices & prioritisation"),
     L("Inerente → residual → alvo · dupla matriz ameaças/oportunidades · velocidade e proximidade",
       "Inherent → residual → target · double threat/opportunity matrix · velocity and proximity"), "🔥", help_key="matrix")

ra = scoring.analyse_risks(p)
if ra.empty:
    st.info(L("Adicione riscos no Registo para ver as matrizes.", "Add risks in the Register to see the matrices."))
    st.stop()

t1, t2, t3, t4 = st.tabs([L("Heatmaps 5×5", "5×5 heatmaps"), L("Movimento do risco", "Risk movement"),
                          L("Prioridade (velocidade)", "Priority (velocity)"), L("Apetite", "Appetite")])
with t1:
    c1, c2, c3 = st.columns(3)
    c1.plotly_chart(charts.heatmap(ra, "inh", title=L("Inerente (sem controlos)", "Inherent (no controls)"), height=420), width="stretch")
    c2.plotly_chart(charts.heatmap(ra, "res", title=L("Residual (controlos atuais)", "Residual (current controls)"), height=420), width="stretch")
    c3.plotly_chart(charts.heatmap(ra, "tgt", title=L("Alvo (após tratamento)", "Target (after treatment)"), height=420), width="stretch")
    if (ra["type"] == "opportunity").any():
        st.markdown(f"#### {L('Dupla matriz P-I (Hillson): oportunidades', 'Double P-I matrix (Hillson): opportunities')}")
        c1, c2 = st.columns(2)
        c1.plotly_chart(charts.heatmap(ra, "inh", opportunity=True, title=L("Oportunidades — atual", "Opportunities — current"), height=380),
                        width="stretch")
        c2.plotly_chart(charts.heatmap(ra, "tgt", opportunity=True, title=L("Oportunidades — alvo", "Opportunities — target"), height=380),
                        width="stretch")
    st.caption(L("🟢 1–4 Baixo · 🟡 5–9 Moderado · 🟠 10–14 Elevado · 🔴 15–25 Crítico. Oportunidades em tons de azul (quanto mais escuro, mais valiosa).",
                 "🟢 1–4 Low · 🟡 5–9 Moderate · 🟠 10–14 High · 🔴 15–25 Critical. Opportunities in blue shades (darker = more valuable)."))
with t2:
    st.plotly_chart(charts.movement(ra, title=L("Do inerente (○) ao residual (●)", "From inherent (○) to residual (●)"), height=520),
                    width="stretch")
    note(L("Cada seta mostra o efeito dos controlos: setas longas = controlos eficazes; pontos sem seta = risco sem controlos "
           "ou com controlos não testados/ineficazes.",
           "Each arrow shows the effect of controls: long arrows = effective controls; dots without arrows = risk without controls "
           "or with untested/ineffective controls."))
with t3:
    st.plotly_chart(charts.priority_bubble(ra, title=L("Score residual × velocidade (tamanho = prioridade)", "Residual score × velocity (size = priority)")),
                    width="stretch")
    top = ra[ra["type"] == "threat"].sort_values("priority", ascending=False)
    st.dataframe(top[["id", "title", "score_res", "velocity", "proximity", "priority"]].rename(columns={
        "id": "ID", "title": L("Risco", "Risk"), "score_res": L("Residual", "Residual"), "velocity": L("Velocidade", "Velocity"),
        "proximity": L("Proximidade", "Proximity"), "priority": L("Prioridade", "Priority")}), hide_index=True, width="stretch")
with t4:
    st.plotly_chart(charts.appetite_bars(ra, title=L("Residual vs. apetite (linha verde) e tolerância (linha vermelha)",
                                                     "Residual vs appetite (green line) and tolerance (red line)")), width="stretch")

interpret_box(I.matrix(p))

from core.ui import ai_assist  # noqa: E402

ai_assist("matrix", I.matrix(p), ra[["id", "title", "type", "category", "score_inh", "score_res", "score_tgt", "appetite", "tolerance",
                                     "appetite_status", "velocity", "priority", "controls"]].to_string(index=False))
