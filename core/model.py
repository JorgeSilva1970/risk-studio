"""Project data model: table schemas, defaults, coercion and (de)serialisation."""
from __future__ import annotations

import datetime as dt
import json
import math
import re

import pandas as pd

from core.catalogs import (CATALOGS, DEFAULT_APPETITE, DEFAULT_IMPACT_THRESHOLDS,
                           MATURITY_DIMENSIONS, code_from_any)

# kind: str | int | float | cat:<catalog> | date | ids
SCHEMAS: dict[str, list[tuple[str, str, object]]] = {
    "risks": [
        ("id", "str", ""), ("type", "cat:type", "threat"), ("category", "cat:category", "operational"),
        ("title", "str", ""), ("cause", "str", ""), ("event", "str", ""), ("effect", "str", ""),
        ("owner", "str", ""), ("objective", "str", ""),
        ("p_inh", "int", 3), ("i_inh", "int", 3), ("velocity", "int", 3), ("proximity", "cat:proximity", "medium"),
        ("p_res_ovr", "int", None), ("i_res_ovr", "int", None),
        ("p_tgt", "int", None), ("i_tgt", "int", None),
        ("strategy", "cat:strategy", "reduce"), ("status", "cat:status", "open"), ("trend", "cat:trend", "stable"),
        ("prob_pct", "float", None), ("imp_min", "float", None), ("imp_ml", "float", None), ("imp_max", "float", None),
        ("notes", "str", ""),
    ],
    "controls": [
        ("id", "str", ""), ("name", "str", ""), ("objective", "str", ""), ("description", "str", ""),
        ("risk_ids", "ids", ""), ("control_type", "cat:control_type", "preventive"),
        ("nature", "cat:nature", "manual"), ("frequency", "cat:frequency", "monthly"), ("line", "cat:line", "first"),
        ("owner", "str", ""), ("evidence", "str", ""),
        ("design_test", "cat:test", "not_tested"), ("operating_test", "cat:test", "not_tested"),
        ("test_date", "date", None), ("tester", "str", ""), ("cost", "float", None), ("notes", "str", ""),
    ],
    "actions": [
        ("id", "str", ""), ("risk_id", "str", ""), ("control_id", "str", ""), ("description", "str", ""),
        ("strategy", "cat:strategy", "reduce"), ("owner", "str", ""),
        ("start", "date", None), ("due", "date", None), ("cost", "float", None),
        ("status", "cat:action_status", "not_started"), ("progress", "int", 0),
    ],
    "kris": [
        ("id", "str", ""), ("risk_id", "str", ""), ("name", "str", ""), ("unit", "str", ""),
        ("direction", "cat:direction", "higher_worse"), ("amber", "float", None), ("red", "float", None),
        ("previous", "float", None), ("current", "float", None), ("frequency", "cat:frequency", "monthly"),
        ("owner", "str", ""),
    ],
    "fmea": [
        ("id", "str", ""), ("process", "str", ""), ("failure_mode", "str", ""), ("effect", "str", ""),
        ("cause", "str", ""), ("current_controls", "str", ""), ("s", "int", 5), ("o", "int", 5), ("d", "int", 5),
        ("action", "str", ""), ("owner", "str", ""),
    ],
    "fair": [
        ("id", "str", ""), ("scenario", "str", ""), ("asset", "str", ""), ("threat", "str", ""),
        ("tef_min", "float", 0.5), ("tef_ml", "float", 2.0), ("tef_max", "float", 6.0),
        ("vuln_min", "float", 0.05), ("vuln_ml", "float", 0.15), ("vuln_max", "float", 0.40),
        ("plm_min", "float", 20000.0), ("plm_ml", "float", 80000.0), ("plm_max", "float", 400000.0),
        ("slef", "float", 0.3),
        ("slm_min", "float", 10000.0), ("slm_ml", "float", 50000.0), ("slm_max", "float", 500000.0),
    ],
    "maturity": [("dim", "str", ""), ("current", "int", 2), ("target", "int", 4), ("evidence", "str", "")],
    "appetite": [("category", "cat:category", "operational"), ("appetite", "int", 9), ("tolerance", "int", 12)],
}

ID_PREFIX = {"risks": "R", "controls": "C", "actions": "A", "kris": "K", "fmea": "F", "fair": "S"}

TABLES = list(SCHEMAS)


def empty_df(table: str) -> pd.DataFrame:
    return pd.DataFrame({f: pd.Series(dtype="object") for f, _, _ in SCHEMAS[table]})


def default_meta() -> dict:
    return {
        "name": "Novo projeto de risco",
        "organisation": "",
        "industry": "other",
        "scope": "",
        "objectives": "",
        "assessor": "",
        "date": dt.date.today().isoformat(),
        "currency": "€",
        "impact_thresholds": list(DEFAULT_IMPACT_THRESHOLDS),
        "risk_capacity": 5_000_000.0,
        "appetite_statement": "",
        "ai_summary": "",
        "version": 1,
    }


def default_appetite() -> pd.DataFrame:
    return pd.DataFrame([{"category": c, "appetite": a, "tolerance": t} for c, (a, t) in DEFAULT_APPETITE.items()])


def default_maturity() -> pd.DataFrame:
    return pd.DataFrame([{"dim": d, "current": 2, "target": 4, "evidence": ""} for d, _, _ in MATURITY_DIMENSIONS])


def new_project() -> dict:
    p = {"meta": default_meta()}
    for t in TABLES:
        p[t] = empty_df(t)
    p["appetite"] = default_appetite()
    p["maturity"] = default_maturity()
    return p


# ------------------------------------------------------------ coercion
def _is_blank(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    if isinstance(v, (list, tuple)):
        return len(v) == 0
    try:
        if pd.isna(v):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(v, str) and v.strip() in ("", "nan", "None", "NaT")


def _to_num(v):
    if _is_blank(v):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("€", "").replace("%", "").replace(" ", "")
    # handle "1.234,56" and "1,234.56"
    if s.count(",") and s.count("."):
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif s.count(",") == 1:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _to_date(v):
    if _is_blank(v):
        return None
    if isinstance(v, dt.datetime):
        return v.date().isoformat()
    if isinstance(v, dt.date):
        return v.isoformat()
    s = str(v).strip()[:19]
    try:
        return dt.date.fromisoformat(s[:10]).isoformat()
    except ValueError:
        pass
    try:
        d = pd.to_datetime(s, dayfirst=True, errors="coerce")
        return None if pd.isna(d) else d.date().isoformat()
    except Exception:
        return None


def normalise_ids(v) -> str:
    if _is_blank(v):
        return ""
    if isinstance(v, (list, tuple)):
        parts = [str(x) for x in v]
    else:
        parts = re.split(r"[,;\s]+", str(v))
    out = []
    for p in parts:
        p = p.strip().upper()
        if p and p not in out:
            out.append(p)
    return ", ".join(out)


def ids_list(v) -> list[str]:
    s = normalise_ids(v)
    return [x for x in s.split(", ") if x] if s else []


def coerce_value(kind: str, v, default=None):
    if kind == "str":
        return default if _is_blank(v) else str(v).strip()
    if kind == "int":
        n = _to_num(v)
        return default if n is None else int(round(n))
    if kind == "float":
        n = _to_num(v)
        return default if n is None else float(n)
    if kind == "date":
        return _to_date(v)
    if kind == "ids":
        return normalise_ids(v)
    if kind.startswith("cat:"):
        return code_from_any(kind[4:], v, default)
    return v


def coerce_df(table: str, df: pd.DataFrame | None) -> pd.DataFrame:
    """Return a clean DataFrame with exactly the schema columns, coerced types."""
    schema = SCHEMAS[table]
    if df is None or len(df) == 0:
        return empty_df(table)
    df = df.copy()
    rows = []
    for rec in df.to_dict(orient="records"):
        row = {}
        for f, kind, default in schema:
            row[f] = coerce_value(kind, rec.get(f), default)
        # drop fully empty rows
        meaningful = [row[f] for f, k, _ in schema if f != "id" and k in ("str",) and row[f]]
        if table in ("maturity", "appetite") or meaningful or row.get("id"):
            rows.append(row)
    out = pd.DataFrame(rows, columns=[f for f, _, _ in schema])
    # clamp 1–5 scales
    for col in ("p_inh", "i_inh", "velocity", "p_res_ovr", "i_res_ovr", "p_tgt", "i_tgt", "current", "target"):
        if col in out:
            out[col] = out[col].apply(lambda x: None if x is None or pd.isna(x) else int(min(5, max(1, x))))
    for col in ("s", "o", "d"):
        if col in out:
            out[col] = out[col].apply(lambda x: 5 if x is None or pd.isna(x) else int(min(10, max(1, x))))
    if "progress" in out:
        out["progress"] = out["progress"].apply(lambda x: 0 if x is None or pd.isna(x) else int(min(100, max(0, x))))
    if table == "appetite":
        out["appetite"] = out["appetite"].apply(lambda x: int(min(25, max(1, x or 9))))
        out["tolerance"] = [int(max(a, min(25, t or a))) for a, t in zip(out["appetite"], out["tolerance"])]
        out = out.drop_duplicates("category", keep="last").reset_index(drop=True)
    return ensure_ids(table, out)


def ensure_ids(table: str, df: pd.DataFrame) -> pd.DataFrame:
    if table not in ID_PREFIX or df.empty:
        return df
    pfx = ID_PREFIX[table]
    df = df.copy()
    used = set()
    nums = []
    for v in df["id"]:
        m = re.match(rf"^{pfx}(\d+)$", str(v or "").upper())
        if m:
            nums.append(int(m.group(1)))
    nxt = (max(nums) if nums else 0) + 1
    new_ids = []
    for v in df["id"]:
        v = str(v or "").strip().upper()
        if not v or v in used:
            v = f"{pfx}{nxt:02d}"
            nxt += 1
        used.add(v)
        new_ids.append(v)
    df["id"] = new_ids
    return df


# -------------------------------------------------------- serialisation
def _clean(v):
    if isinstance(v, float) and math.isnan(v):
        return None
    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:
            pass
    if isinstance(v, (dt.date, dt.datetime, pd.Timestamp)):
        return v.isoformat()[:10]
    return v


def to_json(proj: dict) -> str:
    out = {"meta": proj["meta"]}
    for t in TABLES:
        df = proj.get(t)
        out[t] = [] if df is None else [{k: _clean(v) for k, v in r.items()} for r in df.to_dict(orient="records")]
    return json.dumps(out, ensure_ascii=False, default=str)


def from_json(s: str | dict) -> dict:
    data = json.loads(s) if isinstance(s, str) else s
    p = new_project()
    meta = default_meta()
    meta.update(data.get("meta") or {})
    p["meta"] = meta
    for t in TABLES:
        if t in data and data[t] is not None:
            p[t] = coerce_df(t, pd.DataFrame(data[t]))
    if p["appetite"].empty:
        p["appetite"] = default_appetite()
    else:  # make sure every category exists
        have = set(p["appetite"]["category"])
        extra = [{"category": c, "appetite": a, "tolerance": tt} for c, (a, tt) in DEFAULT_APPETITE.items() if c not in have]
        if extra:
            p["appetite"] = pd.concat([p["appetite"], pd.DataFrame(extra)], ignore_index=True)
    if p["maturity"].empty:
        p["maturity"] = default_maturity()
    return p


def catalog_codes(name: str) -> list[str]:
    return list(CATALOGS[name])
