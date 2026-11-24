import html

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import interpret as I
from core.ui import interpret_box
from core import ai, charts, scoring
from core.catalogs import label
from core.i18n import L
from core.model import ids_list
from core.ui import hero, kpi, pct, proj, table_editor

p = proj()
hero(L("Controlos & matriz risco-controlo (RCM)", "Controls & risk-control matrix (RCM)"),
     L("Um registo de riscos sem controlos é só meia ferramenta — ligue riscos, reforce controlos, gere impacto real.",
       "A risk register without controls is only half a tool — connect risks, strengthen controls, create real impact."), "🛡️", help_key="controls")

steps = [
    ("⚠️", L("Risco", "Risk"), L("Identificar e avaliar", "Identify and assess")),
    ("🎯", L("Objetivo de controlo", "Control objective"), L("O que tem de ser alcançado", "What must be achieved")),
    ("🛡️", L("Controlo", "Control"), L("Implementar para gerir o risco", "Implement to manage risk")),
    ("📄", L("Evidência", "Evidence"), L("Recolher e manter", "Collect and maintain")),
    ("🔍", L("Teste", "Testing"), L("Desenho e eficácia", "Design and effectiveness")),
    ("✅", L("Conclusão", "Conclusion"), L("Eficácia e risco residual", "Effectiveness and residual risk")),
    ("➡️", L("Ação", "Action"), L("Fechar lacunas e melhorar", "Close gaps and improve")),
]
st.markdown("<div class='rs-chain'>" + "".join(
    f"<div class='rs-step'><span class='n'>{i}</span><div style='font-size:1.4rem'>{ic}</div><div class='t'>{t}</div><div class='d'>{d}</div></div>"
    for i, (ic, t, d) in enumerate(steps, 1)) + "</div>", unsafe_allow_html=True)

ca = scoring.analyse_controls(p)
cov = scoring.coverage(p)
k = scoring.kpis(p)
c = st.columns(5)
kpi(c[0], L("Controlos", "Controls"), str(len(ca)))
kpi(c[1], L("Cobertura das ameaças", "Threat coverage"), pct(cov["coverage_pct"]), L(f"{len(cov['risks_no_controls'])} sem controlo", f"{len(cov['risks_no_controls'])} uncovered"),
    "#ef4444" if len(cov["risks_no_controls"]) else "#22c55e")
kpi(c[2], L("Controlos mapeados", "Mapped controls"), pct(cov["mapped_pct"]), L(f"{len(cov['controls_orphan'])} órfãos", f"{len(cov['controls_orphan'])} orphans"),
    "#eab308" if len(cov["controls_orphan"]) else "#22c55e")
kpi(c[3], L("Controlos testados", "Controls tested"), pct(cov["tested_pct"]), L(f"{len(cov['controls_untested'])} por testar", f"{len(cov['controls_untested'])} untested"))
kpi(c[4], L("Cadeia completa (média)", "Chain completeness (avg)"), pct(cov["chain_avg"]))
st.write("")
interpret_box(I.controls(p))
from core.ui import ai_assist  # noqa: E402
ai_assist("controls", I.controls(p))

t1, t2, t3, t4, t5 = st.tabs([L("① Desenho dos controlos", "① Control design"), L("② Evidência & testes", "② Evidence & testing"),
                              L("③ Lacunas de cobertura", "③ Coverage gaps"), L("④ Matriz RCM", "④ RCM matrix"),
                              L("⑤ Cadeia por controlo", "⑤ Chain per control")])

comp_cfg = {
    "concl": st.column_config.TextColumn(L("Conclusão", "Conclusion"), disabled=True),
    "eff": st.column_config.ProgressColumn(L("Eficácia", "Effectiveness"), min_value=0, max_value=1, format="percent"),
    "chain_c": st.column_config.ProgressColumn(L("Cadeia", "Chain"), min_value=0, max_value=1, format="percent"),
}
with t1:
    comp = None
    if not ca.empty:
        comp = pd.DataFrame({"eff": ca["effectiveness"], "chain_c": ca["chain"]})
    table_editor("controls", ["id", "name", "objective", "description", "risk_ids", "control_type", "nature", "frequency", "line",
                              "owner", "cost"], computed=comp, computed_cfg=comp_cfg, height=min(600, 38 * (len(p["controls"]) + 3)),
                 key_suffix="a", help_text=L("Preventivos reduzem a probabilidade; detetivos e corretivos reduzem o impacto; diretivos (políticas, formação) contam a 50%.",
                                             "Preventive controls reduce probability; detective and corrective reduce impact; directive (policies, training) count at 50%."))
with t2:
    comp = None
    if not ca.empty:
        comp = pd.DataFrame({"concl": ca["conclusion"].map(lambda v: label("test", v)), "eff": ca["effectiveness"]})
    table_editor("controls", ["id", "name", "evidence", "design_test", "operating_test", "test_date", "tester", "notes"],
                 computed=comp, computed_cfg=comp_cfg, height=min(600, 38 * (len(p["controls"]) + 3)), key_suffix="b",
                 help_text=L("Teste de desenho (TOD): o controlo, como desenhado, mitiga o risco? Teste de eficácia operacional (TOE): funcionou de forma consistente na amostra do período?",
                             "Test of design (TOD): as designed, does it mitigate the risk? Test of operating effectiveness (TOE): did it operate consistently over the sample period?"))

with t3:
    g1, g2 = cov["risks_no_controls"], cov["controls_orphan"]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='rs-gap red'><h4 style='margin:0'>✖ {L('Riscos sem cobertura de controlo', 'Risks without control coverage')} ({len(g1)})</h4>"
                    f"<div class='sub'>{L('Riscos conhecidos. Sem controlos. Maior exposição.', 'Known risks. No controls. Higher exposure.')}</div></div>",
                    unsafe_allow_html=True)
        if g1.empty:
            st.success(L("Todas as ameaças têm pelo menos um controlo.", "Every threat has at least one control."))
        else:
            st.dataframe(g1[["id", "title", "score_inh", "owner"]].rename(columns={"id": "ID", "title": L("Risco", "Risk"),
                         "score_inh": L("Inerente", "Inherent"), "owner": L("Responsável", "Owner")}), hide_index=True, width="stretch")
            st.caption(L("Riscos não geridos podem gerar problemas maiores. Um registo por si só não reduz o risco.",
                         "Unmanaged risks can lead to bigger problems. A risk register alone doesn't reduce risk."))
    with c2:
        st.markdown(f"<div class='rs-gap amber'><h4 style='margin:0'>? {L('Controlos sem risco claro', 'Controls without a clear risk')} ({len(g2)})</h4>"
                    f"<div class='sub'>{L('Os controlos existem, mas não é claro o que endereçam.', 'Controls exist, but it is unclear what they address.')}</div></div>",
                    unsafe_allow_html=True)
        if g2.empty:
            st.success(L("Todos os controlos estão mapeados para riscos.", "Every control maps to a risk."))
        else:
            st.dataframe(g2[["id", "name", "unknown_ids", "cost"]].rename(columns={"id": "ID", "name": L("Controlo", "Control"),
                         "unknown_ids": L("IDs inexistentes", "Unknown IDs"), "cost": L("Custo", "Cost")}), hide_index=True, width="stretch")
            st.caption(L("Controlos não ligados criam custo, complexidade e incerteza desnecessários. Cada controlo deve mapear para um risco.",
                         "Unlinked controls create unnecessary cost, complexity and uncertainty. Every control should map to a risk."))
    c1, c2 = st.columns(2)
    with c1:
        g3 = cov["controls_ineffective"]
        st.markdown(f"**{L('Controlos ineficazes / parcialmente eficazes', 'Ineffective / partially effective controls')}** ({len(g3)})")
        if not g3.empty:
            st.dataframe(g3[["id", "name", "risk_ids", "has_action"]].assign(conc=g3["conclusion"].map(lambda v: label("test", v)))
                         .rename(columns={"id": "ID", "name": L("Controlo", "Control"), "risk_ids": L("Riscos", "Risks"),
                                          "has_action": L("Tem ação?", "Has action?"), "conc": L("Conclusão", "Conclusion")}),
                         hide_index=True, width="stretch")
    with c2:
        g4 = cov["controls_untested"]
        st.markdown(f"**{L('Controlos por testar', 'Untested controls')}** ({len(g4)})")
        if not g4.empty:
            st.dataframe(g4[["id", "name", "owner"]].rename(columns={"id": "ID", "name": L("Controlo", "Control"), "owner": L("Responsável", "Owner")}),
                         hide_index=True, width="stretch")
    if ai.available() and len(g1):
        st.divider()
        if st.button(L(f"🤖 Pedir ao Agente IA controlos para os {len(g1)} riscos sem cobertura",
                       f"🤖 Ask the AI Agent for controls for the {len(g1)} uncovered risks"), type="primary"):
            with st.spinner(L("O agente está a desenhar controlos…", "The agent is designing controls…")):
                items, err = ai.structured(p, "controls", ai.prompt_controls(list(g1["id"])))
            if err:
                st.error(err)
            else:
                st.session_state["ai_preview"] = {"kind": "controls", "items": items}
                st.switch_page("views/agente.py")

with t4:
    ra = scoring.analyse_risks(p)
    if ra.empty or ca.empty:
        st.info(L("Precisa de riscos e controlos.", "You need risks and controls."))
    else:
        rids = list(ra["id"])
        cids = list(ca["id"])
        z = np.full((len(rids), len(cids)), np.nan)
        for j, crow in enumerate(ca.to_dict(orient="records")):
            for rid in ids_list(crow["risk_ids"]):
                if rid in rids:
                    z[rids.index(rid), j] = crow["effectiveness"]
        txt = [[("" if np.isnan(v) else f"{v:.0%}") for v in row] for row in z]
        fig = go.Figure(go.Heatmap(z=z, x=[f"{c}" for c in cids], y=[f"{r} {t[:28]}" for r, t in zip(rids, ra["title"])], text=txt,
                                   texttemplate="%{text}", colorscale=[[0, "#ef4444"], [0.4, "#eab308"], [1, "#22c55e"]], zmin=0, zmax=0.8,
                                   xgap=2, ygap=2, colorbar=dict(title=L("Eficácia", "Effect."), tickformat=".0%"),
                                   hovertemplate="%{y} ↔ %{x}: %{text}<extra></extra>"))
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(charts._layout(fig, True, L("Matriz Risco × Controlo (eficácia)", "Risk × Control matrix (effectiveness)"),
                                       max(360, 30 * len(rids) + 120)), width="stretch")
        st.caption(L("Linhas vazias = riscos sem controlo · colunas vazias = controlos sem risco.",
                     "Empty rows = risks without controls · empty columns = controls without a risk."))

with t5:
    if ca.empty:
        st.info(L("Sem controlos.", "No controls."))
    else:
        st.plotly_chart(charts.chain_bar(ca, title=L("Completude de cada etapa", "Completeness of each step")), width="stretch")
        names = ["risk", "objective", "control", "evidence", "testing", "conclusion", "action"]
        heads = [L("Risco", "Risk"), L("Objetivo", "Objective"), L("Controlo", "Control"), L("Evidência", "Evidence"),
                 L("Teste", "Testing"), L("Conclusão", "Conclusion"), L("Ação", "Action")]
        rows = []
        for crow in ca.to_dict(orient="records"):
            r = {"ID": crow["id"], L("Controlo", "Control"): crow["name"]}
            for n, h in zip(names, heads):
                r[h] = "✅" if crow["chain_steps"][n] else "❌"
            r["%"] = crow["chain"]
            rows.append(r)
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
                     column_config={"%": st.column_config.ProgressColumn(min_value=0, max_value=1, format="percent")})
        st.caption(L("Teste ✅ = desenho e eficácia testados; Conclusão ✅ = teste datado; Ação ✅ = controlo eficaz ou com ação de melhoria.",
                     "Testing ✅ = design and operation tested; Conclusion ✅ = dated test; Action ✅ = effective control or with an improvement action."))
