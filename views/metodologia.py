import streamlit as st

from core.i18n import L
from core.report import methodology_html
from core.ui import hero, note

hero(L("Metodologia & guia de utilização", "Methodology & user guide"),
     L("Referenciais modernos integrados numa só ferramenta", "Modern frameworks integrated in one tool"), "📚", help_key="method")

c1, c2 = st.columns(2)
with c1:
    st.markdown(f"### {L('Referenciais', 'Frameworks')}")
    st.markdown(L("""
- **ISO 31000:2018** — princípios, quadro e processo de gestão do risco (criar e proteger valor).
- **ISO 31010:2019** — técnicas de apreciação: matriz P-I, Bow-Tie, FMEA, Monte Carlo, cenários, pré-mortem.
- **COSO ERM 2017** — risco integrado na estratégia e desempenho; apetite, tolerância e capacidade.
- **COSO Internal Control 2013** — desenho e eficácia operacional dos controlos.
- **Modelo das Três Linhas (IIA, 2020)** — gestão (1.ª), risco/compliance (2.ª), auditoria interna (3.ª).
- **David Hillson — The Risk Management Handbook / ATOM** — ameaças *e* oportunidades, metalinguagem causa–evento–efeito, dupla matriz P-I, estratégias de resposta a oportunidades.
- **FAIR (Open Group)** — quantificação financeira do risco de informação/ciber.
- **Regulação moderna**: DORA, NIS2, AI Act, CSRD/ESG, Solvência II, Basileia.
""", """
- **ISO 31000:2018** — principles, framework and process (creating and protecting value).
- **ISO 31010:2019** — assessment techniques: P-I matrix, Bow-Tie, FMEA, Monte Carlo, scenarios, pre-mortem.
- **COSO ERM 2017** — risk integrated with strategy and performance; appetite, tolerance and capacity.
- **COSO Internal Control 2013** — control design and operating effectiveness.
- **Three Lines Model (IIA, 2020)** — management (1st), risk/compliance (2nd), internal audit (3rd).
- **David Hillson — The Risk Management Handbook / ATOM** — threats *and* opportunities, cause–event–effect metalanguage, double P-I matrix, opportunity responses.
- **FAIR (Open Group)** — financial quantification of information/cyber risk.
- **Modern regulation**: DORA, NIS2, AI Act, CSRD/ESG, Solvency II, Basel.
"""))
with c2:
    st.markdown(f"### {L('Fluxo de trabalho recomendado', 'Recommended workflow')}")
    st.markdown(L("""
1. **Contexto & apetite** — objetivos, âmbito, escalas e apetite por categoria.
2. **Registo de riscos** — identificar ameaças e oportunidades (ou pedir ao Agente IA); avaliar P, I, velocidade e proximidade.
3. **Controlos & RCM** — desenhar controlos, ligá-los aos riscos, registar evidência e testes → o residual é calculado.
4. **Matrizes & Bow-Tie** — validar a posição dos riscos e as barreiras.
5. **Tratamento & ações** — planos para riscos acima do apetite; custo-benefício (RORI).
6. **KRIs** — indicadores com limiares para monitorização contínua.
7. **Monte Carlo & FAIR** — quantificar a exposição e a reserva de contingência (P80).
8. **Relatórios** — relatório interpretativo para a gestão; exportar Excel; guardar o projeto.
""", """
1. **Context & appetite** — objectives, scope, scales and appetite by category.
2. **Risk register** — identify threats and opportunities (or ask the AI Agent); assess P, I, velocity and proximity.
3. **Controls & RCM** — design controls, link them to risks, record evidence and tests → residual is computed.
4. **Matrices & Bow-Tie** — validate risk positions and barriers.
5. **Treatment & actions** — plans for risks above appetite; cost-benefit (RORI).
6. **KRIs** — indicators with thresholds for continuous monitoring.
7. **Monte Carlo & FAIR** — quantify exposure and contingency reserve (P80).
8. **Reports** — interpretative report for management; export Excel; save the project.
"""))

st.markdown(f"### {L('Fórmulas e legendas', 'Formulas and legends')}")
st.markdown(methodology_html(), unsafe_allow_html=True)
note(L("Os parâmetros (força por natureza do controlo, fatores de teste, amortecimento 0,75, fatores de velocidade/proximidade) são convenções "
       "transparentes e conservadoras; o avaliador pode sempre sobrepor o residual com julgamento profissional fundamentado.",
       "Parameters (strength by control nature, test factors, 0.75 damping, velocity/proximity factors) are transparent, conservative conventions; "
       "the assessor can always override the residual with documented professional judgement."))
