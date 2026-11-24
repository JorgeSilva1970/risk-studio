"""Persistence: PostgreSQL on Render (DATABASE_URL) with SQLite fallback for local use."""
from __future__ import annotations

import datetime as dt
import os

import streamlit as st
from sqlalchemy import (Column, DateTime, Integer, MetaData, String, Table, Text, create_engine, delete,
                        insert, select, update)

metadata = MetaData()
projects = Table(
    "risk_projects", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(200), nullable=False),
    Column("industry", String(60)),
    Column("data", Text, nullable=False),
    Column("created_at", DateTime, default=dt.datetime.utcnow),
    Column("updated_at", DateTime, default=dt.datetime.utcnow),
)


snapshots = Table(
    "risk_snapshots", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("project_id", Integer, nullable=False, index=True),
    Column("label", String(200), default=""),
    Column("data", Text, nullable=False),
    Column("created_at", DateTime, default=dt.datetime.utcnow),
)


analyses = Table(
    "risk_analyses", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("project_id", Integer, nullable=False, index=True),
    Column("snapshot_id", Integer, nullable=True, index=True),
    Column("module", String(40), nullable=False, index=True),
    Column("label", String(200), default=""),
    Column("kpis", Text, default="{}"),
    Column("details", Text, default="{}"),
    Column("interpretation", Text, default=""),
    Column("ai_text", Text, default=""),
    Column("created_at", DateTime, default=dt.datetime.utcnow),
)


def _url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        try:
            url = st.secrets.get("DATABASE_URL", "")  # type: ignore[attr-defined]
        except Exception:
            url = ""
    if not url:
        return "sqlite:///risk_studio.db"
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


@st.cache_resource(show_spinner=False)
def engine():
    url = _url()
    kw = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kw["connect_args"] = {"check_same_thread": False}
    eng = create_engine(url, **kw)
    metadata.create_all(eng)
    return eng


def backend_name() -> str:
    return "PostgreSQL" if _url().startswith("postgresql") else "SQLite (local)"


def list_projects() -> list[dict]:
    with engine().connect() as c:
        rows = c.execute(select(projects.c.id, projects.c.name, projects.c.industry, projects.c.updated_at)
                         .order_by(projects.c.updated_at.desc())).mappings().all()
    return [dict(r) for r in rows]


def save_project(name: str, industry: str, data: str, pid: int | None = None) -> int:
    now = dt.datetime.utcnow()
    with engine().begin() as c:
        if pid:
            res = c.execute(update(projects).where(projects.c.id == pid)
                            .values(name=name, industry=industry, data=data, updated_at=now))
            if res.rowcount:
                return pid
        res = c.execute(insert(projects).values(name=name, industry=industry, data=data, created_at=now, updated_at=now))
        return int(res.inserted_primary_key[0])


def load_project(pid: int) -> str | None:
    with engine().connect() as c:
        r = c.execute(select(projects.c.data).where(projects.c.id == pid)).first()
    return r[0] if r else None


def delete_project(pid: int) -> None:
    with engine().begin() as c:
        c.execute(delete(analyses).where(analyses.c.project_id == pid))
        c.execute(delete(snapshots).where(snapshots.c.project_id == pid))
        c.execute(delete(projects).where(projects.c.id == pid))


# --------------------------------------------------------------- snapshots (periodic risk reviews)
def save_snapshot(pid: int, label: str, data: str) -> int:
    with engine().begin() as c:
        r = c.execute(insert(snapshots).values(project_id=pid, label=label, data=data, created_at=dt.datetime.utcnow()))
        return int(r.inserted_primary_key[0])


def list_snapshots(pid: int) -> list[dict]:
    with engine().connect() as c:
        rows = c.execute(select(snapshots).where(snapshots.c.project_id == pid).order_by(snapshots.c.created_at)).mappings().all()
    return [dict(r) for r in rows]


def delete_snapshot(sid: int) -> None:
    with engine().begin() as c:
        c.execute(delete(analyses).where(analyses.c.snapshot_id == sid))
        c.execute(delete(snapshots).where(snapshots.c.id == sid))


def last_snapshot_date(pid: int):
    with engine().connect() as c:
        r = c.execute(select(snapshots.c.created_at).where(snapshots.c.project_id == pid)
                      .order_by(snapshots.c.created_at.desc())).first()
    return r[0] if r else None


# --------------------------------------------------------------- analyses (one row per module per review / save)
def save_analysis(pid: int, module: str, label: str, kpis: dict, details: dict | None = None, interpretation: str = "",
                  ai_text: str = "", snapshot_id: int | None = None) -> int:
    import json
    with engine().begin() as c:
        r = c.execute(insert(analyses).values(
            project_id=pid, snapshot_id=snapshot_id, module=module, label=label,
            kpis=json.dumps(kpis, ensure_ascii=False, default=str), details=json.dumps(details or {}, ensure_ascii=False, default=str),
            interpretation=interpretation, ai_text=ai_text, created_at=dt.datetime.utcnow()))
        return int(r.inserted_primary_key[0])


def list_analyses(pid: int, module: str | None = None) -> list[dict]:
    import json
    q = select(analyses).where(analyses.c.project_id == pid)
    if module:
        q = q.where(analyses.c.module == module)
    with engine().connect() as c:
        rows = c.execute(q.order_by(analyses.c.created_at)).mappings().all()
    out = []
    for r in rows:
        d_ = dict(r)
        d_["kpis"] = json.loads(d_["kpis"] or "{}")
        d_["details"] = json.loads(d_["details"] or "{}")
        out.append(d_)
    return out


def delete_analysis(aid: int) -> None:
    with engine().begin() as c:
        c.execute(delete(analyses).where(analyses.c.id == aid))
