"""Smoke tests: every page renders without exceptions, in PT and EN, for every example."""
import os
import pytest
from streamlit.testing.v1 import AppTest

os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/risk_studio_test.db")
PAGES = ["painel", "evolucao", "contexto", "registo", "matriz", "tecnicas", "controlos", "tratamento", "kris", "quant",
         "maturidade", "agente", "relatorios", "dados", "metodologia"]


@pytest.mark.parametrize("lang", ["pt", "en"])
@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page, lang):
    at = AppTest.from_file("../app.py", default_timeout=120)
    at.session_state["lang"] = lang
    at.run()
    at.switch_page(f"views/{page}.py")
    at.run()
    assert not at.exception, [e.value for e in at.exception]


@pytest.mark.parametrize("example", ["banking", "health", "aero_mro", "tech_saas", "construction", "retail", "public", "__blank__"])
def test_all_pages_each_example(example):
    from core.examples import load_example
    from core.model import new_project
    at = AppTest.from_file("../app.py", default_timeout=120)
    at.run()
    at.session_state["proj"] = new_project() if example == "__blank__" else load_example(example)
    for page in PAGES:
        at.switch_page(f"views/{page}.py")
        at.run()
        assert not at.exception, (page, [e.value for e in at.exception])


def test_save_buttons_roundtrip():
    """Press every 'Save changes' form button on the editable pages: data must survive unchanged."""
    at = AppTest.from_file("../app.py", default_timeout=120)
    at.run()
    before = at.session_state["proj"]["risks"].copy()
    nctrl = len(at.session_state["proj"]["controls"])
    for page in ["registo", "controlos", "tratamento", "kris", "tecnicas", "maturidade", "contexto", "quant"]:
        at.switch_page(f"views/{page}.py")
        at.run()
        btns = [b for b in at.button if "Guardar" in str(b.label) and "💾 Guardar" != str(b.label)]
        assert btns, page
        btns[0].click()
        at.run()
        assert not at.exception, (page, [e.value for e in at.exception])
    after = at.session_state["proj"]["risks"]
    assert after["id"].tolist() == before["id"].tolist()
    assert after["p_inh"].tolist() == before["p_inh"].tolist()
    assert after["type"].tolist() == before["type"].tolist()
    assert len(at.session_state["proj"]["controls"]) == nctrl
    assert at.session_state["proj"]["controls"]["risk_ids"].tolist()[0] == "R01"


def test_db_save_and_reopen(tmp_path, monkeypatch):
    at = AppTest.from_file("../app.py", default_timeout=120)
    at.run()
    [b for b in at.sidebar.button if "Guardar" in str(b.label)][0].click()
    at.run()
    assert not at.exception
    pid = at.session_state["pid"]
    assert pid
    from core import db
    from core.model import from_json
    p = from_json(db.load_project(pid))
    assert len(p["risks"]) == len(at.session_state["proj"]["risks"])


def test_language_switch_en():
    at = AppTest.from_file("../app.py", default_timeout=120)
    at.session_state["lang"] = "en"
    at.run()
    assert any("Risk dashboard" in str(m.value) or "Risks" in str(m.value) for m in at.markdown)


def test_record_reviews_history_and_comparison():
    at = AppTest.from_file("../app.py", default_timeout=180)
    at.run()
    at.switch_page("views/evolucao.py")
    at.run()
    [b for b in at.button if "Guardar projeto" in str(b.label)][0].click()   # saves + initial review
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    pid = at.session_state["pid"]
    from core import db
    assert len(db.list_snapshots(pid)) == 1
    assert {a["module"] for a in db.list_analyses(pid)} >= {"dashboard", "register", "controls", "quant"}
    # change the project and record a manual review → timeline + comparison render
    at.session_state["proj"]["controls"].loc[5, "operating_test"] = "effective"
    [b for b in at.button if "Registar revisão agora" in str(b.label)][0].click()
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert len(db.list_snapshots(pid)) == 2
    # per-page "save analysis" button
    at.switch_page("views/controlos.py")
    at.run()
    [b for b in at.button if "Guardar análise" in str(b.label)][0].click()
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert any(a["module"] == "controls" and not a["snapshot_id"] for a in db.list_analyses(pid))


def test_query_param_restores_project():
    from core import db
    from core.examples import load_example
    from core.model import to_json
    pid = db.save_project("QP test", "banking", to_json(load_example("banking")))
    at = AppTest.from_file("../app.py", default_timeout=120)
    at.query_params["pid"] = str(pid)
    at.query_params["lang"] = "en"
    at.run()
    assert not at.exception
    assert at.session_state["pid"] == pid and at.session_state["lang"] == "en"
    assert at.session_state["proj"]["meta"]["industry"] == "banking"
