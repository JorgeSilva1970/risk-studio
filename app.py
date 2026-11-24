"""Risk Studio — Enterprise Risk Management (ISO 31000 · COSO ERM · 3 Lines · FAIR)
Run: streamlit run app.py"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

try:  # local development: read .env (ANTHROPIC_API_KEY, DATABASE_URL) — PM Studio convention
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).with_name(".env"))
except Exception:
    pass

st.set_page_config(page_title="Risk Studio", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

import core.theme  # noqa: E402,F401  (registers the Plotly template)
from core import ai, db  # noqa: E402
from core.i18n import L  # noqa: E402
from core.model import from_json  # noqa: E402
from core.ui import (flash, init_state, inject_css, plotly_defaults, proj, save_to_db, set_project,  # noqa: E402
                     sync_query)

VERSION = "v1.2"
init_state()
inject_css()
plotly_defaults()
_assets = Path(__file__).with_name("assets")
st.logo(str(_assets / "logo.svg"), size="large", icon_image=str(_assets / "icon.svg"))

# ------------------------------------------------------------------ sidebar (same layout as PM Studio / Gestão Studio)
with st.sidebar:
    lang_choice = st.segmented_control("Idioma / Language", ["pt", "en"], default=st.session_state.lang,
                                       format_func=lambda x: "🇵🇹 Português" if x == "pt" else "🇬🇧 English",
                                       label_visibility="collapsed", key="lang_sc")
    if lang_choice and lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()

pages = {
    L("Visão geral", "Overview"): [
        st.Page("views/painel.py", title=L("Painel de risco", "Risk dashboard"), icon=":material/dashboard:", default=True),
        st.Page("views/evolucao.py", title=L("Evolução & comparação", "Evolution & comparison"), icon=":material/timeline:"),
        st.Page("views/contexto.py", title=L("Contexto & apetite", "Context & appetite"), icon=":material/explore:"),
    ],
    L("Identificar & avaliar", "Identify & assess"): [
        st.Page("views/registo.py", title=L("Registo de riscos", "Risk register"), icon=":material/list_alt:"),
        st.Page("views/matriz.py", title=L("Matrizes & prioridades", "Matrices & priorities"), icon=":material/grid_on:"),
        st.Page("views/tecnicas.py", title=L("Bow-Tie & FMEA", "Bow-Tie & FMEA"), icon=":material/hub:"),
    ],
    L("Controlar & tratar", "Control & treat"): [
        st.Page("views/controlos.py", title=L("Controlos & RCM", "Controls & RCM"), icon=":material/verified_user:"),
        st.Page("views/tratamento.py", title=L("Tratamento & ações", "Treatment & actions"), icon=":material/task_alt:"),
        st.Page("views/kris.py", title=L("KRIs & monitorização", "KRIs & monitoring"), icon=":material/monitoring:"),
    ],
    L("Quantificar & melhorar", "Quantify & improve"): [
        st.Page("views/quant.py", title=L("Monte Carlo & FAIR", "Monte Carlo & FAIR"), icon=":material/casino:"),
        st.Page("views/maturidade.py", title=L("Maturidade ERM", "ERM maturity"), icon=":material/stairs:"),
    ],
    L("IA, relatórios & dados", "AI, reports & data"): [
        st.Page("views/agente.py", title=L("Agente IA", "AI Agent"), icon=":material/smart_toy:"),
        st.Page("views/relatorios.py", title=L("Relatórios", "Reports"), icon=":material/description:"),
        st.Page("views/dados.py", title=L("Dados & templates", "Data & templates"), icon=":material/upload_file:"),
        st.Page("views/metodologia.py", title=L("Metodologia & guia", "Methodology & guide"), icon=":material/school:"),
    ],
}
nav = st.navigation(pages, expanded=True)

with st.sidebar:
    st.divider()
    p = proj()
    # active project (database) — Gestão Studio style
    try:
        items = db.list_projects()
        db_ok = True
    except Exception as e:  # pragma: no cover
        items, db_ok = [], False
        st.caption(f"⚠️ BD: {e}")
    if db_ok:
        # stable order (by id): a selectbox keeps its position, so ordering by "last updated" would jump to another project after a save
        opts = [None] + sorted(it["id"] for it in items)
        names = {it["id"]: it["name"] for it in items}
        cur = st.session_state.get("pid")
        sel = st.selectbox(L("📁 Projeto ativo", "📁 Active project"), opts, index=opts.index(cur) if cur in opts else 0,
                           format_func=lambda i: (L("— não guardado: ", "— unsaved: ") + str(p["meta"].get("name", ""))[:28]) if i is None else names.get(i, str(i)),
                           key=f"proj_sel_{cur}")
        if sel != cur and sel is not None:
            data = db.load_project(sel)
            if data:
                set_project(from_json(data), sel)
                st.rerun()
    pid = st.session_state.get("pid")
    if pid:
        st.caption(L("Guardado na BD · id ", "Saved in DB · id ") + str(pid) + ("  ✏️ " + L("alterações por guardar", "unsaved changes") if st.session_state.dirty else ""))
    else:
        st.caption(L("⚠️ Ainda não guardado na base de dados", "⚠️ Not saved to the database yet"))
    c1, c2 = st.columns(2)
    if c1.button(L("💾 Guardar", "💾 Save"), width="stretch", type="primary"):
        try:
            pid = save_to_db()
            flash(L(f"Projeto guardado na base de dados ✅ (#{pid})", f"Project saved to the database ✅ (#{pid})"))
            st.rerun()
        except Exception as e:
            st.error(f"DB: {e}")
    st.session_state.autosave = c2.toggle(L("Auto", "Auto"), value=st.session_state.get("autosave", True),
                                          help=L("Guardar automaticamente cada alteração (depois da 1.ª gravação)",
                                                 "Automatically save every change (after the first save)"))

    with st.expander(L("🤖 Agente IA (Claude)", "🤖 AI agent (Claude)"), expanded=False):
        if ai.available():
            st.success(L("Ligado", "Connected") + f" · {ai.model()}")
        else:
            st.info(L("Sem chave API: cálculos, gráficos e relatórios funcionam; a IA fica em modo «gerador de prompt».",
                      "No API key: everything works; AI falls back to the prompt generator."))
        st.text_input(L("Chave API Anthropic (só nesta sessão)", "Anthropic API key (this session only)"), type="password",
                      key="api_key_override", help=L("Em produção defina ANTHROPIC_API_KEY no Render.", "In production set ANTHROPIC_API_KEY on Render."))
        models = list(ai.MODELS)
        st.selectbox(L("Modelo", "Model"), models, index=models.index(ai.model()) if ai.model() in models else 0,
                     format_func=lambda m: ai.MODELS[m], key="ai_model")
        if ai.available() and st.button(L("🔌 Testar ligação", "🔌 Test connection"), key="ai_test", width="stretch"):
            ok, msg = ai.test_connection()
            (st.success if ok else st.error)(msg)
    st.caption(f"💾 {db.backend_name()} · Risk Studio {VERSION}")

nav.run()
sync_query()
