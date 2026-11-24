"""Excel template (single upload point for every module), import and export.

Workbook sheets: LEIA-ME · Contexto · Apetite · Riscos · Controlos · Acoes · KRIs · FMEA · FAIR · Maturidade · Listas
Headers are bilingual-tolerant on import (PT or EN header, or internal code).
Categorical columns use drop-down data validation."""
from __future__ import annotations

import io

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from core.catalogs import CATALOGS, MATURITY_DIMENSIONS
from core.model import SCHEMAS, coerce_df, default_meta, ids_list, new_project

SHEETS = {  # table: (PT sheet, EN sheet)
    "risks": ("Riscos", "Risks"), "controls": ("Controlos", "Controls"), "actions": ("Acoes", "Actions"),
    "kris": ("KRIs", "KRIs"), "fmea": ("FMEA", "FMEA"), "fair": ("FAIR", "FAIR"),
    "maturity": ("Maturidade", "Maturity"), "appetite": ("Apetite", "Appetite"),
}
META_FIELDS = [
    ("name", "Nome do projeto", "Project name"), ("organisation", "Organização", "Organisation"),
    ("industry", "Indústria (código)", "Industry (code)"), ("scope", "Âmbito", "Scope"),
    ("objectives", "Objetivos", "Objectives"), ("assessor", "Avaliador", "Assessor"), ("date", "Data", "Date"),
    ("currency", "Moeda", "Currency"), ("risk_capacity", "Capacidade de risco", "Risk capacity"),
    ("appetite_statement", "Declaração de apetite", "Appetite statement"),
    ("impact_thresholds", "Limiares de impacto (5 valores separados por ;)", "Impact thresholds (5 values separated by ;)"),
]

NAVY = "0B1B2B"
TEAL = "2DD4BF"
HDR_FILL = PatternFill("solid", fgColor=NAVY)
HDR_FONT = Font(bold=True, color="FFFFFF")
REQ_FILL = PatternFill("solid", fgColor="0E7490")
THIN = Side(style="thin", color="CBD5E1")


def _hdr(field: str, lang: str, table: str | None = None) -> str:
    from core.ui import FIELD_LABELS, TABLE_LABELS
    t = TABLE_LABELS.get((table, field)) or FIELD_LABELS.get(field, (field, field))
    return t[1] if lang == "en" else t[0]


def _cat_label(cat: str, code, lang: str) -> str:
    if code is None or (isinstance(code, float) and code != code):
        return ""
    t = CATALOGS[cat].get(str(code))
    return (t[1] if lang == "en" else t[0]) if t else str(code)


def build_workbook(proj: dict | None = None, lang: str = "pt") -> bytes:
    """Blank template (proj=None) or full export of a project."""
    p = proj or new_project()
    wb = Workbook()
    ws = wb.active
    ws.title = "LEIA-ME" if lang == "pt" else "README"
    _readme(ws, lang)

    # Context
    wc = wb.create_sheet("Contexto" if lang == "pt" else "Context")
    wc.append(["Campo" if lang == "pt" else "Field", "Valor" if lang == "pt" else "Value", "código"])
    m = p["meta"] if proj else default_meta()
    for code, pt, en in META_FIELDS:
        v = m.get(code, "")
        if code == "impact_thresholds":
            v = "; ".join(str(int(x)) for x in (v or []))
        wc.append([en if lang == "en" else pt, v, code])
    _style_header(wc, 3)
    wc.column_dimensions["A"].width = 44
    wc.column_dimensions["B"].width = 90
    wc.column_dimensions["C"].width = 18

    # Lists sheet for validations
    wl = wb.create_sheet("Listas" if lang == "pt" else "Lists")
    list_ranges = {}
    for j, (cat, items) in enumerate(CATALOGS.items(), start=1):
        col = get_column_letter(j)
        wl.cell(1, j, cat).font = Font(bold=True)
        for i, (code, (pt, en)) in enumerate(items.items(), start=2):
            wl.cell(i, j, en if lang == "en" else pt)
        list_ranges[cat] = f"'{wl.title}'!${col}$2:${col}${len(items) + 1}"

    for table in ["appetite", "risks", "controls", "actions", "kris", "fmea", "fair", "maturity"]:
        sh = wb.create_sheet(SHEETS[table][1 if lang == "en" else 0])
        schema = SCHEMAS[table]
        sh.append([_hdr(f, lang, table) for f, _, _ in schema])
        sh.append([f for f, _, _ in schema])  # hidden technical row with codes
        df = p.get(table)
        if table == "maturity" and (df is None or df.empty):
            from core.model import default_maturity
            df = default_maturity()
        if df is not None and not df.empty:
            for rec in df.to_dict(orient="records"):
                row = []
                for f, kind, _ in schema:
                    v = rec.get(f)
                    if kind.startswith("cat:"):
                        v = _cat_label(kind[4:], v, lang)
                    elif table == "maturity" and f == "dim":
                        v = next(((en if lang == "en" else pt) for c, pt, en in MATURITY_DIMENSIONS if c == v), v)
                    if v is not None and isinstance(v, float) and v != v:
                        v = None
                    row.append(v)
                sh.append(row)
        _style_header(sh, len(schema))
        sh.row_dimensions[2].hidden = True
        sh.freeze_panes = "B3"
        for j, (f, kind, _) in enumerate(schema, start=1):
            col = get_column_letter(j)
            wide = f in ("title", "cause", "event", "effect", "description", "name", "objective", "failure_mode", "scenario",
                         "evidence", "action", "dim")
            sh.column_dimensions[col].width = 42 if wide else 16
            if kind.startswith("cat:"):
                dv = DataValidation(type="list", formula1=f"={list_ranges[kind[4:]]}", allow_blank=True)
                dv.error = "Valor fora da lista" if lang == "pt" else "Value not in list"
                sh.add_data_validation(dv)
                dv.add(f"{col}3:{col}500")
            elif kind == "int" and f not in ("progress",) and table not in ("appetite",):
                hi = 10 if f in ("s", "o", "d") else 5
                dv = DataValidation(type="whole", operator="between", formula1="1", formula2=str(hi), allow_blank=True)
                sh.add_data_validation(dv)
                dv.add(f"{col}3:{col}500")
            elif kind == "date":
                for r in range(3, 501):
                    sh.cell(r, j).number_format = "DD/MM/YYYY"
            elif kind == "float" and f.startswith(("imp_", "plm", "slm")) or f == "cost":
                for r in range(3, 501):
                    sh.cell(r, j).number_format = "#,##0"
    # data dictionary (Gestão Studio convention: rules + dictionary + example values)
    wd = wb.create_sheet("Dicionario" if lang == "pt" else "Dictionary", 1)
    wd.append(["Folha" if lang == "pt" else "Sheet", "Campo" if lang == "pt" else "Field", "Código", "Tipo" if lang == "pt" else "Type",
               "Valores aceites / regra" if lang == "pt" else "Accepted values / rule", "Ajuda" if lang == "pt" else "Help"])
    from core.ui import FIELD_HELP
    for table in ["appetite", "risks", "controls", "actions", "kris", "fmea", "fair", "maturity"]:
        for f, kind, _ in SCHEMAS[table]:
            if kind.startswith("cat:"):
                rule = " | ".join((en if lang == "en" else pt) for pt, en in CATALOGS[kind[4:]].values())
                typ = "lista" if lang == "pt" else "list"
            elif kind == "int":
                rule = "1–10" if f in ("s", "o", "d") else ("0–100" if f == "progress" else ("1–25" if table == "appetite" else "1–5"))
                typ = "inteiro" if lang == "pt" else "integer"
            elif kind == "float":
                rule = "0–1" if f in ("vuln_min", "vuln_ml", "vuln_max", "slef") else ("0–100" if f == "prob_pct" else (">= 0"))
                typ = "número" if lang == "pt" else "number"
            elif kind == "date":
                rule, typ = "DD/MM/AAAA", "data" if lang == "pt" else "date"
            elif kind == "ids":
                rule, typ = "R01, R03", "IDs"
            else:
                rule, typ = ("auto (R01, C01…)" if f == "id" else ""), "texto" if lang == "pt" else "text"
            h = FIELD_HELP.get(f)
            wd.append([SHEETS[table][1 if lang == "en" else 0], _hdr(f, lang, table), f, typ, rule, (h[1] if lang == "en" else h[0]) if h else ""])
    _style_header(wd, 6)
    for col, w in zip("ABCDEF", (14, 34, 16, 10, 70, 70)):
        wd.column_dimensions[col].width = w
    wd.freeze_panes = "A2"
    wb.move_sheet(wl.title, offset=len(wb.sheetnames))
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def _style_header(ws, ncols: int):
    for j in range(1, ncols + 1):
        c = ws.cell(1, j)
        c.fill = HDR_FILL
        c.font = HDR_FONT
        c.alignment = Alignment(wrap_text=True, vertical="center")
        c.border = Border(bottom=THIN)
    ws.row_dimensions[1].height = 34


def _readme(ws, lang: str):
    pt = [
        "RISK STUDIO — Template único de carregamento",
        "",
        "Como usar:",
        "1. Preencha as folhas que precisar (Contexto, Apetite, Riscos, Controlos, Acoes, KRIs, FMEA, FAIR, Maturidade). Folhas vazias são ignoradas.",
        "2. Não altere a 1.ª linha (cabeçalhos) nem a 2.ª linha oculta (códigos técnicos).",
        "3. Use as listas pendentes nas colunas categóricas. Escalas P e I: 1 a 5. FMEA S/O/D: 1 a 10.",
        "4. IDs (R01, C01, A01, K01…) podem ficar vazios: são gerados automaticamente.",
        "5. Na folha Controlos, a coluna 'Riscos ligados' liga cada controlo aos riscos (ex.: R01, R03). Cada controlo deve mapear para ≥1 risco.",
        "6. Causas e consequências múltiplas: separe por ';' — alimentam automaticamente o diagrama Bow-Tie.",
        "7. Impacto mín./+provável/máx. (€) e Prob. % são opcionais: se vazios, o Monte Carlo usa as escalas.",
        "8. Carregue o ficheiro em 'Dados & Templates' → 'Carregar Excel'. Pode substituir ou acrescentar ao projeto atual.",
        "",
        "Metodologia: ISO 31000:2018 · ISO 31010:2019 · COSO ERM 2017 · COSO IC 2013 · Modelo das 3 Linhas (IIA 2020) · FAIR · Hillson (ATOM).",
    ]
    en = [
        "RISK STUDIO — Single upload template",
        "",
        "How to use:",
        "1. Fill the sheets you need (Context, Appetite, Risks, Controls, Actions, KRIs, FMEA, FAIR, Maturity). Empty sheets are ignored.",
        "2. Do not change row 1 (headers) or the hidden row 2 (technical codes).",
        "3. Use the drop-downs in categorical columns. P and I scales: 1 to 5. FMEA S/O/D: 1 to 10.",
        "4. IDs (R01, C01, A01, K01…) may be left blank: they are generated automatically.",
        "5. In the Controls sheet, 'Linked risks' links each control to risks (e.g. R01, R03). Every control should map to ≥1 risk.",
        "6. Multiple causes and consequences: separate with ';' — they feed the Bow-Tie diagram automatically.",
        "7. Impact min/most likely/max and Prob. % are optional: if blank, Monte Carlo uses the scales.",
        "8. Upload the file in 'Data & Templates' → 'Upload Excel'. You can replace or append to the current project.",
        "",
        "Methodology: ISO 31000:2018 · ISO 31010:2019 · COSO ERM 2017 · COSO IC 2013 · Three Lines Model (IIA 2020) · FAIR · Hillson (ATOM).",
    ]
    for line in (en if lang == "en" else pt):
        ws.append([line])
    ws["A1"].font = Font(bold=True, size=16, color=NAVY)
    ws.column_dimensions["A"].width = 150


# ------------------------------------------------------------------ import
def _header_map(table: str) -> dict[str, str]:
    from core.ui import FIELD_LABELS, TABLE_LABELS
    mp = {}
    for f, _, _ in SCHEMAS[table]:
        mp[f.lower()] = f
        for pt, en in (FIELD_LABELS.get(f, (f, f)), TABLE_LABELS.get((table, f), (f, f))):
            mp[pt.lower().strip()] = f
            mp[en.lower().strip()] = f
    return mp


def _find_sheet(wb, table: str):
    names = {n.lower(): n for n in wb.sheetnames}
    for cand in (SHEETS[table][0], SHEETS[table][1], table, "ações" if table == "actions" else ""):
        if cand and cand.lower() in names:
            return wb[names[cand.lower()]]
    return None


def read_workbook(data: bytes) -> tuple[dict, list[str]]:
    """Parse an uploaded workbook. Returns (partial project dict, messages)."""
    wb = load_workbook(io.BytesIO(data), data_only=True)
    out: dict = {}
    msgs: list[str] = []
    # context
    ctx = None
    for n in wb.sheetnames:
        if n.lower() in ("contexto", "context"):
            ctx = wb[n]
    if ctx is not None:
        meta = {}
        labels = {pt.lower(): code for code, pt, en in META_FIELDS} | {en.lower(): code for code, pt, en in META_FIELDS}
        for row in ctx.iter_rows(min_row=2, values_only=True):
            if not row or row[0] is None:
                continue
            code = (row[2] if len(row) > 2 and row[2] else None) or labels.get(str(row[0]).strip().lower())
            if code:
                meta[code] = row[1]
        if "impact_thresholds" in meta and meta["impact_thresholds"]:
            try:
                vals = [float(str(x).strip().replace(" ", "").replace(",", ".")) for x in str(meta["impact_thresholds"]).split(";") if str(x).strip()]
                meta["impact_thresholds"] = vals[:5] if len(vals) >= 5 else default_meta()["impact_thresholds"]
            except ValueError:
                meta["impact_thresholds"] = default_meta()["impact_thresholds"]
        if "risk_capacity" in meta:
            try:
                meta["risk_capacity"] = float(meta["risk_capacity"] or 0)
            except (TypeError, ValueError):
                meta.pop("risk_capacity")
        if "industry" in meta:
            from core.catalogs import INDUSTRIES
            v = str(meta["industry"] or "").strip()
            meta["industry"] = next((k for k, (pt, en) in INDUSTRIES.items() if v.lower() in (k, pt.lower(), en.lower())), "other")
        meta = {k: v for k, v in meta.items() if v not in (None, "")}
        if meta:
            out["meta"] = meta
            msgs.append(f"Contexto: {len(meta)} campos")
    for table in SHEETS:
        sh = _find_sheet(wb, table)
        if sh is None:
            continue
        rows = list(sh.iter_rows(values_only=True))
        if not rows:
            continue
        hmap = _header_map(table)
        header = [hmap.get(str(h).strip().lower()) if h is not None else None for h in rows[0]]
        start = 1
        # technical row with codes (row 2) takes precedence when present
        if len(rows) > 1 and sum(1 for v in rows[1] if v and str(v) in hmap.values()) >= max(1, len(SCHEMAS[table]) // 2):
            header = [str(v) if v and str(v) in hmap.values() else None for v in rows[1]]
            start = 2
        recs = []
        for r in rows[start:]:
            if r is None or all(v is None or str(v).strip() == "" for v in r):
                continue
            recs.append({h: v for h, v in zip(header, r) if h})
        if not recs:
            continue
        df = pd.DataFrame(recs)
        if table == "maturity" and "dim" in df:
            lab2code = {pt.lower(): c for c, pt, en in MATURITY_DIMENSIONS} | {en.lower(): c for c, pt, en in MATURITY_DIMENSIONS}
            df["dim"] = df["dim"].map(lambda v: lab2code.get(str(v).strip().lower(), v))
        out[table] = coerce_df(table, df)
        msgs.append(f"{SHEETS[table][0]}: {len(out[table])}")
    return out, msgs


def reid(parsed: dict, proj: dict) -> dict:
    """Give imported rows IDs that don't collide with the project and rewrite every cross-reference
    (controls.risk_ids, actions.risk_id/control_id, kris.risk_id) so links survive an append."""
    import re as _re

    from core.model import ID_PREFIX
    out = {k: (v.copy() if hasattr(v, "copy") else v) for k, v in parsed.items()}
    maps: dict[str, dict[str, str]] = {}
    for table, pfx in ID_PREFIX.items():
        if table not in out or out[table] is None or out[table].empty or proj.get(table) is None:
            continue
        nums = [int(m.group(1)) for v in proj[table]["id"] for m in [_re.match(rf"^{pfx}(\d+)$", str(v))] if m] if not proj[table].empty else []
        nxt = (max(nums) if nums else 0) + 1
        mp = {}
        for old_id in out[table]["id"]:
            mp[str(old_id)] = f"{pfx}{nxt:02d}"
            nxt += 1
        out[table] = out[table].assign(id=[mp[str(i)] for i in out[table]["id"]])
        maps[table] = mp
    rm, cm = maps.get("risks", {}), maps.get("controls", {})
    if "controls" in out and not out["controls"].empty and rm:
        out["controls"]["risk_ids"] = out["controls"]["risk_ids"].map(lambda s_: ", ".join(rm.get(x, x) for x in ids_list(s_)))
    for t, col, mp in (("actions", "risk_id", rm), ("actions", "control_id", cm), ("kris", "risk_id", rm)):
        if t in out and not out[t].empty and mp:
            out[t][col] = out[t][col].map(lambda v, m_=mp: m_.get(str(v), v) if v else v)
    return out


def merge_into(proj: dict, parsed: dict, mode: str = "replace") -> dict:
    """mode: 'replace' (tables present in the file replace the project's) or 'append' (IDs re-numbered, links preserved)."""
    p = {k: (v.copy() if hasattr(v, "copy") else v) for k, v in proj.items()}
    if "meta" in parsed:
        p["meta"] = {**p["meta"], **parsed["meta"]}
    if mode == "append":
        parsed = reid(parsed, proj)
    for table in SHEETS:
        if table not in parsed:
            continue
        new = parsed[table]
        if mode == "append" and table not in ("appetite", "maturity") and not p[table].empty:
            p[table] = coerce_df(table, pd.concat([p[table], new], ignore_index=True))
        elif table in ("appetite", "maturity") and not p[table].empty:
            key = "category" if table == "appetite" else "dim"
            base = p[table].set_index(key)
            upd = new.set_index(key)
            base.update(upd)
            extra = upd[~upd.index.isin(base.index)]
            p[table] = coerce_df(table, pd.concat([base, extra]).reset_index())
        else:
            p[table] = new
    return p
