import datetime as dt
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import charts, db, scoring
from core import history as H
from core.i18n import L
from core.model import from_json
from core.ui import ai_assist, flash, hero, interpret_box, kpi, money, note, pct, proj, save_to_db, set_project

def _n1(v, sign: bool = False) -> str:
    s_ = f"{float(v or 0):+.1f}" if sign else f"{float(v or 0):.1f}"
    return s_.replace(".", ",") if st.session_state.get("lang", "pt") == "pt" else s_


p = proj()
hero(L("Evolução & comparação", "Evolution & comparison"),
     L("Base de dados de análises (PostgreSQL) · linha temporal · cenário passado vs. atual",
       "Analysis database (PostgreSQL) · timeline · past vs current scenario"), "📈", help_key="evolution")

pid = st.session_state.get("pid")
if not pid:
    st.info(L("Guarde o projeto na base de dados para ativar o histórico. A partir daí, a primeira gravação de cada dia regista "
              "automaticamente uma revisão e pode registar revisões manuais (ex.: comité de risco mensal).",
              "Save the project to the database to enable history. From then on, the first save of each day records a review "
              "automatically and you can record manual reviews (e.g. monthly risk committee)."), icon="💾")
    if st.button(L("💾 Guardar projeto e registar a 1.ª revisão", "💾 Save project and record the 1st review"), type="primary"):
        pid = save_to_db()  # the first save of the day records the initial review automatically
        if not db.list_snapshots(pid):
            H.record_review(p, pid, L(f"Revisão inicial {dt.date.today():%d/%m/%Y}", f"Initial review {dt.date.today():%Y-%m-%d}"))
        flash(L("Projeto guardado e revisão registada ✔", "Project saved and review recorded ✔"))
        st.rerun()
    st.stop()

c1, c2 = st.columns([3, 1])
lab = c1.text_input(L("Etiqueta da revisão", "Review label"), value=L(f"Revisão {dt.date.today():%d/%m/%Y}", f"Review {dt.date.today():%Y-%m-%d}"))
if c2.button(L("📸 Registar revisão agora", "📸 Record review now"), type="primary", width="stretch"):
    st.session_state["_auto_review"] = (pid, dt.date.today().isoformat())  # manual review replaces today's automatic one
    save_to_db()
    H.record_review(p, pid, lab)
    flash(L("Revisão registada ✔ (fotografia do projeto + análises de todos os módulos)", "Review recorded ✔ (project snapshot + every module's analysis)"))
    st.rerun()

snaps = db.list_snapshots(pid)
analyses = db.list_analyses(pid)
st.caption(L(f"💾 {db.backend_name()} · {len(snaps)} revisões · {len(analyses)} análises guardadas · revisão automática na 1.ª gravação de cada dia.",
             f"💾 {db.backend_name()} · {len(snaps)} reviews · {len(analyses)} saved analyses · automatic review on the first save of each day."))

t1, t2, t3, t4 = st.tabs([L("① Linha temporal", "① Timeline"), L("② Passado vs. atual", "② Past vs current"),
                          L("③ Análises guardadas", "③ Saved analyses"), L("④ Gerir revisões", "④ Manage reviews")])

# ------------------------------------------------------------------ timeline
with t1:
    if not snaps:
        st.info(L("Ainda não há revisões. Registe a primeira acima.", "No reviews yet. Record the first one above."))
    else:
        by_sid: dict = {}
        for a in analyses:
            if a["snapshot_id"]:
                by_sid.setdefault(a["snapshot_id"], {})[a["module"]] = a
        rows, per_risk = [], {}
        cur_k = H.state_kpis(p)
        points = [(f"{s['label']} · #{s['id']}", str(s["created_at"])[:10], by_sid.get(s["id"], {})) for s in snaps]
        for name, date, mods in points:
            k_ = {**(mods.get("dashboard", {}).get("kpis") or {}), **(mods.get("quant", {}).get("kpis") or {}),
                  **(mods.get("controls", {}).get("kpis") or {}), **(mods.get("maturity", {}).get("kpis") or {})}
            rows.append({"point": name, "date": date, **k_})
            for rid, d in (mods.get("register", {}).get("details") or {}).items():
                if d.get("type") == "threat":
                    per_risk.setdefault(f"{rid} {d.get('title', '')[:28]}", {})[name] = d.get("res")
        rows.append({"point": L("Atual", "Current"), "date": dt.date.today().isoformat(), **cur_k})
        ra = scoring.analyse_risks(p)
        for r in ra[ra["type"] == "threat"].to_dict(orient="records") if not ra.empty else []:
            per_risk.setdefault(f"{r['id']} {r['title'][:28]}", {})[L("Atual", "Current")] = r["score_res"]
        hist = pd.DataFrame(rows)
        x = hist["point"]
        cc = st.columns(4)
        first, last = hist.iloc[0], hist.iloc[-1]

        def _d(col, fmt="1f"):
            a, b = first.get(col), last.get(col)
            if a is None or b is None or pd.isna(a) or pd.isna(b):
                return ""
            d = b - a
            return (_n1(d, True) if fmt == "1f" else (f"{d * 100:+.0f} p.p." if fmt == "pct" else f"{d:+,.0f}")) + L(" desde a 1.ª revisão", " since 1st review")
        kpi(cc[0], L("Score residual médio", "Avg residual score"), _n1(last.get("avg_res", 0)), _d("avg_res"))
        kpi(cc[1], L("Fora da tolerância", "Outside tolerance"), f"{int(last.get('outside', 0) or 0)}", _d("outside"), "#e34948")
        kpi(cc[2], L("Cobertura de controlos", "Control coverage"), pct(last.get("coverage") or 0), _d("coverage", "pct"), "#1f9d55")
        kpi(cc[3], L("Perda esperada residual", "Residual expected loss"), money(last.get("eal_res")), _d("eal_res", "money"), "#eb6834")
        st.write("")
        c1, c2 = st.columns(2)
        fig = go.Figure()
        for col, nm in [("avg_inh", L("Inerente médio", "Avg inherent")), ("avg_res", L("Residual médio", "Avg residual"))]:
            if col in hist:
                fig.add_trace(go.Scatter(x=x, y=hist[col], name=nm, mode="lines+markers", line=dict(width=3)))
        for col, nm, colr in [("outside", L("Fora da tolerância", "Outside tolerance"), "#e34948"), ("critical_res", L("Críticos", "Critical"), "#eb6834")]:
            if col in hist:
                fig.add_trace(go.Bar(x=x, y=hist[col], name=nm, yaxis="y2", opacity=0.45, marker_color=colr))
        fig.update_layout(yaxis=dict(rangemode="tozero", title="Score"), yaxis2=dict(overlaying="y", side="right", showgrid=False, rangemode="tozero",
                                                                                      dtick=1, title=L("n.º riscos", "# risks")),
                          legend=dict(orientation="h", y=1.12, x=0), barmode="group", margin=dict(t=80))
        c1.plotly_chart(charts._layout(fig, False, L("Exposição ao longo do tempo", "Exposure over time"), 380), width="stretch")
        fig = go.Figure()
        for col, nm in [("coverage", L("Cobertura", "Coverage")), ("tested", L("Testados", "Tested")), ("chain", L("Cadeia", "Chain")),
                        ("reduction", L("Redução", "Reduction"))]:
            if col in hist:
                fig.add_trace(go.Scatter(x=x, y=hist[col], name=nm, mode="lines+markers", line=dict(width=3)))
        fig.update_yaxes(tickformat=".0%", range=[0, 1.05])
        fig.update_layout(legend=dict(orientation="h", y=1.12, x=0), margin=dict(t=80))
        c2.plotly_chart(charts._layout(fig, False, L("Qualidade do sistema de controlo", "Control system quality"), 380), width="stretch")
        if "eal_res" in hist:
            fig = go.Figure()
            for col, nm in [("eal_inh", L("Perda esperada inerente", "Inherent expected loss")), ("eal_res", L("Perda esperada residual", "Residual expected loss")),
                            ("p80_res", "P80"), ("var95_res", "VaR 95%")]:
                if col in hist:
                    fig.add_trace(go.Scatter(x=x, y=hist[col], name=nm, mode="lines+markers", line=dict(width=3)))
            if p["meta"].get("risk_capacity"):
                fig.add_hline(y=p["meta"]["risk_capacity"], line=dict(dash="dash", color="#e34948"), annotation_text=L("Capacidade", "Capacity"))
            fig.update_layout(legend=dict(orientation="h", y=1.12, x=0), margin=dict(t=80))
            st.plotly_chart(charts._layout(fig, False, L("Exposição financeira (Monte Carlo) ao longo do tempo", "Financial exposure (Monte Carlo) over time"), 380),
                            width="stretch")
        if per_risk:
            pr = pd.DataFrame(per_risk).T.reindex(columns=list(x))
            fig = go.Figure(go.Heatmap(z=pr.values, x=list(pr.columns), y=list(pr.index), colorscale=[[0, "#1f9d55"], [0.35, "#eda100"], [0.6, "#eb6834"], [1, "#c62828"]],
                                       zmin=1, zmax=25, text=pr.values, texttemplate="%{text}", xgap=2, ygap=2, colorbar=dict(title="Score")))
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(charts._layout(fig, False, L("Score residual por risco em cada revisão", "Residual score per risk at each review"),
                                           max(320, 28 * len(pr) + 120)), width="stretch")
        with st.expander(L("Tabela de indicadores por revisão", "Indicators per review table")):
            st.dataframe(hist, hide_index=True, width="stretch")

# ------------------------------------------------------------------ past vs current
with t2:
    if not snaps:
        st.info(L("Registe pelo menos uma revisão para comparar.", "Record at least one review to compare."))
    else:
        opts = {s["id"]: f"{s['label']} · {str(s['created_at'])[:16]}" for s in snaps}
        c1, c2, c3 = st.columns([2, 2, 1])
        old_id = c1.selectbox(L("Cenário passado", "Past scenario"), list(opts), index=0, format_func=lambda i: opts[i])
        new_opts = {0: L("Atual (projeto aberto)", "Current (open project)"), **opts}
        new_id = c2.selectbox(L("Comparar com", "Compare with"), list(new_opts), index=0, format_func=lambda i: new_opts[i])
        with_mc = c3.toggle(L("Incluir Monte Carlo", "Include Monte Carlo"), True)
        snap_by = {s["id"]: s for s in snaps}
        old = from_json(snap_by[old_id]["data"])
        new = p if new_id == 0 else from_json(snap_by[new_id]["data"])
        with st.spinner(L("A comparar…", "Comparing…")):
            cmp = H.compare(old, new, with_mc)
        interpret_box(cmp["narrative"], L("Interpretação automática da evolução", "Automatic interpretation of the evolution"))
        sym = {"better": "🟢 ▲", "worse": "🔴 ▼", "=": "—"}

        def fmtv(v, f):
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return "—"
            return {"int": f"{int(v)}", "1f": _n1(v), "pct": pct(v), "money": money(v)}[f]
        kt = pd.DataFrame([{L("Indicador", "Indicator"): r["metric"], L("Passado", "Past"): fmtv(r["past"], r["fmt"]),
                            L("Atual", "Current"): fmtv(r["current"], r["fmt"]),
                            "Δ": ("" if r["fmt"] in ("money",) else "") + (fmtv(r["delta"], r["fmt"]) if r["fmt"] != "pct" else f"{r['delta'] * 100:+.0f} p.p."),
                            L("Avaliação", "Assessment"): sym[r["verdict"]]} for r in cmp["kpis"]])
        st.dataframe(kt, hide_index=True, width="stretch")
        ra_o, ra_n = scoring.analyse_risks(old), scoring.analyse_risks(new)
        c1, c2 = st.columns(2)
        if not ra_o.empty:
            c1.plotly_chart(charts.heatmap(ra_o, "res", title=L("Residual — passado", "Residual — past"), height=400), width="stretch")
        if not ra_n.empty:
            c2.plotly_chart(charts.heatmap(ra_n, "res", title=L("Residual — atual", "Residual — current"), height=400), width="stretch")
        if cmp["changes"]:
            st.markdown(f"**{L('Riscos com alteração de score ou de posição face ao apetite', 'Risks whose score or appetite position changed')}**")
            ch = pd.DataFrame(cmp["changes"])
            ch["status_past"] = ch["status_past"].map(scoring.appetite_label)
            ch["status_now"] = ch["status_now"].map(scoring.appetite_label)
            ch["Δ"] = ch["delta"].map(lambda d: f"{'🔴 +' if d > 0 else ('🟢 ' if d < 0 else '')}{d}")
            st.dataframe(ch[["id", "title", "past", "current", "Δ", "status_past", "status_now"]].rename(columns={
                "id": "ID", "title": L("Risco", "Risk"), "past": L("Passado", "Past"), "current": L("Atual", "Current"),
                "status_past": L("Apetite (passado)", "Appetite (past)"), "status_now": L("Apetite (atual)", "Appetite (current)")}),
                hide_index=True, width="stretch")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**{L('Novos riscos', 'New risks')}** ({len(cmp['added'])})")
            for i, t in cmp["added"]:
                st.markdown(f"- {i} · {t}")
        with c2:
            st.markdown(f"**{L('Riscos retirados', 'Removed risks')}** ({len(cmp['removed'])})")
            for i, t in cmp["removed"]:
                st.markdown(f"- {i} · {t}")
        if cmp["ctrl_changes"]:
            from core.catalogs import label as clabel
            st.markdown(f"**{L('Controlos cuja conclusão do teste mudou', 'Controls whose test conclusion changed')}**")
            st.dataframe(pd.DataFrame(cmp["ctrl_changes"]).assign(past=lambda d: d["past"].map(lambda v: clabel("test", v)),
                                                                   current=lambda d: d["current"].map(lambda v: clabel("test", v))),
                         hide_index=True, width="stretch")
        ai_assist("evolution", cmp["narrative"], H.compare_text(cmp),
                  page_title=L(f"Evolução: {opts[old_id]} → {new_opts[new_id]}", f"Evolution: {opts[old_id]} → {new_opts[new_id]}"))

# ------------------------------------------------------------------ saved analyses
with t3:
    if not analyses:
        st.info(L("Ainda não há análises guardadas. Use «💾 Guardar análise no histórico» em qualquer página ou registe uma revisão.",
                  "No saved analyses yet. Use '💾 Save analysis to history' on any page or record a review."))
    else:
        mods = sorted({a["module"] for a in analyses})
        sel = st.multiselect(L("Módulos", "Modules"), mods, default=mods, format_func=H.mod_name)
        only_ai = st.toggle(L("Só análises com texto do agente IA", "Only analyses with AI agent text"), False)
        items = [a for a in reversed(analyses) if a["module"] in sel and (a["ai_text"] or not only_ai)]
        tbl = pd.DataFrame([{L("Data", "Date"): str(a["created_at"])[:16], L("Módulo", "Module"): H.mod_name(a["module"]),
                             L("Etiqueta", "Label"): a["label"], L("Revisão", "Review"): "📸" if a["snapshot_id"] else "💾",
                             "IA": "🤖" if a["ai_text"] else ""} for a in items])
        st.dataframe(tbl, hide_index=True, width="stretch")
        for a in items[:40]:
            if not (a["interpretation"] or a["ai_text"]):
                continue
            with st.expander(f"{str(a['created_at'])[:16]} · {H.mod_name(a['module'])} · {a['label']}"):
                if a["interpretation"]:
                    st.markdown("**🧭 " + L("Leitura automática", "Automatic reading") + "**\n" + "\n".join(f"- {x}" for x in a["interpretation"].splitlines()))
                if a["ai_text"]:
                    st.markdown("**🤖 " + L("Agente IA", "AI agent") + "**")
                    st.markdown(a["ai_text"])
                if a["kpis"]:
                    st.json(a["kpis"], expanded=False)
                if st.button("🗑️", key=f"da_{a['id']}"):
                    db.delete_analysis(a["id"])
                    st.rerun()
        st.download_button(L("⬇️ Exportar histórico de análises (JSON)", "⬇️ Export analysis history (JSON)"),
                           json.dumps(analyses, ensure_ascii=False, default=str, indent=1), f"risk_studio_historico_{pid}.json", "application/json")

# ------------------------------------------------------------------ manage reviews
with t4:
    if not snaps:
        st.caption("—")
    for sn in reversed(snaps):
        a, b, c = st.columns([5, 1, 1])
        a.markdown(f"**{sn['label']}** · {str(sn['created_at'])[:16]}")
        if b.button(L("Restaurar", "Restore"), key=f"rs_{sn['id']}", help=L("Abre esta versão na sessão (grave depois para a tornar atual)", "Opens this version in the session")):
            set_project(from_json(sn["data"]), pid)
            flash(L("Versão restaurada na sessão — grave para a tornar a versão atual.", "Version restored in the session — save to make it current."))
            st.rerun()
        if c.button("🗑️", key=f"rd_{sn['id']}"):
            db.delete_snapshot(sn["id"])
            st.rerun()
    note(L("Cada revisão guarda uma fotografia completa do projeto (JSON) e uma linha por módulo na tabela <code>risk_analyses</code> "
           "(indicadores, detalhe por risco/controlo, leitura automática e texto do agente). Em produção estas tabelas ficam no PostgreSQL do Render.",
           "Each review stores a full project snapshot (JSON) and one row per module in the <code>risk_analyses</code> table "
           "(indicators, per-risk/control detail, automatic reading and agent text). In production these tables live in Render's PostgreSQL."))
