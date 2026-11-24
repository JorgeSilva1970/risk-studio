import pandas as pd
import streamlit as st

from core import ai, charts, montecarlo as mc, scoring
from core.i18n import L
from core.ui import hero, interpret_box, kpi, money, note, pct, proj, table_editor

p = proj()
cur = p["meta"].get("currency", "€")
cap = p["meta"].get("risk_capacity")
hero(L("Quantificação: Monte Carlo & FAIR", "Quantification: Monte Carlo & FAIR"),
     L("Distribuição da perda anual, P80/VaR/CVaR, sensibilidade e curvas de excedência",
       "Annual loss distribution, P80/VaR/CVaR, sensitivity and loss exceedance curves"), "🎲", help_key="quant")

t1, t2 = st.tabs([L("Monte Carlo do registo", "Register Monte Carlo"), L("FAIR (ciber / eventos de perda)", "FAIR (cyber / loss events)")])

with t1:
    ra = scoring.analyse_risks(p)
    inp = mc.build_inputs(ra, p["meta"]["impact_thresholds"]) if not ra.empty else pd.DataFrame()
    if inp.empty:
        st.info(L("Sem riscos abertos para simular.", "No open risks to simulate."))
    else:
        note(L("Cada risco é modelado como <b>ocorrência Bernoulli</b> (probabilidade anual) × <b>impacto PERT</b> (mín., + provável, máx.). "
               "A <b>correlação ρ</b> (cópula gaussiana) representa riscos que tendem a materializar-se em conjunto (ex.: crise). "
               "O cenário residual reduz probabilidade e impacto de acordo com a eficácia dos controlos. Oportunidades entram como ganhos (negativos).",
               "Each risk is modelled as a <b>Bernoulli occurrence</b> (annual probability) × <b>PERT impact</b> (min, most likely, max). "
               "The <b>correlation ρ</b> (Gaussian copula) captures risks that tend to materialise together (e.g. a crisis). "
               "The residual scenario reduces probability and impact according to control effectiveness. Opportunities enter as gains (negative)."))
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        n = c1.select_slider(L("Iterações", "Iterations"), [1000, 5000, 10000, 20000, 50000], value=10000)
        rho = c2.slider(L("Correlação ρ", "Correlation ρ"), 0.0, 0.9, 0.2, 0.05)
        seed = c3.number_input("Seed", 0, 99999, 42)
        incl_opp = c4.toggle(L("Incluir oportunidades", "Include opportunities"), True)
        data = inp if incl_opp else inp[inp["type"] == "threat"]
        if data.empty:
            st.stop()
        with st.spinner(L("A simular…", "Simulating…")):
            ti, mi = mc.simulate(data, n, rho, seed)
            tr, mr = mc.simulate(data, n, rho, seed, residual=True)
        si, sr = mc.stats(ti, cap), mc.stats(tr, cap)
        st.session_state["mc_settings"] = {"n": n, "rho": rho}
        c = st.columns(6)
        kpi(c[0], L("Perda esperada", "Expected loss"), money(sr["mean"]), L(f"inerente {money(si['mean'])}", f"inherent {money(si['mean'])}"))
        kpi(c[1], "P50", money(sr["p50"]), L(f"inerente {money(si['p50'])}", f"inherent {money(si['p50'])}"))
        kpi(c[2], L("P80 · contingência", "P80 · contingency"), money(sr["p80"]), L(f"inerente {money(si['p80'])}", f"inherent {money(si['p80'])}"), "#f97316")
        kpi(c[3], "VaR 95%", money(sr["p95"]), L(f"inerente {money(si['p95'])}", f"inherent {money(si['p95'])}"), "#ef4444")
        kpi(c[4], "CVaR 95%", money(sr["cvar95"]), L("média dos 5% piores anos", "mean of worst 5% years"), "#ef4444")
        kpi(c[5], L("P(perda > capacidade)", "P(loss > capacity)"), pct(sr.get("p_exceed_capacity", 0), 1),
            L(f"capacidade {money(cap)}", f"capacity {money(cap)}"), "#ef4444" if sr.get("p_exceed_capacity", 0) > 0.05 else "#22c55e")
        st.write("")
        c1, c2 = st.columns(2)
        c1.plotly_chart(charts.histogram(ti, tr, sr, cur=cur, title=L("Distribuição da perda líquida anual", "Net annual loss distribution")),
                        width="stretch")
        c2.plotly_chart(charts.s_curve(ti, tr, cur=cur, title=L("Curva S (probabilidade acumulada)", "S-curve (cumulative probability)")),
                        width="stretch")
        sens = mc.sensitivity(mr, tr, data)
        c1, c2 = st.columns(2)
        c1.plotly_chart(charts.tornado(sens, title=L("Tornado — que riscos mais explicam a variância (residual)", "Tornado — which risks drive variance (residual)")),
                        width="stretch")
        curves = {L("Inerente", "Inherent"): mc.exceedance_curve(ti), L("Residual", "Residual"): mc.exceedance_curve(tr)}
        c2.plotly_chart(charts.exceedance(curves, cur=cur, capacity=cap, title=L("Curva de excedência de perdas (LEC)", "Loss exceedance curve (LEC)")),
                        width="stretch")
        with st.expander(L("Pressupostos por risco", "Per-risk assumptions")):
            show = data[["id", "title", "type", "prob_inh", "prob_res", "lo", "ml", "hi", "k_res", "ev_inh", "ev_res", "source"]].copy()
            st.dataframe(show, hide_index=True, width="stretch", column_config={
                "prob_inh": st.column_config.NumberColumn(L("Prob. inerente", "Inherent prob."), format="percent"),
                "prob_res": st.column_config.NumberColumn(L("Prob. residual", "Residual prob."), format="percent"),
                "lo": st.column_config.NumberColumn(L("Mín.", "Min"), format="localized"),
                "ml": st.column_config.NumberColumn(L("+ Provável", "Most likely"), format="localized"),
                "hi": st.column_config.NumberColumn(L("Máx.", "Max"), format="localized"),
                "k_res": st.column_config.NumberColumn(L("Fator impacto residual", "Residual impact factor"), format="%.2f"),
                "ev_inh": st.column_config.NumberColumn(L("VE inerente", "Inherent EV"), format="localized"),
                "ev_res": st.column_config.NumberColumn(L("VE residual", "Residual EV"), format="localized"),
                "source": st.column_config.TextColumn(L("Fonte", "Source"))})
            st.caption(L("Fonte 'scale' = derivado da escala de impacto do Contexto; 'user' = estimativa de três pontos do Registo.",
                         "Source 'scale' = derived from the Context impact scale; 'user' = three-point estimate from the Register."))
        interp = L(
            f"Com os controlos atuais, a perda líquida anual esperada é **{money(sr['mean'])}** (vs. {money(si['mean'])} sem controlos). "
            f"Para um nível de confiança de 80%, recomenda-se uma **reserva de contingência de {money(sr['p80'])}**. Num ano adverso (1 em 20) "
            f"a perda pode chegar a **{money(sr['p95'])}**, e a média desses anos extremos é **{money(sr['cvar95'])}**. "
            f"A probabilidade de exceder a capacidade de risco é **{pct(sr.get('p_exceed_capacity', 0), 1)}**. "
            f"O risco que mais contribui para a variabilidade é **{sens.iloc[0]['id']} {sens.iloc[0]['title']}**.",
            f"With current controls the expected net annual loss is **{money(sr['mean'])}** (vs {money(si['mean'])} without controls). "
            f"At 80% confidence a **contingency reserve of {money(sr['p80'])}** is recommended. In an adverse year (1 in 20) losses may reach "
            f"**{money(sr['p95'])}**, and the average of those extreme years is **{money(sr['cvar95'])}**. "
            f"The probability of exceeding risk capacity is **{pct(sr.get('p_exceed_capacity', 0), 1)}**. "
            f"The risk contributing most to variability is **{sens.iloc[0]['id']} {sens.iloc[0]['title']}**.")
        interpret_box(interp)
        from core.ui import ai_assist
        ai_assist("quant", [interp.replace("**", "")], f"inerente={si}\nresidual={sr}\ncapacidade={cap}\nrho={rho}\nsensibilidade=\n{sens.head(10).to_string(index=False)}")

with t2:
    note(L("<b>FAIR</b> (Factor Analysis of Information Risk, Open Group): <b>LEF</b> = frequência de eventos de ameaça (TEF/ano) × "
           "<b>vulnerabilidade</b> (prob. de sucesso). Perda por evento = <b>perda primária</b> (resposta, produtividade, substituição) + "
           "<b>perda secundária</b> (coimas, reputação, litígio) com a probabilidade indicada. ALE = perda anualizada.",
           "<b>FAIR</b> (Factor Analysis of Information Risk, Open Group): <b>LEF</b> = threat event frequency (TEF/yr) × "
           "<b>vulnerability</b> (probability of success). Loss per event = <b>primary loss</b> (response, productivity, replacement) + "
           "<b>secondary loss</b> (fines, reputation, litigation) with the given probability. ALE = annualised loss."))
    st.write("")
    table_editor("fair", ["id", "scenario", "asset", "threat", "tef_min", "tef_ml", "tef_max", "vuln_min", "vuln_ml", "vuln_max",
                          "plm_min", "plm_ml", "plm_max", "slef", "slm_min", "slm_ml", "slm_max"])
    if not p["fair"].empty:
        rows, curves = [], {}
        for sc in p["fair"].to_dict(orient="records"):
            r = mc.simulate_fair(sc, 20000)
            s = mc.stats(r["ale"])
            rows.append({"ID": sc["id"], L("Cenário", "Scenario"): sc["scenario"], "LEF": round(float(r["lef"].mean()), 2),
                         L("P(≥1 evento)", "P(≥1 event)"): float((r["events"] > 0).mean()), "ALE": s["mean"], "P90": s["p90"],
                         "P95": s["p95"], "P99": s["p99"]})
            curves[f"{sc['id']} · {str(sc['scenario'])[:28]}"] = mc.exceedance_curve(r["ale"])
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", column_config={
            L("P(≥1 evento)", "P(≥1 event)"): st.column_config.NumberColumn(format="percent"),
            "ALE": st.column_config.NumberColumn(format="localized"), "P90": st.column_config.NumberColumn(format="localized"),
            "P95": st.column_config.NumberColumn(format="localized"), "P99": st.column_config.NumberColumn(format="localized")})
        st.plotly_chart(charts.exceedance(curves, cur=cur, capacity=cap, title=L("Curvas de excedência de perdas (FAIR)", "Loss exceedance curves (FAIR)")),
                        width="stretch")
