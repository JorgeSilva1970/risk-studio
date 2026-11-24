"""Live tests against the Anthropic API (skipped when ANTHROPIC_API_KEY is not set)."""
import os
import pytest
from streamlit.testing.v1 import AppTest

pytestmark = pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="no API key")


def test_identify_and_add_risks():
    at = AppTest.from_file("../app.py", default_timeout=300)
    at.run()
    n0 = len(at.session_state["proj"]["risks"])
    at.switch_page("views/agente.py")
    at.run()
    at.slider[0].set_value(3)
    [b for b in at.button if b.key == "b_risks"][0].click()
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    prev = at.session_state["ai_preview"]
    assert prev["kind"] == "risks" and len(prev["items"]) >= 3, prev.get("err")
    [b for b in at.button if "Acrescentar" in str(b.label)][0].click()
    at.run()
    assert not at.exception
    risks = at.session_state["proj"]["risks"]
    assert len(risks) == n0 + len(prev["items"])
    assert risks["id"].is_unique
    assert set(risks["type"]) <= {"threat", "opportunity"}


def test_report_with_ai_summary():
    at = AppTest.from_file("../app.py", default_timeout=300)
    at.run()
    at.switch_page("views/relatorios.py")
    at.run()
    [b for b in at.button if "sumário executivo IA" in str(b.label)][0].click()
    at.run()
    assert at.session_state["proj"]["meta"]["ai_summary"]
    [b for b in at.button if "Gerar relatório" in str(b.label)][0].click()
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    h = at.session_state["report_html"]
    assert "Sumário executivo" in h and "plotly" in h and len(h) > 50_000
    open("/tmp/report_test.html", "w").write(h)


def test_extract_risks_from_docx():
    import io
    import logging
    logging.disable(logging.CRITICAL)
    from docx import Document
    from core import ai
    from core.examples import load_example
    d = Document()
    d.add_heading("Relatório de auditoria interna — Sinistros 2026", 1)
    d.add_paragraph("Constatação 1: 12% dos pagamentos acima de 10 mil euros não tiveram dupla validação; risco de pagamentos indevidos.")
    d.add_paragraph("Constatação 2: o plano de continuidade do sistema de sinistros não é testado desde 2023.")
    d.add_paragraph("Recomendação: implementar bloqueio automático no workflow e testar o plano de continuidade semestralmente.")
    bio = io.BytesIO()
    d.save(bio)
    txt = ai.document_text("auditoria.docx", bio.getvalue())
    assert "dupla validação" in txt
    items, err = ai.structured(load_example("insurance"), "risks", ai.prompt_extract("risks", "auditoria.docx", txt))
    assert err is None and len(items) >= 2


def test_connection_ok():
    from core import ai
    ok, msg = ai.test_connection()
    assert ok, msg


def test_page_assistant_interprets_and_saves():
    at = AppTest.from_file("../app.py", default_timeout=300)
    at.run()
    at.switch_page("views/controlos.py")
    at.run()
    [b for b in at.button if "Interpretar" in str(b.label)][0].click()
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    txt = at.session_state["aiassist_controls"]
    assert len(txt) > 200 and "⚠️" not in txt[:5]
    [b for b in at.button if "Guardar análise" in str(b.label)][0].click()
    at.run()
    from core import db
    a = [x for x in db.list_analyses(at.session_state["pid"]) if x["module"] == "controls" and x["ai_text"]]
    assert a and a[-1]["ai_text"] == txt
