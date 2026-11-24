"""Generative AI agent (Anthropic Claude).

* Chat with full project context (streaming).
* Structured generation through forced tool use (JSON schema) → rows that can be
  added straight into the register / RCM / actions / KRIs.
* Interpretation of results (heatmap, Monte Carlo, coverage) and executive summary.
The API key is read from the session (sidebar), st.secrets or the ANTHROPIC_API_KEY
environment variable — it is never stored in the project or database."""
from __future__ import annotations

import json
import os
from typing import Iterator

import pandas as pd
import streamlit as st

from core import scoring
from core.catalogs import CATALOGS, INDUSTRIES, label
from core.i18n import lang

MODELS = {
    "claude-sonnet-5-5": "Claude Sonnet 5.5 (recomendado)",
    "claude-opus-5-5": "Claude Opus 5.5 (máxima qualidade)",
    "claude-haiku-5-5": "Claude Haiku 5.5 (rápido)",
}
DEFAULT_MODEL = "claude-sonnet-5-5"


EFFORT = os.environ.get("ANTHROPIC_EFFORT", "medium")  # low | medium | high (PM Studio convention)


def _oc(extra: dict | None = None) -> dict:
    """output_config with the reasoning effort (and optionally a JSON-schema format)."""
    oc = dict(extra or {})
    if EFFORT:
        oc["effort"] = EFFORT
    return {"output_config": oc} if oc else {}


def api_key() -> str | None:
    k = (st.session_state.get("api_key_override") or "").strip()
    if k:
        return k
    try:
        k = st.secrets.get("ANTHROPIC_API_KEY")  # type: ignore[attr-defined]
    except Exception:
        k = None
    return k or os.environ.get("ANTHROPIC_API_KEY")


def available() -> bool:
    return bool(api_key())


def model() -> str:
    return st.session_state.get("ai_model") or os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL


def test_connection() -> tuple[bool, str]:
    """Minimal request to validate key and model (Gestão Studio convention)."""
    try:
        r = client().messages.create(model=model(), max_tokens=10, messages=[{"role": "user", "content": "Responde apenas: ok"}])
        return True, f"{model()} · " + "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    except Exception as e:
        s = str(e)
        if "401" in s or "authentication" in s.lower():
            return False, "Chave inválida ou revogada (401)." if lang() == "pt" else "Invalid or revoked key (401)."
        if "404" in s or "not_found" in s:
            return False, (f"Modelo «{model()}» indisponível para esta chave (404)." if lang() == "pt" else f"Model '{model()}' not available for this key (404).")
        if "429" in s:
            return False, "Limite de pedidos/créditos atingido (429)." if lang() == "pt" else "Rate/credit limit reached (429)."
        return False, s[:300]


def client():
    import anthropic
    return anthropic.Anthropic(api_key=api_key(), max_retries=2, timeout=180)


# ------------------------------------------------------------- context
def project_context(proj: dict, max_rows: int = 40) -> str:
    m = proj["meta"]
    ra = scoring.analyse_risks(proj)
    ca = scoring.analyse_controls(proj)
    kp = scoring.kpis(proj)
    kr = scoring.analyse_kris(proj)
    acts = scoring.analyse_actions(proj)
    ind = INDUSTRIES.get(m.get("industry"), ("", ""))[0]
    lines = [
        f"ORGANIZAÇÃO: {m.get('organisation')} | PROJETO: {m.get('name')} | INDÚSTRIA: {ind}",
        f"ÂMBITO: {m.get('scope')}", f"OBJETIVOS: {m.get('objectives')}",
        f"DECLARAÇÃO DE APETITE: {m.get('appetite_statement')}",
        f"CAPACIDADE DE RISCO: {m.get('risk_capacity')} {m.get('currency')} | ESCALA DE IMPACTO (limiares €): {m.get('impact_thresholds')}",
        "KPIs: " + json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in kp.items()}, ensure_ascii=False),
        "",
        "REGISTO DE RISCOS (id | tipo | categoria | título | causa | evento | efeito | P×I inerente | P×I residual | apetite | estado apetite | controlos | ações):",
    ]
    for r in ra.head(max_rows).to_dict(orient="records"):
        lines.append(f"- {r['id']} | {r['type']} | {r['category']} | {r['title']} | {r.get('cause','')} | {r.get('event','')} | "
                     f"{r.get('effect','')} | {r['p_inh']}×{r['i_inh']}={r['score_inh']} | {r['p_res']}×{r['i_res']}={r['score_res']} | "
                     f"{r['appetite']} | {r['appetite_status']} | {r['controls'] or '—'} | {r['n_actions']}")
    lines.append("")
    lines.append("CONTROLOS (id | nome | tipo | natureza | riscos | teste desenho | teste operacional | conclusão | eficácia):")
    for c in ca.head(max_rows).to_dict(orient="records"):
        lines.append(f"- {c['id']} | {c['name']} | {c['control_type']} | {c['nature']} | {c['risk_ids'] or 'SEM RISCO'} | "
                     f"{c['design_test']} | {c['operating_test']} | {c['conclusion']} | {c['effectiveness']:.2f}")
    if not acts.empty:
        lines.append("")
        lines.append("AÇÕES (id | risco | descrição | estado | prazo | atrasada):")
        for a in acts.head(max_rows).to_dict(orient="records"):
            lines.append(f"- {a['id']} | {a['risk_id']} | {a['description']} | {a['status']} | {a['due']} | {a['overdue']}")
    if not kr.empty:
        lines.append("")
        lines.append("KRIs (id | risco | nome | atual | âmbar | vermelho | RAG):")
        for k in kr.to_dict(orient="records"):
            lines.append(f"- {k['id']} | {k['risk_id']} | {k['name']} | {k['current']} | {k['amber']} | {k['red']} | {k['rag']}")
    return "\n".join(lines)


def system_prompt(proj: dict) -> str:
    lang_name = "inglês" if lang() == "en" else "português europeu (PT-PT)"
    return f"""És o Risk Studio Agent, um consultor sénior de gestão de risco (CRO, auditor interno e atuário) com domínio de
ISO 31000:2018, ISO 31010:2019, COSO ERM 2017 (Integrating with Strategy and Performance), COSO Internal Control 2013,
Modelo das Três Linhas do IIA (2020), FAIR, DORA, NIS2, AI Act, Solvência II, Basileia III/IV e da abordagem de
David Hillson (ATOM, ameaças e oportunidades, atitude perante o risco, metalinguagem causa–evento–efeito).
Princípios que aplicas: cada risco deve ter controlos (um registo sem controlos é só meia ferramenta) e cada controlo deve
mapear para um risco; a cadeia Risco → Objetivo de controlo → Controlo → Evidência → Teste → Conclusão → Ação deve estar
completa; avalias risco inerente, residual e alvo face ao apetite e tolerância; consideras velocidade e proximidade;
recomendas KRIs com limiares; quantificas quando há dados (Monte Carlo, P80, VaR, CVaR); desafias vieses (otimismo,
ancoragem, pensamento de grupo) com respeito e de forma construtiva.
Responde em {lang_name}, de forma estruturada, concreta e acionável; usa os IDs (R01, C03…) quando te referires a itens do
projeto. Não inventes factos sobre a organização: se faltar informação, assume pressupostos explícitos.

CONTEXTO ATUAL DO PROJETO:
{project_context(proj)}"""


def _err(e: Exception) -> str:
    name = type(e).__name__
    msg = str(e)
    if "authentication" in name.lower() or "401" in msg:
        return "Chave da API inválida ou sem permissões." if lang() == "pt" else "Invalid API key or missing permissions."
    if "rate" in name.lower() or "429" in msg:
        return "Limite de pedidos atingido — tente novamente dentro de instantes." if lang() == "pt" else "Rate limit reached — retry shortly."
    if "overloaded" in msg.lower() or "529" in msg:
        return "Serviço sobrecarregado — tente novamente." if lang() == "pt" else "Service overloaded — please retry."
    return f"{name}: {msg[:300]}"


# ---------------------------------------------------------------- chat
def stream_chat(proj: dict, history: list[dict], max_tokens: int = 3000) -> Iterator[str]:
    try:
        with client().messages.stream(model=model(), max_tokens=max_tokens, system=system_prompt(proj),
                                      messages=history[-20:], **_oc()) as s:
            for text in s.text_stream:
                yield text
    except Exception as e:  # pragma: no cover - network
        yield f"\n\n⚠️ {_err(e)}"


def complete(proj: dict, prompt: str, max_tokens: int = 2500) -> str:
    try:
        r = client().messages.create(model=model(), max_tokens=max_tokens, system=system_prompt(proj),
                                     messages=[{"role": "user", "content": prompt}], **_oc())
        return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    except Exception as e:  # pragma: no cover
        return f"⚠️ {_err(e)}"


# ---------------------------------------------------------- structured
def _enum(cat: str) -> dict:
    return {"type": "string", "enum": list(CATALOGS[cat])}


SCHEMAS = {
    "risks": {
        "type": "object",
        "properties": {"items": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "type": _enum("type"), "category": _enum("category"),
                "title": {"type": "string", "description": "Título curto do risco"},
                "cause": {"type": "string", "description": "Causas separadas por ';'"},
                "event": {"type": "string"}, "effect": {"type": "string", "description": "Consequências separadas por ';'"},
                "owner": {"type": "string", "description": "Função responsável"},
                "p_inh": {"type": "integer", "minimum": 1, "maximum": 5}, "i_inh": {"type": "integer", "minimum": 1, "maximum": 5},
                "velocity": {"type": "integer", "minimum": 1, "maximum": 5}, "proximity": _enum("proximity"),
                "strategy": _enum("strategy"),
                "imp_min": {"type": "number"}, "imp_ml": {"type": "number"}, "imp_max": {"type": "number"},
                "rationale": {"type": "string", "description": "Justificação breve da avaliação"},
            },
            "required": ["type", "category", "title", "cause", "event", "effect", "owner", "p_inh", "i_inh", "velocity",
                         "proximity", "strategy", "rationale"],
        }}},
        "required": ["items"],
    },
    "controls": {
        "type": "object",
        "properties": {"items": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "risk_ids": {"type": "string", "description": "IDs dos riscos mitigados, ex.: 'R01, R03'"},
                "name": {"type": "string"}, "objective": {"type": "string", "description": "Objetivo de controlo"},
                "description": {"type": "string"}, "control_type": _enum("control_type"), "nature": _enum("nature"),
                "frequency": _enum("frequency"), "line": _enum("line"), "owner": {"type": "string"},
                "evidence": {"type": "string", "description": "Evidência a recolher e reter"},
                "cost": {"type": "number", "description": "Custo anual estimado"},
                "test_procedure": {"type": "string", "description": "Procedimento de teste (desenho e eficácia operacional)"},
            },
            "required": ["risk_ids", "name", "objective", "description", "control_type", "nature", "frequency", "line",
                         "owner", "evidence", "test_procedure"],
        }}},
        "required": ["items"],
    },
    "actions": {
        "type": "object",
        "properties": {"items": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "risk_id": {"type": "string"}, "control_id": {"type": "string"}, "description": {"type": "string"},
                "strategy": _enum("strategy"), "owner": {"type": "string"},
                "duration_days": {"type": "integer", "minimum": 1, "maximum": 730}, "cost": {"type": "number"},
            },
            "required": ["risk_id", "description", "strategy", "owner", "duration_days"],
        }}},
        "required": ["items"],
    },
    "kris": {
        "type": "object",
        "properties": {"items": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "risk_id": {"type": "string"}, "name": {"type": "string"}, "unit": {"type": "string"},
                "direction": _enum("direction"), "amber": {"type": "number"}, "red": {"type": "number"},
                "frequency": _enum("frequency"), "owner": {"type": "string"},
                "rationale": {"type": "string", "description": "Porque é um indicador avançado (leading) do risco"},
            },
            "required": ["risk_id", "name", "unit", "direction", "amber", "red", "frequency", "owner"],
        }}},
        "required": ["items"],
    },
}


def _strict(schema):
    """Structured-outputs friendly schema: additionalProperties false, no numeric bounds."""
    if isinstance(schema, dict):
        out = {k: _strict(v) for k, v in schema.items() if k not in ("minimum", "maximum")}
        if out.get("type") == "object":
            out["additionalProperties"] = False
        return out
    if isinstance(schema, list):
        return [_strict(x) for x in schema]
    return schema


def _parse_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        a, b = text.find("{"), text.rfind("}")
        return json.loads(text[a:b + 1]) if a >= 0 and b > a else {}


def structured(proj: dict, kind: str, instruction: str, max_tokens: int = 8000) -> tuple[list[dict], str | None]:
    """Structured generation (JSON schema). Primary path: structured outputs;
    fallback: tool use. Returns (items, error)."""
    schema = SCHEMAS[kind]
    c = client()
    try:
        r = c.messages.create(
            model=model(), max_tokens=max_tokens, system=system_prompt(proj),
            messages=[{"role": "user", "content": instruction}],
            **_oc({"format": {"type": "json_schema", "schema": _strict(schema)}}),
        )
        text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        items = (_parse_json(text) or {}).get("items", [])
        return [i for i in items if isinstance(i, dict)], None
    except Exception as first:  # pragma: no cover - fallback for models without structured outputs
        try:
            tool = {"name": f"submit_{kind}", "description": f"Submete a lista de {kind}.", "input_schema": schema}
            r = c.messages.create(
                model=model(), max_tokens=max_tokens, system=system_prompt(proj), tools=[tool],
                tool_choice={"type": "auto"},
                messages=[{"role": "user", "content": instruction + f"\n\nResponde OBRIGATORIAMENTE chamando a ferramenta {tool['name']}."}],
            )
            for b in r.content:
                if getattr(b, "type", "") == "tool_use":
                    items = (b.input or {}).get("items", [])
                    return [i for i in items if isinstance(i, dict)], None
            return [], _err(first)
        except Exception as e:
            return [], _err(e)


def items_to_df(items: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(items) if items else pd.DataFrame()


# ---------------------------------------------------------- quick tasks
def prompt_identify(n: int, focus: str) -> str:
    return (f"Identifica {n} novos riscos relevantes (ameaças e pelo menos uma oportunidade) para esta organização, "
            f"que ainda NÃO estejam no registo. Foco: {focus or 'abrangente (estratégicos, operacionais, emergentes, ESG, ciber, IA)'}. "
            "Usa metalinguagem causa–evento–efeito, avalia P e I inerentes (1–5), velocidade, proximidade, estratégia "
            "e estima impacto financeiro mín./+provável/máx. coerente com a escala de impacto do projeto.")


def prompt_controls(risk_ids: list[str]) -> str:
    ids = ", ".join(risk_ids) if risk_ids else "os riscos sem controlos ou com controlos ineficazes"
    return (f"Propõe controlos internos robustos para {ids}. Combina controlos preventivos, detetivos e corretivos, "
            "privilegia automação quando possível, define objetivo de controlo, evidência e procedimento de teste. "
            "Cada controlo tem de mapear para pelo menos um risco existente (campo risk_ids).")


def prompt_actions(risk_ids: list[str]) -> str:
    ids = ", ".join(risk_ids) if risk_ids else "os riscos acima do apetite e os controlos ineficazes"
    return (f"Propõe um plano de tratamento SMART para {ids}: ações concretas, estratégia (ameaças: evitar/mitigar/"
            "transferir/aceitar/escalar; oportunidades: explorar/potenciar/partilhar/aceitar), responsável, duração e custo.")


def prompt_kris(risk_ids: list[str]) -> str:
    ids = ", ".join(risk_ids) if risk_ids else "os riscos mais prioritários"
    return (f"Propõe KRIs (indicadores-chave de risco), preferencialmente leading indicators, para {ids}, "
            "com unidade, sentido, limiares âmbar e vermelho realistas, frequência e responsável.")


PROMPTS_TEXT = {
    "exec": ("Escreve um sumário executivo para a Comissão Executiva / Conselho (máx. 450 palavras): perfil de risco global, "
             "top 5 riscos residuais, riscos fora do apetite, lacunas de cobertura risco↔controlo, eficácia dos controlos, "
             "KRIs em alerta, ações atrasadas, oportunidades e 5 recomendações priorizadas. Usa títulos e listas curtas.",
             "Write an executive summary for the Executive Committee / Board (max 450 words): overall risk profile, top 5 residual "
             "risks, risks outside appetite, risk↔control coverage gaps, control effectiveness, KRIs on alert, overdue actions, "
             "opportunities and 5 prioritised recommendations. Use headings and short lists."),
    "bias": ("Atua como 'advogado do diabo' / 2.ª linha de defesa: desafia as avaliações do registo. Identifica avaliações "
             "provavelmente subestimadas ou sobrestimadas, vieses cognitivos prováveis, riscos interligados (efeitos em cascata), "
             "riscos emergentes em falta e controlos com eficácia questionável. Termina com perguntas para o workshop de risco.",
             "Act as devil's advocate / 2nd line: challenge the register's assessments. Identify likely under/over-estimated "
             "ratings, probable cognitive biases, interconnected risks (cascades), missing emerging risks and controls of "
             "questionable effectiveness. Finish with questions for the risk workshop."),
    "premortem": ("Conduz um pré-mortem: imagina que daqui a 12 meses os objetivos falharam de forma grave. Descreve 5 histórias "
                  "plausíveis de falha (cadeias causa→evento→efeito), sinais de alerta precoce e as barreiras que teriam evitado cada uma.",
                  "Run a pre-mortem: imagine that 12 months from now the objectives have failed badly. Describe 5 plausible failure "
                  "stories (cause→event→effect chains), early warning signs and the barriers that would have prevented each."),
    "scenarios": ("Desenvolve 3 cenários de stress (moderado, severo, extremo mas plausível) combinando os riscos do registo, "
                  "com narrativa, riscos ativados, impacto estimado face à capacidade de risco e respostas de gestão.",
                  "Develop 3 stress scenarios (moderate, severe, extreme-but-plausible) combining register risks, with narrative, "
                  "triggered risks, estimated impact vs risk capacity and management responses."),
    "audit": ("Prepara um programa de auditoria interna baseado no risco (3.ª linha) para os 12 meses seguintes: universo auditável, "
              "priorização, testes de controlo-chave e amostragem, a partir dos riscos e controlos do projeto.",
              "Prepare a risk-based internal audit plan (3rd line) for the next 12 months: audit universe, prioritisation, key "
              "control tests and sampling, based on the project's risks and controls."),
}


def interpret(proj: dict, section: str, data: str) -> str:
    q = ("Interpreta os seguintes resultados da secção '{s}' do Risk Studio para um decisor não técnico: o que significam, "
         "o que preocupa, o que está bem e 3 recomendações concretas. Máx. 250 palavras.\n\nDADOS:\n{d}").format(s=section, d=data)
    if lang() == "en":
        q = (f"Interpret the following results from the Risk Studio '{section}' section for a non-technical decision maker: "
             f"what they mean, what is concerning, what is fine and 3 concrete recommendations. Max 250 words.\n\nDATA:\n{data}")
    return complete(proj, q, 1200)


def lbl(cat: str, code) -> str:
    return label(cat, code)


# ------------------------------------------------------------- documents (Word / PDF / text)
def document_text(name: str, data: bytes, max_pages: int = 60, max_chars: int = 120_000) -> str:
    """Plain text from an uploaded .docx, .pdf, .txt or .md file (PM Studio convention)."""
    import io
    n = name.lower()
    if n.endswith(".docx"):
        from docx import Document
        d = Document(io.BytesIO(data))
        parts = [p.text for p in d.paragraphs if p.text.strip()]
        for t in d.tables:
            for row in t.rows:
                parts.append(" | ".join(c.text.strip() for c in row.cells))
        return "\n".join(parts)[:max_chars]
    if n.endswith(".pdf"):
        from pypdf import PdfReader
        rd = PdfReader(io.BytesIO(data))
        return "\n".join((pg.extract_text() or "") for pg in rd.pages[:max_pages])[:max_chars]
    return data.decode("utf-8", errors="ignore")[:max_chars]


def prompt_extract(kind: str, doc_name: str, text: str) -> str:
    what = {"risks": "riscos (ameaças e oportunidades)", "controls": "controlos internos existentes ou recomendados",
            "actions": "ações de tratamento / recomendações", "kris": "indicadores-chave de risco"}[kind]
    return (f"Extrai do documento «{doc_name}» (relatório de auditoria, política, ata, relatório de risco, plano…) todos os {what} "
            "que nele estejam descritos ou claramente implícitos. Não inventes factos: se o documento não indicar avaliação, estima-a "
            "de forma conservadora e explica no campo de justificação/procedimento. Usa IDs de riscos existentes do projeto quando "
            "os itens se referirem a eles.\n\n=== DOCUMENTO ===\n" + text)


# ------------------------------------------------------------- prompt generator (no API key)
def build_prompt(proj: dict, task: str) -> str:
    """Ready-to-paste prompt for any AI assistant when there is no API key (Gestão Studio convention)."""
    lang_name = "português europeu (PT-PT)" if lang() == "pt" else "English"
    tasks = {
        "exec": PROMPTS_TEXT["exec"][0],
        "bias": PROMPTS_TEXT["bias"][0],
        "premortem": PROMPTS_TEXT["premortem"][0],
        "scenarios": PROMPTS_TEXT["scenarios"][0],
        "audit": PROMPTS_TEXT["audit"][0],
        "risks": prompt_identify(8, "") + " Apresenta o resultado numa tabela com as colunas: tipo, categoria, título, causa, evento, efeito, responsável, P, I, velocidade, estratégia.",
        "controls": prompt_controls([]) + " Apresenta numa tabela: riscos, controlo, objetivo, tipo, natureza, frequência, linha, responsável, evidência, procedimento de teste.",
        "kris": prompt_kris([]) + " Apresenta numa tabela: risco, KRI, unidade, sentido, âmbar, vermelho, frequência, responsável.",
    }
    if task not in tasks and len(task) > 40:  # a full page prompt (per-page assistant without key)
        return (f"Atua como consultor sénior de gestão de risco (ISO 31000, COSO ERM, Modelo das 3 Linhas, Hillson). "
                f"Responde em {lang_name}.\n\n## Contexto do projeto (exportado do Risk Studio)\n{project_context(proj, 25)}\n\n{task}")
    return (f"Atua como consultor sénior de gestão de risco (ISO 31000, COSO ERM, Modelo das 3 Linhas, Hillson). "
            f"Responde em {lang_name}.\n\n## Contexto do projeto (exportado do Risk Studio)\n{project_context(proj)}\n\n"
            f"## Tarefa\n{tasks.get(task, task)}")


# ------------------------------------------------------------- per-page assistant (every analysis page)
PAGE_MODES = {
    "interpret": ("Interpreta estes resultados para um decisor: o que significam, o que preocupa, o que está bem, pressupostos frágeis. "
                  "Estrutura: ### Leitura · ### O que preocupa · ### O que está bem · ### Pressupostos a validar. Máx. 350 palavras.",
                  "Interpret these results for a decision maker: meaning, concerns, strengths, fragile assumptions. "
                  "Structure: ### Reading · ### Concerns · ### Strengths · ### Assumptions to validate. Max 350 words."),
    "recommend": ("Com base nestes resultados, propõe 5 recomendações priorizadas (o quê, quem, até quando, impacto esperado no risco) "
                  "e indica que outra página/técnica do Risk Studio usar a seguir. Máx. 350 palavras.",
                  "Based on these results, propose 5 prioritised recommendations (what, who, by when, expected effect on risk) "
                  "and say which other Risk Studio page/technique to use next. Max 350 words."),
}


def page_prompt(proj: dict, page: str, data_text: str, rule_lines: list[str], mode: str = "interpret", question: str = "") -> str:
    task = question.strip() if mode == "ask" and question.strip() else PAGE_MODES[mode if mode in PAGE_MODES else "interpret"][1 if lang() == "en" else 0]
    return (f"Página do Risk Studio: «{page}».\n\nDados e resultados desta página:\n{data_text[:30000]}\n\n"
            "Leitura automática por regras (já mostrada ao utilizador — não repitas, aprofunda):\n" + "\n".join(f"- {x}" for x in rule_lines) +
            f"\n\nTarefa: {task}")


def page_assist(proj: dict, page: str, data_text: str, rule_lines: list[str], mode: str = "interpret", question: str = "") -> str:
    return complete(proj, page_prompt(proj, page, data_text, rule_lines, mode, question), 2500)
