"""Tamanna Central Server - Flask API and report dashboard."""
import json
import os
from datetime import datetime, timezone

from flask import Flask, abort, jsonify, render_template_string, request
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

DB_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/reports.db")
API_TOKEN = os.environ.get("ORCHESTRATOR_TOKEN", "")

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {},
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
    if not API_TOKEN:
        abort(503, description="Server authentication is not configured")
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        abort(401)
    token = auth.split(" ", 1)[1].strip()
    if not token or token != API_TOKEN:
        abort(403)


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
            build_ok=str(data.get("build_ok", False)),
            committed=str(data.get("committed", False)),
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


@app.get("/")
def index():
    session = Session()
    try:
        rows = session.query(Report).order_by(Report.id.desc()).limit(200).all()
    finally:
        session.close()
    template = """
    <!doctype html><html lang="en"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Tamanna Central Server</title></head><body>
    <h1>Tamanna Central Server</h1><p>Recent authorized agent reports</p>
    <table border="1" cellpadding="6"><tr><th>ID</th><th>Agent</th><th>Time</th>
    <th>Branch</th><th>Build</th><th>Committed</th><th>Commit</th></tr>
    {% for r in rows %}<tr><td>{{ r.id }}</td><td>{{ r.agent_id }}</td>
    <td>{{ r.timestamp }}</td><td>{{ r.branch }}</td><td>{{ r.build_ok }}</td>
    <td>{{ r.committed }}</td><td>{{ r.commit_sha }}</td></tr>{% endfor %}
    </table></body></html>
    """
    return render_template_string(template, rows=rows)
