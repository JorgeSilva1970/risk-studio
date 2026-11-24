# 🛡️ Risk Studio

Aplicação web de **gestão de risco empresarial (ERM)** em Python/Streamlit, da mesma família do *Gestão Studio* e do *PM Studio*: interface bilingue PT/EN, PostgreSQL no Render, local único de upload, modelos do professor, exemplos por indústria, relatórios interpretativos e **agente generativo Claude**.

## Novidades v1.2
- **Agente IA em todas as páginas de análise** (painel, registo, matrizes, Bow-Tie/FMEA, controlos, tratamento, KRIs, Monte Carlo, maturidade e evolução): por baixo da *interpretação automática* (regras, sem IA) há o painel **🤖 Agente IA** com **🧠 Interpretar**, **🎯 Recomendações**, **💬 Pergunta livre** sobre a página e **💾 Guardar análise no histórico**. Sem chave API mostra o prompt pronto a copiar.
- **Base de dados de análises (PostgreSQL)**: tabelas `risk_snapshots` (fotografia completa do projeto) e `risk_analyses` (uma linha por módulo: indicadores, detalhe por risco/controlo, leitura automática e texto do agente). A **1.ª gravação de cada dia** regista uma revisão automática; pode registar revisões manuais (ex.: comité de risco).
- **Página 📈 Evolução & comparação**: linha temporal (exposição, qualidade dos controlos, perda esperada Monte Carlo, score por risco), **cenário passado vs. atual** (ou duas revisões) com 🟢▲/🔴▼, riscos agravados/reduzidos, novos/retirados, controlos cuja conclusão mudou e interpretação IA da evolução; histórico de análises guardadas; restaurar versões.
- **ZIP de templates em branco** (`Templates_Risk_Studio.zip`), no formato do Gestão Studio: `00_INDICE.xlsx` + um ficheiro por módulo com a 1.ª folha **«Instruções»** (o que é, autor/origem, referência, quando usar, como ler, **como preencher** em 7 passos, **dicionário de dados** e **exemplo de preenchimento**), folha **«campos»** (células amarelas) e folhas de dados `modulo.tabela` (cabeçalhos dourados = lista pendente; comentário em cada cabeçalho com a regra). Inclui o RiskRegister do professor. O upload aceita os ficheiros soltos ou o **ZIP inteiro**; templates em branco são ignorados.
- Correção: o seletor de projeto ativo podia saltar para outro projeto depois de gravar (a lista estava ordenada por "última alteração"); agora a ordem é estável.

## Convenções partilhadas com o PM Studio e o Gestão Studio
| Convenção | Onde |
|---|---|
| Tema claro e paleta azul do Gestão Studio; template Plotly registado globalmente; câmara dos gráficos exporta **PNG 3×** com nome do projeto | `core/theme.py`, `ui.plotly_defaults()` |
| Cada página: cabeçalho com o projeto ativo, **legenda "o que é · como se lê · fontes"** e **interpretação automática** por regras (sem IA) | `core/help_texts.py`, `core/interpret.py` |
| Barra lateral: idioma 🇵🇹/🇬🇧, **projeto ativo**, 💾 Guardar + **Auto** (grava cada alteração após a 1.ª gravação), 🤖 Agente IA com chave de sessão, modelo e **🔌 Testar ligação** | `app.py` |
| O URL guarda `?lang=..&pid=..`: recarregar o browser reabre o mesmo projeto | `ui.init_state()/sync_query()` |
| Agente: `ANTHROPIC_EFFORT`, respostas estruturadas (JSON schema), **rascunho → Acrescentar / Substituir / Descartar**, extração de **Word/PDF**, **gerador de prompt sem chave** | `core/ai.py`, `views/agente.py` |
| **Modelos do professor**: RiskRegister_Template (4×4) importado e exportado no formato original; Modelo 8 e projetos do PM Studio (JSON) importados | `core/professor.py`, `templates/` |
| Template Excel com folha **Dicionário** (campo, código, tipo, valores aceites, ajuda) e listas pendentes; upload de vários ficheiros de uma vez | `core/excel_io.py`, `views/dados.py` |
| Render Blueprint (frankfurt, health check, Python 3.13, `ANTHROPIC_EFFORT`), `.env` com python-dotenv, `.streamlit/secrets.toml.example` | `render.yaml` |
| **Revisões periódicas** (snapshots) com evolução do perfil de risco e restauro de versões | `core/db.py`, KRIs → Revisões & histórico |

### Escala do professor (4×4) ↔ Risk Studio (5×5)
Conversão **pelo nome do nível**, sem inventar níveis: probabilidade *Unlikely→2 Improvável, Possible→3 Possível, Likely→4 Provável, Almost certain→5 Quase certa*; impacto *Minor→2 Menor, Moderate→3 Moderado, Major→4 Maior, Severe→5 Catastrófico*. Na exportação, o nível 1 junta-se ao nível mais baixo do 4×4.
*Mitigação existente* → **controlo** ligado ao risco; *mitigação proposta* → **ação de tratamento**; no PM Studio, *ação corretiva + gatilho* → **controlo corretivo** («se e quando…»). O RiskRegister exportado leva os 8 riscos mais prioritários (as linhas do modelo original); o resto segue no Excel completo.

## Referenciais integrados
ISO 31000:2018 · ISO 31010:2019 · COSO ERM 2017 · COSO Internal Control 2013 · Modelo das Três Linhas (IIA 2020) · Hillson / ATOM (ameaças **e** oportunidades) · FAIR · DORA / NIS2 / AI Act.

## Módulos
| Secção | O que faz |
|---|---|
| **Painel de risco** | KPIs, matriz residual, leitura interpretativa automática, top riscos, eficácia de controlos, posição face ao apetite, cadeia Risco→Ação |
| **Contexto & apetite** | Âmbito, objetivos, declaração de apetite, escala financeira de impacto, capacidade de risco, apetite/tolerância por categoria, escalas multidimensionais |
| **Registo de riscos** | Ameaças e oportunidades, metalinguagem causa→evento→efeito, P×I inerente, velocidade, proximidade, residual calculado (ou manual), alvo, estimativas PERT, ficha do risco |
| **Matrizes & prioridades** | Heatmaps 5×5 inerente/residual/alvo, dupla matriz de oportunidades, movimento do risco, bolhas de prioridade, residual vs. apetite/tolerância |
| **Bow-Tie & FMEA** | Bow-tie automático a partir de causas, consequências e controlos ligados (cor = resultado do teste); FMEA com RPN, Action Priority e Pareto |
| **Controlos & RCM** | Cadeia ControlKit (Risco → Objetivo → Controlo → Evidência → Teste → Conclusão → Ação), testes de desenho/eficácia, **riscos sem controlos** e **controlos sem risco**, matriz Risco×Controlo |
| **Tratamento & ações** | Plano SMART, Gantt, ações em atraso, custo-benefício e **RORI** (Return on Risk Investment) |
| **KRIs & monitorização** | Indicadores com limiares âmbar/vermelho, sentido, tendência, gauges; **revisões periódicas** (snapshots) com evolução e restauro |
| **Monte Carlo & FAIR** | Bernoulli×PERT com cópula gaussiana (ρ), perda esperada, P50/P80/VaR95/CVaR95, P(perda > capacidade), tornado, curva S, LEC; cenários FAIR (TEF×Vulnerabilidade, perdas primárias/secundárias) |
| **Maturidade ERM** | Autoavaliação em 12 dimensões (ISO 31000 / COSO ERM), radar atual vs. alvo |
| **Agente IA** | Chat com contexto total do projeto; gera riscos, controlos, ações e KRIs estruturados (rascunho → Acrescentar/Substituir/Descartar); **extrai riscos de Word/PDF** (relatórios de auditoria, atas, políticas); sumário executivo, desafio 2.ª linha, pré-mortem, cenários de stress, plano de auditoria; **gerador de prompt** sem chave |
| **Relatórios** | Relatório HTML interpretativo (gráficos incluídos, funciona offline, imprimível para PDF), Excel completo, **RiskRegister do professor no formato original**, backup JSON |
| **Dados & templates** | **Local único de upload** (template Risk Studio, RiskRegister do professor, Modelo 8 e projetos do PM Studio; vários ficheiros de uma vez; Novo/Substituir/Acrescentar com renumeração de IDs), 8 exemplos por indústria, projetos guardados, novo/restaurar |
| **Metodologia** | Referenciais, fluxo recomendado, fórmulas e legendas |

## Correr localmente
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # coloque a sua ANTHROPIC_API_KEY
streamlit run app.py
```
Sem `DATABASE_URL`, os projetos ficam num ficheiro SQLite local (`risk_studio.db`).

## GitHub
```bash
git init
git add .
git commit -m "Risk Studio v1.1"
git branch -M main
git remote add origin https://github.com/JorgeSilva1970/risk-studio.git
git push -u origin main
```

## Deploy no Render (GitHub → Render)
1. Crie o repositório `JorgeSilva1970/risk-studio` no GitHub e faça push desta pasta (comandos acima).
2. No Render: **New → Blueprint** e escolha o repositório. O `render.yaml` cria o *web service* e a base de dados PostgreSQL e liga o `DATABASE_URL` automaticamente.
3. Em **Environment**, defina `ANTHROPIC_API_KEY` (marcado como secreto; nunca o coloque no código nem no GitHub).
4. Alternativa manual: *Web Service* com
   - Build: `pip install -r requirements.txt`
   - Start: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
   - Variáveis: `ANTHROPIC_API_KEY`, `DATABASE_URL` (Internal Database URL do PostgreSQL), opcional `ANTHROPIC_MODEL` (por defeito `claude-sonnet-5-5`).

## Testes
```bash
pytest -q                                  # testes: núcleo, páginas PT/EN, exemplos, BD, URL, revisões/comparação, templates ZIP, formatos do professor/PM Studio
ANTHROPIC_API_KEY=... pytest tests/test_ai_live.py   # 5 testes ao vivo do agente (gerar, relatório, extração de Word, ligação, assistente por página)
```

## Metodologia de cálculo (resumo)
- **Score** = P (1–5) × I (1–5); níveis 1–4 Baixo · 5–9 Moderado · 10–14 Elevado · 15–25 Crítico.
- **Eficácia do controlo** e = força da natureza (automático 0,80 · manual dep. TI 0,65 · manual 0,55) × fator teste de desenho × fator teste operacional (eficaz 1 · parcial 0,5 · não testado 0,3 · ineficaz 0).
- **Residual**: E_prev = 1−Π(1−e) (preventivos; diretivos a 50%); E_mit idem (detetivos a 60%, corretivos 100%). P_res = P − arred(E_prev × (P−1) × 0,75); I_res análogo. O avaliador pode sobrepor.
- **Prioridade** = residual × fator de velocidade (0,8–1,2) × fator de proximidade (0,9–1,1).
- **Monte Carlo**: ocorrência Bernoulli com cópula gaussiana (ρ) × impacto PERT; oportunidades entram como ganhos.
- **FAIR**: LEF = TEF × Vulnerabilidade; ALE = Σ (perda primária + P(secundária) × perda secundária), eventos Poisson.

## Estrutura
```
app.py                 navegação, barra lateral, idioma, guardar/abrir
core/                  catalogs, model, scoring, montecarlo, charts, theme, ai, db, history, excel_io, templates_zip, professor, report, interpret, help_texts, examples, ui, i18n
templates/             RiskRegister_Template.xlsx (modelo original do professor)
views/                 15 páginas (inclui evolucao.py)
assets/                logótipo
tests/                 testes automáticos
render.yaml            blueprint Render (web + PostgreSQL)
```
