"""Tamanna Central Server: authenticated report API and health endpoints."""
import hmac
import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, jsonify, request
from bridge import register_bridge
from security.service_protocol import verify_request
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker
from werkzeug.middleware.proxy_fix import ProxyFix

DB_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/reports.db")
TRUST_PROXY = os.environ.get("TRUST_PROXY", "false").lower() == "true"
API_TOKEN = os.environ.get("ORCHESTRATOR_TOKEN", "")
MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", "1048576"))
RATE_LIMIT_PER_MINUTE = max(1, int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60")))
CORS_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.environ.get("CORS_ORIGINS", "").split(",")
    if origin.strip()
}

if MAX_CONTENT_LENGTH < 1:
    raise ValueError("MAX_CONTENT_LENGTH must be positive")

database_url = make_url(DB_URL)
if database_url.get_backend_name() == "sqlite" and database_url.database not in (None, "", ":memory:"):
    database_path = Path(database_url.database).expanduser()
    database_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
Base = declarative_base()
Session = sessionmaker(bind=engine)
app = Flask(__name__)

# Authenticated ChatGPT MCP bridge and Tamanna service message queue.
register_bridge(app, engine, Session)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
if TRUST_PROXY:
    # Enable only when the app is reachable exclusively through trusted reverse proxies.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

_rate_lock = threading.Lock()
_rate_events = {}


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    agent_id = Column(String(128), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    branch = Column(String(128))
    build_ok = Column(String(32))
    committed = Column(String(32))
    commit_sha = Column(String(64))
    payload = Column(Text, nullable=False)


Base.metadata.create_all(engine)


def require_token():
    """Require a configured bearer token and compare it in constant time."""
    token = API_TOKEN
    if len(token) < 32:
        abort(503, description="Server authentication token is missing or too short")
    auth = request.headers.get("Authorization", "")
    scheme, separator, supplied = auth.partition(" ")
    if not separator or scheme.lower() != "bearer" or not supplied.strip():
        abort(401)
    if not hmac.compare_digest(supplied.strip(), token):
        abort(403)


def enforce_rate_limit():
    """Small per-process API limiter; use an edge proxy for distributed limits."""
    now = time.monotonic()
    client = request.remote_addr or "unknown"
    with _rate_lock:
        events = [stamp for stamp in _rate_events.get(client, []) if now - stamp < 60]
        if len(events) >= RATE_LIMIT_PER_MINUTE:
            _rate_events[client] = events
            abort(429, description="Rate limit exceeded")
        events.append(now)
        _rate_events[client] = events
        if len(_rate_events) > 10000:
            cutoff = now - 60
            for key in list(_rate_events):
                kept = [stamp for stamp in _rate_events[key] if stamp >= cutoff]
                if kept:
                    _rate_events[key] = kept
                else:
                    _rate_events.pop(key, None)


@app.before_request
def api_request_guard():
    if request.path.startswith(("/api/", "/mcp", "/bridge/", "/protocol/")):
        enforce_rate_limit()


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Cache-Control", "no-store")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    origin = request.headers.get("Origin", "").rstrip("/")
    if origin and origin in CORS_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"error": "request body too large"}), 413


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "not found"}), 404


@app.errorhandler(429)
def too_many_requests(error):
    return jsonify({"error": getattr(error, "description", "rate limit exceeded")}), 429


@app.get("/health")
def health():
    """Unauthenticated liveness endpoint; does not expose secrets or DB data."""
    return jsonify({"status": "ok", "service": "tamanna-central-server"}), 200


@app.get("/health/ready")
def readiness():
    """Readiness check verifies the database connection without exposing details."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return jsonify({"status": "ready", "database": "ok"}), 200
    except SQLAlchemyError:
        app.logger.exception("Readiness check failed")
        return jsonify({"status": "not_ready"}), 503


@app.post("/api/report")
def api_report():
    require_token()
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "expected a JSON object"}), 400

    agent_id = data.get("agent_id")
    if not isinstance(agent_id, str) or not agent_id.strip():
        return jsonify({"error": "agent_id must be a non-empty string"}), 400
    for field, limit in (("branch", 128), ("commit_sha", 64)):
        value = data.get(field, "")
        if value is not None and (not isinstance(value, str) or len(value) > limit):
            return jsonify({"error": f"{field} must be a string of at most {limit} characters"}), 400

    session = Session()
    try:
        rep = Report(
            agent_id=agent_id.strip()[:128],
            timestamp=datetime.now(timezone.utc),
            branch=(data.get("branch") or "")[:128],
            build_ok=str(data.get("build_ok", False))[:32],
            committed=str(data.get("committed", False))[:32],
            commit_sha=(data.get("commit_sha") or "")[:64],
            payload=json.dumps(data, ensure_ascii=False),
        )
        session.add(rep)
        session.commit()
        return jsonify({"status": "ok", "id": rep.id}), 201
    except SQLAlchemyError:
        session.rollback()
        app.logger.exception("Could not persist report")
        return jsonify({"error": "database operation failed"}), 500
    finally:
        session.close()


@app.get("/api/reports")
def list_reports():
    """Return report metadata only to callers with the server bearer token."""
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
    """Service metadata only; the public website is served by the web tier."""
    return jsonify({
        "service": "Tamanna Central Server",
        "status": "running",
        "health": "/health",
        "readiness": "/health/ready",
        "api": "/api/report",
    })


if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
        debug=os.environ.get("APP_DEBUG", "false").lower() == "true",
    )


# TAMANNA_PROTOCOL_V1

@app.post("/protocol/v1/report")
def protocol_v1_report():
    raw_body = request.get_data(cache=True)
    if not verify_request(request.method, request.path, request.headers, raw_body):
        abort(401, description="Invalid service protocol authentication")
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "expected a JSON object"}), 400
    agent_id = data.get("agent_id")
    if not isinstance(agent_id, str) or not agent_id.strip() or len(agent_id) > 128:
        return jsonify({"error": "agent_id must be a non-empty string up to 128 characters"}), 400
    session = Session()
    try:
        rep = Report(
            agent_id=agent_id.strip(),
            timestamp=datetime.now(timezone.utc),
            branch=str(data.get("branch", ""))[:128],
            build_ok=str(data.get("build_ok", False))[:32],
            committed=str(data.get("committed", False))[:32],
            commit_sha=str(data.get("commit_sha", ""))[:64],
            payload=json.dumps(data, ensure_ascii=False),
        )
        session.add(rep)
        session.commit()
        return jsonify({"status": "ok", "id": rep.id, "protocol": "tamanna-service/1"}), 201
    except SQLAlchemyError:
        session.rollback()
        app.logger.exception("Protocol report persistence failed")
        return jsonify({"error": "database operation failed"}), 500
    finally:
        session.close()


@app.get("/protocol/v1")
def protocol_v1_info():
    return jsonify({
        "protocol": "tamanna-service/1",
        "authentication": "HMAC-SHA256",
        "signed_fields": ["method", "path", "timestamp", "nonce", "sha256(body)"],
        "max_clock_skew_seconds": 300,
        "report_endpoint": "POST /protocol/v1/report",
    }), 200
# END TAMANNA_PROTOCOL_V1
