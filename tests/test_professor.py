"""Course formats: professor RiskRegister (4×4), PM Studio Model 8 and PM Studio project JSON."""
import logging
import os

logging.disable(logging.CRITICAL)
from core import professor as PR  # noqa: E402
from core.examples import load_example  # noqa: E402
from core.excel_io import merge_into  # noqa: E402
from core.model import ids_list  # noqa: E402

FX = os.path.join(os.path.dirname(__file__), "fixtures")


def test_scale_mapping_by_name():
    assert [PR.lik4_to5(x) for x in ("Unlikely", "Possible", "Likely", "Almost certain")] == [2, 3, 4, 5]
    assert [PR.imp4_to5(x) for x in ("Minor", "Moderate", "Major", "Severe")] == [2, 3, 4, 5]
    assert [PR.to4(x) for x in (1, 2, 3, 4, 5)] == [1, 1, 2, 3, 4]


def test_blank_professor_template_skips_example_row():
    t, _, kind = PR.parse_upload("RiskRegister_Template.xlsx", open(PR.TPL, "rb").read())
    assert kind == "risk_register" and len(t["risks"]) == 0


def test_professor_roundtrip_keeps_mitigation_as_controls_and_actions():
    p = load_example("insurance")
    data, warn = PR.export_risk_register(p)
    assert warn == [] or "8" in warn[0]
    t, _, kind = PR.parse_upload("rr.xlsx", data)
    assert kind == "risk_register" and len(t["risks"]) == min(8, (p["risks"]["type"] == "threat").sum())
    assert set(t["controls"]["control_type"]) <= {"preventive", "corrective"}
    assert all(ids_list(x)[0] in set(t["risks"]["id"]) for x in t["controls"]["risk_ids"])


def test_pm_project_json_and_model8():
    t, meta, kind = PR.parse_upload("p.json", open(os.path.join(FX, "pm_studio_project.json"), "rb").read())
    assert kind == "pm_project" and len(t["risks"]) >= 1 and meta["name"].startswith("Riscos")
    assert (t["controls"]["control_type"] == "corrective").any()
    t8, _, k8 = PR.parse_upload("m8.xlsx", open(os.path.join(FX, "Modelo_8_Matriz_gestao_riscos.xlsx"), "rb").read())
    assert k8 == "pm_model8" and len(t8["risks"]) == 0


def test_append_keeps_links():
    p = load_example("insurance")
    t, _, _ = PR.parse_upload("p.json", open(os.path.join(FX, "pm_studio_project.json"), "rb").read())
    merged = merge_into(p, t, "append")
    assert merged["risks"]["id"].is_unique and merged["controls"]["id"].is_unique
    new_ctrl = merged["controls"].iloc[len(p["controls"]):]
    new_risks = set(merged["risks"]["id"].iloc[len(p["risks"]):])
    for x in new_ctrl["risk_ids"]:
        assert set(ids_list(x)) <= new_risks
    new_act = merged["actions"].iloc[len(p["actions"]):]
    assert set(new_act["risk_id"]) <= new_risks


def test_templates_zip_structure_and_roundtrip():
    import io
    import zipfile

    from openpyxl import load_workbook

    from core import templates_zip as T
    from core.ui import to_display
    z = zipfile.ZipFile(io.BytesIO(T.build_zip("pt")))
    names = z.namelist()
    assert "Templates_Risk_Studio/00_INDICE.xlsx" in names
    assert "Templates_Risk_Studio/0_Modelos_do_professor/RiskRegister_Template.xlsx" in names
    assert len([n for n in names if n.endswith(".xlsx")]) == 10
    p = load_example("insurance")
    for m in T.MODULES:
        wb = load_workbook(io.BytesIO(T.build_module(m, "pt")))
        assert wb.sheetnames[0] == "Instruções"
        # blank template → nothing imported
        parsed, msgs = T.read_module_workbook(T.build_module(m, "pt"))
        assert not any(k for k in parsed if k != "meta"), m[1]
        for table, sheet in m[5]:
            if table in ("appetite", "maturity"):
                continue
            ws = wb[sheet]
            cols = [f for f, _ in T._fields(table)]
            for i, rec in enumerate(to_display(table, p[table]).to_dict("records"), start=2):
                for j, f in enumerate(cols, 1):
                    v = rec.get(f)
                    if isinstance(v, list):
                        v = ", ".join(v)
                    if v is not None and v == v:
                        ws.cell(i, j, v)
            bio = io.BytesIO()
            wb.save(bio)
            parsed, _ = T.read_module_workbook(bio.getvalue())
            assert len(parsed[table]) == len(p[table])
            assert list(parsed[table]["id"]) == list(p[table]["id"])
