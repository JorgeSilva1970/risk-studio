"""Shared UI: session state, styling, editable tables, KPI cards, formatting."""
from __future__ import annotations

import datetime as dt
import html

import pandas as pd
import streamlit as st

from core import db
from core.catalogs import CATALOGS, label, labels
from core.i18n import L, lang
from core.model import SCHEMAS, coerce_df, ids_list, new_project, to_json

# ------------------------------------------------------------- labels
FIELD_LABELS: dict[str, tuple[str, str]] = {
    "id": ("ID", "ID"), "type": ("Tipo", "Type"), "category": ("Categoria", "Category"),
    "title": ("Risco (título)", "Risk (title)"), "cause": ("Causa(s) — separar por ;", "Cause(s) — separate with ;"),
    "event": ("Evento de risco", "Risk event"), "effect": ("Consequência(s) — separar por ;", "Consequence(s) — separate with ;"),
    "owner": ("Responsável", "Owner"), "objective": ("Objetivo afetado", "Objective affected"),
    "p_inh": ("P inerente", "Inherent P"), "i_inh": ("I inerente", "Inherent I"), "velocity": ("Velocidade", "Velocity"),
    "proximity": ("Proximidade", "Proximity"), "p_res_ovr": ("P residual (manual)", "Residual P (override)"),
    "i_res_ovr": ("I residual (manual)", "Residual I (override)"), "p_tgt": ("P alvo", "Target P"), "i_tgt": ("I alvo", "Target I"),
    "strategy": ("Estratégia", "Strategy"), "status": ("Estado", "Status"), "trend": ("Tendência", "Trend"),
    "prob_pct": ("Prob. % (quant.)", "Prob. % (quant.)"), "imp_min": ("Impacto mín.", "Impact min"),
    "imp_ml": ("Impacto + provável", "Impact most likely"), "imp_max": ("Impacto máx.", "Impact max"),
    "notes": ("Notas", "Notes"),
    "name": ("Controlo", "Control"), "description": ("Descrição", "Description"),
    "risk_ids": ("Riscos ligados", "Linked risks"), "control_type": ("Tipo de controlo", "Control type"),
    "nature": ("Natureza", "Nature"), "frequency": ("Frequência", "Frequency"), "line": ("Linha (3 Linhas)", "Line (3 Lines)"),
    "evidence": ("Evidência", "Evidence"), "design_test": ("Teste de desenho", "Design test"),
    "operating_test": ("Teste de eficácia operacional", "Operating effectiveness test"), "test_date": ("Data do teste", "Test date"),
    "tester": ("Testado por", "Tested by"), "cost": ("Custo anual", "Annual cost"),
    "risk_id": ("Risco", "Risk"), "control_id": ("Controlo", "Control"), "start": ("Início", "Start"), "due": ("Prazo", "Due"),
    "progress": ("Progresso %", "Progress %"), "unit": ("Unidade", "Unit"), "direction": ("Sentido", "Direction"),
    "amber": ("Limiar âmbar", "Amber threshold"), "red": ("Limiar vermelho", "Red threshold"),
    "previous": ("Valor anterior", "Previous value"), "current": ("Valor atual", "Current value"),
    "process": ("Processo / etapa", "Process / step"), "failure_mode": ("Modo de falha", "Failure mode"),
    "current_controls": ("Controlos atuais", "Current controls"), "s": ("S (gravidade)", "S (severity)"),
    "o": ("O (ocorrência)", "O (occurrence)"), "d": ("D (deteção)", "D (detection)"), "action": ("Ação recomendada", "Recommended action"),
    "scenario": ("Cenário", "Scenario"), "asset": ("Ativo", "Asset"), "threat": ("Agente de ameaça", "Threat actor"),
    "tef_min": ("TEF mín./ano", "TEF min/yr"), "tef_ml": ("TEF + provável", "TEF most likely"), "tef_max": ("TEF máx.", "TEF max"),
    "vuln_min": ("Vuln. mín.", "Vuln. min"), "vuln_ml": ("Vuln. + provável", "Vuln. most likely"), "vuln_max": ("Vuln. máx.", "Vuln. max"),
    "plm_min": ("Perda primária mín.", "Primary loss min"), "plm_ml": ("Perda primária + provável", "Primary loss most likely"),
    "plm_max": ("Perda primária máx.", "Primary loss max"), "slef": ("Prob. perda secundária", "Secondary loss prob."),
    "slm_min": ("Perda secundária mín.", "Secondary loss min"), "slm_ml": ("Perda secundária + provável", "Secondary loss most likely"),
    "slm_max": ("Perda secundária máx.", "Secondary loss max"),
    "appetite": ("Apetite (score máx.)", "Appetite (max score)"), "tolerance": ("Tolerância (score máx.)", "Tolerance (max score)"),
    "target": ("Alvo", "Target"), "dim": ("Dimensão", "Dimension"),
}

FIELD_HELP: dict[str, tuple[str, str]] = {
    "title": ("Use a metalinguagem: 'Devido a <causa>, pode ocorrer <evento>, levando a <efeito>'.",
              "Use risk metalanguage: 'Because of <cause>, <event> may occur, leading to <effect>'."),
    "p_inh": ("1 Rara · 2 Improvável · 3 Possível · 4 Provável · 5 Quase certa (sem controlos)",
              "1 Rare · 2 Unlikely · 3 Possible · 4 Likely · 5 Almost certain (before controls)"),
    "i_inh": ("1 Insignificante … 5 Catastrófico (sem controlos)", "1 Insignificant … 5 Catastrophic (before controls)"),
    "velocity": ("Rapidez com que o impacto se materializa: 1 meses/anos … 5 imediato",
                 "How fast the impact materialises: 1 months/years … 5 immediate"),
    "p_res_ovr": ("Opcional: deixe vazio para cálculo automático a partir da eficácia dos controlos",
                  "Optional: leave blank to compute from control effectiveness"),
    "i_res_ovr": ("Opcional: deixe vazio para cálculo automático", "Optional: leave blank for automatic calculation"),
    "p_tgt": ("Nível que se pretende atingir após o tratamento", "Level intended after treatment"),
    "prob_pct": ("Probabilidade anual em % para Monte Carlo (opcional; senão usa a escala)",
                 "Annual probability % for Monte Carlo (optional; otherwise scale midpoint)"),
    "imp_ml": ("Impacto financeiro mais provável (para Monte Carlo)", "Most likely financial impact (Monte Carlo)"),
    "risk_ids": ("Riscos que o controlo mitiga — cada controlo deve mapear para ≥1 risco",
                 "Risks the control addresses — every control should map to ≥1 risk"),
    "design_test": ("O controlo, se operar como desenhado, mitiga o risco?", "If operated as designed, does the control mitigate the risk?"),
    "operating_test": ("O controlo funcionou de forma consistente no período (amostra)?",
                       "Did the control operate consistently over the period (sample)?"),
    "slef": ("Fração de eventos com perdas secundárias (0–1)", "Share of events with secondary losses (0–1)"),
    "vuln_ml": ("Probabilidade (0–1) de a ameaça ter sucesso", "Probability (0–1) the threat succeeds"),
}


TABLE_LABELS: dict[tuple[str, str], tuple[str, str]] = {
    ("controls", "objective"): ("Objetivo de controlo", "Control objective"),
    ("controls", "notes"): ("Notas / procedimento de teste", "Notes / test procedure"),
    ("maturity", "current"): ("Atual (1–5)", "Current (1–5)"),
    ("maturity", "target"): ("Alvo (1–5)", "Target (1–5)"),
    ("maturity", "evidence"): ("Evidência / justificação", "Evidence / rationale"),
    ("appetite", "category"): ("Categoria", "Category"),
    ("kris", "name"): ("Indicador (KRI)", "Indicator (KRI)"),
    ("kris", "frequency"): ("Frequência de medição", "Measurement frequency"),
    ("actions", "description"): ("Ação", "Action"),
    ("fmea", "owner"): ("Responsável", "Owner"),
}


def flabel(field: str, table: str | None = None) -> str:
    t = TABLE_LABELS.get((table, field)) or FIELD_LABELS.get(field, (field, field))
    return t[1] if lang() == "en" else t[0]


def fhelp(field: str) -> str | None:
    t = FIELD_HELP.get(field)
    return (t[1] if lang() == "en" else t[0]) if t else None


# ------------------------------------------------------------- state
def init_state():
    ss = st.session_state
    ss.setdefault("lang", "pt")
    ss.setdefault("ver", {})
    ss.setdefault("pid", None)
    ss.setdefault("dirty", False)
    ss.setdefault("autosave", True)
    ss.setdefault("chat", [])
    if "proj" not in ss:
        # restore language and last project after a browser reload (?lang=..&pid=..) — PM Studio behaviour
        qp = st.query_params
        if qp.get("lang") in ("pt", "en"):
            ss.lang = qp.get("lang")
        loaded = None
        if qp.get("pid"):
            try:
                from core.model import from_json
                data = db.load_project(int(qp.get("pid")))
                loaded = from_json(data) if data else None
            except Exception:
                loaded = None
        if loaded:
            ss.proj = loaded
            ss.pid = int(qp.get("pid"))
            ss.example_loaded = False
        else:
            from core.examples import load_example
            ss.proj = load_example("insurance")
            ss.example_loaded = True


def sync_query():
    """Keep ?lang and ?pid in the URL so a browser reload reopens the same project."""
    try:
        qp = st.query_params
        if qp.get("lang") != st.session_state.lang:
            qp["lang"] = st.session_state.lang
        pid = st.session_state.get("pid")
        if pid and qp.get("pid") != str(pid):
            qp["pid"] = str(pid)
        if not pid and "pid" in qp:
            del qp["pid"]
    except Exception:
        pass


def proj() -> dict:
    return st.session_state.proj


def bump(table: str):
    v = st.session_state.ver
    v[table] = v.get(table, 0) + 1


def bump_all():
    for t in SCHEMAS:
        bump(t)
    bump("meta")


def set_project(p: dict, pid: int | None = None):
    st.session_state.proj = p
    st.session_state.pid = pid
    st.session_state.dirty = False
    st.session_state.chat = []
    st.session_state.pop("mc_result", None)
    st.session_state.pop("ai_preview", None)
    st.session_state.example_loaded = False
    bump_all()


def mark_dirty():
    st.session_state.dirty = True
    autosave()


def autosave():
    pid = st.session_state.get("pid")
    if not pid or not st.session_state.get("autosave", True):
        return
    try:
        p = proj()
        db.save_project(p["meta"]["name"], p["meta"].get("industry", ""), to_json(p), pid)
        st.session_state.dirty = False
        _auto_review(pid)
    except Exception:
        pass


def _auto_review(pid: int) -> None:
    """First save of each day records a review (snapshot + module analyses) for the timeline."""
    today = dt.date.today().isoformat()
    if st.session_state.get("_auto_review") == (pid, today):
        return
    from core import history as H
    if H.maybe_auto_review(proj(), pid):
        st.session_state["_flash"] = st.session_state.get("_flash", []) + [
            L("📸 Revisão automática do dia registada (Evolução & comparação).", "📸 Daily automatic review recorded (Evolution & comparison).")]
    st.session_state["_auto_review"] = (pid, today)


def save_to_db() -> int:
    p = proj()
    pid = db.save_project(p["meta"]["name"], p["meta"].get("industry", ""), to_json(p), st.session_state.get("pid"))
    st.session_state.pid = pid
    st.session_state.dirty = False
    _auto_review(pid)
    return pid


# ---------------------------------------------------------- formatting
def money(v, cur: str | None = None, dec: int = 0) -> str:
    cur = cur or proj()["meta"].get("currency", "€")
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    if lang() == "en":
        return f"{cur}{v:,.{dec}f}"
    s = f"{v:,.{dec}f}".replace(",", " ").replace(".", ",")
    return f"{s} {cur}"


def pct(v, dec=0) -> str:
    if v is None:
        return "—"
    s = f"{v * 100:.{dec}f}%"
    return s.replace(".", ",") if lang() == "pt" else s


# ------------------------------------------------------------- styling
def inject_css():
    from core.theme import CSS
    st.markdown(CSS, unsafe_allow_html=True)


def flash(msg: str) -> None:
    """Toast shown on the NEXT run (st.toast followed by st.rerun would be lost)."""
    st.session_state.setdefault("_flash", []).append(msg)


def show_flash() -> None:
    for m_ in st.session_state.pop("_flash", []):
        st.toast(m_)


def hero(title: str, subtitle: str = "", icon: str = "", help_key: str | None = None):
    """Page header: title band, active project, legend (what it is · how to read · sources)."""
    show_flash()
    st.session_state["_fig_page"] = title
    st.session_state["_fig_n"] = 0
    st.markdown(f"<div class='rs-hero'><h1>{icon} {html.escape(title)}</h1><p>{html.escape(subtitle)}</p></div>",
                unsafe_allow_html=True)
    m = proj()["meta"]
    from core.catalogs import INDUSTRIES
    from core.i18n import tr
    st.caption(f"📁 **{m.get('name', '')}** · {tr(INDUSTRIES.get(m.get('industry'), ('', '')))}")
    if help_key:
        help_panel(help_key)


def help_panel(key: str, expanded: bool = False):
    from core.help_texts import H, SRC
    h = H.get(key)
    if not h:
        return
    what, how, srcs = h["en" if lang() == "en" else "pt"]
    with st.expander(L("ℹ️ Legenda — o que é, como se lê e fontes", "ℹ️ Legend — what it is, how to read it, sources"), expanded=expanded):
        st.markdown(f"**{L('O que é', 'What it is')}.** {what}")
        st.markdown(f"**{L('Como se lê', 'How to read it')}.** {how}")
        st.markdown(f"**{L('Fontes', 'Sources')}:**\n" + "\n".join(f"- {SRC[s]}" for s in srcs if s in SRC))


def interpret_box(lines: list[str] | str, title: str | None = None):
    """Rule-based interpretation (works without AI), PM Studio style."""
    if not lines:
        return
    if isinstance(lines, str):
        lines = [lines]
    with st.container(border=True):
        st.markdown(f"**🧭 {title or L('Interpretação automática', 'Automatic interpretation')}**")
        st.markdown("\n".join(f"- {x}" for x in lines))


def ai_assist(module: str, lines: list[str] | None = None, data_text: str | None = None, page_title: str | None = None):
    """Generic AI agent for every analysis page (complements the rule-based box): interpret, recommend, ask,
    and save the analysis (rules + AI text + KPIs) to the database for temporal comparison. Without a key → prompt generator."""
    import json

    from core import ai
    from core import history as H
    lines = lines or []
    page_title = page_title or H.mod_name(module)
    if data_text is None:
        kp, det = H.module_summary(proj(), module)
        data_text = json.dumps({"kpis": kp, "details": det}, ensure_ascii=False, default=str)[:30000]
    key = f"aiassist_{module}"
    with st.expander(L("🤖 Agente IA — interpretar, recomendar e guardar esta análise", "🤖 AI agent — interpret, recommend and save this analysis"),
                     expanded=bool(st.session_state.get(key))):
        if ai.available():
            c1, c2, c3 = st.columns([1, 1, 2])
            mode = None
            if c1.button(L("🧠 Interpretar", "🧠 Interpret"), key=f"{key}_i", type="primary", width="stretch"):
                mode = "interpret"
            if c2.button(L("🎯 Recomendações", "🎯 Recommendations"), key=f"{key}_r", width="stretch"):
                mode = "recommend"
            q = c3.text_input(L("Pergunta sobre esta página", "Question about this page"), key=f"{key}_q",
                              placeholder=L("ex.: que risco devo tratar primeiro e porquê?", "e.g. which risk should I treat first and why?"),
                              label_visibility="collapsed")
            if q and st.button(L("💬 Perguntar", "💬 Ask"), key=f"{key}_a"):
                mode = "ask"
            if mode:
                with st.spinner(L("O agente está a analisar…", "The agent is analysing…")):
                    st.session_state[key] = ai.page_assist(proj(), page_title, data_text, lines, mode, q or "")
            if st.session_state.get(key):
                with st.container(border=True):
                    st.markdown(st.session_state[key])
        else:
            st.caption(L("Sem chave API: copie o prompt (botão no canto do bloco) e cole-o em qualquer assistente de IA.",
                         "No API key: copy the prompt (button in the block corner) into any AI assistant."))
            st.code(ai.build_prompt(proj(), ai.page_prompt(proj(), page_title, data_text, lines, "interpret")), language="markdown")
        c1, c2 = st.columns([1, 3])
        if c1.button(L("💾 Guardar análise no histórico", "💾 Save analysis to history"), key=f"{key}_s", width="stretch"):
            try:
                pid = st.session_state.get("pid") or save_to_db()
                kp, det = H.module_summary(proj(), module) if module in H.MODULES else ({}, {})
                lab = f"{page_title} · {dt.datetime.now():%d/%m/%Y %H:%M}"
                db.save_analysis(pid, module, lab, kp, det, "\n".join(lines), st.session_state.get(key, "") or "")
                st.toast(L("Análise guardada na base de dados ✔ — veja em «Evolução & comparação».",
                           "Analysis saved to the database ✔ — see 'Evolution & comparison'."))
            except Exception as e:
                st.error(f"DB: {e}")
        c2.caption(L("Guarda os indicadores desta página, a leitura automática e o texto do agente com data e hora (PostgreSQL), para comparar com análises futuras.",
                     "Stores this page's indicators, the automatic reading and the agent text with a timestamp (PostgreSQL) for future comparison."))


def kpi(col, label_: str, value: str, sub: str = "", colour: str = "#2a78d6"):
    col.markdown(f"<div class='rs-kpi' style='border-left-color:{colour}'><div class='l'>{html.escape(label_)}</div>"
                 f"<div class='v'>{html.escape(value)}</div><div class='s'>{html.escape(sub)}</div></div>",
                 unsafe_allow_html=True)


def pill(text: str, colour: str) -> str:
    return f"<span class='rs-pill' style='background:{colour}1f;border:1px solid {colour};color:{colour}'>{html.escape(text)}</span>"


def note(text: str, kind: str = ""):
    st.markdown(f"<div class='rs-note {kind}'>{text}</div>", unsafe_allow_html=True)


def _slug(s: str) -> str:
    import re
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")[:50] or "risk"


def _fig_name(title: str | None = None) -> str:
    st.session_state["_fig_n"] = st.session_state.get("_fig_n", 0) + 1
    base = title or st.session_state.get("_fig_page") or "grafico"
    n = st.session_state["_fig_n"]
    return f"{base}" + (f" {n}" if not title and n > 1 else "")


def plotly_defaults() -> None:
    """Every Plotly chart: camera button downloads a PNG at 3× (≈300 dpi on A4) with a meaningful file name; no logo."""
    from streamlit.delta_generator import DeltaGenerator
    if getattr(DeltaGenerator.plotly_chart, "_rs_patched", False):
        return
    orig = DeltaGenerator.plotly_chart

    def patched(self, figure_or_data, *args, config=None, **kwargs):
        try:
            t = figure_or_data.layout.title.text if hasattr(figure_or_data, "layout") else None
        except Exception:
            t = None
        try:
            fname = f"{_slug(proj()['meta'].get('name', 'risk'))[:40]}_{_slug(_fig_name(t))}"
        except Exception:
            fname = "risk_studio"
        cfg = {"displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 3, "filename": fname}}
        cfg.update(config or {})
        return orig(self, figure_or_data, *args, config=cfg, **kwargs)
    patched._rs_patched = True
    DeltaGenerator.plotly_chart = patched
    try:
        st.plotly_chart = patched.__get__(st._main, DeltaGenerator)
    except Exception:
        pass


# ------------------------------------------------------- table editor
def _col_config(table: str, field: str, kind: str, risk_ids: list[str]):
    lab, hlp = flabel(field, table), fhelp(field)
    if field == "id":
        return st.column_config.TextColumn(lab, disabled=True, width="small")
    if field == "risk_id":
        return st.column_config.SelectboxColumn(lab, options=risk_ids, width="small")
    if field == "control_id":
        cids = list(proj()["controls"]["id"]) if not proj()["controls"].empty else []
        return st.column_config.SelectboxColumn(lab, options=cids, width="small")
    if kind == "str":
        wide = field in ("title", "cause", "event", "effect", "description", "failure_mode", "scenario", "name", "objective")
        return st.column_config.TextColumn(lab, help=hlp, width="large" if wide else "medium")
    if kind == "int":
        if field in ("s", "o", "d"):
            return st.column_config.NumberColumn(lab, help=hlp, min_value=1, max_value=10, step=1, width="small")
        if field == "progress":
            return st.column_config.NumberColumn(lab, min_value=0, max_value=100, step=5, format="%d%%", width="small")
        return st.column_config.NumberColumn(lab, help=hlp, min_value=1, max_value=5 if table != "appetite" else 25, step=1, width="small")
    if kind == "float":
        if field in ("vuln_min", "vuln_ml", "vuln_max", "slef"):
            return st.column_config.NumberColumn(lab, help=hlp, min_value=0.0, max_value=1.0, step=0.01, format="%.2f")
        if field == "prob_pct":
            return st.column_config.NumberColumn(lab, help=hlp, min_value=0.0, max_value=100.0, step=1.0, format="%.0f%%")
        if field.startswith("tef"):
            return st.column_config.NumberColumn(lab, help=hlp, min_value=0.0, step=0.1, format="%.2f")
        return st.column_config.NumberColumn(lab, help=hlp, format="localized", min_value=None)
    if kind == "date":
        return st.column_config.DateColumn(lab, help=hlp, format="DD/MM/YYYY")
    if kind == "ids":
        return st.column_config.MultiselectColumn(lab, help=hlp, options=risk_ids, width="medium")
    if kind.startswith("cat:"):
        return st.column_config.SelectboxColumn(lab, help=hlp, options=labels(kind[4:]), required=False, width="medium")
    return lab


def to_display(table: str, df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    for field, kind, _ in SCHEMAS[table]:
        if field not in d:
            continue
        if kind.startswith("cat:"):
            d[field] = d[field].map(lambda v, c=kind[4:]: label(c, v) if v is not None and v == v else None)
        elif kind == "date":
            d[field] = d[field].map(lambda v: dt.date.fromisoformat(v[:10]) if isinstance(v, str) and v else None)
        elif kind == "ids":
            d[field] = d[field].map(ids_list)
    return d


def table_editor(table: str, fields: list[str], computed: pd.DataFrame | None = None,
                 computed_cfg: dict | None = None, height: int | None = None, fixed: bool = False,
                 key_suffix: str = "", row_filter=None, help_text: str | None = None,
                 lead_computed: bool = False) -> None:
    """Editable table inside a form. `computed` columns (same index) are shown read-only."""
    p = proj()
    base = p[table].reset_index(drop=True)
    view = base if row_filter is None else base[row_filter(base)]
    disp = to_display(table, view)
    order = list(fields)
    cfg = {}
    rids = list(p["risks"]["id"]) if not p["risks"].empty else []
    kinds = {f: k for f, k, _ in SCHEMAS[table]}
    for f in fields:
        cfg[f] = _col_config(table, f, kinds[f], rids)
    if computed is not None and not computed.empty and len(computed) == len(view):
        for c in computed.columns:
            disp[c] = computed[c].values
            if lead_computed:
                order.insert(0, c)
            else:
                order.append(c)
        cfg.update(computed_cfg or {})
    for c in disp.columns:
        if c not in order:
            cfg.setdefault(c, None)
    ver = st.session_state.ver.get(table, 0)
    with st.form(f"form_{table}{key_suffix}_{ver}_{lang()}", border=False):
        if help_text:
            st.caption(help_text)
        edited = st.data_editor(
            disp, column_config=cfg, column_order=order, hide_index=True, width="stretch",
            num_rows="fixed" if fixed else "dynamic", height=height or "auto", key=f"ed_{table}{key_suffix}_{ver}_{lang()}",
        )
        c1, c2 = st.columns([1, 4])
        ok = c1.form_submit_button(L("💾 Guardar alterações", "💾 Save changes"), type="primary", width="stretch")
        c2.caption(L("As alterações só são aplicadas ao clicar em Guardar. Adicione linhas no fim da tabela; "
                     "selecione linhas e use o caixote para apagar.",
                     "Changes apply when you click Save. Add rows at the bottom; select rows and use the bin to delete."))
    if ok:
        keep = [f for f, _, _ in SCHEMAS[table]]
        new_part = edited[[c for c in keep if c in edited.columns]]
        if row_filter is not None:
            rest = base[~row_filter(base)]
            new_part = pd.concat([rest, coerce_df(table, new_part)], ignore_index=True)
        p[table] = coerce_df(table, new_part)
        bump(table)
        mark_dirty()
        flash(L("Alterações guardadas ✔", "Changes saved ✔"))
        st.rerun()


def require_rows(table: str, msg_pt: str, msg_en: str) -> bool:
    if proj()[table].empty:
        st.info(L(msg_pt, msg_en))
        return False
    return True


def risk_options(only_type: str | None = None) -> dict[str, str]:
    r = proj()["risks"]
    if r.empty:
        return {}
    if only_type:
        r = r[r["type"] == only_type]
    return {row["id"]: f"{row['id']} · {row['title']}" for row in r.to_dict(orient="records")}


def new_blank_project():
    set_project(new_project())
