import datetime as dt

import pandas as pd
import streamlit as st

from core import ai
from core.catalogs import label
from core.i18n import L
from core.model import coerce_df
from core.ui import bump, flash, hero, mark_dirty, note, proj, risk_options

p = proj()
hero(L("Agente IA de risco", "AI risk agent"),
     L("Claude como consultor sénior de risco: identifica, desafia, propõe controlos, KRIs e planos, extrai riscos de documentos e escreve relatórios",
       "Claude as a senior risk advisor: identifies, challenges, proposes controls, KRIs and plans, extracts risks from documents and writes reports"),
     "🤖", help_key="agent")

ON = ai.available()
if ON:
    st.caption(L(f"🟢 Ligado · {ai.model()} · esforço {ai.EFFORT} — configure a chave e o modelo na barra lateral (🤖 Agente IA).",
                 f"🟢 Connected · {ai.model()} · effort {ai.EFFORT} — set key and model in the sidebar (🤖 AI agent)."))
else:
    st.warning(L("Sem chave API: use o **gerador de prompt** (último separador) e cole o resultado em qualquer assistente de IA. "
                 "Para ativar o agente, cole a chave na barra lateral (🤖 Agente IA) ou defina ANTHROPIC_API_KEY no Render.",
                 "No API key: use the **prompt generator** (last tab) and paste it into any AI assistant. To enable the agent, paste the key "
                 "in the sidebar (🤖 AI agent) or set ANTHROPIC_API_KEY on Render."), icon="🔑")

NAMES = {"risks": L("riscos", "risks"), "controls": L("controlos", "controls"), "actions": L("ações", "actions"), "kris": "KRIs"}
opts = risk_options()


def run_structured(kind: str, prompt: str, source: str = ""):
    with st.spinner(L("O agente está a trabalhar… (pode demorar 1–2 min)", "The agent is working… (may take 1–2 min)")):
        items, err = ai.structured(p, kind, prompt)
    st.session_state["ai_preview"] = {"kind": kind, "items": items, "err": err, "source": source}


t1, t2, t3, t4 = st.tabs([L("① Gerar itens", "① Generate items"), L("② Extrair de documentos", "② Extract from documents"),
                          L("③ Análises e relatórios", "③ Analyses and reports"), L("④ Gerador de prompt (sem chave)", "④ Prompt generator (no key)")])
with t1:
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown(f"**① {L('Identificar novos riscos', 'Identify new risks')}**")
            n = st.slider(L("Quantidade", "Number"), 3, 15, 6)
            focus = st.text_input(L("Foco (opcional)", "Focus (optional)"), placeholder=L("ex.: ESG, IA generativa, cadeia de abastecimento", "e.g. ESG, generative AI, supply chain"))
            if st.button(L("Identificar riscos", "Identify risks"), type="primary", key="b_risks", disabled=not ON):
                run_structured("risks", ai.prompt_identify(n, focus))
        with st.container(border=True):
            st.markdown(f"**③ {L('Plano de tratamento', 'Treatment plan')}**")
            sel_a = st.multiselect(L("Riscos (vazio = acima do apetite)", "Risks (empty = above appetite)"), list(opts), format_func=lambda x: opts[x],
                                   key="ms_a", placeholder=L("Escolha riscos", "Choose risks"))
            if st.button(L("Propor ações", "Propose actions"), type="primary", key="b_actions", disabled=not ON):
                run_structured("actions", ai.prompt_actions(sel_a))
    with c2:
        with st.container(border=True):
            st.markdown(f"**② {L('Desenhar controlos', 'Design controls')}**")
            sel_c = st.multiselect(L("Riscos (vazio = sem cobertura / ineficazes)", "Risks (empty = uncovered / ineffective)"), list(opts),
                                   format_func=lambda x: opts[x], key="ms_c", placeholder=L("Escolha riscos", "Choose risks"))
            if st.button(L("Propor controlos", "Propose controls"), type="primary", key="b_controls", disabled=not ON):
                run_structured("controls", ai.prompt_controls(sel_c))
        with st.container(border=True):
            st.markdown(f"**④ {L('Indicadores KRI', 'KRI indicators')}**")
            sel_k = st.multiselect(L("Riscos (vazio = prioritários)", "Risks (empty = priority)"), list(opts), format_func=lambda x: opts[x],
                                   key="ms_k", placeholder=L("Escolha riscos", "Choose risks"))
            if st.button(L("Propor KRIs", "Propose KRIs"), type="primary", key="b_kris", disabled=not ON):
                run_structured("kris", ai.prompt_kris(sel_k))

with t2:
    note(L("Carregue relatórios de auditoria, políticas, atas de comité, relatórios de risco ou planos (<b>Word, PDF, TXT</b>). "
           "O agente extrai os itens descritos no documento para revisão antes de entrarem no projeto.",
           "Upload audit reports, policies, committee minutes, risk reports or plans (<b>Word, PDF, TXT</b>). "
           "The agent extracts the items described in the document for review before they enter the project."))
    docs = st.file_uploader(L("Documentos", "Documents"), type=["docx", "pdf", "txt", "md"], accept_multiple_files=True, key="ai_docs")
    kind = st.radio(L("Extrair", "Extract"), ["risks", "controls", "actions", "kris"], horizontal=True, format_func=lambda k: NAMES[k], key="ai_doc_kind")
    if docs and st.button(L("📄 Extrair com o agente", "📄 Extract with the agent"), type="primary", disabled=not ON):
        texts = []
        for d in docs:
            try:
                txt = ai.document_text(d.name, d.getvalue())
                texts.append(f"### {d.name}\n{txt}")
            except Exception as e:
                st.error(f"{d.name}: {e}")
        full = "\n\n".join(texts)
        if not full.strip():
            st.error(L("Não foi possível ler texto dos documentos (PDF digitalizado sem OCR?).", "Could not read text (scanned PDF without OCR?)."))
        else:
            st.caption(L(f"{len(full):,} caracteres lidos.", f"{len(full):,} characters read."))
            run_structured(kind, ai.prompt_extract(kind, ", ".join(d.name for d in docs), full), source=", ".join(d.name for d in docs))

with t3:
    labels_ = {"exec": L("📑 Sumário executivo", "📑 Executive summary"), "bias": L("😈 Desafiar avaliações (2.ª linha)", "😈 Challenge assessments (2nd line)"),
               "premortem": L("⚰️ Pré-mortem", "⚰️ Pre-mortem"), "scenarios": L("🌪️ Cenários de stress", "🌪️ Stress scenarios"),
               "audit": L("🔍 Plano de auditoria (3.ª linha)", "🔍 Audit plan (3rd line)")}
    cols = st.columns(len(labels_))
    for (kk, lab), col in zip(labels_.items(), cols):
        if col.button(lab, width="stretch", key=f"txt_{kk}", disabled=not ON):
            with st.spinner(L("A escrever…", "Writing…")):
                st.session_state.setdefault("ai_text", {})[kk] = ai.complete(p, ai.PROMPTS_TEXT[kk][1 if st.session_state.lang == "en" else 0], 4000)
            st.session_state["ai_text_last"] = kk
    last = st.session_state.get("ai_text_last")
    if last and st.session_state.get("ai_text", {}).get(last):
        with st.container(border=True):
            st.markdown(f"#### {labels_[last]}")
            st.markdown(st.session_state["ai_text"][last])
            c1, c2 = st.columns(2)
            if c1.button(L("Usar no relatório", "Use in report"), key="use_rep"):
                p["meta"]["ai_summary"] = st.session_state["ai_text"][last]
                mark_dirty()
                st.toast(L("Incluído no relatório ✔", "Included in report ✔"))
            c2.download_button(L("⬇️ Descarregar (Markdown)", "⬇️ Download (Markdown)"), st.session_state["ai_text"][last], f"risk_studio_{last}.md")

with t4:
    st.caption(L("Funciona sem chave: copie o prompt (botão de copiar no canto do bloco) e cole-o no Claude, ChatGPT ou Gemini. "
                 "O prompt inclui todo o contexto do projeto.",
                 "Works without a key: copy the prompt (copy button in the block corner) and paste it into Claude, ChatGPT or Gemini. "
                 "The prompt includes the full project context."))
    tasks = {"exec": labels_["exec"], "risks": L("Identificar riscos", "Identify risks"), "controls": L("Desenhar controlos", "Design controls"),
             "kris": L("Propor KRIs", "Propose KRIs"), "bias": labels_["bias"], "premortem": labels_["premortem"],
             "scenarios": labels_["scenarios"], "audit": labels_["audit"]}
    task = st.selectbox(L("Tarefa", "Task"), list(tasks), format_func=lambda k: tasks[k], key="pg_task")
    st.code(ai.build_prompt(p, task), language="markdown")

# ---------------------------------------------------------------- preview (draft → append / replace / discard)
prev = st.session_state.get("ai_preview")
if prev:
    st.divider()
    kind = prev["kind"]
    st.subheader(L(f"Rascunho do agente — {NAMES[kind]}", f"Agent draft — {NAMES[kind]}") + (f" · 📄 {prev['source']}" if prev.get("source") else ""))
    if prev.get("err"):
        st.error(prev["err"])
    items = prev.get("items") or []
    if not items and not prev.get("err"):
        st.info(L("O agente não encontrou itens.", "The agent found no items."))
    if items:
        df = pd.DataFrame(items)
        df.insert(0, "incluir", True)
        for col, cat in [("type", "type"), ("category", "category"), ("strategy", "strategy"), ("proximity", "proximity"),
                         ("control_type", "control_type"), ("nature", "nature"), ("frequency", "frequency"), ("line", "line"),
                         ("direction", "direction")]:
            if col in df:
                df[col] = df[col].map(lambda v, c=cat: label(c, v))
        st.caption(L("Reveja, edite se necessário e desmarque o que não quiser incluir.", "Review, edit if needed and untick what you don't want to include."))
        edited = st.data_editor(df, hide_index=True, width="stretch", key=f"prev_{kind}_{len(items)}",
                                column_config={"incluir": st.column_config.CheckboxColumn(L("Incluir", "Include"))})

        def _prepare() -> pd.DataFrame:
            sel = edited[edited["incluir"]].drop(columns=["incluir"])
            if kind == "actions":
                today = dt.date.today()
                dur = sel["duration_days"] if "duration_days" in sel else pd.Series([30] * len(sel), index=sel.index)
                sel = sel.assign(start=today.isoformat(),
                                 due=[(today + dt.timedelta(days=int(d or 30))).isoformat() for d in dur],
                                 status="not_started", progress=0)
            if kind == "controls":
                sel = sel.assign(design_test="not_tested", operating_test="not_tested")
                if "test_procedure" in sel:
                    sel["notes"] = sel["test_procedure"].map(lambda t: f"{L('Procedimento de teste', 'Test procedure')}: {t}")
            if kind == "risks":
                sel = sel.assign(status="open", trend="stable")
                if "rationale" in sel:
                    sel["notes"] = sel["rationale"]
            return coerce_df(kind, sel.assign(id=""))

        c1, c2, c3 = st.columns(3)
        if c1.button(L("✅ Acrescentar", "✅ Append"), type="primary", key="ai_app"):
            new = _prepare()
            p[kind] = coerce_df(kind, pd.concat([p[kind], new], ignore_index=True))
            bump(kind)
            mark_dirty()
            st.session_state.pop("ai_preview", None)
            flash(L(f"{len(new)} {NAMES[kind]} acrescentados ✔", f"{len(new)} {NAMES[kind]} appended ✔"))
            st.rerun()
        if c2.button(L("♻️ Substituir", "♻️ Replace"), key="ai_rep",
                     help=L("Substitui toda a tabela por este rascunho", "Replaces the whole table with this draft")):
            new = _prepare()
            p[kind] = coerce_df(kind, new)
            bump(kind)
            mark_dirty()
            st.session_state.pop("ai_preview", None)
            flash(L(f"Tabela de {NAMES[kind]} substituída ({len(new)}) ✔", f"{NAMES[kind]} table replaced ({len(new)}) ✔"))
            st.rerun()
        if c3.button(L("🗑️ Descartar", "🗑️ Discard"), key="ai_del"):
            st.session_state.pop("ai_preview", None)
            st.rerun()

# -------------------------------------------------------------------- chat
st.divider()
st.subheader(L("💬 Conversa com o agente", "💬 Chat with the agent"))
if not ON:
    st.caption(L("Disponível com chave API.", "Available with an API key."))
else:
    note(L("Exemplos: <i>“Que riscos estão subavaliados?”</i> · <i>“Desenha um bow-tie textual para o R03”</i> · <i>“Que apetite faz sentido para ciber?”</i> · "
           "<i>“Compara o nosso perfil com boas práticas DORA”</i>",
           "Examples: <i>“Which risks are under-rated?”</i> · <i>“Draw a textual bow-tie for R03”</i> · <i>“What appetite makes sense for cyber?”</i> · "
           "<i>“Compare our profile with DORA good practice”</i>"))
    for msg in st.session_state.chat:
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🛡️"):
            st.markdown(msg["content"])
    q = st.chat_input(L("Pergunte ao agente de risco…", "Ask the risk agent…"))
    if q:
        st.session_state.chat.append({"role": "user", "content": q})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(q)
        with st.chat_message("assistant", avatar="🛡️"):
            ans = st.write_stream(ai.stream_chat(p, st.session_state.chat))
        st.session_state.chat.append({"role": "assistant", "content": ans if isinstance(ans, str) else "".join(ans)})
    if st.session_state.chat and st.button(L("🗑️ Limpar conversa", "🗑️ Clear chat")):
        st.session_state.chat = []
        st.rerun()
