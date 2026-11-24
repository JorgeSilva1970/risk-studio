import datetime as dt
import re

import streamlit as st
import streamlit.components.v1 as components

from core import ai
from core.excel_io import build_workbook
from core.i18n import L, lang
from core.model import to_json
from core.report import build_html, narrative
from core.ui import hero, mark_dirty, note, proj

p = proj()
hero(L("Relatórios", "Reports"), L("Relatório interpretativo HTML (imprimível em PDF) · exportação Excel · cópia de segurança JSON",
                                   "Interpretative HTML report (printable to PDF) · Excel export · JSON backup"), "📄", help_key="reports")

slug = re.sub(r"[^A-Za-z0-9]+", "_", p["meta"].get("name", "risk"))[:40].strip("_") or "risk"
today = dt.date.today().strftime("%Y%m%d")

st.subheader(L("Relatório de gestão de risco", "Risk management report"))
secs = {
    "exec": L("Sumário executivo e interpretação", "Executive summary and interpretation"), "context": L("Contexto e apetite", "Context and appetite"),
    "heatmaps": L("Matrizes de risco", "Risk matrices"), "register": L("Registo de riscos", "Risk register"),
    "controls": L("Controlos e RCM", "Controls and RCM"), "coverage": L("Lacunas de cobertura", "Coverage gaps"),
    "bowtie": "Bow-Tie", "treatment": L("Plano de tratamento", "Treatment plan"), "kris": "KRIs",
    "quant": "Monte Carlo", "fair": "FAIR", "fmea": "FMEA", "maturity": L("Maturidade", "Maturity"), "method": L("Metodologia", "Methodology"),
}
cols = st.columns(4)
inc = {k: cols[i % 4].checkbox(v, True, key=f"sec_{k}") for i, (k, v) in enumerate(secs.items())}

ai_sum = p["meta"].get("ai_summary", "")
c1, c2 = st.columns([3, 2])
with c1:
    use_ai = st.toggle(L("Incluir análise do Agente IA no sumário", "Include AI Agent analysis in the summary"), bool(ai_sum))
with c2:
    if ai.available() and st.button(L("🤖 Gerar/atualizar sumário executivo IA", "🤖 Generate/refresh AI executive summary")):
        with st.spinner(L("A escrever sumário…", "Writing summary…")):
            p["meta"]["ai_summary"] = ai.complete(p, ai.PROMPTS_TEXT["exec"][1 if lang() == "en" else 0], 3000)
            mark_dirty()
        st.rerun()
if ai_sum:
    with st.expander(L("Ver sumário IA incluído", "View included AI summary")):
        st.markdown(ai_sum)

with st.expander(L("Pré-visualizar interpretação automática", "Preview automatic interpretation")):
    for t in narrative(p):
        st.markdown(f"- {t}")

if st.button(L("🧾 Gerar relatório", "🧾 Build report"), type="primary"):
    with st.spinner(L("A gerar relatório…", "Building report…")):
        st.session_state["report_html"] = build_html(p, inc, st.session_state.get("mc_settings"), ai_sum if use_ai else "")
if st.session_state.get("report_html"):
    h = st.session_state["report_html"]
    st.download_button(L("⬇️ Descarregar relatório HTML", "⬇️ Download HTML report"), h, f"RiskStudio_{slug}_{today}.html", "text/html",
                       type="primary")
    st.caption(L("Abra o HTML no browser e use Imprimir → Guardar como PDF para obter o PDF.",
                 "Open the HTML in a browser and use Print → Save as PDF to get a PDF."))
    with st.expander(L("Pré-visualizar relatório", "Preview report"), expanded=True):
        components.html(h, height=900, scrolling=True)

st.divider()
st.subheader(L("Exportações de dados", "Data exports"))
from core.professor import export_risk_register

c1, c2, c3 = st.columns(3)
_rr, _rw = export_risk_register(p)
c3.download_button(L("⬇️ RiskRegister do professor (original)", "⬇️ Professor's RiskRegister (original)"), _rr,
                   f"RiskRegister_{slug}_{today}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch",
                   help=L("Escala 4×4 e formato originais; avaliação residual atual; mitigação existente = controlos, proposta = ações.",
                          "Original 4×4 format; current residual assessment; existing mitigation = controls, proposed = actions."))
c1.download_button(L("⬇️ Excel completo (mesmo formato do template)", "⬇️ Full Excel (same format as template)"),
                   build_workbook(p, lang()), f"RiskStudio_{slug}_{today}.xlsx",
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")
c2.download_button(L("⬇️ Cópia de segurança JSON", "⬇️ JSON backup"), to_json(p), f"RiskStudio_{slug}_{today}.json", "application/json",
                   width="stretch")
note(L("O Excel exportado pode ser editado e voltado a carregar em <i>Dados & templates</i> — é o mesmo formato do template.",
       "The exported Excel can be edited and uploaded again in <i>Data & templates</i> — it uses the same format as the template."))
