import logging
logging.disable(logging.CRITICAL)
from core.examples import EXAMPLES, load_example
from core import scoring, montecarlo as mc
from core.excel_io import build_workbook, read_workbook, merge_into
from core.model import new_project, to_json, from_json


def test_examples_roundtrip_json_and_excel():
    for k in EXAMPLES:
        p = load_example(k)
        p2 = from_json(to_json(p))
        assert p2["risks"]["id"].tolist() == p["risks"]["id"].tolist()
        parsed, msgs = read_workbook(build_workbook(p, "pt"))
        p3 = merge_into(new_project(), parsed, "replace")
        for t in ["risks", "controls", "actions", "kris", "fmea", "fair"]:
            assert len(p3[t]) == len(p[t]), (k, t)
        assert p3["risks"]["type"].tolist() == p["risks"]["type"].tolist()
        assert p3["controls"]["risk_ids"].tolist() == p["controls"]["risk_ids"].tolist()
        assert p3["meta"]["impact_thresholds"] == p["meta"]["impact_thresholds"]
        # EN template too
        parsed_en, _ = read_workbook(build_workbook(p, "en"))
        p4 = merge_into(new_project(), parsed_en, "replace")
        assert p4["controls"]["control_type"].tolist() == p["controls"]["control_type"].tolist()


def test_residual_never_above_inherent_and_coverage():
    for k in EXAMPLES:
        p = load_example(k)
        ra = scoring.analyse_risks(p)
        assert (ra["p_res"] <= ra["p_inh"]).all() and (ra["i_res"] <= ra["i_inh"]).all()
        cov = scoring.coverage(p)
        assert 0 <= cov["coverage_pct"] <= 1


def test_montecarlo_residual_lower():
    p = load_example("insurance")
    ra = scoring.analyse_risks(p)
    inp = mc.build_inputs(ra, p["meta"]["impact_thresholds"])
    ti, _ = mc.simulate(inp, 20000, 0.2)
    tr, _ = mc.simulate(inp, 20000, 0.2, residual=True)
    assert tr.mean() < ti.mean()
    s = mc.stats(ti, 1e6)
    assert s["p50"] <= s["p80"] <= s["p95"] <= s["cvar95"]


def test_append_assigns_new_ids():
    p = load_example("banking")
    parsed, _ = read_workbook(build_workbook(p, "pt"))
    merged = merge_into(p, parsed, "append")
    assert len(merged["risks"]) == 2 * len(p["risks"])
    assert merged["risks"]["id"].is_unique


def test_empty_project():
    p = new_project()
    assert scoring.kpis(p)["n_risks"] == 0
    assert scoring.analyse_risks(p).empty
