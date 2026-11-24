"""Temporal comparison: module summaries stored in PostgreSQL (risk_analyses) at every review,
and past-vs-current comparison of two project states."""
from __future__ import annotations

import datetime as dt

import pandas as pd

from core import montecarlo as mc
from core import scoring
from core.i18n import L

MODULES = {
    "dashboard": ("Perfil de risco", "Risk profile"),
    "register": ("Registo de riscos", "Risk register"),
    "matrix": ("Matrizes & prioridades", "Matrices & priorities"),
    "controls": ("Controlos & RCM", "Controls & RCM"),
    "treatment": ("Tratamento & ações", "Treatment & actions"),
    "kris": ("KRIs", "KRIs"),
    "quant": ("Monte Carlo", "Monte Carlo"),
    "fair": ("FAIR", "FAIR"),
    "techniques": ("Bow-Tie & FMEA", "Bow-Tie & FMEA"),
    "maturity": ("Maturidade ERM", "ERM maturity"),
    "evolution": ("Evolução & comparação", "Evolution & comparison"),
}


def mod_name(key: str) -> str:
    t = MODULES.get(key, (key, key))
    return L(t[0], t[1])


def mc_quick(p: dict, n: int = 4000, rho: float = 0.2) -> dict:
    ra = scoring.analyse_risks(p)
    if ra.empty:
        return {}
    inp = mc.build_inputs(ra, p["meta"]["impact_thresholds"])
    if inp.empty:
        return {}
    ti, _ = mc.simulate(inp, n, rho, 42)
    tr, _ = mc.simulate(inp, n, rho, 42, residual=True)
    si, sr = mc.stats(ti, p["meta"].get("risk_capacity")), mc.stats(tr, p["meta"].get("risk_capacity"))
    return {"eal_inh": si["mean"], "eal_res": sr["mean"], "p80_res": sr["p80"], "var95_res": sr["p95"], "cvar95_res": sr["cvar95"],
            "p_exceed_res": sr.get("p_exceed_capacity", 0.0)}


def module_summary(p: dict, module: str) -> tuple[dict, dict]:
    """(kpis, details) for one module — what gets stored for temporal comparison."""
    k = scoring.kpis(p)
    if module in ("dashboard", "matrix"):
        keys = ["n_risks", "n_threats", "n_opps", "critical_inh", "critical_res", "outside", "above_appetite", "avg_inh", "avg_res",
                "reduction", "coverage", "tested", "overdue", "kri_red"]
        return {x: k[x] for x in keys}, {}
    if module == "register":
        ra = scoring.analyse_risks(p)
        det = {r["id"]: {"title": r["title"], "type": r["type"], "category": r["category"], "inh": int(r["score_inh"]), "res": int(r["score_res"]),
                         "tgt": int(r["score_tgt"]), "status": r["appetite_status"], "priority": float(r["priority"])}
               for r in ra.to_dict(orient="records")} if not ra.empty else {}
        return {x: k[x] for x in ("n_risks", "avg_inh", "avg_res", "outside", "critical_res")}, det
    if module == "controls":
        ca = scoring.analyse_controls(p)
        det = {c["id"]: {"name": c["name"], "conclusion": c["conclusion"], "eff": float(c["effectiveness"]), "risks": c["risk_ids"]}
               for c in ca.to_dict(orient="records")} if not ca.empty else {}
        return {"n_controls": k["n_controls"], "coverage": k["coverage"], "mapped": k["mapped"], "tested": k["tested"], "chain": k["chain"],
                "avg_eff": float(ca["effectiveness"].mean()) if not ca.empty else 0.0, "no_controls": k["no_controls"], "orphans": k["orphans"]}, det
    if module == "treatment":
        a = scoring.analyse_actions(p)
        return {"n_actions": k["n_actions"], "done": k["done"], "overdue": k["overdue"],
                "progress": float(a["progress"].mean()) if not a.empty else 0.0,
                "cost": float(a["cost"].fillna(0).sum()) if not a.empty else 0.0}, {}
    if module == "kris":
        kr = scoring.analyse_kris(p)
        det = {r["id"]: {"name": r["name"], "current": r["current"], "rag": r["rag"]} for r in kr.to_dict(orient="records")} if not kr.empty else {}
        return {"n_kris": k["n_kris"], "kri_red": k["kri_red"], "kri_amber": k["kri_amber"]}, det
    if module == "quant":
        return mc_quick(p), {}
    if module == "fair":
        det = {}
        for sc in p["fair"].to_dict(orient="records"):
            r = mc.simulate_fair(sc, 4000)
            s = mc.stats(r["ale"])
            det[sc["id"]] = {"scenario": sc["scenario"], "ale": s["mean"], "p95": s["p95"]}
        return {"ale_total": sum(v["ale"] for v in det.values())}, det
    if module == "techniques":
        f = scoring.analyse_fmea(p)
        return {"n_fmea": int(len(f)), "ap_high": int((f["ap"] == "H").sum()) if not f.empty else 0,
                "max_rpn": int(f["rpn"].max()) if not f.empty else 0}, ({r["id"]: int(r["rpn"]) for r in f.to_dict(orient="records")} if not f.empty else {})
    if module == "maturity":
        cur, tgt = scoring.maturity_index(p)
        return {"maturity": cur, "maturity_target": tgt}, {r["dim"]: int(r["current"]) for r in p["maturity"].to_dict(orient="records")}
    return {}, {}


def record_review(p: dict, pid: int, label: str, auto: bool = False) -> int:
    """Snapshot of the whole project + one analysis row per module (for time series and comparisons)."""
    from core import db
    from core import interpret as I
    from core.model import to_json
    sid = db.save_snapshot(pid, label, to_json(p))
    interp = {"dashboard": [], "matrix": I.matrix(p), "controls": I.controls(p), "treatment": I.treatment(p), "kris": I.kris(p),
              "maturity": I.maturity(p), "techniques": I.fmea(p)}
    for mod in ("dashboard", "register", "controls", "treatment", "kris", "quant", "fair", "techniques", "maturity"):
        try:
            kp, det = module_summary(p, mod)
            db.save_analysis(pid, mod, label, kp, det, "\n".join(interp.get(mod, [])), "", snapshot_id=sid)
        except Exception:
            continue
    return sid


def maybe_auto_review(p: dict, pid: int) -> bool:
    """Automatic daily review: first save of each day records a snapshot (so evolution exists without manual effort)."""
    from core import db
    try:
        last = db.last_snapshot_date(pid)
        if last is None or last.date() < dt.datetime.utcnow().date():
            record_review(p, pid, L(f"Automática {dt.date.today():%d/%m/%Y}", f"Automatic {dt.date.today():%Y-%m-%d}"), auto=True)
            return True
    except Exception:
        pass
    return False


# ------------------------------------------------------------------ comparison
KPI_ROWS = [  # key, PT, EN, higher_is_better, format
    ("n_risks", "N.º de riscos", "Number of risks", None, "int"),
    ("avg_inh", "Score inerente médio", "Avg inherent score", False, "1f"),
    ("avg_res", "Score residual médio", "Avg residual score", False, "1f"),
    ("critical_res", "Riscos críticos (residual)", "Critical risks (residual)", False, "int"),
    ("outside", "Fora da tolerância", "Outside tolerance", False, "int"),
    ("above_appetite", "Acima do apetite", "Above appetite", False, "int"),
    ("reduction", "Redução pelos controlos", "Reduction by controls", True, "pct"),
    ("coverage", "Cobertura de controlos", "Control coverage", True, "pct"),
    ("tested", "Controlos testados", "Controls tested", True, "pct"),
    ("chain", "Completude da cadeia", "Chain completeness", True, "pct"),
    ("overdue", "Ações em atraso", "Overdue actions", False, "int"),
    ("kri_red", "KRIs a vermelho", "Red KRIs", False, "int"),
    ("eal_res", "Perda esperada residual", "Residual expected loss", False, "money"),
    ("p80_res", "P80 residual (contingência)", "Residual P80 (contingency)", False, "money"),
    ("var95_res", "VaR 95% residual", "Residual VaR 95%", False, "money"),
    ("maturity", "Índice de maturidade", "Maturity index", True, "1f"),
]


def state_kpis(p: dict, with_mc: bool = True) -> dict:
    k = scoring.kpis(p)
    out = {x[0]: k.get(x[0]) for x in KPI_ROWS if x[0] in k}
    if with_mc:
        out.update(mc_quick(p))
    out["maturity"] = scoring.maturity_index(p)[0]
    return out


def compare(old: dict, new: dict, with_mc: bool = True) -> dict:
    ko, kn = state_kpis(old, with_mc), state_kpis(new, with_mc)
    rows = []
    for key, pt, en, hib, fmt in KPI_ROWS:
        a, b = ko.get(key), kn.get(key)
        if a is None and b is None:
            continue
        d = (b or 0) - (a or 0)
        verdict = "="
        if hib is not None and abs(d) > 1e-9:
            verdict = "better" if (d > 0) == hib else "worse"
        rows.append({"key": key, "metric": L(pt, en), "past": a, "current": b, "delta": d, "verdict": verdict, "fmt": fmt})
    ra_o, ra_n = scoring.analyse_risks(old), scoring.analyse_risks(new)
    o = ra_o.set_index("id") if not ra_o.empty else pd.DataFrame()
    n = ra_n.set_index("id") if not ra_n.empty else pd.DataFrame()
    ids_o, ids_n = set(o.index), set(n.index)
    added = sorted(ids_n - ids_o)
    removed = sorted(ids_o - ids_n)
    common = sorted(ids_o & ids_n)
    changes = []
    for rid in common:
        so, sn = int(o.loc[rid, "score_res"]), int(n.loc[rid, "score_res"])
        if so != sn or o.loc[rid, "appetite_status"] != n.loc[rid, "appetite_status"]:
            changes.append({"id": rid, "title": n.loc[rid, "title"], "past": so, "current": sn, "delta": sn - so,
                            "status_past": o.loc[rid, "appetite_status"], "status_now": n.loc[rid, "appetite_status"]})
    ca_o, ca_n = scoring.analyse_controls(old), scoring.analyse_controls(new)
    co = ca_o.set_index("id") if not ca_o.empty else pd.DataFrame()
    cn = ca_n.set_index("id") if not ca_n.empty else pd.DataFrame()
    ctrl_changes = []
    for cid in sorted(set(co.index) & set(cn.index)):
        if co.loc[cid, "conclusion"] != cn.loc[cid, "conclusion"]:
            ctrl_changes.append({"id": cid, "name": cn.loc[cid, "name"], "past": co.loc[cid, "conclusion"], "current": cn.loc[cid, "conclusion"]})
    res = {"kpis": rows, "added": [(i, n.loc[i, "title"]) for i in added], "removed": [(i, o.loc[i, "title"]) for i in removed],
           "changes": changes, "ctrl_added": sorted(set(cn.index) - set(co.index)), "ctrl_removed": sorted(set(co.index) - set(cn.index)),
           "ctrl_changes": ctrl_changes}
    res["narrative"] = narrative(res)
    return res


def narrative(c: dict) -> list[str]:
    out = []
    kp = {r["key"]: r for r in c["kpis"]}
    if "avg_res" in kp:
        r = kp["avg_res"]
        trend = L("desceu", "fell") if r["delta"] < 0 else (L("subiu", "rose") if r["delta"] > 0 else L("manteve-se", "was unchanged"))
        a_, b_ = f"{(r['past'] or 0):.1f}", f"{(r['current'] or 0):.1f}"
        out.append(L(f"O score residual médio {trend} de **{a_.replace('.', ',')}** para **{b_.replace('.', ',')}**.",
                     f"The average residual score {trend} from **{(r['past'] or 0):.1f}** to **{(r['current'] or 0):.1f}**."))
    better = [r["metric"] for r in c["kpis"] if r["verdict"] == "better"]
    worse = [r["metric"] for r in c["kpis"] if r["verdict"] == "worse"]
    if better:
        out.append(L("✅ Melhorou: " + ", ".join(better) + ".", "✅ Improved: " + ", ".join(better) + "."))
    if worse:
        out.append(L("⚠️ Piorou: " + ", ".join(worse) + ".", "⚠️ Worsened: " + ", ".join(worse) + "."))
    up = [x for x in c["changes"] if x["delta"] > 0]
    down = [x for x in c["changes"] if x["delta"] < 0]
    if up:
        out.append(L("Riscos agravados: " + ", ".join(f"{x['id']} ({x['past']}→{x['current']})" for x in up) + ".",
                     "Risks worsened: " + ", ".join(f"{x['id']} ({x['past']}→{x['current']})" for x in up) + "."))
    if down:
        out.append(L("Riscos reduzidos: " + ", ".join(f"{x['id']} ({x['past']}→{x['current']})" for x in down) + ".",
                     "Risks reduced: " + ", ".join(f"{x['id']} ({x['past']}→{x['current']})" for x in down) + "."))
    if c["added"]:
        out.append(L(f"Novos riscos: {', '.join(i for i, _ in c['added'])}.", f"New risks: {', '.join(i for i, _ in c['added'])}."))
    if c["removed"]:
        out.append(L(f"Riscos retirados do registo: {', '.join(i for i, _ in c['removed'])}.", f"Risks removed: {', '.join(i for i, _ in c['removed'])}."))
    if c["ctrl_added"] or c["ctrl_removed"]:
        out.append(L(f"Controlos novos: {', '.join(c['ctrl_added']) or '—'} · retirados: {', '.join(c['ctrl_removed']) or '—'}.",
                     f"New controls: {', '.join(c['ctrl_added']) or '—'} · removed: {', '.join(c['ctrl_removed']) or '—'}."))
    if c["ctrl_changes"]:
        out.append(L("Mudou a conclusão do teste em: " + ", ".join(x["id"] for x in c["ctrl_changes"]) + ".",
                     "Test conclusion changed in: " + ", ".join(x["id"] for x in c["ctrl_changes"]) + "."))
    if len(out) <= 1:
        out.append(L("Sem alterações materiais entre os dois momentos.", "No material changes between the two points in time."))
    return out


def compare_text(c: dict) -> str:
    lines = ["KPI | passado | atual | Δ | avaliação"]
    for r in c["kpis"]:
        lines.append(f"{r['metric']} | {r['past']} | {r['current']} | {r['delta']} | {r['verdict']}")
    lines.append("Riscos alterados: " + "; ".join(f"{x['id']} {x['title']} {x['past']}→{x['current']} ({x['status_past']}→{x['status_now']})" for x in c["changes"]))
    lines.append("Novos: " + "; ".join(f"{i} {t}" for i, t in c["added"]) + " | Retirados: " + "; ".join(f"{i} {t}" for i, t in c["removed"]))
    lines.append("Controlos novos/retirados: " + ", ".join(c["ctrl_added"]) + " / " + ", ".join(c["ctrl_removed"]))
    lines.append("Conclusões de teste alteradas: " + "; ".join(f"{x['id']} {x['past']}→{x['current']}" for x in c["ctrl_changes"]))
    return "\n".join(lines)
