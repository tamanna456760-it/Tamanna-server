"""Tamanna Central Server - authenticated report API."""
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, jsonify, request
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

DB_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/reports.db")
API_TOKEN = os.environ.get("ORCHESTRATOR_TOKEN", "")

# Ensure relative SQLite database paths have a parent directory before connecting.
if DB_URL.startswith("sqlite:///") and not DB_URL.startswith("sqlite:////"):
    sqlite_path = DB_URL.removeprefix("sqlite:///")
    if sqlite_path and sqlite_path != ":memory:":
        Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
Base = declarative_base()
Session = sessionmaker(bind=engine)
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_CONTENT_LENGTH", "1048576"))


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    agent_id = Column(String(128))
    timestamp = Column(DateTime(timezone=True))
    branch = Column(String(128))
    build_ok = Column(String(32))
    committed = Column(String(32))
    commit_sha = Column(String(64))
    payload = Column(Text)


Base.metadata.create_all(engine)


def require_token():
    """Require a configured bearer token and compare it in constant time."""
    if not API_TOKEN:
        abort(503, description="Server authentication is not configured")
    auth = request.headers.get("Authorization", "")
    scheme, separator, supplied = auth.partition(" ")
    if not separator or scheme.lower() != "bearer" or not supplied.strip():
        abort(401)
    if not hmac.compare_digest(supplied.strip(), API_TOKEN):
        abort(403)


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Cache-Control", "no-store")
    return response


@app.get("/health")
def health():
    """Unauthenticated liveness endpoint; does not expose secrets or DB data."""
    return jsonify({"status": "ok", "service": "tamanna-central-server"}), 200


@app.post("/api/report")
def api_report():
    require_token()
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "expected a JSON object"}), 400
    session = Session()
    try:
        rep = Report(
            agent_id=str(data.get("agent_id", ""))[:128],
            timestamp=datetime.now(timezone.utc),
            branch=str(data.get("branch", ""))[:128],
            build_ok=str(data.get("build_ok", False))[:32],
            committed=str(data.get("committed", False))[:32],
            commit_sha=str(data.get("commit_sha") or "")[:64],
            payload=json.dumps(data, ensure_ascii=False),
        )
        session.add(rep)
        session.commit()
        return jsonify({"status": "ok"}), 201
    except SQLAlchemyError:
        session.rollback()
        app.logger.exception("Could not persist report")
        return jsonify({"error": "database operation failed"}), 500
    finally:
        session.close()


@app.get("/api/reports")
def list_reports():
    """Return report data only to callers with the server bearer token."""
    require_token()
    session = Session()
    try:
        rows = session.query(Report).order_by(Report.id.desc()).limit(200).all()
        return jsonify([
            {
                "id": row.id,
                "agent_id": row.agent_id,
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "branch": row.branch,
                "build_ok": row.build_ok,
                "committed": row.committed,
                "commit_sha": row.commit_sha,
            }
            for row in rows
        ])
    finally:
        session.close()


@app.get("/")
def index():
    """Public, non-sensitive service landing page; never disclose stored reports."""
    return jsonify({
        "service": "Tamanna Central Server",
        "status": "running",
        "health": "/health",
        "api": "/api/report",
    })
