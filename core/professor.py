"""Course formats (same ones used by PM Studio):

* the professor's **RiskRegister_Template.xlsx** (sheet "RiskRegister", 4×4 scale, rows 11+),
* PM Studio **Modelo 8 — Matriz de gestão de riscos** (sheet "1 Riscos", headers "Label [field]"),
* a whole **PM Studio project (JSON)** — its `risks` table.

The 4×4 scale is mapped to the 5×5 scale **by level name** (no level is invented):
likelihood Unlikely→2 Improvável, Possible→3 Possível, Likely→4 Provável, Almost certain→5 Quase certa;
impact Minor→2 Menor, Moderate→3 Moderado, Major→4 Maior, Severe→5 Catastrófico.
The reverse mapping folds level 1 into the lowest 4×4 level.

Mitigation follows the ControlKit logic: *existing mitigation* becomes a **control** linked to the risk,
*proposed mitigation* becomes a **treatment action**, a PM Studio *corrective action + trigger* becomes a
**corrective control** ("if and when …")."""
from __future__ import annotations

import io
import json
import os
import re

import pandas as pd
from openpyxl import load_workbook

from core.catalogs import code_from_any
from core.model import coerce_df, ids_list

TPL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "RiskRegister_Template.xlsx")
EXAMPLE_DESC = "Political distortion of the project's findings"

LIK4 = {4: "Almost certain", 3: "Likely", 2: "Possible", 1: "Unlikely"}
IMP4 = {4: "Severe", 3: "Major", 2: "Moderate", 1: "Minor"}
LIK4_PT = {"quase certo": 4, "quase certa": 4, "provável": 3, "possível": 2, "improvável": 1}
IMP4_PT = {"severo": 4, "grave": 3, "moderado": 2, "menor": 1}

TYPE_TO_CAT = {
    "project/programme delivery": "project", "human resources": "people", "communication and reputation": "reputational",
    "financial": "financial", "it": "cyber", "safety, security and logistics": "health_safety", "political": "strategic",
    "other (rare)": "operational",
    # PT labels used in PM Studio lists
    "execução do projeto/programa": "project", "recursos humanos": "people", "comunicação e reputação": "reputational",
    "financeiro": "financial", "ti": "cyber", "segurança e logística": "health_safety", "político": "strategic", "outro (raro)": "operational",
}
CAT_TO_TYPE = {
    "project": "Project/programme delivery", "operational": "Project/programme delivery", "people": "Human resources",
    "reputational": "Communication and reputation", "financial": "Financial", "cyber": "IT",
    "health_safety": "Safety, security and logistics", "supply_chain": "Safety, security and logistics",
    "strategic": "Political", "compliance": "Other (rare)", "esg": "Other (rare)",
}


def lik4_to5(v) -> int:
    if isinstance(v, str):
        s = v.strip().lower()
        n = {x.lower(): k for k, x in LIK4.items()}.get(s) or LIK4_PT.get(s)
        if n is None:
            try:
                n = int(float(s))
            except ValueError:
                n = 2
    else:
        n = int(v or 2)
    return min(5, max(1, n + 1))


def imp4_to5(v) -> int:
    if isinstance(v, str):
        s = v.strip().lower()
        n = {x.lower(): k for k, x in IMP4.items()}.get(s) or IMP4_PT.get(s)
        if n is None:
            try:
                n = int(float(s))
            except ValueError:
                n = 2
    else:
        n = int(v or 2)
    return min(5, max(1, n + 1))


def to4(v5) -> int:
    return max(1, min(4, int(v5 or 1) - 1))


def _s(v) -> str:
    return "" if v is None or (isinstance(v, float) and v != v) else str(v).strip()


# ------------------------------------------------------------------ generic PM-style rows → project tables
def from_pm_rows(rows: list[dict], source: str) -> dict:
    """rows use PM Studio field names: type, description, likelihood, impact, target_exposure, existing_mitigation,
    proposed_mitigation, risk_manager, risk_owner, review_by, review, strategy, contingency, corrective_action,
    trigger, preventive_activity, level_affected, id."""
    risks, controls, actions = [], [], []
    for i, r in enumerate(rows, 1):
        desc = _s(r.get("description"))
        if not desc or desc == EXAMPLE_DESC:
            continue
        rid = f"R{len(risks) + 1:02d}"
        notes = [f"Fonte: {source}" + (f" ({_s(r.get('id'))})" if _s(r.get("id")) else "")]
        if _s(r.get("target_exposure")):
            notes.append(f"Exposição-alvo 4×4: {_s(r.get('target_exposure'))}")
        if _s(r.get("review_by")):
            notes.append(f"Rever até: {_s(r.get('review_by'))}")
        if _s(r.get("review")):
            notes.append(f"Revisão: {_s(r.get('review'))}")
        if _s(r.get("level_affected")):
            notes.append(f"Nível afetado (logframe): {_s(r.get('level_affected'))}")
        p5, i5 = lik4_to5(r.get("likelihood")), imp4_to5(r.get("impact"))
        strat = code_from_any("strategy", _s(r.get("strategy")), "reduce")
        risks.append({
            "id": rid, "type": "opportunity" if strat in ("exploit", "enhance", "share") else "threat",
            "category": TYPE_TO_CAT.get(_s(r.get("type")).lower(), "operational"), "title": desc[:140], "event": desc,
            "owner": _s(r.get("risk_owner")) or _s(r.get("risk_manager")), "p_inh": p5, "i_inh": i5, "velocity": 3,
            "proximity": "medium", "strategy": strat, "status": "open", "trend": "stable", "notes": " · ".join(notes),
        })
        if _s(r.get("existing_mitigation")):
            controls.append({"name": _s(r.get("existing_mitigation"))[:120], "description": _s(r.get("existing_mitigation")),
                             "objective": f"Reduzir a probabilidade de: {desc[:80]}", "risk_ids": rid, "control_type": "preventive",
                             "nature": "manual", "frequency": "monthly", "line": "first", "owner": _s(r.get("risk_manager")),
                             "design_test": "not_tested", "operating_test": "not_tested", "notes": f"Mitigação existente ({source})"})
        if _s(r.get("corrective_action")):
            trig = _s(r.get("trigger"))
            controls.append({"name": _s(r.get("corrective_action"))[:120],
                             "description": _s(r.get("corrective_action")) + (f" — se e quando {trig}" if trig else ""),
                             "objective": f"Limitar a consequência de: {desc[:80]}", "risk_ids": rid, "control_type": "corrective",
                             "nature": "manual", "frequency": "adhoc", "line": "first", "owner": _s(r.get("risk_manager")),
                             "design_test": "not_tested", "operating_test": "not_tested", "notes": f"Ação corretiva ({source})"})
        prop = _s(r.get("proposed_mitigation")) or _s(r.get("preventive_activity"))
        if prop:
            cost = r.get("contingency")
            try:
                cost = float(cost) if cost not in (None, "") else None
            except (TypeError, ValueError):
                cost = None
            actions.append({"risk_id": rid, "description": prop, "strategy": strat if strat != "accept" else "reduce",
                            "owner": _s(r.get("risk_manager")) or _s(r.get("risk_owner")), "cost": cost, "status": "not_started", "progress": 0})
    return {"risks": coerce_df("risks", pd.DataFrame(risks)), "controls": coerce_df("controls", pd.DataFrame(controls)),
            "actions": coerce_df("actions", pd.DataFrame(actions))}


# ------------------------------------------------------------------ readers
def is_risk_register(wb) -> bool:
    return any(n.lower() == "riskregister" for n in wb.sheetnames)


def read_risk_register(wb) -> list[dict]:
    ws = wb[next(n for n in wb.sheetnames if n.lower() == "riskregister")]
    rows = []
    for r in range(11, 263):
        desc = ws[f"C{r}"].value
        if not desc:
            continue
        rows.append({"type": ws[f"B{r}"].value, "description": desc, "likelihood": ws[f"D{r}"].value, "impact": ws[f"G{r}"].value,
                     "target_exposure": ws[f"K{r}"].value, "existing_mitigation": ws[f"L{r}"].value, "proposed_mitigation": ws[f"M{r}"].value,
                     "risk_manager": ws[f"N{r}"].value, "risk_owner": ws[f"O{r}"].value, "review_by": ws[f"P{r}"].value, "review": ws[f"Q{r}"].value})
    return rows


def read_bracket_sheet(wb) -> list[dict]:
    """PM Studio sheets whose header cells read 'Label [field]' (Modelo 8 '1 Riscos', extended workbook 'Riscos')."""
    out = []
    for ws in wb.worksheets:
        marker = " ".join(str(ws[c].value or "") for c in ("A1", "A2"))
        is_risks = "[table:risks]" in marker or ws.title.lower() in ("1 riscos", "riscos", "risks")
        if not is_risks:
            continue
        hdr = None
        for r in range(1, 12):
            vals = [str(c.value or "") for c in ws[r]]
            if sum(1 for v in vals if re.search(r"\[[a-z_]+\]$", v)) >= 2:
                hdr = r
                break
        if not hdr:
            continue
        fields = {}
        for c in ws[hdr]:
            m = re.search(r"\[([a-z_]+)\]$", str(c.value or ""))
            if m:
                fields[c.column] = m.group(1)
        if "description" not in fields.values() or "likelihood" not in fields.values():
            continue
        for r in range(hdr + 1, ws.max_row + 1):
            rec = {f: ws.cell(r, col).value for col, f in fields.items()}
            if any(v not in (None, "") for v in rec.values()):
                out.append(rec)
    return out


def detect_pm_project(data: dict) -> bool:
    rs = data.get("risks")
    return isinstance(rs, list) and isinstance(data.get("meta"), dict) and (not rs or "likelihood" in rs[0] or "description" in rs[0]) \
        and not (rs and "p_inh" in rs[0])


def read_pm_project(data: dict) -> tuple[dict, dict]:
    parsed = from_pm_rows(data.get("risks", []), "PM Studio")
    m = data.get("meta", {})
    meta = {"name": f"Riscos — {m.get('name', 'Projeto PM Studio')}", "scope": m.get("description", "") or m.get("name", ""),
            "objectives": "; ".join(str(o.get("text", "")) for o in data.get("objectives", [])[:6] if isinstance(o, dict))}
    return parsed, meta


def parse_upload(name: str, content: bytes) -> tuple[dict | None, dict, str]:
    """Return (tables or None, meta, kind) for a course-format file, or (None, {}, '') if not recognised."""
    n = name.lower()
    if n.endswith(".json"):
        try:
            data = json.loads(content.decode("utf-8"))
        except Exception:
            return None, {}, ""
        if isinstance(data, dict) and detect_pm_project(data):
            t, meta = read_pm_project(data)
            return t, meta, "pm_project"
        return None, {}, ""
    if n.endswith(".xlsx"):
        wb = load_workbook(io.BytesIO(content), data_only=True)
        if is_risk_register(wb):
            return from_pm_rows(read_risk_register(wb), "RiskRegister"), {}, "risk_register"
        if any("[table:risks]" in " ".join(str(ws[c].value or "") for c in ("A1", "A2")) for ws in wb.worksheets) or any(
                ws.title.lower() == "1 riscos" for ws in wb.worksheets):
            return from_pm_rows(read_bracket_sheet(wb), "PM Studio — Modelo 8"), {}, "pm_model8"
    return None, {}, ""


# ------------------------------------------------------------------ writer (original format)
def export_risk_register(proj: dict) -> tuple[bytes, list[str]]:
    """Fill the professor's RiskRegister_Template in its ORIGINAL format (rows 11–18, drop-downs and merges untouched).
    Like PM Studio, only the 8 highest-priority threats fit; the rest go to the Risk Studio workbook. Returns (bytes, warnings)."""
    from core import scoring
    from core.i18n import L
    wb = load_workbook(TPL)
    ws = wb["RiskRegister"]
    ra = scoring.analyse_risks(proj)
    ra = ra[ra["type"] == "threat"].sort_values("priority", ascending=False) if not ra.empty else ra
    ca = proj["controls"]
    acts = proj["actions"]
    first, last = 11, 18
    cap = last - first + 1
    warn = []
    if len(ra) > cap:
        warn.append(L(f"O modelo do professor tem {cap} linhas: seguem os {cap} riscos mais prioritários; os restantes {len(ra) - cap} estão no Excel completo do Risk Studio.",
                      f"The professor's template has {cap} rows: the {cap} highest-priority risks are included; the other {len(ra) - cap} are in the full Risk Studio workbook."))
    for r in range(first, last + 1):
        for c in "BCDGJKLMNOPQ":
            ws[f"{c}{r}"].value = None
    for k, x in enumerate(ra.head(cap).to_dict(orient="records")):
        r = first + k
        rid = x["id"]
        lc = ca[ca["risk_ids"].apply(lambda s: rid in ids_list(s))] if not ca.empty else ca
        la = acts[acts["risk_id"] == rid] if not acts.empty else acts
        ws[f"B{r}"] = CAT_TO_TYPE.get(x["category"], "Other (rare)")
        ws[f"C{r}"] = x["title"] if not x.get("event") or x["event"] == x["title"] else f"{x['title']} — {x['event']}"
        ws[f"D{r}"] = LIK4[to4(x["p_res"])]
        ws[f"G{r}"] = IMP4[to4(x["i_res"])]
        ws[f"J{r}"] = f'=IFERROR((5-MATCH(D{r},$D$264:$D$267,0))*(5-MATCH(G{r},$G$264:$G$267,0)),"")'
        ws[f"K{r}"] = to4(x["p_tgt_f"]) * to4(x["i_tgt_f"])
        ws[f"L{r}"] = "; ".join(f"{c['id']} {c['name']}" for c in lc.to_dict(orient="records")) if not lc.empty else ""
        ws[f"M{r}"] = "; ".join(f"{a['id']} {a['description']}" for a in la.to_dict(orient="records")) if not la.empty else ""
        ws[f"N{r}"] = "; ".join(sorted({str(a["owner"]) for a in la.to_dict(orient="records") if a.get("owner")})) if not la.empty else ""
        ws[f"O{r}"] = x.get("owner") or ""
        due = [str(a["due"]) for a in la.to_dict(orient="records") if a.get("due")] if not la.empty else []
        ws[f"P{r}"] = min(due) if due else ""
        ws[f"Q{r}"] = (x.get("notes") or "")[:250]
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue(), warn
