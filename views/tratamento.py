import pandas as pd
import streamlit as st

from core import interpret as I
from core.ui import interpret_box
from core import ai, charts, montecarlo as mc, scoring
from core.catalogs import label
from core.i18n import L
from core.ui import hero, kpi, money, note, pct, proj, table_editor

p = proj()
hero(L("Tratamento do risco & plano de ações", "Risk treatment & action plan"),
     L("Ameaças: evitar · mitigar · transferir · aceitar · escalar — Oportunidades: explorar · potenciar · partilhar · aceitar",
       "Threats: avoid · mitigate · transfer · accept · escalate — Opportunities: exploit · enhance · share · accept"), "🛠️", help_key="treatment")

acts = scoring.analyse_actions(p)
k = scoring.kpis(p)
c = st.columns(5)
kpi(c[0], L("Ações", "Actions"), str(k["n_actions"]))
kpi(c[1], L("Concluídas", "Done"), str(k["done"]), colour="#22c55e")
kpi(c[2], L("Em atraso", "Overdue"), str(k["overdue"]), colour="#ef4444" if k["overdue"] else "#22c55e")
kpi(c[3], L("Progresso médio", "Average progress"), f"{acts['progress'].mean():.0f}%" if not acts.empty else "—")
kpi(c[4], L("Custo total do plano", "Total plan cost"), money(acts["cost"].fillna(0).sum()) if not acts.empty else "—")
st.write("")
interpret_box(I.treatment(p))
from core.ui import ai_assist  # noqa: E402
ai_assist("treatment", I.treatment(p))

t1, t2, t3 = st.tabs([L("Plano de ações", "Action plan"), L("Cronograma (Gantt)", "Timeline (Gantt)"),
                      L("Custo-benefício do tratamento", "Treatment cost-benefit")])
with t1:
    comp = None
    if not acts.empty:
        comp = pd.DataFrame({"late": acts["overdue"].map(lambda v: "⏰" if v else "")})
    table_editor("actions", ["id", "risk_id", "control_id", "description", "strategy", "owner", "start", "due", "cost", "status", "progress"],
                 computed=comp, computed_cfg={"late": st.column_config.TextColumn(L("Atraso", "Late"), disabled=True, width="small")},
                 height=min(600, 38 * (len(p["actions"]) + 3)),
                 help_text=L("Ligue cada ação a um risco (R..) e, se aplicável, ao controlo que melhora (C..). Ações SMART: específicas, mensuráveis, com responsável e prazo.",
                             "Link each action to a risk (R..) and, if applicable, to the control it improves (C..). SMART actions: specific, measurable, owned and dated."))
    ra = scoring.analyse_risks(p)
    need = ra[(ra["type"] == "threat") & (ra["appetite_status"].isin(["outside", "tolerance"])) & (ra["n_actions"] == 0)] if not ra.empty else ra
    if not need.empty:
        st.warning(L(f"Riscos acima do apetite sem qualquer ação: {', '.join(need['id'])}",
                     f"Risks above appetite without any action: {', '.join(need['id'])}"), icon="⚠️")
        if ai.available() and st.button(L("🤖 Pedir ao Agente IA um plano para estes riscos", "🤖 Ask the AI Agent for a plan for these risks")):
            with st.spinner(L("A preparar plano…", "Preparing plan…")):
                items, err = ai.structured(p, "actions", ai.prompt_actions(list(need["id"])))
            if err:
                st.error(err)
            else:
                st.session_state["ai_preview"] = {"kind": "actions", "items": items}
                st.switch_page("views/agente.py")

with t2:
    if acts.empty:
        st.info(L("Sem ações.", "No actions."))
    else:
        st.plotly_chart(charts.gantt(acts), width="stretch")
        st.caption(L("Cinza = não iniciada · azul = em curso · verde = concluída · vermelho = em atraso. Linha tracejada = hoje.",
                     "Grey = not started · blue = in progress · green = done · red = overdue. Dotted line = today."))

with t3:
    note(L("Compara a <b>redução da perda esperada anual</b> (inerente − residual, via escalas/estimativas PERT) com o <b>custo anual dos controlos</b> "
           "ligados a cada risco. <b>RORI</b> (Return on Risk Investment) = (redução − custo) / custo. Valores elevados justificam o investimento; "
           "negativos sugerem controlos sobredimensionados ou mal desenhados.",
           "Compares the <b>reduction in annual expected loss</b> (inherent − residual, via scales/PERT estimates) with the <b>annual cost of the "
           "controls</b> linked to each risk. <b>RORI</b> (Return on Risk Investment) = (reduction − cost) / cost. High values justify the investment; "
           "negative ones suggest over-engineered or poorly designed controls."))
    ra = scoring.analyse_risks(p)
    inp = mc.build_inputs(ra, p["meta"]["impact_thresholds"]) if not ra.empty else pd.DataFrame()
    if inp.empty:
        st.info(L("Sem dados.", "No data."))
    else:
        df = inp[inp["type"] == "threat"].merge(ra[["id", "ctrl_cost", "controls"]], on="id")
        df["reduction"] = df["ev_inh"] - df["ev_res"]
        df["rori"] = [(r - c) / c if c else None for r, c in zip(df["reduction"], df["ctrl_cost"])]
        show = df[["id", "title", "controls", "ev_inh", "ev_res", "reduction", "ctrl_cost", "rori"]].sort_values("reduction", ascending=False)
        st.dataframe(show.rename(columns={"id": "ID", "title": L("Risco", "Risk"), "controls": L("Controlos", "Controls"),
                                          "ev_inh": L("Perda esperada inerente", "Inherent expected loss"),
                                          "ev_res": L("Perda esperada residual", "Residual expected loss"),
                                          "reduction": L("Redução", "Reduction"), "ctrl_cost": L("Custo controlos", "Control cost"), "rori": "RORI"}),
                     hide_index=True, width="stretch",
                     column_config={c: st.column_config.NumberColumn(format="localized") for c in
                                    [L("Perda esperada inerente", "Inherent expected loss"), L("Perda esperada residual", "Residual expected loss"),
                                     L("Redução", "Reduction"), L("Custo controlos", "Control cost")]} |
                                   {"RORI": st.column_config.NumberColumn(format="%.1fx")})
        tot_red, tot_cost = df["reduction"].sum(), df["ctrl_cost"].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric(L("Redução total da perda esperada", "Total expected-loss reduction"), money(tot_red))
        c2.metric(L("Custo anual dos controlos", "Annual control cost"), money(tot_cost))
        c3.metric("RORI", f"{(tot_red - tot_cost) / tot_cost:.1f}x" if tot_cost else "—")
