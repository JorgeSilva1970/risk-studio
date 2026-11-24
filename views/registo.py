import pandas as pd
import streamlit as st

from core import scoring
from core.catalogs import label
from core.i18n import L
from core.model import ids_list
from core.ui import hero, money, note, pill, proj, risk_options, table_editor

p = proj()
hero(L("Registo de riscos", "Risk register"),
     L("Ameaças e oportunidades · metalinguagem causa → evento → efeito · inerente, residual e alvo",
       "Threats and opportunities · cause → event → effect metalanguage · inherent, residual and target"), "📋", help_key="register")

note(L("Descreva cada risco com a <b>metalinguagem de Hillson</b>: <i>“Devido a &lt;causa&gt;, pode ocorrer &lt;evento incerto&gt;, "
       "levando a &lt;efeito nos objetivos&gt;”</i>. Inclua também <b>oportunidades</b> (riscos positivos). "
       "O residual é calculado automaticamente a partir dos controlos ligados e testados em <i>Controlos & RCM</i>.",
       "Describe each risk with <b>Hillson's metalanguage</b>: <i>“Because of &lt;cause&gt;, &lt;uncertain event&gt; may occur, "
       "leading to &lt;effect on objectives&gt;”</i>. Include <b>opportunities</b> (upside risks) too. "
       "Residual is computed automatically from the linked, tested controls in <i>Controls & RCM</i>."))
st.write("")

ra = scoring.analyse_risks(p)
comp_cfg = {
    "score_inh": st.column_config.NumberColumn(L("Score inerente", "Inherent score"), disabled=True, width="small"),
    "level_inh": st.column_config.TextColumn(L("Nível inerente", "Inherent level"), disabled=True, width="small"),
    "score_res": st.column_config.NumberColumn(L("Score residual", "Residual score"), disabled=True, width="small"),
    "level_res": st.column_config.TextColumn(L("Nível residual", "Residual level"), disabled=True, width="small"),
    "app": st.column_config.TextColumn(L("Apetite", "Appetite"), disabled=True, width="medium"),
    "controls": st.column_config.TextColumn(L("Controlos", "Controls"), disabled=True, width="small"),
    "priority": st.column_config.NumberColumn(L("Prioridade", "Priority"), disabled=True, width="small"),
}

t1, t2, t3, t4 = st.tabs([L("① Identificação & avaliação", "① Identification & assessment"),
                          L("② Resposta, alvo & residual manual", "② Response, target & residual override"),
                          L("③ Quantificação (€)", "③ Quantification"),
                          L("🔎 Ficha do risco", "🔎 Risk card")])

with t1:
    comp = None
    if not ra.empty:
        comp = pd.DataFrame({"score_inh": ra["score_inh"], "level_inh": ra["level_inh"], "score_res": ra["score_res"],
                             "level_res": ra["level_res"], "app": ra["appetite_status"].map(scoring.appetite_label),
                             "controls": ra["controls"]})
    table_editor("risks", ["id", "type", "category", "title", "cause", "event", "effect", "owner", "objective",
                           "p_inh", "i_inh", "velocity", "proximity"], computed=comp, computed_cfg=comp_cfg,
                 height=min(620, 38 * (len(p["risks"]) + 3)), key_suffix="a")

with t2:
    comp = None
    if not ra.empty:
        comp = pd.DataFrame({"score_res": ra["score_res"], "priority": ra["priority"],
                             "app": ra["appetite_status"].map(scoring.appetite_label)})
    table_editor("risks", ["id", "title", "strategy", "status", "trend", "p_res_ovr", "i_res_ovr", "p_tgt", "i_tgt", "notes"],
                 computed=comp, computed_cfg=comp_cfg, height=min(620, 38 * (len(p["risks"]) + 3)), key_suffix="b",
                 help_text=L("Residual manual: só preencha se discordar do cálculo automático (julgamento do avaliador). "
                             "Alvo: nível pretendido após o plano de tratamento.",
                             "Residual override: fill only if you disagree with the automatic calculation (assessor judgement). "
                             "Target: level intended after the treatment plan."))

with t3:
    table_editor("risks", ["id", "title", "type", "prob_pct", "imp_min", "imp_ml", "imp_max"], height=min(620, 38 * (len(p["risks"]) + 3)),
                 key_suffix="c", help_text=L("Opcional. Estimativas de três pontos (PERT) para o Monte Carlo. Nas oportunidades, o impacto é o ganho. "
                                             "Se vazio, usa o ponto médio das escalas de probabilidade e impacto.",
                                             "Optional. Three-point (PERT) estimates for Monte Carlo. For opportunities the impact is the gain. "
                                             "If blank, scale midpoints are used."))

with t4:
    opts = risk_options()
    if not opts:
        st.info(L("Sem riscos no registo.", "No risks in the register."))
    else:
        rid = st.selectbox(L("Risco", "Risk"), list(opts), format_func=lambda x: opts[x])
        r = ra[ra["id"] == rid].iloc[0].to_dict()
        opp = r["type"] == "opportunity"
        st.markdown(f"### {r['id']} · {r['title']}")
        st.markdown(pill(label("type", r["type"]), "#3b82f6" if opp else "#f97316") + pill(label("category", r["category"]), "#2a78d6") +
                    pill(f"{L('Inerente','Inherent')} {r['score_inh']} · {r['level_inh']}", r["colour_inh"]) +
                    pill(f"{L('Residual','Residual')} {r['score_res']} · {r['level_res']}", r["colour_res"]) +
                    pill(f"{L('Alvo','Target')} {r['score_tgt']}", "#a78bfa") +
                    pill(scoring.appetite_label(r["appetite_status"]), scoring.APPETITE_LABELS[r["appetite_status"]][2]),
                    unsafe_allow_html=True)
        st.markdown(L(f"> **Devido a** {r.get('cause') or '…'}, **pode ocorrer** {r.get('event') or '…'}, **levando a** {r.get('effect') or '…'}.",
                      f"> **Because of** {r.get('cause') or '…'}, **{r.get('event') or '…'}** may occur, **leading to** {r.get('effect') or '…'}."))
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(L("Responsável", "Owner"), r.get("owner") or "—")
        c2.metric(L("Velocidade / proximidade", "Velocity / proximity"), f"{r['velocity']} · {label('proximity', r['proximity'])}")
        c3.metric(L("Eficácia preventiva / mitigação", "Preventive / mitigating effectiveness"), f"{r['e_prev']:.0%} / {r['e_mit']:.0%}")
        c4.metric(L("Estratégia", "Strategy"), label("strategy", r["strategy"]))
        ca = scoring.analyse_controls(p)
        lc = ca[ca["risk_ids"].apply(lambda s: rid in ids_list(s))] if not ca.empty else ca
        st.markdown(f"**{L('Controlos ligados', 'Linked controls')}**")
        if lc.empty:
            st.error(L("Sem controlos ligados — risco sem cobertura.", "No linked controls — risk not covered."), icon="❌") if not opp else st.caption("—")
        else:
            st.dataframe(lc.assign(tp=lc["control_type"].map(lambda v: label("control_type", v)),
                                   cc=lc["conclusion"].map(lambda v: label("test", v)))[["id", "name", "tp", "cc", "effectiveness"]]
                         .rename(columns={"id": "ID", "name": L("Controlo", "Control"), "tp": L("Tipo", "Type"),
                                          "cc": L("Conclusão", "Conclusion"), "effectiveness": L("Eficácia", "Effectiveness")}),
                         hide_index=True, width="stretch",
                         column_config={L("Eficácia", "Effectiveness"): st.column_config.ProgressColumn(min_value=0, max_value=1, format="percent")})
        a = p["actions"]
        la = a[a["risk_id"] == rid] if not a.empty else a
        st.markdown(f"**{L('Ações de tratamento', 'Treatment actions')}** ({len(la)})")
        if not la.empty:
            st.dataframe(la[["id", "description", "owner", "due", "status", "progress"]].assign(
                status=la["status"].map(lambda v: label("action_status", v))), hide_index=True, width="stretch")
        k = p["kris"]
        lk = k[k["risk_id"] == rid] if not k.empty else k
        if not lk.empty:
            st.markdown(f"**KRIs** ({len(lk)})")
            st.dataframe(lk[["id", "name", "current", "amber", "red", "unit"]], hide_index=True, width="stretch")
        if r.get("imp_ml") is not None and r.get("imp_ml") == r.get("imp_ml"):
            st.caption(L(f"Impacto estimado: {money(r['imp_min'])} – {money(r['imp_ml'])} – {money(r['imp_max'])}",
                         f"Estimated impact: {money(r['imp_min'])} – {money(r['imp_ml'])} – {money(r['imp_max'])}"))

st.write("")
from core.ui import ai_assist  # noqa: E402
ai_assist("register", [])
