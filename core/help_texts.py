"""Legends for every page: what it is, how to read it, sources (bibliography). PM Studio style."""

SRC = {
    "iso31000": "ISO (2018). *ISO 31000:2018 — Risk management — Guidelines*. Genebra: International Organization for Standardization.",
    "iso31010": "IEC/ISO (2019). *IEC 31010:2019 — Risk management — Risk assessment techniques*. Genebra: IEC.",
    "coso_erm": "COSO (2017). *Enterprise Risk Management — Integrating with Strategy and Performance*. Committee of Sponsoring Organizations of the Treadway Commission.",
    "coso_ic": "COSO (2013). *Internal Control — Integrated Framework*. Committee of Sponsoring Organizations of the Treadway Commission.",
    "iia": "The Institute of Internal Auditors (2020). *The IIA's Three Lines Model — An update of the Three Lines of Defense*. Lake Mary, FL: IIA.",
    "hillson": "Hillson, D. (ed.) (2016). *The Risk Management Handbook: A Practical Guide to Managing the Multiple Dimensions of Risk*. London: Kogan Page.",
    "atom": "Hillson, D. & Simon, P. (2020). *Practical Project Risk Management: The ATOM Methodology*, 3.ª ed. Oakland: Berrett-Koehler.",
    "hillson_opp": "Hillson, D. (2004). *Effective Opportunity Management for Projects: Exploiting Positive Risk*. New York: Marcel Dekker.",
    "kaplan": "Kaplan, R. S. & Mikes, A. (2012). Managing Risks: A New Framework. *Harvard Business Review*, 90(6), 48–60.",
    "fair": "Freund, J. & Jones, J. (2014). *Measuring and Managing Information Risk: A FAIR Approach*. Oxford: Butterworth-Heinemann; The Open Group (2020) Risk Taxonomy (O-RT) v3.",
    "hubbard": "Hubbard, D. W. & Seiersen, R. (2023). *How to Measure Anything in Cybersecurity Risk*, 2.ª ed. Hoboken: Wiley.",
    "vose": "Vose, D. (2008). *Risk Analysis: A Quantitative Guide*, 3.ª ed. Chichester: Wiley.",
    "fmea": "AIAG & VDA (2019). *FMEA Handbook*; IEC 60812:2018 — Failure modes and effects analysis (FMEA and FMECA).",
    "bowtie": "CCPS (2018). *Bow Ties in Risk Management: A Concept Book for Process Safety*. Hoboken: Wiley/AIChE.",
    "pmbok": "Project Management Institute (2021). *A Guide to the Project Management Body of Knowledge (PMBOK® Guide)*, 7.ª ed. — Risk performance domain.",
    "kri": "COSO (2010). *Developing Key Risk Indicators to Strengthen Enterprise Risk Management*. COSO / North Carolina State University ERM Initiative.",
    "appetite": "COSO (2020). *Risk Appetite — Critical to Success: Using Risk Appetite to Thrive in a Changing World*.",
    "rmm": "RIMS (2015). *Risk Maturity Model*; ISO 31000:2018 §5 (framework) como referência de autoavaliação.",
    "course": "Materiais da unidade curricular (professor): RiskRegister (escala 4×4, exposição = probabilidade × impacto, mitigação existente/proposta, gestor e dono do risco) e matriz de gestão de riscos.",
    "controlkit": "ControlKit (2025). *A risk register without controls is only half a tool* — cadeia Risco → Objetivo de controlo → Controlo → Evidência → Teste → Conclusão → Ação.",
    "dora": "Regulamento (UE) 2022/2554 (DORA) e Diretiva (UE) 2022/2555 (NIS2); Regulamento (UE) 2024/1689 (AI Act).",
}

H = {
    "dashboard": {
        "pt": ("Visão consolidada do **perfil de risco**: número de ameaças e oportunidades, riscos críticos antes e depois dos controlos, "
               "posição face ao apetite, cobertura risco↔controlo, ações em atraso e KRIs em alerta.",
               "Compare sempre **inerente → residual**: a diferença é o valor criado pelos controlos. Os riscos **fora da tolerância** "
               "exigem decisão (tratar, escalar ou aceitar formalmente). A leitura interpretativa é gerada por regras e não precisa de IA.",
               ["iso31000", "coso_erm", "kaplan"]),
        "en": ("Consolidated view of the **risk profile**: threats and opportunities, critical risks before and after controls, position vs appetite, "
               "risk↔control coverage, overdue actions and KRIs on alert.",
               "Always compare **inherent → residual**: the difference is the value created by controls. Risks **outside tolerance** require a decision "
               "(treat, escalate or formally accept). The interpretation is rule-based and does not need AI.",
               ["iso31000", "coso_erm", "kaplan"]),
    },
    "context": {
        "pt": ("Estabelece o **âmbito, contexto e critérios de risco** (ISO 31000 §6.3): objetivos em risco, escalas de probabilidade e impacto, "
               "**apetite** (risco que a organização aceita para atingir objetivos), **tolerância** (desvio máximo aceitável) e **capacidade** (perda máxima absorvível).",
               "As escalas definem como se pontua cada risco (1–5). O impacto é multidimensional: use o critério mais severo entre financeiro, reputação, "
               "pessoas, conformidade e operações. O apetite por categoria é o limite do score residual.",
               ["iso31000", "coso_erm", "appetite"]),
        "en": ("Sets the **scope, context and risk criteria** (ISO 31000 §6.3): objectives at risk, probability and impact scales, **appetite** (risk accepted "
               "to achieve objectives), **tolerance** (maximum acceptable deviation) and **capacity** (maximum absorbable loss).",
               "Scales define how each risk is scored (1–5). Impact is multi-dimensional: use the most severe criterion. Appetite by category caps the residual score.",
               ["iso31000", "coso_erm", "appetite"]),
    },
    "register": {
        "pt": ("Registo vivo de **ameaças e oportunidades** (Hillson). Cada risco é descrito em metalinguagem **causa → evento → efeito**, avaliado em probabilidade e impacto "
               "(1–5), velocidade e proximidade. O residual é calculado a partir dos controlos ligados e testados; o alvo é o nível pretendido após o tratamento.",
               "Score = P × I. Um risco é **inerente** antes dos controlos, **residual** com os controlos atuais e **alvo** depois do plano de tratamento. "
               "Use o residual manual só com julgamento fundamentado. Estimativas de três pontos (€) alimentam o Monte Carlo.",
               ["iso31000", "hillson", "atom", "course"]),
        "en": ("Living register of **threats and opportunities** (Hillson). Each risk uses **cause → event → effect** metalanguage, scored on probability and impact (1–5), "
               "velocity and proximity. Residual comes from linked, tested controls; target is the level intended after treatment.",
               "Score = P × I. **Inherent** before controls, **residual** with current controls, **target** after treatment. Override residual only with documented "
               "judgement. Three-point estimates feed Monte Carlo.",
               ["iso31000", "hillson", "atom", "course"]),
    },
    "matrix": {
        "pt": ("Matrizes probabilidade × impacto 5×5 (inerente, residual e alvo), **dupla matriz** para oportunidades, movimento do risco e priorização por velocidade e proximidade.",
               "Verde 1–4 baixo · amarelo 5–9 moderado · laranja 10–14 elevado · vermelho 15–25 crítico. Setas longas = controlos eficazes. "
               "A prioridade combina o score residual com a rapidez com que o impacto se materializa e a proximidade temporal.",
               ["iso31010", "hillson_opp", "pmbok"]),
        "en": ("5×5 probability × impact matrices (inherent, residual, target), **double matrix** for opportunities, risk movement and prioritisation by velocity and proximity.",
               "Green 1–4 low · yellow 5–9 moderate · orange 10–14 high · red 15–25 critical. Long arrows = effective controls. Priority combines residual score with velocity and proximity.",
               ["iso31010", "hillson_opp", "pmbok"]),
    },
    "techniques": {
        "pt": ("**Bow-Tie**: causas → barreiras preventivas → evento de topo → barreiras de mitigação → consequências. **FMEA**: modos de falha de um processo, "
               "com gravidade (S), ocorrência (O) e deteção (D) de 1 a 10.",
               "No Bow-Tie, um lado sem barreiras ou com barreiras vermelhas/cinzentas indica onde investir. No FMEA, RPN = S×O×D; a **Action Priority** (H/M/L) "
               "dá prioridade à gravidade, mesmo com RPN moderado.",
               ["bowtie", "fmea", "iso31010"]),
        "en": ("**Bow-Tie**: causes → preventive barriers → top event → mitigating barriers → consequences. **FMEA**: process failure modes with severity (S), occurrence (O) and detection (D) 1–10.",
               "In the Bow-Tie, a side with no barriers or red/grey barriers shows where to invest. In FMEA, RPN = S×O×D; **Action Priority** (H/M/L) favours severity.",
               ["bowtie", "fmea", "iso31010"]),
    },
    "controls": {
        "pt": ("Matriz risco-controlo (**RCM**) e cadeia completa **Risco → Objetivo de controlo → Controlo → Evidência → Teste → Conclusão → Ação**. "
               "Cada controlo tem tipo (preventivo, detetivo, corretivo, diretivo), natureza (manual/automático), linha de defesa e resultado dos testes de desenho e de eficácia operacional.",
               "Dois painéis de lacunas: **riscos sem controlos** (exposição não gerida) e **controlos sem risco** (custo sem benefício demonstrável). A eficácia de cada controlo "
               "combina a natureza com os testes e determina o residual.",
               ["coso_ic", "iia", "controlkit"]),
        "en": ("Risk-control matrix (**RCM**) and the full chain **Risk → Control objective → Control → Evidence → Testing → Conclusion → Action**. "
               "Each control has a type, nature, line of defence and design/operating test results.",
               "Two gap panels: **risks without controls** (unmanaged exposure) and **controls without a risk** (cost without demonstrable benefit). Control effectiveness "
               "combines nature and tests and drives the residual.",
               ["coso_ic", "iia", "controlkit"]),
    },
    "treatment": {
        "pt": ("Plano de tratamento com ações SMART ligadas a riscos e controlos. Estratégias para ameaças (evitar, mitigar, transferir, aceitar, escalar) e "
               "oportunidades (explorar, potenciar, partilhar, aceitar).",
               "Priorize os riscos fora da tolerância. A análise **custo-benefício (RORI)** compara a redução da perda esperada com o custo dos controlos: "
               "RORI > 0 cria valor; negativo sugere controlos sobredimensionados.",
               ["iso31000", "pmbok", "atom", "hubbard"]),
        "en": ("Treatment plan with SMART actions linked to risks and controls. Threat strategies (avoid, mitigate, transfer, accept, escalate) and opportunity strategies (exploit, enhance, share, accept).",
               "Prioritise risks outside tolerance. **RORI** compares the reduction in expected loss with control cost: RORI > 0 creates value.",
               ["iso31000", "pmbok", "atom", "hubbard"]),
    },
    "kris": {
        "pt": ("**Indicadores-chave de risco** com limiares âmbar (alerta) e vermelho (ação imediata), de preferência **leading indicators** (antecipam o risco). "
               "Inclui o histórico de revisões do registo (snapshots).",
               "RAG: 🟢 dentro do limite · 🟡 alerta · 🔴 ação. A tendência compara com o valor anterior conforme o sentido do indicador. "
               "O histórico mostra se a exposição está a subir ou a descer entre revisões.",
               ["kri", "coso_erm", "iso31000"]),
        "en": ("**Key risk indicators** with amber (warning) and red (immediate action) thresholds, preferably **leading indicators**. Includes register review history (snapshots).",
               "RAG: 🟢 within limits · 🟡 warning · 🔴 action. Trend compares with the previous value given the indicator direction. History shows whether exposure is rising or falling.",
               ["kri", "coso_erm", "iso31000"]),
    },
    "quant": {
        "pt": ("Quantificação financeira: **Monte Carlo** do registo (ocorrência Bernoulli × impacto PERT, com correlação por cópula gaussiana) e cenários **FAIR** "
               "(frequência de eventos × vulnerabilidade × magnitude da perda).",
               "Perda esperada = média; **P80** = reserva de contingência típica; **VaR95** = perda num ano adverso (1 em 20); **CVaR95** = média dos 5% piores anos. "
               "O tornado mostra que riscos mais explicam a variabilidade; a curva de excedência dá P(perda > x).",
               ["vose", "fair", "hubbard", "iso31010"]),
        "en": ("Financial quantification: register **Monte Carlo** (Bernoulli × PERT with Gaussian-copula correlation) and **FAIR** scenarios.",
               "Expected loss = mean; **P80** = typical contingency; **VaR95** = loss in a 1-in-20 year; **CVaR95** = mean of the worst 5%. Tornado = main drivers; LEC = P(loss > x).",
               ["vose", "fair", "hubbard", "iso31010"]),
    },
    "maturity": {
        "pt": ("Autoavaliação da **maturidade da gestão de risco** em 12 dimensões (ISO 31000 e COSO ERM), de 1 (inicial) a 5 (otimizado/integrado).",
               "O radar compara o nível atual com o alvo; os maiores gaps são as prioridades de desenvolvimento. Registe a evidência de cada classificação.",
               ["rmm", "iso31000", "coso_erm"]),
        "en": ("Self-assessment of **risk management maturity** in 12 dimensions (ISO 31000, COSO ERM), from 1 (initial) to 5 (optimised).",
               "The radar compares current vs target; the largest gaps are the development priorities. Record evidence for each rating.",
               ["rmm", "iso31000", "coso_erm"]),
    },
    "agent": {
        "pt": ("Agente generativo (Claude) com o contexto completo do projeto: identifica riscos, desenha controlos, propõe ações e KRIs, extrai riscos de documentos "
               "Word/PDF, escreve sumários executivos, faz pré-mortem, cenários de stress e desafia as avaliações.",
               "Tudo o que o agente gera é um **rascunho**: reveja e escolha Acrescentar, Substituir ou Descartar. Sem chave API, use o **gerador de prompt** "
               "e cole-o em qualquer assistente de IA.",
               ["iso31000", "hillson", "dora"]),
        "en": ("Generative agent (Claude) with full project context: identifies risks, designs controls, proposes actions and KRIs, extracts risks from Word/PDF documents, "
               "writes executive summaries, pre-mortems, stress scenarios and challenges assessments.",
               "Everything the agent generates is a **draft**: review and choose Append, Replace or Discard. Without an API key, use the **prompt generator**.",
               ["iso31000", "hillson", "dora"]),
    },
    "reports": {
        "pt": ("Relatório interpretativo HTML (com gráficos, funciona offline e imprime em PDF), exportação Excel no formato do template, "
               "RiskRegister do professor no formato original e cópia de segurança JSON.",
               "Escolha as secções; o sumário IA é opcional. O Excel exportado pode ser editado e carregado outra vez.",
               ["iso31000", "course"]),
        "en": ("Interpretative HTML report (charts included, works offline, prints to PDF), Excel export in template format, the professor's RiskRegister in its original format and a JSON backup.",
               "Pick the sections; the AI summary is optional. The exported Excel can be edited and uploaded again.",
               ["iso31000", "course"]),
    },
    "data": {
        "pt": ("**Local único de carregamento**: template Risk Studio, RiskRegister do professor, Modelo 8 e projetos do PM Studio (JSON) — vários ficheiros de uma vez. "
               "Inclui 8 exemplos por indústria e a gestão de projetos guardados.",
               "Escolha Novo projeto, Substituir ou Acrescentar. As escalas 4×4 do professor são convertidas para 5×5 pelo nome do nível "
               "(Improvável→2, Possível→3, Provável→4, Quase certo→5; Menor→2, Moderado→3, Grave→4, Severo→5).",
               ["course", "iso31000"]),
        "en": ("**Single upload point**: Risk Studio template, the professor's RiskRegister, Model 8 and PM Studio projects (JSON) — several files at once. Includes 8 industry examples and saved projects.",
               "Choose New project, Replace or Append. The professor's 4×4 scales are mapped to 5×5 by level name.",
               ["course", "iso31000"]),
    },
    "evolution": {
        "pt": ("**Base de dados de análises** (PostgreSQL): cada revisão guarda uma fotografia do projeto e os indicadores de todos os módulos; "
               "cada página pode guardar a sua análise (leitura automática + texto do agente IA). Permite ver a **evolução temporal** e comparar "
               "um **cenário passado** com o **atual** (ou duas revisões entre si).",
               "Linha temporal: tendência da exposição, da qualidade dos controlos e da perda esperada. Comparação: 🟢 ▲ melhorou · 🔴 ▼ piorou; "
               "riscos agravados/reduzidos, novos/retirados e controlos cuja conclusão do teste mudou. A 1.ª gravação de cada dia regista uma revisão automática.",
               ["iso31000", "kri", "coso_erm"]),
        "en": ("**Analysis database** (PostgreSQL): every review stores a project snapshot and the indicators of every module; each page can save its analysis "
               "(automatic reading + AI agent text). Shows the **trend over time** and compares a **past scenario** with the **current** one (or two reviews).",
               "Timeline: trend of exposure, control quality and expected loss. Comparison: 🟢 ▲ improved · 🔴 ▼ worsened; risks worsened/reduced, new/removed and "
               "controls whose test conclusion changed. The first save of each day records an automatic review.",
               ["iso31000", "kri", "coso_erm"]),
    },
    "method": {
        "pt": ("Referenciais, fluxo de trabalho recomendado, fórmulas e legendas usados em toda a aplicação.",
               "Os parâmetros são convenções transparentes e conservadoras; o avaliador pode sobrepor o residual com julgamento fundamentado.",
               ["iso31000", "iso31010", "coso_erm", "coso_ic", "iia", "hillson", "fair"]),
        "en": ("Frameworks, recommended workflow, formulas and legends used across the app.",
               "Parameters are transparent, conservative conventions; the assessor can override the residual with documented judgement.",
               ["iso31000", "iso31010", "coso_erm", "coso_ic", "iia", "hillson", "fair"]),
    },
}
