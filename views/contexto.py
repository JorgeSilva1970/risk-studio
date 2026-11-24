import datetime as dt

import pandas as pd
import streamlit as st

from core.catalogs import IMPACT_DESCRIPTORS, IMPACT_SCALE, INDUSTRIES, PROB_SCALE
from core.i18n import L, lang, tr
from core.ui import bump, flash, hero, mark_dirty, money, note, proj, table_editor

p = proj()
m = p["meta"]
hero(L("Contexto, critérios & apetite", "Context, criteria & appetite"),
     L("ISO 31000 §6.3 — âmbito, contexto e critérios de risco · COSO ERM — apetite, tolerância e capacidade",
       "ISO 31000 §6.3 — scope, context and risk criteria · COSO ERM — appetite, tolerance and capacity"), "🧭", help_key="context")

steps = [
    (L("Comunicar & consultar", "Communicate & consult"), L("Partes interessadas", "Stakeholders")),
    (L("Âmbito & contexto", "Scope & context"), L("Objetivos e critérios", "Objectives and criteria")),
    (L("Identificar", "Identify"), L("Causa → evento → efeito", "Cause → event → effect")),
    (L("Analisar", "Analyse"), L("P × I, velocidade", "P × I, velocity")),
    (L("Avaliar", "Evaluate"), L("Face ao apetite", "Against appetite")),
    (L("Tratar", "Treat"), L("Controlos e ações", "Controls and actions")),
    (L("Monitorizar & rever", "Monitor & review"), L("KRIs, testes", "KRIs, testing")),
    (L("Registar & reportar", "Record & report"), L("Relatórios", "Reports")),
]
st.markdown("<div class='rs-chain'>" + "".join(
    f"<div class='rs-step'><span class='n'>{i}</span><div class='t'>{t}</div><div class='d'>{d}</div></div>"
    for i, (t, d) in enumerate(steps, 1)) + "</div>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs([L("Contexto do projeto", "Project context"), L("Apetite & tolerância", "Appetite & tolerance"),
                            L("Escalas de avaliação", "Assessment scales")])

with tab1:
    with st.form(f"meta_{st.session_state.ver.get('meta', 0)}"):
        c1, c2 = st.columns(2)
        name = c1.text_input(L("Nome do projeto / avaliação", "Project / assessment name"), m.get("name", ""))
        org = c2.text_input(L("Organização", "Organisation"), m.get("organisation", ""))
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        keys = list(INDUSTRIES)
        ind = c1.selectbox(L("Indústria", "Industry"), keys, index=keys.index(m.get("industry", "other")) if m.get("industry") in keys else len(keys) - 1,
                           format_func=lambda k: tr(INDUSTRIES[k]))
        assessor = c2.text_input(L("Avaliador / responsável", "Assessor / owner"), m.get("assessor", ""))
        try:
            d0 = dt.date.fromisoformat(str(m.get("date"))[:10])
        except ValueError:
            d0 = dt.date.today()
        date = c3.date_input(L("Data", "Date"), d0, format="DD/MM/YYYY")
        currency = c4.selectbox(L("Moeda", "Currency"), ["€", "$", "£", "R$", "Kz", "MT"],
                                index=["€", "$", "£", "R$", "Kz", "MT"].index(m.get("currency", "€")) if m.get("currency", "€") in ["€", "$", "£", "R$", "Kz", "MT"] else 0)
        scope = st.text_area(L("Âmbito (unidades, processos, projeto)", "Scope (units, processes, project)"), m.get("scope", ""), height=70)
        objectives = st.text_area(L("Objetivos estratégicos / do projeto afetados pelo risco", "Strategic / project objectives at risk"),
                                  m.get("objectives", ""), height=80)
        appetite_statement = st.text_area(L("Declaração de apetite ao risco (aprovada pelo órgão de gestão)", "Risk appetite statement (approved by the board)"),
                                          m.get("appetite_statement", ""), height=90)
        st.markdown(f"**{L('Escala financeira de impacto — limite superior de cada nível', 'Financial impact scale — upper bound of each level')}**")
        th = list(m.get("impact_thresholds") or [10_000, 100_000, 500_000, 2_000_000, 10_000_000])
        cc = st.columns(6)
        vals = []
        for i in range(5):
            vals.append(cc[i].number_input(f"{i + 1} · {IMPACT_SCALE[i + 1][1 if lang() == 'en' else 0]}", min_value=0.0,
                                           value=float(th[i]), step=1000.0, format="%.0f"))
        cap = cc[5].number_input(L("Capacidade de risco", "Risk capacity"), min_value=0.0, value=float(m.get("risk_capacity") or 0),
                                 step=10000.0, format="%.0f", help=L("Perda máxima que a organização consegue absorver (usada no Monte Carlo).",
                                                                    "Maximum loss the organisation can absorb (used in Monte Carlo)."))
        if st.form_submit_button(L("💾 Guardar contexto", "💾 Save context"), type="primary"):
            vals = sorted(vals)
            m.update(name=name or m["name"], organisation=org, industry=ind, assessor=assessor, date=date.isoformat(),
                     currency=currency, scope=scope, objectives=objectives, appetite_statement=appetite_statement,
                     impact_thresholds=vals, risk_capacity=cap)
            bump("meta")
            mark_dirty()
            flash(L("Contexto guardado ✔", "Context saved ✔"))
            st.rerun()

with tab2:
    note(L("<b>Apetite</b> = nível de risco residual que a organização está disposta a aceitar na prossecução dos objetivos. "
           "<b>Tolerância</b> = desvio máximo aceitável; acima dela é obrigatória decisão (tratar, escalar ou aceitar formalmente). "
           "<b>Capacidade</b> = perda máxima absorvível. Valores em score P×I (1–25).",
           "<b>Appetite</b> = residual risk level the organisation is willing to accept in pursuit of its objectives. "
           "<b>Tolerance</b> = maximum acceptable deviation; above it a decision is mandatory (treat, escalate or formally accept). "
           "<b>Capacity</b> = maximum absorbable loss. Values on the P×I score (1–25)."))
    st.write("")
    table_editor("appetite", ["category", "appetite", "tolerance"], fixed=True)
    st.caption(L(f"Capacidade de risco atual: {money(m.get('risk_capacity'))}", f"Current risk capacity: {money(m.get('risk_capacity'))}"))

with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{L('Probabilidade (horizonte de 12 meses)', 'Probability (12-month horizon)')}**")
        st.dataframe(pd.DataFrame([{"Nível": k, L("Descrição", "Description"): v[0][1 if lang() == "en" else 0], L("Intervalo", "Range"): v[1],
                                    L("Ponto médio (Monte Carlo)", "Midpoint (Monte Carlo)"): f"{v[2]:.0%}"} for k, v in PROB_SCALE.items()]),
                     hide_index=True, width="stretch")
        st.markdown(f"**{L('Velocidade', 'Velocity')}** — " + L("1 anos · 2 meses · 3 semanas · 4 dias · 5 imediato (horas)",
                                                                 "1 years · 2 months · 3 weeks · 4 days · 5 immediate (hours)"))
    with c2:
        st.markdown(f"**{L('Impacto (multidimensional)', 'Impact (multi-dimensional)')}**")
        th = m.get("impact_thresholds")
        rows = []
        for i in range(1, 6):
            row = {"Nível": i, L("Descrição", "Description"): IMPACT_SCALE[i][1 if lang() == "en" else 0],
                   L("Financeiro até", "Financial up to"): money(th[i - 1])}
            for key, (title, levels) in IMPACT_DESCRIPTORS.items():
                row[tr(title)] = tr(levels[i - 1])
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.markdown(L("**Níveis de risco (score P×I):** 🟢 1–4 Baixo · 🟡 5–9 Moderado · 🟠 10–14 Elevado · 🔴 15–25 Crítico. "
                  "Use o critério mais severo entre as dimensões de impacto.",
                  "**Risk levels (P×I score):** 🟢 1–4 Low · 🟡 5–9 Moderate · 🟠 10–14 High · 🔴 15–25 Critical. "
                  "Use the most severe criterion across impact dimensions."))
