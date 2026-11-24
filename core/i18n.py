"""Bilingual helpers (PT-PT / EN).

Usage:
    from core.i18n import L, lang
    st.header(L("Registo de Riscos", "Risk Register"))
"""
from __future__ import annotations

import streamlit as st

LANGS = {"pt": "Português", "en": "English"}


def lang() -> str:
    return st.session_state.get("lang", "pt")


def L(pt: str, en: str) -> str:
    """Return the string for the active language."""
    return en if lang() == "en" else pt


def tr(d: dict | tuple | str) -> str:
    """Translate a {'pt':..,'en':..} dict or (pt, en) tuple."""
    if isinstance(d, dict):
        return d.get(lang(), d.get("pt", ""))
    if isinstance(d, (tuple, list)):
        return d[1] if lang() == "en" else d[0]
    return str(d)
