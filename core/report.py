"""Interpretative narrative (rule-based) and self-contained HTML report."""
from __future__ import annotations

import datetime as dt
import html

import markdown as md_lib
import numpy as np
import pandas as pd

from core import charts, montecarlo as mc, scoring
from core.catalogs import INDUSTRIES, MATURITY_DIMENSIONS, label
from core.i18n import L, lang
from core.model import ids_list


def _m(v, cur="€"):
    if v is None:
        return "—"
    if lang() == "en":
        return f"{cur}{v:,.0f}"
    return f"{v:,.0f}".replace(",", " ") + f" {cur}"


def _p(v):
    s = f"{v * 100:.0f}%"
    return s


def narrative(proj: dict) -> list[str]:
    """Plain-language interpretation of the current risk profile."""
    k = scoring.kpis(proj)
    ra = scoring.analyse_risks(proj)
    cov = scoring.coverage(proj)
    out: list[str] = []
    if k["n_risks"] == 0:
        return [L("O registo está vazio. Comece por identificar riscos no Registo, carregar o template Excel ou pedir ao Agente IA.",
                  "The register is empty. Start by identifying risks in the Register, uploading the Excel template or asking the AI Agent.")]
    thr = ra[ra["type"] == "threat"]
    out.append(L(
        f"O perfil inclui **{k['n_threats']} ameaças** e **{k['n_opps']} oportunidades**. A exposição média passa de "
        f"**{k['avg_inh']:.1f}".replace(".", ",") + f"** (inerente) para **{k['avg_res']:.1f}".replace(".", ",") + f"** (residual), uma redução de **{_p(k['reduction'])}** atribuível aos controlos.",
        f"The profile includes **{k['n_threats']} threats** and **{k['n_opps']} opportunities**. Average exposure falls from "
        f"**{k['avg_inh']:.1f}** (inherent) to **{k['avg_res']:.1f}** (residual), a **{_p(k['reduction'])}** reduction attributable to controls."))
    if k["outside"]:
        ids = ", ".join(thr[thr["appetite_status"] == "outside"].sort_values("priority", ascending=False)["id"])
        out.append(L(f"⚠️ **{k['outside']} risco(s) estão fora da tolerância** ({ids}) e exigem decisão da gestão: tratamento adicional, "
                     f"escalonamento ou aceitação formal documentada.",
                     f"⚠️ **{k['outside']} risk(s) are outside tolerance** ({ids}) and require a management decision: further treatment, "
                     f"escalation or formally documented acceptance."))
    elif k["above_appetite"]:
        out.append(L(f"{k['above_appetite']} risco(s) estão acima do apetite mas dentro da tolerância — monitorizar de perto.",
                     f"{k['above_appetite']} risk(s) are above appetite but within tolerance — monitor closely."))
    else:
        out.append(L("✅ Todos os riscos residuais estão dentro do apetite definido.", "✅ All residual risks are within the defined appetite."))
    if k["no_controls"]:
        ids = ", ".join(cov["risks_no_controls"]["id"])
        out.append(L(f"🔴 **Riscos sem cobertura de controlo:** {ids}. Um registo de riscos sem controlos é só meia ferramenta — "
                     f"defina controlos ou justifique a aceitação.",
                     f"🔴 **Risks without control coverage:** {ids}. A risk register without controls is only half a tool — "
                     f"define controls or justify acceptance."))
    if k["orphans"]:
        ids = ", ".join(cov["controls_orphan"]["id"])
        out.append(L(f"🟠 **Controlos sem risco associado:** {ids}. Geram custo e complexidade sem benefício demonstrável — "
                     f"mapeie-os para um risco ou considere descontinuá-los.",
                     f"🟠 **Controls without a clear risk:** {ids}. They add cost and complexity without demonstrable benefit — "
                     f"map them to a risk or consider retiring them."))
    out.append(L(f"Cobertura de controlos: **{_p(k['coverage'])}** das ameaças; **{_p(k['tested'])}** dos controlos testados; "
                 f"completude média da cadeia Risco→Ação: **{_p(k['chain'])}**.",
                 f"Control coverage: **{_p(k['coverage'])}** of threats; **{_p(k['tested'])}** of controls tested; "
                 f"average Risk→Action chain completeness: **{_p(k['chain'])}**."))
    if not thr.empty:
        top = thr.sort_values("priority", ascending=False).head(3)
        lst = "; ".join(f"{r['id']} {r['title']} (score {r['score_res']}, {L('prioridade','priority')} {r['priority']})" for r in top.to_dict(orient="records"))
        out.append(L(f"Prioridades (score residual × velocidade × proximidade): {lst}.",
                     f"Priorities (residual score × velocity × proximity): {lst}."))
    if k["overdue"]:
        out.append(L(f"⏰ {k['overdue']} ação(ões) de tratamento em atraso.", f"⏰ {k['overdue']} treatment action(s) overdue."))
    if k["kri_red"]:
        out.append(L(f"📈 {k['kri_red']} KRI(s) em vermelho e {k['kri_amber']} em âmbar — sinais precoces de agravamento.",
                     f"📈 {k['kri_red']} KRI(s) red and {k['kri_amber']} amber — early warning of deterioration."))
    return out


# ------------------------------------------------------------------ HTML
CSS = """
body{font-family:Inter,Segoe UI,Arial,sans-serif;color:#0f172a;margin:0;background:#f1f5f9}
.wrap{max-width:1100px;margin:0 auto;background:white;padding:36px 46px}
.cover{background:linear-gradient(135deg,#0f2a4a 0%,#1d5aa6 60%,#2a78d6 100%);color:white;padding:38px 46px;border-radius:14px;margin-bottom:26px}
.cover h1{margin:0 0 6px;font-size:30px}.cover p{margin:2px 0;color:#cbd5e1}
h2{border-bottom:3px solid #2a78d6;padding-bottom:6px;margin-top:34px;color:#0f2a4a}
h3{color:#1d5aa6}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.kpi{border:1px solid #e2e8f0;border-left:5px solid #2a78d6;border-radius:10px;padding:10px 12px}
.kpi .v{font-size:22px;font-weight:700}.kpi .l{font-size:11px;color:#64748b;text-transform:uppercase}
table{border-collapse:collapse;width:100%;font-size:12px;margin:8px 0}
th{background:#0f2a4a;color:white;text-align:left;padding:6px}
td{border-bottom:1px solid #e2e8f0;padding:5px 6px;vertical-align:top}
tr:nth-child(even) td{background:#f8fafc}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;color:white;font-size:11px;font-weight:600}
.note{background:#f6f9fd;border-left:4px solid #2a78d6;padding:10px 14px;border-radius:6px;font-size:13px}
.gap{border-radius:10px;padding:10px 14px;margin:6px 0}.gap.red{background:#fef2f2;border:1px solid #fca5a5}
.gap.amber{background:#fffbeb;border:1px solid #fcd34d}
.legend{font-size:12px;color:#475569}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
footer{margin-top:40px;font-size:11px;color:#64748b;border-top:1px solid #e2e8f0;padding-top:10px}
@media print{body{background:white}.wrap{padding:0}h2{page-break-before:auto}.pb{page-break-before:always}}
"""


def _tbl(df: pd.DataFrame, cols: dict[str, str]) -> str:
    if df is None or df.empty:
        return f"<p class='legend'>{L('Sem registos.', 'No records.')}</p>"
    h = "<table><tr>" + "".join(f"<th>{html.escape(v)}</th>" for v in cols.values()) + "</tr>"
    for r in df.to_dict(orient="records"):
        h += "<tr>"
        for c in cols:
            v = r.get(c, "")
            if isinstance(v, str) and v.startswith("<span"):
                h += f"<td>{v}</td>"
            else:
                if v is None or (isinstance(v, float) and np.isnan(v)):
                    v = ""
                h += f"<td>{html.escape(str(v))}</td>"
        h += "</tr>"
    return h + "</table>"


def _pill(text, col):
    return f"<span class='pill' style='background:{col}'>{html.escape(str(text))}</span>"


def build_html(proj: dict, include: dict | None = None, mc_settings: dict | None = None, ai_summary: str = "") -> str:
    inc = {k: True for k in ["exec", "context", "heatmaps", "register", "controls", "coverage", "bowtie", "treatment",
                             "kris", "quant", "fair", "fmea", "maturity", "method"]}
    if include:
        inc.update(include)
    m = proj["meta"]
    cur = m.get("currency", "€")
    ra = scoring.analyse_risks(proj)
    ca = scoring.analyse_controls(proj)
    cov = scoring.coverage(proj)
    k = scoring.kpis(proj)
    figs_js = {"first": True}

    def fig(f):
        inc_js = True if figs_js["first"] else False  # inline plotly.js: report works offline
        figs_js["first"] = False
        return f.to_html(full_html=False, include_plotlyjs=inc_js, config={"displayModeBar": False})

    ind = INDUSTRIES.get(m.get("industry"), ("", ""))
    parts = [f"<!DOCTYPE html><html lang='{lang()}'><head><meta charset='utf-8'><title>{html.escape(m.get('name',''))} — Risk Studio</title>"
             f"<style>{CSS}</style></head><body><div class='wrap'>"]
    parts.append(f"<div class='cover'><p>RISK STUDIO · {L('Relatório de Gestão de Risco', 'Risk Management Report')}</p>"
                 f"<h1>{html.escape(m.get('name',''))}</h1><p>{html.escape(m.get('organisation',''))} · {ind[1] if lang()=='en' else ind[0]}</p>"
                 f"<p>{L('Data', 'Date')}: {dt.date.today().strftime('%d/%m/%Y')} · {L('Avaliador', 'Assessor')}: {html.escape(m.get('assessor') or '—')}</p></div>")

    if inc["exec"]:
        parts.append(f"<h2>1. {L('Sumário executivo', 'Executive summary')}</h2><div class='kpis'>")
        for lab, val in [(L("Riscos", "Risks"), k["n_risks"]), (L("Fora da tolerância", "Outside tolerance"), k["outside"]),
                         (L("Críticos (residual)", "Critical (residual)"), k["critical_res"]), (L("Redução pelos controlos", "Reduction by controls"), _p(k["reduction"])),
                         (L("Cobertura de controlos", "Control coverage"), _p(k["coverage"])), (L("Controlos testados", "Controls tested"), _p(k["tested"])),
                         (L("Ações em atraso", "Overdue actions"), k["overdue"]), (L("KRIs a vermelho", "Red KRIs"), k["kri_red"])]:
            parts.append(f"<div class='kpi'><div class='l'>{lab}</div><div class='v'>{val}</div></div>")
        parts.append("</div><h3>" + L("Interpretação", "Interpretation") + "</h3><div class='note'>" +
                     "".join(f"<p>{md_lib.markdown(t)[3:-4]}</p>" for t in narrative(proj)) + "</div>")
        if ai_summary:
            parts.append(f"<h3>{L('Análise do Agente IA', 'AI Agent analysis')}</h3><div>{md_lib.markdown(ai_summary, extensions=['tables'])}</div>")

    if inc["context"]:
        parts.append(f"<h2>2. {L('Contexto, objetivos e apetite', 'Context, objectives and appetite')}</h2>")
        parts.append(f"<p><b>{L('Âmbito', 'Scope')}:</b> {html.escape(m.get('scope') or '—')}</p>"
                     f"<p><b>{L('Objetivos', 'Objectives')}:</b> {html.escape(m.get('objectives') or '—')}</p>"
                     f"<p><b>{L('Declaração de apetite', 'Appetite statement')}:</b> {html.escape(m.get('appetite_statement') or '—')}</p>"
                     f"<p><b>{L('Capacidade de risco', 'Risk capacity')}:</b> {_m(m.get('risk_capacity'), cur)}</p>")
        ap = proj["appetite"].copy()
        ap["cat"] = ap["category"].map(lambda c: label("category", c))
        parts.append(_tbl(ap, {"cat": L("Categoria", "Category"), "appetite": L("Apetite", "Appetite"), "tolerance": L("Tolerância", "Tolerance")}))

    if inc["heatmaps"] and not ra.empty:
        parts.append(f"<h2 class='pb'>3. {L('Matrizes de risco', 'Risk matrices')}</h2><div class='grid2'>")
        parts.append("<div>" + fig(charts.heatmap(ra, "inh", dark=False, title=L("Inerente", "Inherent"), height=420)) + "</div>")
        parts.append("<div>" + fig(charts.heatmap(ra, "res", dark=False, title=L("Residual", "Residual"), height=420)) + "</div></div>")
        parts.append(fig(charts.appetite_bars(ra, dark=False, title=L("Residual vs. apetite e tolerância", "Residual vs appetite and tolerance"))))
        if (ra["type"] == "opportunity").any():
            parts.append(fig(charts.heatmap(ra, "res", opportunity=True, dark=False, title=L("Oportunidades", "Opportunities"), height=380)))
        parts.append(f"<p class='legend'>{L('Score = Probabilidade × Impacto (1–25). Níveis: 1–4 Baixo · 5–9 Moderado · 10–14 Elevado · 15–25 Crítico. O residual considera a eficácia testada dos controlos ligados.', 'Score = Probability × Impact (1–25). Levels: 1–4 Low · 5–9 Moderate · 10–14 High · 15–25 Critical. Residual reflects the tested effectiveness of linked controls.')}</p>")

    if inc["register"] and not ra.empty:
        parts.append(f"<h2 class='pb'>4. {L('Registo de riscos', 'Risk register')}</h2>")
        r = ra.sort_values("priority", ascending=False).copy()
        r["tp"] = r["type"].map(lambda v: label("type", v))
        r["cat"] = r["category"].map(lambda v: label("category", v))
        r["inh"] = [_pill(f"{s}", c) for s, c in zip(r["score_inh"], r["colour_inh"])]
        r["res"] = [_pill(f"{s}", c) for s, c in zip(r["score_res"], r["colour_res"])]
        r["app"] = r["appetite_status"].map(scoring.appetite_label)
        r["strat"] = r["strategy"].map(lambda v: label("strategy", v))
        parts.append(_tbl(r, {"id": "ID", "tp": L("Tipo", "Type"), "cat": L("Categoria", "Category"), "title": L("Risco", "Risk"),
                              "owner": L("Responsável", "Owner"), "inh": L("Inerente", "Inherent"), "res": L("Residual", "Residual"),
                              "app": L("Apetite", "Appetite"), "controls": L("Controlos", "Controls"), "strat": L("Estratégia", "Strategy")}))

    if inc["controls"] and not ca.empty:
        parts.append(f"<h2 class='pb'>5. {L('Controlos e matriz risco-controlo (RCM)', 'Controls and risk-control matrix (RCM)')}</h2>")
        parts.append(fig(charts.chain_bar(ca, dark=False, title=L("Completude da cadeia Risco → Ação", "Risk → Action chain completeness"))))
        c = ca.copy()
        c["tp"] = c["control_type"].map(lambda v: label("control_type", v))
        c["nat"] = c["nature"].map(lambda v: label("nature", v))
        c["concl"] = [_pill(label("test", v), charts.CONCL_COL.get(v, "#64748b")) for v in c["conclusion"]]
        c["eff"] = c["effectiveness"].map(lambda v: f"{v:.0%}")
        parts.append(_tbl(c, {"id": "ID", "name": L("Controlo", "Control"), "risk_ids": L("Riscos", "Risks"), "tp": L("Tipo", "Type"),
                              "nat": L("Natureza", "Nature"), "owner": L("Responsável", "Owner"), "concl": L("Conclusão", "Conclusion"),
                              "eff": L("Eficácia", "Effectiveness")}))

    if inc["coverage"]:
        parts.append(f"<h2>6. {L('Lacunas de cobertura', 'Coverage gaps')}</h2>")
        g1 = cov["risks_no_controls"]
        g2 = cov["controls_orphan"]
        parts.append(f"<div class='gap red'><b>✖ {L('Riscos sem cobertura de controlo', 'Risks without control coverage')} ({len(g1)})</b><br>"
                     + (", ".join(f"{a} {b}" for a, b in zip(g1["id"], g1["title"])) if len(g1) else L("Nenhum", "None")) + "</div>")
        parts.append(f"<div class='gap amber'><b>? {L('Controlos sem risco claro', 'Controls without a clear risk')} ({len(g2)})</b><br>"
                     + (", ".join(f"{a} {b}" for a, b in zip(g2["id"], g2["name"])) if len(g2) else L("Nenhum", "None")) + "</div>")
        g3 = cov["controls_ineffective"]
        if len(g3):
            parts.append(f"<div class='gap amber'><b>{L('Controlos ineficazes ou parcialmente eficazes', 'Ineffective or partially effective controls')} ({len(g3)})</b><br>"
                         + ", ".join(f"{a} {b}" for a, b in zip(g3["id"], g3["name"])) + "</div>")

    if inc["bowtie"] and not ra.empty:
        top = ra[ra["type"] == "threat"].sort_values("priority", ascending=False).head(2)
        if not top.empty:
            parts.append(f"<h2 class='pb'>7. {L('Análise Bow-Tie (riscos prioritários)', 'Bow-Tie analysis (priority risks)')}</h2>")
            for r in top.to_dict(orient="records"):
                parts.append(f"<h3>{r['id']} — {html.escape(r['title'])}</h3>" + fig(charts.bowtie(r, ca, dark=False, height=480)))

    if inc["treatment"]:
        acts = scoring.analyse_actions(proj)
        parts.append(f"<h2 class='pb'>8. {L('Plano de tratamento', 'Treatment plan')}</h2>")
        if not acts.empty:
            parts.append(fig(charts.gantt(acts, dark=False)))
            a = acts.copy()
            a["st"] = [_pill(label("action_status", s) + (" ⏰" if o else ""), "#ef4444" if o else "#0e7490") for s, o in zip(a["status"], a["overdue"])]
            a["strat"] = a["strategy"].map(lambda v: label("strategy", v))
            a["cst"] = a["cost"].map(lambda v: _m(v, cur) if v is not None and v == v else "")
            parts.append(_tbl(a, {"id": "ID", "risk_id": L("Risco", "Risk"), "description": L("Ação", "Action"), "strat": L("Estratégia", "Strategy"),
                                  "owner": L("Responsável", "Owner"), "due": L("Prazo", "Due"), "cst": L("Custo", "Cost"), "st": L("Estado", "Status")}))
        else:
            parts.append(_tbl(acts, {}))

    if inc["kris"]:
        kr = scoring.analyse_kris(proj)
        parts.append(f"<h2>9. {L('Indicadores-chave de risco (KRIs)', 'Key risk indicators (KRIs)')}</h2>")
        if not kr.empty:
            col = {"green": "#22c55e", "amber": "#eab308", "red": "#ef4444", "na": "#94a3b8"}
            kr = kr.copy()
            kr["rag_p"] = [_pill(x.upper(), col[x]) for x in kr["rag"]]
            kr["tr"] = kr["trend_calc"].map(lambda v: label("trend", v))
            parts.append(_tbl(kr, {"id": "ID", "risk_id": L("Risco", "Risk"), "name": "KRI", "current": L("Atual", "Current"),
                                   "amber": L("Âmbar", "Amber"), "red": L("Vermelho", "Red"), "rag_p": "RAG", "tr": L("Tendência", "Trend")}))
        else:
            parts.append(_tbl(kr, {}))

    if inc["quant"] and not ra.empty:
        s = mc_settings or {"n": 10000, "rho": 0.2}
        inp = mc.build_inputs(ra, proj["meta"]["impact_thresholds"])
        if not inp.empty:
            ti, mi = mc.simulate(inp, s["n"], s["rho"])
            tr, _ = mc.simulate(inp, s["n"], s["rho"], residual=True)
            si, sr = mc.stats(ti, m.get("risk_capacity")), mc.stats(tr, m.get("risk_capacity"))
            parts.append(f"<h2 class='pb'>10. {L('Quantificação Monte Carlo', 'Monte Carlo quantification')}</h2>")
            parts.append(f"<p class='legend'>{s['n']:,} {L('iterações · correlação', 'iterations · correlation')} ρ={s['rho']:.2f} · PERT/Bernoulli</p>")
            stab = pd.DataFrame([
                {"m": L("Perda esperada (média)", "Expected loss (mean)"), "i": _m(si["mean"], cur), "r": _m(sr["mean"], cur)},
                {"m": "P50", "i": _m(si["p50"], cur), "r": _m(sr["p50"], cur)},
                {"m": L("P80 (contingência)", "P80 (contingency)"), "i": _m(si["p80"], cur), "r": _m(sr["p80"], cur)},
                {"m": "VaR 95%", "i": _m(si["p95"], cur), "r": _m(sr["p95"], cur)},
                {"m": "CVaR 95%", "i": _m(si["cvar95"], cur), "r": _m(sr["cvar95"], cur)},
                {"m": L("P(perda > capacidade)", "P(loss > capacity)"), "i": _p(si.get("p_exceed_capacity", 0)), "r": _p(sr.get("p_exceed_capacity", 0))},
            ])
            parts.append(_tbl(stab, {"m": L("Métrica", "Metric"), "i": L("Inerente", "Inherent"), "r": L("Residual", "Residual")}))
            parts.append(fig(charts.histogram(ti, tr, sr, dark=False, cur=cur)))
            parts.append(fig(charts.tornado(mc.sensitivity(mi, ti, inp), dark=False, title=L("Sensibilidade (tornado)", "Sensitivity (tornado)"))))

    if inc["fair"] and not proj["fair"].empty:
        parts.append(f"<h2>11. {L('Cenários FAIR (ciber / eventos de perda)', 'FAIR scenarios (cyber / loss events)')}</h2>")
        rows, curves = [], {}
        for sc in proj["fair"].to_dict(orient="records"):
            r = mc.simulate_fair(sc)
            stt = mc.stats(r["ale"])
            rows.append({"id": sc["id"], "s": sc["scenario"], "lef": f"{r['lef'].mean():.2f}", "ale": _m(stt["mean"], cur),
                         "p90": _m(stt["p90"], cur), "p95": _m(stt["p95"], cur)})
            curves[f"{sc['id']} {sc['scenario'][:30]}"] = mc.exceedance_curve(r["ale"])
        parts.append(_tbl(pd.DataFrame(rows), {"id": "ID", "s": L("Cenário", "Scenario"), "lef": L("LEF/ano", "LEF/yr"),
                                                "ale": "ALE", "p90": "P90", "p95": "P95"}))
        parts.append(fig(charts.exceedance(curves, dark=False, cur=cur, title=L("Curvas de excedência de perdas", "Loss exceedance curves"))))

    if inc["fmea"] and not proj["fmea"].empty:
        f = scoring.analyse_fmea(proj)
        parts.append(f"<h2>12. FMEA</h2>")
        parts.append(_tbl(f.sort_values("rpn", ascending=False), {"id": "ID", "process": L("Processo", "Process"), "failure_mode": L("Modo de falha", "Failure mode"),
                                                                   "s": "S", "o": "O", "d": "D", "rpn": "RPN", "ap": "AP", "action": L("Ação", "Action")}))

    if inc["maturity"]:
        mm = proj["maturity"].copy()
        names = [next(((en if lang() == "en" else pt) for c, pt, en in MATURITY_DIMENSIONS if c == d), d) for d in mm["dim"]]
        parts.append(f"<h2 class='pb'>13. {L('Maturidade da gestão de risco', 'Risk management maturity')}</h2>")
        parts.append(fig(charts.radar(mm, names, dark=False)))

    if inc["method"]:
        parts.append(f"<h2>14. {L('Metodologia e legendas', 'Methodology and legends')}</h2><div class='legend'>{methodology_html()}</div>")
    parts.append(f"<footer>Risk Studio · ISO 31000 · COSO ERM · {L('Gerado em', 'Generated on')} {dt.datetime.now().strftime('%d/%m/%Y %H:%M')}</footer>")
    parts.append("</div></body></html>")
    return "".join(parts)


def methodology_html() -> str:
    items = [
        L("<b>Processo ISO 31000:2018</b> — comunicação e consulta; âmbito, contexto e critérios; identificação, análise e avaliação; tratamento; monitorização e revisão; registo e reporte.",
          "<b>ISO 31000:2018 process</b> — communication & consultation; scope, context & criteria; identification, analysis & evaluation; treatment; monitoring & review; recording & reporting."),
        L("<b>Score</b> = Probabilidade (1–5) × Impacto (1–5). Inerente = sem controlos; Residual = com os controlos atuais; Alvo = após tratamento.",
          "<b>Score</b> = Probability (1–5) × Impact (1–5). Inherent = without controls; Residual = with current controls; Target = after treatment."),
        L("<b>Eficácia do controlo</b> e = força da natureza (automático 0,80 · manual dep. TI 0,65 · manual 0,55) × fator do teste de desenho × fator do teste operacional (eficaz 1 · parcial 0,5 · não testado 0,3 · ineficaz 0).",
          "<b>Control effectiveness</b> e = nature strength (automated 0.80 · IT-dependent manual 0.65 · manual 0.55) × design test factor × operating test factor (effective 1 · partial 0.5 · not tested 0.3 · ineffective 0)."),
        L("<b>Residual</b>: E_prev = 1−Π(1−e) dos controlos preventivos (diretivos a 50%); E_mit idem para detetivos (60%) e corretivos. P_res = P − arred(E_prev×(P−1)×0,75); I_res análogo. Pode ser substituído por julgamento do avaliador.",
          "<b>Residual</b>: E_prev = 1−Π(1−e) of preventive controls (directive at 50%); E_mit likewise for detective (60%) and corrective. P_res = P − round(E_prev×(P−1)×0.75); I_res likewise. Assessor judgement can override."),
        L("<b>Prioridade</b> = score residual × fator de velocidade (0,8–1,2) × fator de proximidade (0,9–1,1).",
          "<b>Priority</b> = residual score × velocity factor (0.8–1.2) × proximity factor (0.9–1.1)."),
        L("<b>Apetite e tolerância</b> por categoria (COSO ERM): dentro do apetite · acima do apetite mas dentro da tolerância · fora da tolerância (decisão obrigatória).",
          "<b>Appetite and tolerance</b> by category (COSO ERM): within appetite · above appetite but within tolerance · outside tolerance (decision required)."),
        L("<b>Cadeia de controlo</b>: Risco → Objetivo de controlo → Controlo → Evidência → Teste → Conclusão → Ação. Cada risco deve ter controlos e cada controlo deve mapear para um risco.",
          "<b>Control chain</b>: Risk → Control objective → Control → Evidence → Testing → Conclusion → Action. Every risk should have controls and every control should map to a risk."),
        L("<b>Monte Carlo</b>: ocorrência Bernoulli (probabilidade anual) com cópula gaussiana (ρ) e impacto PERT (mín., + provável, máx.). Métricas: média (perda esperada), P50, P80, VaR95, CVaR95.",
          "<b>Monte Carlo</b>: Bernoulli occurrence (annual probability) with Gaussian copula (ρ) and PERT impact (min, most likely, max). Metrics: mean (expected loss), P50, P80, VaR95, CVaR95."),
        L("<b>FAIR</b>: LEF = TEF × Vulnerabilidade; perda por evento = perda primária + (prob. secundária × perda secundária); ALE = Σ perdas no ano (Poisson).",
          "<b>FAIR</b>: LEF = TEF × Vulnerability; loss per event = primary + (secondary probability × secondary loss); ALE = Σ annual losses (Poisson)."),
        L("<b>Oportunidades</b> (Hillson): tratadas com explorar · potenciar · partilhar · aceitar, em matriz própria (tons de azul).",
          "<b>Opportunities</b> (Hillson): handled with exploit · enhance · share · accept, on their own matrix (blue shades)."),
    ]
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"
