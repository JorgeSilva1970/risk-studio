from types import SimpleNamespace

import streamlit as st

from core import db
from core.catalogs import INDUSTRIES
from core.examples import EXAMPLES, load_example
from core.excel_io import build_workbook, merge_into, read_workbook
from core.professor import export_risk_register, parse_upload
from core.templates_zip import build_zip, read_module_workbook, read_zip


@st.cache_data(show_spinner=False)
def _zip(lg: str) -> bytes:
    return build_zip(lg)


def is_module_file(content: bytes) -> bool:
    import io

    from openpyxl import load_workbook

    from core.templates_zip import is_module_workbook
    try:
        return is_module_workbook(load_workbook(io.BytesIO(content), read_only=True))
    except Exception:
        return False
from core.i18n import L, lang, tr
from core.model import from_json, new_project
from core.ui import flash, hero, mark_dirty, note, proj, set_project

hero(L("Dados & templates", "Data & templates"),
     L("Local único de carregamento · template Excel · exemplos por indústria · projetos guardados",
       "Single upload point · Excel template · industry examples · saved projects"), "📂", help_key="data")

t1, t2, t3, t4 = st.tabs([L("① Template & carregamento", "① Template & upload"), L("② Exemplos por indústria", "② Industry examples"),
                          L("③ Projetos guardados", "③ Saved projects"), L("④ Novo / restaurar", "④ New / restore")])

TNAMES = {"risks": L("riscos", "risks"), "controls": L("controlos", "controls"), "actions": L("ações", "actions")}

with t1:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"#### {L('1. Descarregar modelos', '1. Download templates')}")
        st.caption(L("Template Risk Studio: um único ficheiro com todas as folhas (Contexto, Apetite, Riscos, Controlos, Ações, KRIs, FMEA, FAIR, "
                     "Maturidade), listas pendentes, instruções e dicionário de dados.",
                     "Risk Studio template: one file with every sheet, drop-down lists, instructions and a data dictionary."))
        st.download_button(L("⬇️ ZIP com todos os templates em branco (um por módulo)", "⬇️ ZIP with every blank template (one per module)"),
                           _zip(lang()), "Templates_Risk_Studio.zip", "application/zip", type="primary", width="stretch",
                           help=L("Como no Gestão Studio: 00_INDICE + um ficheiro por módulo com a folha «Instruções» (como preencher, regras, dicionário "
                                  "e exemplo), «campos» e folhas de dados com listas pendentes; inclui o RiskRegister do professor.",
                                  "Like Gestão Studio: 00_INDICE + one file per module with the 'Instruções' sheet, 'campos' and data sheets; "
                                  "includes the professor's RiskRegister."))
        st.download_button(L("⬇️ Template único (todas as folhas num só ficheiro)", "⬇️ Single template (all sheets in one file)"), build_workbook(None, lang()),
                           "RiskStudio_template.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
        st.download_button(L("⬇️ Template preenchido com o projeto atual", "⬇️ Template filled with the current project"),
                           build_workbook(proj(), lang()), "RiskStudio_projeto.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
        rr, warn = export_risk_register(proj())
        st.download_button(L("⬇️ RiskRegister do professor (formato original, preenchido)", "⬇️ Professor's RiskRegister (original format, filled)"),
                           rr, "RiskRegister_Template.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
        for w in warn:
            st.caption("ℹ️ " + w)
    with c2:
        st.markdown(f"#### {L('2. Carregar ficheiros (local único)', '2. Upload files (single place)')}")
        st.caption(L("Aceita vários ficheiros de uma vez: **templates por módulo** (.xlsx) ou o **ZIP inteiro** preenchido, template único, "
                     "**RiskRegister do professor** (.xlsx), **Modelo 8 do PM Studio** (.xlsx), **projeto do PM Studio** (.json) e cópias de segurança (.json).",
                     "Accepts several files at once: **module templates** (.xlsx) or the whole filled **ZIP**, single template, **professor's RiskRegister** (.xlsx), "
                     "**PM Studio Model 8** (.xlsx), **PM Studio project** (.json) and backups (.json)."))
        ups = st.file_uploader(L("Ficheiros", "Files"), type=["xlsx", "json", "zip"], accept_multiple_files=True, key="multi_up")
        mode = st.radio(L("Modo", "Mode"), ["new", "replace", "append"], horizontal=True, index=2 if not st.session_state.get("example_loaded") else 0,
                        format_func=lambda m: {"new": L("Novo projeto", "New project"), "replace": L("Substituir tabelas do atual", "Replace current tables"),
                                               "append": L("Acrescentar ao atual", "Append to current")}[m])
        if ups and st.button(L("Importar", "Import"), type="primary"):
            base = new_project() if mode == "new" else proj()
            msgs, errors = [], []
            first, imported = True, False
            files = []
            for up in ups:
                if up.name.lower().endswith(".zip"):
                    try:
                        files += read_zip(up.getvalue())
                    except Exception as e:
                        errors.append(f"{up.name}: {e}")
                else:
                    files.append((up.name, up.getvalue()))
            for name, content in files:
                up = SimpleNamespace(name=name)
                try:
                    tables, meta, kind = parse_upload(up.name, content)
                    if tables is not None and not any(len(v) for v in tables.values()):
                        msgs.append(L(f"**{up.name}**: modelo em branco (sem dados) — ignorado.", f"**{up.name}**: blank template (no data) — skipped."))
                        continue
                    if tables is not None:
                        parsed = dict(tables)
                        if meta and (mode == "new"):
                            parsed["meta"] = meta
                        kinds = {"risk_register": "RiskRegister", "pm_model8": "PM Studio · Modelo 8", "pm_project": "PM Studio"}
                        msgs.append(f"**{up.name}** ({kinds[kind]}): " + " · ".join(f"{len(v)} {TNAMES.get(k, k)}" for k, v in tables.items()))
                    elif up.name.lower().endswith(".json"):
                        bk = from_json(content.decode("utf-8"))
                        parsed = {k: bk[k] for k in bk if k != "meta"}
                        if mode == "new":
                            parsed["meta"] = bk["meta"]
                        msgs.append(f"**{up.name}** (Risk Studio JSON): {len(bk['risks'])} {L('riscos', 'risks')}")
                    elif is_module_file(content):
                        parsed, m_ = read_module_workbook(content)
                        if not m_:
                            msgs.append(L(f"**{up.name}**: template em branco (sem dados) — ignorado.", f"**{up.name}**: blank template (no data) — skipped."))
                            continue
                        msgs.append(f"**{up.name}** (template): " + " · ".join(m_))
                    else:
                        parsed, m_ = read_workbook(content)
                        if not m_:
                            errors.append(L(f"{up.name}: formato não reconhecido.", f"{up.name}: format not recognised."))
                            continue
                        msgs.append(f"**{up.name}** (Risk Studio): " + " · ".join(m_))
                    m_mode = "replace" if (mode in ("new", "replace") and first) else "append"
                    base = merge_into(base, parsed, m_mode)
                    first = False
                    imported = True
                except Exception as e:
                    errors.append(f"{up.name}: {e}")
            if imported:
                set_project(base, None if mode == "new" else st.session_state.get("pid"))
                if mode != "new":
                    mark_dirty()
                flash(L("Importado ✔", "Imported ✔"))
            if msgs:
                st.session_state["import_msgs"] = msgs
                st.rerun()
            for e in errors:
                st.error(e)
        for m_ in st.session_state.pop("import_msgs", []):
            st.success(m_)
    note(L("Regras: não altere os cabeçalhos; os IDs podem ficar vazios; na folha Controlos, a coluna <b>Riscos ligados</b> faz a ligação "
           "risco↔controlo (ex.: R01, R03); causas/consequências múltiplas separadas por <b>;</b> alimentam o Bow-Tie. "
           "No RiskRegister do professor, a <b>mitigação existente</b> passa a controlo ligado ao risco e a <b>mitigação proposta</b> a ação de tratamento; "
           "a escala 4×4 é convertida para 5×5 pelo nome do nível. Ao acrescentar, os IDs são renumerados e as ligações mantêm-se.",
           "Rules: don't change headers; IDs can be blank; in the Controls sheet <b>Linked risks</b> links risk↔control (e.g. R01, R03); multiple "
           "causes/consequences separated by <b>;</b> feed the Bow-Tie. In the professor's RiskRegister, <b>existing mitigation</b> becomes a control linked "
           "to the risk and <b>proposed mitigation</b> a treatment action; the 4×4 scale maps to 5×5 by level name. When appending, IDs are renumbered and links kept."))

with t2:
    st.caption(L("Casos completos (riscos, controlos com testes, ações, KRIs, FMEA/FAIR quando aplicável), com lacunas intencionais para demonstrar a análise de cobertura.",
                 "Complete cases (risks, tested controls, actions, KRIs, FMEA/FAIR where relevant) with deliberate gaps to demonstrate coverage analysis."))
    cols = st.columns(4)
    for i, key in enumerate(EXAMPLES):
        ex = EXAMPLES[key]
        with cols[i % 4].container(border=True):
            st.markdown(f"**{tr(INDUSTRIES[key])}**")
            st.caption(ex["meta"]["name"])
            st.caption(f"{len(ex['risks'])} {L('riscos', 'risks')} · {len(ex['controls'])} {L('controlos', 'controls')}")
            if st.button(L("Carregar", "Load"), key=f"ex_{key}", width="stretch"):
                set_project(load_example(key))
                st.success(L("Exemplo carregado.", "Example loaded."))
                st.switch_page("views/painel.py")

with t3:
    try:
        items = db.list_projects()
    except Exception as e:
        items = []
        st.error(f"DB: {e}")
    st.caption(L(f"Base de dados: {db.backend_name()} · {len(items)} projetos", f"Database: {db.backend_name()} · {len(items)} projects"))
    for it in items:
        c1, c2, c3, c4 = st.columns([4, 2, 1, 1])
        c1.markdown(f"**{it['name']}**  \n<small>#{it['id']} · {tr(INDUSTRIES.get(it['industry'] or 'other', ('', '')))}</small>", unsafe_allow_html=True)
        c2.caption(str(it["updated_at"])[:16])
        if c3.button(L("Abrir", "Open"), key=f"o_{it['id']}"):
            set_project(from_json(db.load_project(it["id"])), it["id"])
            st.switch_page("views/painel.py")
        if c4.button("🗑️", key=f"d_{it['id']}", help=L("Apagar", "Delete")):
            st.session_state["confirm_del"] = it["id"]
        if st.session_state.get("confirm_del") == it["id"]:
            st.warning(L(f"Apagar definitivamente '{it['name']}'?", f"Permanently delete '{it['name']}'?"))
            a, b = st.columns(2)
            if a.button(L("Sim, apagar", "Yes, delete"), key=f"y_{it['id']}", type="primary"):
                db.delete_project(it["id"])
                if st.session_state.get("pid") == it["id"]:
                    st.session_state.pid = None
                st.session_state.pop("confirm_del", None)
                st.rerun()
            if b.button(L("Cancelar", "Cancel"), key=f"n_{it['id']}"):
                st.session_state.pop("confirm_del", None)
                st.rerun()

with t4:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"#### {L('Projeto em branco', 'Blank project')}")
        name = st.text_input(L("Nome", "Name"), L("Novo projeto de risco", "New risk project"))
        if st.button(L("Criar projeto em branco", "Create blank project"), type="primary"):
            np_ = new_project()
            np_["meta"]["name"] = name
            set_project(np_)
            st.switch_page("views/contexto.py")
    with c2:
        st.markdown(f"#### {L('Restaurar cópia JSON', 'Restore JSON backup')}")
        js = st.file_uploader("JSON", type=["json"], key="json_up")
        if js is not None and st.button(L("Restaurar", "Restore")):
            try:
                set_project(from_json(js.getvalue().decode("utf-8")))
                st.success(L("Projeto restaurado.", "Project restored."))
            except Exception as e:
                st.error(str(e))
