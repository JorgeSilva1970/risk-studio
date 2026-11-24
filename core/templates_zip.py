"""Blank templates ZIP — same convention as Gestão Studio:

Templates_Risk_Studio/
  00_INDICE.xlsx                         (index of every template)
  0_Modelos_do_professor/RiskRegister_Template.xlsx
  1_Contexto_e_Apetite/01_contexto_apetite.xlsx
  2_Identificacao_e_Avaliacao/02_registo_riscos.xlsx, 03_fmea.xlsx
  3_Controlo_e_Tratamento/04_controlos_rcm.xlsx, 05_plano_acoes.xlsx, 06_kris.xlsx
  4_Quantificacao/07_fair.xlsx
  5_Maturidade/08_maturidade.xlsx

Each workbook: sheet «Instruções» (what it is, author/origin, reference, when to use, how to read, HOW TO FILL steps,
DATA DICTIONARY and FILLED EXAMPLE), sheet «campos» (general parameters, yellow «valor» cells) when the module has them,
and one data sheet per table named «modulo.tabela» (row 1 = headers; golden headers have a drop-down list; hover a header
to see its rule). Rows from 2; rows whose main column is empty are ignored."""
from __future__ import annotations

import io
import os
import zipfile

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from core.catalogs import CATALOGS, IMPACT_SCALE, INDUSTRIES, MATURITY_DIMENSIONS
from core.model import SCHEMAS, coerce_df

BLUE = "1D5AA6"
GOLD = "B8860B"
YELLOW = "FFF8DC"
ROOT = "Templates_Risk_Studio"
N_ROWS = 300

# (folder, file stem, icon, (PT name, EN name), help key, [(table, sheet name)], has_campos, main field per table, when-to-use PT/EN)
MODULES = [
    ("1_Contexto_e_Apetite", "01_contexto_apetite", "🧭", ("Contexto, critérios e apetite ao risco", "Context, criteria and risk appetite"), "context",
     [("appetite", "contexto.apetite")], True, {"appetite": "category"},
     ("No início de cada ciclo de gestão de risco e sempre que mudem os objetivos, a estratégia ou a declaração de apetite.",
      "At the start of every risk cycle and whenever objectives, strategy or the appetite statement change.")),
    ("2_Identificacao_e_Avaliacao", "02_registo_riscos", "📋", ("Registo de riscos (ameaças e oportunidades)", "Risk register (threats and opportunities)"), "register",
     [("risks", "registo.riscos")], False, {"risks": "title"},
     ("Workshops de identificação, revisões periódicas (mensal/trimestral), novos projetos, mudanças relevantes no contexto.",
      "Identification workshops, periodic reviews (monthly/quarterly), new projects, material changes in context.")),
    ("2_Identificacao_e_Avaliacao", "03_fmea", "⚙️", ("FMEA – modos de falha e efeitos", "FMEA – failure modes and effects"), "techniques",
     [("fmea", "fmea.modos")], False, {"fmea": "failure_mode"},
     ("Processos críticos, novos produtos/serviços, alterações de processo, segurança e qualidade.",
      "Critical processes, new products/services, process changes, safety and quality.")),
    ("3_Controlo_e_Tratamento", "04_controlos_rcm", "🛡️", ("Controlos e matriz risco-controlo (RCM)", "Controls and risk-control matrix (RCM)"), "controls",
     [("controls", "controlos.rcm")], False, {"controls": "name"},
     ("Desenho e teste de controlos internos, auditorias, certificações (ISO, SOX, DORA), revisão anual do sistema de controlo.",
      "Internal control design and testing, audits, certifications (ISO, SOX, DORA), annual review of the control system.")),
    ("3_Controlo_e_Tratamento", "05_plano_acoes", "🛠️", ("Plano de tratamento e ações", "Treatment and action plan"), "treatment",
     [("actions", "tratamento.acoes")], False, {"actions": "description"},
     ("Depois da avaliação: para riscos acima do apetite, controlos ineficazes e oportunidades a explorar.",
      "After assessment: for risks above appetite, ineffective controls and opportunities to exploit.")),
    ("3_Controlo_e_Tratamento", "06_kris", "📈", ("Indicadores-chave de risco (KRIs)", "Key risk indicators (KRIs)"), "kris",
     [("kris", "kris.indicadores")], False, {"kris": "name"},
     ("Monitorização contínua dos riscos prioritários; atualize o valor atual em cada período de reporte.",
      "Continuous monitoring of priority risks; update the current value each reporting period.")),
    ("4_Quantificacao", "07_fair", "🎲", ("Cenários FAIR (ciber / eventos de perda)", "FAIR scenarios (cyber / loss events)"), "quant",
     [("fair", "fair.cenarios")], False, {"fair": "scenario"},
     ("Quantificar em € riscos de informação/ciber ou outros eventos de perda recorrentes, para decidir investimentos e seguros.",
      "Quantify information/cyber or other recurring loss events in €, to decide investments and insurance.")),
    ("5_Maturidade", "08_maturidade", "🧩", ("Maturidade da gestão de risco (ERM)", "Risk management (ERM) maturity"), "maturity",
     [("maturity", "maturidade.dimensoes")], False, {"maturity": "current"},
     ("Autoavaliação anual do sistema de gestão de risco e definição do plano de desenvolvimento.",
      "Annual self-assessment of the risk management system and development plan.")),
]
SHEET_TO_TABLE = {sheet: table for m in MODULES for table, sheet in m[5]}

META_CAMPOS = [  # campo, PT, EN, kind, rule PT
    ("name", "Nome do projeto / avaliação", "Project / assessment name", "text", "Texto livre (curto e específico)"),
    ("organisation", "Organização", "Organisation", "text", "Texto livre"),
    ("industry", "Indústria", "Industry", "list", "Escolher da lista: " + " | ".join(v[0] for v in INDUSTRIES.values())),
    ("scope", "Âmbito (unidades, processos, projeto)", "Scope", "text", "Texto livre"),
    ("objectives", "Objetivos em risco", "Objectives at risk", "text", "Texto livre; separe objetivos por ;"),
    ("assessor", "Avaliador / responsável", "Assessor / owner", "text", "Texto livre"),
    ("date", "Data da avaliação", "Assessment date", "date", "Data DD/MM/AAAA"),
    ("currency", "Moeda", "Currency", "list", "Escolher: € | $ | £ | R$ | Kz | MT"),
    ("risk_capacity", "Capacidade de risco (perda máxima absorvível)", "Risk capacity", "num", "Número ≥ 0, sem símbolos"),
    ("appetite_statement", "Declaração de apetite ao risco", "Risk appetite statement", "text", "Texto aprovado pelo órgão de gestão"),
] + [(f"impact_{i}", f"Limite superior do impacto {i} – {IMPACT_SCALE[i][0]}", f"Impact {i} upper bound – {IMPACT_SCALE[i][1]}", "num",
      "Número ≥ 0; os 5 limites devem ser crescentes") for i in range(1, 6)]


def _lab(table: str, field: str, lang: str) -> str:
    from core.ui import FIELD_LABELS, TABLE_LABELS
    t = TABLE_LABELS.get((table, field)) or FIELD_LABELS.get(field, (field, field))
    return t[1] if lang == "en" else t[0]


def _cat_labels(cat: str, lang: str) -> list[str]:
    return [(en if lang == "en" else pt) for pt, en in CATALOGS[cat].values()]


def _rule(table: str, field: str, kind: str, lang: str) -> tuple[str, str]:
    """(type, rule) for the dictionary and header comments."""
    pt = lang != "en"
    if field == "id":
        return ("Texto" if pt else "Text", "Opcional. Ex.: R01, C01, A01. Preencha se quiser ligar outras folhas a esta linha; vazio = gerado automaticamente."
                if pt else "Optional. E.g. R01, C01, A01. Fill it to link other sheets to this row; blank = generated automatically.")
    if kind.startswith("cat:"):
        return ("Lista" if pt else "List", ("Escolher da lista: " if pt else "Choose from list: ") + " | ".join(_cat_labels(kind[4:], lang)))
    if kind == "int":
        if field in ("s", "o", "d"):
            rng = "1 e 10" if pt else "1 and 10"
        elif field == "progress":
            rng = "0 e 100" if pt else "0 and 100"
        elif table == "appetite":
            rng = "1 e 25 (score P×I residual máximo)" if pt else "1 and 25 (max residual P×I score)"
        else:
            rng = "1 e 5" if pt else "1 and 5"
        return ("Número inteiro" if pt else "Integer", ("Inteiro entre " if pt else "Integer between ") + rng)
    if kind == "float":
        if field in ("vuln_min", "vuln_ml", "vuln_max", "slef"):
            return ("Número" if pt else "Number", "Entre 0 e 1 (ex.: 0,15 = 15%)" if pt else "Between 0 and 1 (e.g. 0.15 = 15%)")
        if field == "prob_pct":
            return ("Número" if pt else "Number", "Opcional. Percentagem 0–100 (probabilidade anual)" if pt else "Optional. Percentage 0–100 (annual probability)")
        return ("Número" if pt else "Number", "Número ≥ 0, sem símbolos (€, %)" if pt else "Number ≥ 0, no symbols")
    if kind == "date":
        return ("Data" if pt else "Date", "DD/MM/AAAA" if pt else "DD/MM/YYYY")
    if kind == "ids":
        return ("IDs", "IDs dos riscos separados por vírgula (ex.: R01, R03) — devem existir no registo de riscos" if pt else
                "Risk IDs separated by commas (e.g. R01, R03) — must exist in the risk register")
    return ("Texto" if pt else "Text", "Texto livre (curto e específico)" if pt else "Free text (short and specific)")


def _fields(table: str) -> list[tuple[str, str]]:
    return [(f, k) for f, k, _ in SCHEMAS[table]]


def _example_df(table: str, lang: str) -> pd.DataFrame:
    from core.examples import load_example
    from core.ui import to_display
    p = load_example("insurance" if table != "fmea" else "health")
    df = p[table].head(3).copy()
    if table == "maturity":
        names = {c: (en if lang == "en" else pt) for c, pt, en in MATURITY_DIMENSIONS}
        df["dim"] = df["dim"].map(names)
    for f, kind, _ in SCHEMAS[table]:
        if kind.startswith("cat:") and f in df:
            items = CATALOGS[kind[4:]]
            df[f] = df[f].map(lambda v, it=items: (it[v][1] if lang == "en" else it[v][0]) if v in it else v)
    return df


def _header_style(cell, gold=False):
    cell.fill = PatternFill("solid", fgColor=GOLD if gold else BLUE)
    cell.font = Font(bold=True, color="FFFFFF")
    cell.alignment = Alignment(wrap_text=True, vertical="center")


def _instructions(ws, mod, lang: str):
    from core.help_texts import H, SRC
    folder, stem, icon, names, hkey, tables, has_campos, main, when = mod
    pt = lang != "en"
    what, how, srcs = H[hkey]["en" if lang == "en" else "pt"]
    clean = lambda s: s.replace("**", "").replace("*", "")  # noqa: E731
    ws.column_dimensions["A"].width = 26
    for c, w in zip("BCDE", (34, 16, 48, 40)):
        ws.column_dimensions[c].width = w
    ws["A1"] = f"{icon} {names[1] if lang == 'en' else names[0]}"
    ws["A1"].font = Font(bold=True, size=16, color=BLUE)
    ws["A2"] = ("Template Risk Studio · preencher e carregar em «📂 Dados & templates»" if pt else
                "Risk Studio template · fill in and upload in '📂 Data & templates'")
    ws["A2"].font = Font(italic=True, color="595959")
    r = 4

    def row(label, text, bold_label=True, height=None):
        nonlocal r
        ws.cell(r, 1, label).font = Font(bold=bold_label)
        ws.cell(r, 2, text).alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
        ws.cell(r, 1).alignment = Alignment(vertical="top")
        ws.row_dimensions[r].height = height or max(18, 15 * (1 + len(str(text)) // 120))
        r += 1
    first_src = SRC.get(srcs[0], "")
    row("O que é" if pt else "What it is", clean(what))
    row("Autor / origem" if pt else "Author / origin", first_src.split(".")[0] + "." if first_src else "—")
    row("Referência" if pt else "Reference", clean(" · ".join(SRC[s] for s in srcs if s in SRC)))
    row("Quando usar" if pt else "When to use", when[1] if lang == "en" else when[0])
    row("Como ler os resultados" if pt else "How to read the results", clean(how))
    r += 1
    ws.cell(r, 1, "COMO PREENCHER" if pt else "HOW TO FILL IN").font = Font(bold=True, color=BLUE, size=12)
    r += 1
    data_sheets = ", ".join(f"«{s}»" for _, s in tables)
    steps = [
        "Não altere os nomes das folhas nem os cabeçalhos (linha 1 de cada folha de dados).",
        ("Folha «campos»: preencha apenas a coluna «valor» (células amarelas – parâmetros gerais da análise)." if has_campos
         else "Este template não tem parâmetros gerais: preencha diretamente a(s) folha(s) de dados " + data_sheets + "."),
        "Folhas de dados: uma linha por registo, a partir da linha 2. Pode acrescentar quantas linhas precisar (até 300 com validação).",
        "Colunas com cabeçalho dourado têm lista pendente: escolha um valor da lista. Passe o rato sobre um cabeçalho para ver a regra.",
        "Números sem símbolos (€, %), use vírgula ou ponto decimal; as validações rejeitam valores fora do intervalo.",
        "Linhas com a coluna principal vazia são ignoradas. A coluna ID é opcional: preencha-a (R01, C01…) quando quiser ligar controlos, "
        "ações ou KRIs a um risco. Grave em .xlsx e carregue na app (pode carregar vários templates ou o ZIP inteiro de uma vez).",
        "Em alternativa, pode preencher diretamente na app, carregar o RiskRegister do professor ou pedir ao Agente IA que gere os dados.",
    ]
    steps_en = [
        "Do not rename sheets or change headers (row 1 of each data sheet).",
        ("Sheet 'campos': fill only the 'valor' column (yellow cells – general parameters)." if has_campos
         else "This template has no general parameters: fill the data sheet(s) " + data_sheets + " directly."),
        "Data sheets: one row per record, from row 2. Add as many rows as needed (up to 300 validated).",
        "Golden headers have a drop-down list: pick a value. Hover a header to see its rule.",
        "Numbers without symbols (€, %), comma or dot decimals; validations reject out-of-range values.",
        "Rows with an empty main column are ignored. The ID column is optional: fill it (R01, C01…) to link controls, actions or KRIs to a risk. "
        "Save as .xlsx and upload in the app (several templates or the whole ZIP at once).",
        "Alternatively fill in the app, upload the professor's RiskRegister or ask the AI Agent to generate the data.",
    ]
    for i, s in enumerate(steps_en if lang == "en" else steps, 1):
        row(f"Passo {i}" if pt else f"Step {i}", s, bold_label=True)
    r += 1
    ws.cell(r, 1, "DICIONÁRIO DE DADOS" if pt else "DATA DICTIONARY").font = Font(bold=True, color=BLUE, size=12)
    r += 1
    for j, h in enumerate(["Folha" if pt else "Sheet", "Coluna / campo" if pt else "Column / field", "Tipo" if pt else "Type",
                           "Regra / valores permitidos" if pt else "Rule / accepted values", "Exemplo" if pt else "Example"], 1):
        _header_style(ws.cell(r, j))
    r += 1
    if has_campos:
        from core.examples import load_example
        m = load_example("insurance")["meta"]
        for campo, lpt, len_, kind, rule in META_CAMPOS:
            ex = m.get(campo) if not campo.startswith("impact_") else m["impact_thresholds"][int(campo[-1]) - 1]
            if campo == "industry":
                ex = INDUSTRIES.get(ex, ("", ""))[1 if lang == "en" else 0]
            vals = ["campos", len_ if lang == "en" else lpt, {"text": "Texto", "num": "Número", "date": "Data", "list": "Lista"}[kind], rule, ex]
            for j, v in enumerate(vals, 1):
                ws.cell(r, j, v).alignment = Alignment(wrap_text=True, vertical="top")
            r += 1
    for table, sheet in tables:
        ex = _example_df(table, lang)
        for f, kind in _fields(table):
            typ, rule = _rule(table, f, kind, lang)
            v = ex[f].iloc[0] if (not ex.empty and f in ex) else ""
            if isinstance(v, float) and v != v:
                v = ""
            for j, val in enumerate([sheet, _lab(table, f, lang), typ, rule, v], 1):
                ws.cell(r, j, val).alignment = Alignment(wrap_text=True, vertical="top")
            r += 1
    r += 1
    ws.cell(r, 1, "EXEMPLO DE PREENCHIMENTO (primeiras linhas do caso exemplo)" if pt else "FILLED-IN EXAMPLE (first rows of the sample case)").font = \
        Font(bold=True, color=BLUE, size=12)
    r += 1
    for table, sheet in tables:
        ws.cell(r, 1, f"Folha «{sheet}»" if pt else f"Sheet '{sheet}'").font = Font(bold=True)
        r += 1
        ex = _example_df(table, lang)
        cols = [f for f, _ in _fields(table)]
        for k in range(0, len(cols), 5):
            chunk = cols[k:k + 5]
            for j, f in enumerate(chunk, 1):
                _header_style(ws.cell(r, j))
                ws.cell(r, j).value = _lab(table, f, lang)
            r += 1
            for rec in ex.to_dict(orient="records"):
                for j, f in enumerate(chunk, 1):
                    v = rec.get(f)
                    ws.cell(r, j, None if (v is None or (isinstance(v, float) and v != v)) else v).alignment = Alignment(wrap_text=True, vertical="top")
                r += 1


def _campos(wb, lang: str):
    ws = wb.create_sheet("campos")
    for j, h in enumerate(["ferramenta", "campo", "descricao", "valor", "regra"], 1):
        _header_style(ws.cell(1, j))
        ws.cell(1, j).value = h
    lists = {"industry": [v[1 if lang == "en" else 0] for v in INDUSTRIES.values()], "currency": ["€", "$", "£", "R$", "Kz", "MT"]}
    for i, (campo, lpt, len_, kind, rule) in enumerate(META_CAMPOS, start=2):
        ws.cell(i, 1, "contexto")
        ws.cell(i, 2, campo)
        ws.cell(i, 3, len_ if lang == "en" else lpt)
        ws.cell(i, 4).fill = PatternFill("solid", fgColor=YELLOW)
        ws.cell(i, 5, rule)
        if kind == "list":
            dv = DataValidation(type="list", formula1='"' + ",".join(lists[campo]) + '"', allow_blank=True)
            ws.add_data_validation(dv)
            dv.add(f"D{i}")
        elif kind == "num":
            dv = DataValidation(type="decimal", operator="greaterThanOrEqual", formula1="0", allow_blank=True)
            ws.add_data_validation(dv)
            dv.add(f"D{i}")
            ws.cell(i, 4).number_format = "#,##0"
        elif kind == "date":
            ws.cell(i, 4).number_format = "DD/MM/YYYY"
    for c, w in zip("ABCDE", (14, 22, 46, 60, 60)):
        ws.column_dimensions[c].width = w
    ws.freeze_panes = "A2"


def _data_sheet(wb, table: str, sheet: str, lang: str, lists_ws):
    ws = wb.create_sheet(sheet)
    fields = _fields(table)
    for j, (f, kind) in enumerate(fields, 1):
        c = ws.cell(1, j, _lab(table, f, lang))
        _header_style(c, gold=kind.startswith("cat:"))
        typ, rule = _rule(table, f, kind, lang)
        c.comment = Comment(f"{typ} — {rule}", "Risk Studio", width=320, height=120)
        col = get_column_letter(j)
        wide = f in ("title", "cause", "event", "effect", "description", "name", "objective", "failure_mode", "scenario", "evidence",
                     "action", "dim", "notes", "current_controls", "process", "asset", "threat")
        ws.column_dimensions[col].width = 44 if wide else 18
        rng = f"{col}2:{col}{N_ROWS + 1}"
        dv = None
        if kind.startswith("cat:"):
            vals = _cat_labels(kind[4:], lang)
            inline = '"' + ",".join(vals) + '"'
            if len(inline) <= 250 and "," not in "".join(vals):
                dv = DataValidation(type="list", formula1=inline, allow_blank=True)
            else:  # long lists (or labels with commas) live in the hidden sheet
                k = getattr(lists_ws, "_rs_cols", 0) + 1
                lists_ws._rs_cols = k
                lc = get_column_letter(k)
                lists_ws.cell(1, k, kind[4:])
                for i, v in enumerate(vals, start=2):
                    lists_ws.cell(i, k, v)
                dv = DataValidation(type="list", formula1=f"'_listas'!${lc}$2:${lc}${len(vals) + 1}", allow_blank=True)
        elif kind == "int" and f != "id":
            lo, hi = (1, 10) if f in ("s", "o", "d") else ((0, 100) if f == "progress" else ((1, 25) if table == "appetite" else (1, 5)))
            dv = DataValidation(type="whole", operator="between", formula1=str(lo), formula2=str(hi), allow_blank=True)
        elif kind == "float":
            if f in ("vuln_min", "vuln_ml", "vuln_max", "slef"):
                dv = DataValidation(type="decimal", operator="between", formula1="0", formula2="1", allow_blank=True)
            elif f == "prob_pct":
                dv = DataValidation(type="decimal", operator="between", formula1="0", formula2="100", allow_blank=True)
            else:
                dv = DataValidation(type="decimal", operator="greaterThanOrEqual", formula1="0", allow_blank=True)
        elif kind == "date":
            dv = DataValidation(type="date", operator="greaterThan", formula1="36526", allow_blank=True)
            for r in range(2, N_ROWS + 2):
                ws.cell(r, j).number_format = "DD/MM/YYYY"
        if dv is not None:
            dv.error = "Valor inválido — veja a regra no comentário do cabeçalho." if lang != "en" else "Invalid value — see the rule in the header comment."
            dv.errorTitle = "Risk Studio"
            ws.add_data_validation(dv)
            dv.add(rng)
    ws.freeze_panes = "A2"
    # structural rows that must exist (appetite categories, maturity dimensions) — values left blank
    if table == "appetite":
        for i, (code, (pt, en)) in enumerate(CATALOGS["category"].items(), start=2):
            ws.cell(i, 1, en if lang == "en" else pt)
    if table == "maturity":
        for i, (code, pt, en) in enumerate(MATURITY_DIMENSIONS, start=2):
            ws.cell(i, 1, en if lang == "en" else pt)


def build_module(mod, lang: str = "pt") -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Instruções" if lang != "en" else "Instructions"
    _instructions(ws, mod, lang)
    ws.page_setup.orientation = "landscape"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    if mod[6]:
        _campos(wb, lang)
    lists_ws = wb.create_sheet("_listas")
    for table, sheet in mod[5]:
        _data_sheet(wb, table, sheet, lang, lists_ws)
    if not getattr(lists_ws, "_rs_cols", 0):
        wb.remove(lists_ws)
    else:
        lists_ws.sheet_state = "hidden"
        wb.move_sheet("_listas", offset=len(wb.sheetnames))
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def build_index(lang: str = "pt") -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Índice" if lang != "en" else "Index"
    ws["A1"] = "Risk Studio – templates em branco" if lang != "en" else "Risk Studio – blank templates"
    ws["A1"].font = Font(bold=True, size=15, color=BLUE)
    ws["A2"] = ("Cada ficheiro tem a folha «Instruções» (como preencher, regras, dicionário e exemplo) e as folhas de dados "
                "(«campos» quando há parâmetros gerais). Preencha e carregue na app em «📂 Dados & templates» – pode carregar vários ficheiros "
                "ou o ZIP inteiro ao mesmo tempo. O RiskRegister do professor segue no formato original (escala 4×4)." if lang != "en" else
                "Each file has the 'Instruções' sheet (how to fill, rules, dictionary and example) and the data sheets ('campos' when there are "
                "general parameters). Fill and upload in '📂 Data & templates' – several files or the whole ZIP at once. The professor's "
                "RiskRegister keeps its original format (4×4 scale).")
    ws.merge_cells("A2:E2")
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[2].height = 48
    for j, h in enumerate(["#", "Template" if lang == "en" else "Modelo", "Categoria" if lang != "en" else "Category",
                           "Ficheiro" if lang != "en" else "File", "Folhas de dados" if lang != "en" else "Data sheets"], 1):
        _header_style(ws.cell(3, j))
        ws.cell(3, j).value = h
    r = 4
    ws.append([0, "RiskRegister (modelo do professor)" if lang != "en" else "RiskRegister (professor's template)",
               "Modelos do professor" if lang != "en" else "Professor's templates", "0_Modelos_do_professor/RiskRegister_Template.xlsx", "RiskRegister"])
    for i, m in enumerate(MODULES, 1):
        ws.append([i, m[3][1] if lang == "en" else m[3][0], m[0].split("_", 1)[1].replace("_", " "), f"{m[0]}/{m[1]}.xlsx",
                   ", ".join(([] if not m[6] else ["campos"]) + [s for _, s in m[5]])])
    for c, w in zip("ABCDE", (5, 48, 28, 52, 40)):
        ws.column_dimensions[c].width = w
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def build_zip(lang: str = "pt") -> bytes:
    from core.professor import TPL
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{ROOT}/00_INDICE.xlsx", build_index(lang))
        with open(TPL, "rb") as fh:
            z.writestr(f"{ROOT}/0_Modelos_do_professor/RiskRegister_Template.xlsx", fh.read())
        for m in MODULES:
            z.writestr(f"{ROOT}/{m[0]}/{m[1]}.xlsx", build_module(m, lang))
    return bio.getvalue()


# ------------------------------------------------------------------ reader
def is_module_workbook(wb) -> bool:
    return any(n in SHEET_TO_TABLE for n in wb.sheetnames) or "campos" in wb.sheetnames


def read_module_workbook(content: bytes) -> tuple[dict, list[str]]:
    """Parse a filled module template. Returns (parsed tables/meta, messages)."""
    from core.excel_io import _header_map
    wb = load_workbook(io.BytesIO(content), data_only=True)
    out, msgs = {}, []
    if "campos" in wb.sheetnames:
        ws = wb["campos"]
        meta, th = {}, {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or len(row) < 4 or row[1] is None or row[3] in (None, ""):
                continue
            campo, val = str(row[1]).strip(), row[3]
            if campo.startswith("impact_"):
                try:
                    th[int(campo[-1])] = float(str(val).replace(" ", "").replace(",", "."))
                except ValueError:
                    pass
            elif campo == "industry":
                v = str(val).strip().lower()
                meta["industry"] = next((k for k, (pt, en) in INDUSTRIES.items() if v in (k, pt.lower(), en.lower())), "other")
            elif campo == "risk_capacity":
                try:
                    meta["risk_capacity"] = float(str(val).replace(" ", "").replace(",", "."))
                except ValueError:
                    pass
            elif campo == "date":
                meta["date"] = val.date().isoformat() if hasattr(val, "date") else str(val)[:10]
            else:
                meta[campo] = str(val)
        if len(th) == 5:
            meta["impact_thresholds"] = sorted(th[i] for i in range(1, 6))
        if meta:
            out["meta"] = meta
            msgs.append(f"campos: {len(meta)}")
    for sheet, table in SHEET_TO_TABLE.items():
        if sheet not in wb.sheetnames:
            continue
        ws = wb[sheet]
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            continue
        hmap = _header_map(table)
        header = [hmap.get(str(h).strip().lower()) if h is not None else None for h in rows[0]]
        main = next(m[7][table] for m in MODULES if table in m[7])
        recs = []
        for r in rows[1:]:
            rec = {h: v for h, v in zip(header, r) if h}
            if table == "appetite":
                if rec.get("appetite") in (None, ""):
                    continue
            elif table == "maturity":
                if rec.get("current") in (None, "") and rec.get("target") in (None, ""):
                    continue
                lab2code = {pt.lower(): c for c, pt, en in MATURITY_DIMENSIONS} | {en.lower(): c for c, pt, en in MATURITY_DIMENSIONS}
                rec["dim"] = lab2code.get(str(rec.get("dim", "")).strip().lower(), rec.get("dim"))
            elif rec.get(main) in (None, ""):
                continue
            recs.append(rec)
        if recs:
            out[table] = coerce_df(table, pd.DataFrame(recs))
            msgs.append(f"{sheet}: {len(out[table])}")
    return out, msgs


def read_zip(content: bytes) -> list[tuple[str, bytes]]:
    """xlsx files inside an uploaded ZIP (e.g. the whole filled template pack)."""
    files = []
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        for n in sorted(z.namelist()):
            base = os.path.basename(n)
            if n.lower().endswith((".xlsx", ".json")) and not base.startswith(("~$", "._")) and "__MACOSX" not in n:
                if base.lower().startswith("00_indice"):
                    continue
                files.append((base, z.read(n)))
    return files
