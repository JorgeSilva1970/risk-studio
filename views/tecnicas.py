import pandas as pd
import streamlit as st

from core import charts, scoring
from core import interpret as I
from core.ui import interpret_box
from core.i18n import L
from core.ui import bump, hero, mark_dirty, note, proj, risk_options, table_editor

p = proj()
hero(L("Técnicas ISO 31010: Bow-Tie & FMEA", "ISO 31010 techniques: Bow-Tie & FMEA"),
     L("Causas → barreiras preventivas → evento → barreiras de mitigação → consequências · modos de falha e RPN",
       "Causes → preventive barriers → event → mitigating barriers → consequences · failure modes and RPN"), "🎀", help_key="techniques")

t1, t2 = st.tabs(["🎀 Bow-Tie", "⚙️ FMEA"])
with t1:
    opts = risk_options()
    if not opts:
        st.info(L("Adicione riscos no Registo.", "Add risks in the Register."))
    else:
        ra = scoring.analyse_risks(p)
        default = ra[ra["type"] == "threat"].sort_values("priority", ascending=False)["id"].tolist()
        keys = list(opts)
        rid = st.selectbox(L("Risco a analisar", "Risk to analyse"), keys, index=keys.index(default[0]) if default else 0,
                           format_func=lambda x: opts[x])
        r = ra[ra["id"] == rid].iloc[0].to_dict()
        ca = scoring.analyse_controls(p)
        st.plotly_chart(charts.bowtie(r, ca), width="stretch")
        st.caption(L("Cor das barreiras = conclusão do teste: 🟢 eficaz · 🟡 parcial · 🔴 ineficaz · ⚪ não testado. "
                     "Barreiras preventivas = controlos preventivos/diretivos ligados; de mitigação = detetivos/corretivos.",
                     "Barrier colour = test conclusion: 🟢 effective · 🟡 partial · 🔴 ineffective · ⚪ not tested. "
                     "Preventive barriers = linked preventive/directive controls; mitigating = detective/corrective."))
        interpret_box(I.bowtie(p, rid))
        with st.form(f"bt_{rid}_{st.session_state.ver.get('risks', 0)}"):
            st.markdown(f"**{L('Editar causas e consequências deste risco', 'Edit causes and consequences of this risk')}**")
            c1, c2, c3 = st.columns(3)
            causes = c1.text_area(L("Causas (uma por linha)", "Causes (one per line)"),
                                  "\n".join(x.strip() for x in str(r.get("cause") or "").split(";") if x.strip()), height=150)
            event = c2.text_area(L("Evento de risco (topo)", "Risk event (top event)"), r.get("event") or "", height=150)
            cons = c3.text_area(L("Consequências (uma por linha)", "Consequences (one per line)"),
                                "\n".join(x.strip() for x in str(r.get("effect") or "").split(";") if x.strip()), height=150)
            if st.form_submit_button(L("💾 Guardar", "💾 Save"), type="primary"):
                df = p["risks"]
                i = df.index[df["id"] == rid][0]
                df.at[i, "cause"] = "; ".join(x.strip() for x in causes.splitlines() if x.strip())
                df.at[i, "event"] = event.strip()
                df.at[i, "effect"] = "; ".join(x.strip() for x in cons.splitlines() if x.strip())
                bump("risks")
                mark_dirty()
                st.rerun()
        note(L("Para acrescentar barreiras, crie controlos em <i>Controlos & RCM</i> e ligue-os a este risco. Barreiras ausentes ou "
               "ineficazes num dos lados do laço indicam onde investir.",
               "To add barriers, create controls in <i>Controls & RCM</i> and link them to this risk. Missing or ineffective barriers "
               "on either side of the knot show where to invest."))

with t2:
    note(L("<b>FMEA</b> (ISO 31010 / IEC 60812): para cada modo de falha avalie S = gravidade, O = ocorrência e D = deteção (1–10). "
           "<b>RPN</b> = S×O×D. <b>AP</b> (Action Priority, lógica AIAG-VDA simplificada) = H/M/L, privilegiando a gravidade.",
           "<b>FMEA</b> (ISO 31010 / IEC 60812): for each failure mode rate S = severity, O = occurrence and D = detection (1–10). "
           "<b>RPN</b> = S×O×D. <b>AP</b> (Action Priority, simplified AIAG-VDA logic) = H/M/L, giving priority to severity."))
    st.write("")
    f = scoring.analyse_fmea(p)
    comp = None
    if not f.empty:
        comp = pd.DataFrame({"rpn": f["rpn"], "ap": f["ap"]})
    table_editor("fmea", ["id", "process", "failure_mode", "effect", "cause", "current_controls", "s", "o", "d", "action", "owner"],
                 computed=comp, computed_cfg={"rpn": st.column_config.NumberColumn("RPN", disabled=True),
                                              "ap": st.column_config.TextColumn("AP", disabled=True)})
    if not f.empty:
        st.plotly_chart(charts.pareto(f, title=L("Pareto do RPN (cor = Action Priority)", "RPN Pareto (colour = Action Priority)")),
                        width="stretch")
        interpret_box(I.fmea(p))

st.write("")
from core.ui import ai_assist  # noqa: E402
ai_assist("techniques", I.fmea(p))
