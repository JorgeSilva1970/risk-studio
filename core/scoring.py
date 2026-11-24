"""Risk analytics: scores, residual risk from control effectiveness, appetite,
coverage gaps (risk ↔ control), KRIs, actions and FMEA.

Methodology (documented in the Methodology page):
* Score = Probability (1–5) × Impact (1–5).
* Control effectiveness e = nature strength × f(design test) × f(operating test).
* Combined preventive effectiveness  E_p = 1 − Π(1 − e_i)   (directive controls count 50 %).
* Combined mitigating effectiveness E_m = 1 − Π(1 − e_i)   (detective 60 %, corrective 100 %).
* Residual P = P_inh − round(E_p × (P_inh − 1) × 0.75); residual I likewise with E_m (min 1)
  (assessor overrides take precedence).
* Priority = residual score × velocity factor × proximity factor.
"""
from __future__ import annotations

import datetime as dt
import math

import numpy as np
import pandas as pd

from core.catalogs import (LEVELS, NATURE_STRENGTH, OPP_LEVELS, PROXIMITY_FACTOR, TEST_FACTOR,
                           VELOCITY_FACTOR)
from core.i18n import lang
from core.model import ids_list


def _round_half_up(x: float) -> int:
    return int(math.floor(x + 0.5))


def _n(v, default=None):
    if v is None:
        return default
    try:
        if pd.isna(v):
            return default
    except (TypeError, ValueError):
        pass
    return v


def level_of(score: float | None, opportunity: bool = False) -> tuple[str, str, str]:
    """Return (code, label, colour) for a 1–25 score."""
    if score is None or (isinstance(score, float) and math.isnan(score)):
        return ("na", "—", "#64748b")
    table = OPP_LEVELS if opportunity else LEVELS
    s = max(1, min(25, int(round(score))))
    for lo, hi, code, pt, en, col in table:
        if lo <= s <= hi:
            return (code, en if lang() == "en" else pt, col)
    return ("na", "—", "#64748b")


def level_label(code: str, opportunity=False) -> str:
    for lo, hi, c, pt, en, col in (OPP_LEVELS if opportunity else LEVELS):
        if c == code:
            return en if lang() == "en" else pt
    return "—"


# --------------------------------------------------------------- controls
def control_effectiveness(row: dict) -> tuple[float, str]:
    d = row.get("design_test") or "not_tested"
    o = row.get("operating_test") or "not_tested"
    nature = row.get("nature") or "manual"
    e = NATURE_STRENGTH.get(nature, 0.55) * TEST_FACTOR.get(d, 0.3) * TEST_FACTOR.get(o, 0.3)
    if d == "ineffective" or o == "ineffective":
        concl = "ineffective"
    elif d == "effective" and o == "effective":
        concl = "effective"
    elif "not_tested" in (d, o) and "partial" not in (d, o):
        concl = "not_tested"
    else:
        concl = "partial"
    return round(e, 3), concl


def analyse_controls(proj: dict) -> pd.DataFrame:
    c = proj["controls"].copy()
    if c.empty:
        return c.assign(effectiveness=pd.Series(dtype=float), conclusion=pd.Series(dtype=object),
                        n_risks=pd.Series(dtype=int), orphan=pd.Series(dtype=bool),
                        unknown_ids=pd.Series(dtype=object), chain=pd.Series(dtype=float),
                        chain_steps=pd.Series(dtype=object), has_action=pd.Series(dtype=bool))
    risk_ids = set(proj["risks"]["id"]) if not proj["risks"].empty else set()
    act = proj["actions"]
    act_ctrl = set(act["control_id"].dropna().astype(str).str.upper()) if not act.empty else set()
    effs, concls, nrisk, orphan, unknown, chain, steps, has_act = [], [], [], [], [], [], [], []
    for r in c.to_dict(orient="records"):
        e, concl = control_effectiveness(r)
        ids = ids_list(r.get("risk_ids"))
        valid = [i for i in ids if i in risk_ids]
        bad = [i for i in ids if i not in risk_ids]
        effs.append(e)
        concls.append(concl)
        nrisk.append(len(valid))
        orphan.append(len(valid) == 0)
        unknown.append(", ".join(bad))
        ha = str(r.get("id", "")).upper() in act_ctrl
        has_act.append(ha)
        # ControlKit 7-step chain: Risk → Objective → Control → Evidence → Testing → Conclusion → Action
        tested = r.get("design_test") not in (None, "not_tested") and r.get("operating_test") not in (None, "not_tested")
        s = {
            "risk": len(valid) > 0,
            "objective": bool(_n(r.get("objective"), "")),
            "control": bool(_n(r.get("name"), "")) ,
            "evidence": bool(_n(r.get("evidence"), "")),
            "testing": tested,
            "conclusion": tested and bool(_n(r.get("test_date"), "")),
            "action": concl == "effective" or ha,
        }
        steps.append(s)
        chain.append(sum(s.values()) / 7)
    c["effectiveness"] = effs
    c["conclusion"] = concls
    c["n_risks"] = nrisk
    c["orphan"] = orphan
    c["unknown_ids"] = unknown
    c["chain"] = chain
    c["chain_steps"] = steps
    c["has_action"] = has_act
    return c


# ------------------------------------------------------------------ risks
CONTROL_DAMPING = 0.75  # even perfect controls rarely remove a risk entirely


def residual_level(level: int, eff: float) -> int:
    """Residual level = inherent − round(E × (inherent − 1) × damping), floor 1."""
    return max(1, int(level) - _round_half_up(eff * (int(level) - 1) * CONTROL_DAMPING))


def _combine(effs: list[float]) -> float:
    prod = 1.0
    for e in effs:
        prod *= (1 - max(0.0, min(1.0, e)))
    return 1 - prod


def analyse_risks(proj: dict) -> pd.DataFrame:
    r = proj["risks"].copy()
    cols_extra = ["score_inh", "level_inh", "colour_inh", "n_controls", "controls", "e_prev", "e_mit",
                  "p_res", "i_res", "score_res", "level_res", "colour_res", "p_tgt_f", "i_tgt_f", "score_tgt",
                  "appetite", "tolerance", "appetite_status", "priority", "n_actions", "reduction",
                  "ctrl_cost"]
    if r.empty:
        for col in cols_extra:
            r[col] = pd.Series(dtype=object)
        return r
    ctrl = analyse_controls(proj)
    app = proj["appetite"].set_index("category").to_dict(orient="index") if not proj["appetite"].empty else {}
    act = proj["actions"]
    act_count = act["risk_id"].astype(str).str.upper().value_counts().to_dict() if not act.empty else {}

    links: dict[str, list[dict]] = {}
    for crow in ctrl.to_dict(orient="records"):
        for rid in ids_list(crow.get("risk_ids")):
            links.setdefault(rid, []).append(crow)

    out = {k: [] for k in cols_extra}
    for row in r.to_dict(orient="records"):
        opp = row.get("type") == "opportunity"
        p, i = int(_n(row.get("p_inh"), 3)), int(_n(row.get("i_inh"), 3))
        s_inh = p * i
        lc = level_of(s_inh, opp)
        cl = links.get(str(row.get("id")).upper(), [])
        prev = [c["effectiveness"] * (0.5 if c.get("control_type") == "directive" else 1.0)
                for c in cl if c.get("control_type") in ("preventive", "directive")]
        mit = [c["effectiveness"] * (0.6 if c.get("control_type") == "detective" else 1.0)
               for c in cl if c.get("control_type") in ("detective", "corrective")]
        ep, em = (_combine(prev), _combine(mit)) if not opp else (0.0, 0.0)
        pr = _n(row.get("p_res_ovr"))
        ir = _n(row.get("i_res_ovr"))
        p_res = int(pr) if pr is not None else residual_level(p, ep)
        i_res = int(ir) if ir is not None else residual_level(i, em)
        s_res = p_res * i_res
        lr = level_of(s_res, opp)
        pt = _n(row.get("p_tgt"))
        it = _n(row.get("i_tgt"))
        pt = int(pt) if pt is not None else p_res
        it = int(it) if it is not None else i_res
        a = app.get(row.get("category"), {"appetite": 9, "tolerance": 12})
        if opp:
            status = "opportunity"
        elif s_res <= a["appetite"]:
            status = "within"
        elif s_res <= a["tolerance"]:
            status = "tolerance"
        else:
            status = "outside"
        pri = s_res * VELOCITY_FACTOR.get(int(_n(row.get("velocity"), 3)), 1.0) * \
            PROXIMITY_FACTOR.get(row.get("proximity") or "medium", 1.0)
        out["score_inh"].append(s_inh)
        out["level_inh"].append(lc[1])
        out["colour_inh"].append(lc[2])
        out["n_controls"].append(len(cl))
        out["controls"].append(", ".join(c["id"] for c in cl))
        out["e_prev"].append(round(ep, 3))
        out["e_mit"].append(round(em, 3))
        out["p_res"].append(p_res)
        out["i_res"].append(i_res)
        out["score_res"].append(s_res)
        out["level_res"].append(lr[1])
        out["colour_res"].append(lr[2])
        out["p_tgt_f"].append(pt)
        out["i_tgt_f"].append(it)
        out["score_tgt"].append(pt * it)
        out["appetite"].append(a["appetite"])
        out["tolerance"].append(a["tolerance"])
        out["appetite_status"].append(status)
        out["priority"].append(round(pri, 1))
        out["n_actions"].append(int(act_count.get(str(row.get("id")).upper(), 0)))
        out["reduction"].append(round(1 - s_res / s_inh, 3) if s_inh else 0)
        out["ctrl_cost"].append(sum(float(_n(c.get("cost"), 0) or 0) / max(1, len(ids_list(c.get("risk_ids"))))
                                    for c in cl))
    for k, v in out.items():
        r[k] = v
    return r


APPETITE_LABELS = {
    "within": ("Dentro do apetite", "Within appetite", "#22c55e"),
    "tolerance": ("Acima do apetite (dentro da tolerância)", "Above appetite (within tolerance)", "#eab308"),
    "outside": ("Fora da tolerância", "Outside tolerance", "#ef4444"),
    "opportunity": ("Oportunidade", "Opportunity", "#3b82f6"),
}


def appetite_label(code: str) -> str:
    t = APPETITE_LABELS.get(code, ("—", "—", "#64748b"))
    return t[1] if lang() == "en" else t[0]


# ---------------------------------------------------------------- coverage
def coverage(proj: dict) -> dict:
    ra = analyse_risks(proj)
    ca = analyse_controls(proj)
    threats = ra[ra["type"] == "threat"] if not ra.empty else ra
    res = {
        "risks_no_controls": threats[threats["n_controls"] == 0] if not threats.empty else threats,
        "controls_orphan": ca[ca["orphan"]] if not ca.empty else ca,
        "controls_unknown_ids": ca[ca["unknown_ids"] != ""] if not ca.empty else ca,
        "controls_untested": ca[ca["conclusion"] == "not_tested"] if not ca.empty else ca,
        "controls_ineffective": ca[ca["conclusion"].isin(["ineffective", "partial"])] if not ca.empty else ca,
        "outside_no_action": threats[(threats["appetite_status"] == "outside") & (threats["n_actions"] == 0)]
        if not threats.empty else threats,
    }
    n_t = len(threats)
    res["coverage_pct"] = (1 - len(res["risks_no_controls"]) / n_t) if n_t else 0.0
    n_c = len(ca)
    res["mapped_pct"] = (1 - len(res["controls_orphan"]) / n_c) if n_c else 0.0
    res["tested_pct"] = (1 - len(res["controls_untested"]) / n_c) if n_c else 0.0
    res["chain_avg"] = float(ca["chain"].mean()) if n_c else 0.0
    return res


# ------------------------------------------------------------------- KRIs
def kri_status(row: dict) -> str:
    cur, amber, red = _n(row.get("current")), _n(row.get("amber")), _n(row.get("red"))
    if cur is None or amber is None or red is None:
        return "na"
    if row.get("direction") == "lower_worse":
        return "red" if cur <= red else ("amber" if cur <= amber else "green")
    return "red" if cur >= red else ("amber" if cur >= amber else "green")


def kri_trend(row: dict) -> str:
    cur, prev = _n(row.get("current")), _n(row.get("previous"))
    if cur is None or prev is None or cur == prev:
        return "stable"
    worse = cur > prev if row.get("direction") != "lower_worse" else cur < prev
    return "up" if worse else "down"


def analyse_kris(proj: dict) -> pd.DataFrame:
    k = proj["kris"].copy()
    if k.empty:
        k["rag"] = pd.Series(dtype=object)
        k["trend_calc"] = pd.Series(dtype=object)
        return k
    recs = k.to_dict(orient="records")
    k["rag"] = [kri_status(r) for r in recs]
    k["trend_calc"] = [kri_trend(r) for r in recs]
    return k


# ---------------------------------------------------------------- actions
def analyse_actions(proj: dict, today: dt.date | None = None) -> pd.DataFrame:
    a = proj["actions"].copy()
    today = today or dt.date.today()
    if a.empty:
        a["overdue"] = pd.Series(dtype=bool)
        return a
    od = []
    for r in a.to_dict(orient="records"):
        due = r.get("due")
        st = r.get("status")
        try:
            d = dt.date.fromisoformat(str(due)[:10]) if due else None
        except ValueError:
            d = None
        od.append(bool(d and d < today and st not in ("done", "cancelled")))
    a["overdue"] = od
    return a


# ------------------------------------------------------------------- FMEA
def analyse_fmea(proj: dict) -> pd.DataFrame:
    f = proj["fmea"].copy()
    if f.empty:
        f["rpn"] = pd.Series(dtype=int)
        f["ap"] = pd.Series(dtype=object)
        return f
    f["rpn"] = (f["s"].astype(int) * f["o"].astype(int) * f["d"].astype(int))
    ap = []
    for s, o, d in zip(f["s"], f["o"], f["d"]):
        # simplified AIAG-VDA Action Priority logic
        if s >= 9 and (o >= 4 or d >= 7):
            ap.append("H")
        elif s >= 7 and o >= 6:
            ap.append("H")
        elif s * o * d >= 200:
            ap.append("H")
        elif s * o * d >= 100 or (s >= 7 and d >= 5):
            ap.append("M")
        else:
            ap.append("L")
    f["ap"] = ap
    return f


# ---------------------------------------------------------------- summary
def kpis(proj: dict) -> dict:
    ra = analyse_risks(proj)
    cov = coverage(proj)
    acts = analyse_actions(proj)
    kr = analyse_kris(proj)
    thr = ra[ra["type"] == "threat"] if not ra.empty else ra
    return {
        "n_risks": int(len(ra)),
        "n_threats": int(len(thr)),
        "n_opps": int((ra["type"] == "opportunity").sum()) if not ra.empty else 0,
        "n_controls": int(len(proj["controls"])),
        "critical_inh": int((thr["score_inh"] >= 15).sum()) if not thr.empty else 0,
        "critical_res": int((thr["score_res"] >= 15).sum()) if not thr.empty else 0,
        "outside": int((thr["appetite_status"] == "outside").sum()) if not thr.empty else 0,
        "above_appetite": int(thr["appetite_status"].isin(["outside", "tolerance"]).sum()) if not thr.empty else 0,
        "avg_inh": float(thr["score_inh"].mean()) if not thr.empty else 0.0,
        "avg_res": float(thr["score_res"].mean()) if not thr.empty else 0.0,
        "reduction": float(1 - thr["score_res"].sum() / thr["score_inh"].sum()) if not thr.empty and thr["score_inh"].sum() else 0.0,
        "coverage": cov["coverage_pct"],
        "mapped": cov["mapped_pct"],
        "tested": cov["tested_pct"],
        "chain": cov["chain_avg"],
        "n_actions": int(len(acts)),
        "overdue": int(acts["overdue"].sum()) if not acts.empty else 0,
        "done": int((acts["status"] == "done").sum()) if not acts.empty else 0,
        "kri_red": int((kr["rag"] == "red").sum()) if not kr.empty else 0,
        "kri_amber": int((kr["rag"] == "amber").sum()) if not kr.empty else 0,
        "n_kris": int(len(kr)),
        "no_controls": int(len(cov["risks_no_controls"])),
        "orphans": int(len(cov["controls_orphan"])),
    }


def maturity_index(proj: dict) -> tuple[float, float]:
    m = proj["maturity"]
    if m.empty:
        return 0.0, 0.0
    return float(np.mean(m["current"])), float(np.mean(m["target"]))
