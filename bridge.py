"""Authenticated, durable message bridge and stateless MCP Streamable HTTP endpoint."""
import json
import os
import secrets
import time
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, abort
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class BridgeMessage(Base):
    __tablename__ = "bridge_messages"
    id = Column(String(64), primary_key=True)
    conversation_id = Column(String(128), nullable=False, index=True)
    idempotency_key = Column(String(128), nullable=False, unique=True)
    status = Column(String(24), nullable=False, index=True)
    message_text = Column(Text, nullable=False)
    reply_text = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

def register_bridge(app, engine, Session):
    Base.metadata.create_all(engine)
    bp = Blueprint("tamanna_bridge", __name__)
    max_chars = max(256, int(os.getenv("BRIDGE_MAX_MESSAGE_CHARS", "12000")))
   
    def bearer_matches(env_name):
        expected = os.getenv(env_name, "")
        auth = request.headers.get("Authorization", "")
        scheme, _, supplied = auth.partition(" ")
        return bool(len(expected) >= 32 and scheme.lower() == "bearer" and secrets.compare_digest(supplied, expected))

    def require_mcp():
        if not bearer_matches("MCP_BEARER_TOKEN"):
            abort(401)

    def require_service():
        if not bearer_matches("TAMANNA_BRIDGE_SERVICE_TOKEN"):
            abort(401)

    def rpc_error(request_id, code, message):
        return jsonify({"jsonrpc":"2.0","id":request_id,"error":{"code":code,"message":message}})

    @bp.route("/mcp", methods=["POST"])
    def mcp_endpoint():
        require_mcp()
        if not request.is_json:
            return jsonify({"error":"application/json required"}), 415
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0":
            return rpc_error(None, -32600, "Invalid JSON-RPC request"), 400
        method = payload.get("method")
        params = payload.get("params") or {}
        rid = payload.get("id")
        if method == "initialize":
            return jsonify({"jsonrpc":"2.0","id":rid,"result":{"protocolVersion":"2025-03-26","capabilities":{"tools":{}},"serverInfo":{"name":"tamanna-bridge","version":"1.0.0"}}})
        if method == "notifications/initialized":
            return ("", 202)
        if method == "ping":
            return jsonify({"jsonrpc":"2.0","id":rid,"result":{}})
        if method == "tools/list":
            tools = [
              {"name":"send_user_message","description":"Send the current user instruction to Tamanna AI and return a message ID.","inputSchema":{"type":"object","properties":{"text":{"type":"string","minLength":1,"maxLength":max_chars},"conversation_id":{"type":"string","maxLength":128},"idempotency_key":{"type":"string","minLength":8,"maxLength":128}},"required":["text","conversation_id","idempotency_key"],"additionalProperties":False}},
              {"name":"wait_for_tamanna_reply","description":"Check whether Tamanna AI has replied to a previously submitted message.","inputSchema":{"type":"object","properties":{"message_id":{"type":"string","maxLength":64}},"required":["message_id"],"additionalProperties":False}}
            ]
            return jsonify({"jsonrpc":"2.0","id":rid,"result":{"tools":tools}})
        if method == "tools/call":
            name = params.get("name")
            args = params.get("arguments") or {}
            if name == "send_user_message":
                text_value = args.get("text")
                conv = args.get("conversation_id")
                idem = args.get("idempotency_key")
                if not all(isinstance(v, str) and v.strip() for v in (text_value, conv, idem)) or len(text_value) > max_chars or len(conv) > 128 or len(idem) > 128:
                    return rpc_error(rid, -32602, "Invalid arguments"), 400
                db = Session()
                try:
                    row = db.query(BridgeMessage).filter_by(idempotency_key=idem).one_or_none()
                    created = row is None
                    if row is None:
                        now = datetime.now(timezone.utc)
                        row = BridgeMessage(id=secrets.token_hex(16), conversation_id=conv, idempotency_key=idem, status="queued", message_text=text_value, created_at=now, updated_at=now)
                        db.add(row); db.commit()
                    result = {"message_id":row.id,"status":row.status,"duplicate_submission":not created}
                finally:
                    db.close()
                return jsonify({"jsonrpc":"2.0","id":rid,"result":{"content":[{"type":"text","text":json.dumps(result)}]}})
            if name == "wait_for_tamanna_reply":
                mid = args.get("message_id")
                if not isinstance(mid, str) or not mid:
                    return rpc_error(rid, -32602, "message_id required"), 400
                db = Session()
                try:
                    row = db.query(BridgeMessage).filter_by(id=mid).one_or_none()
                    result = {"message_id":mid,"status":"not_found"} if row is None else {"message_id":mid,"status":row.status,"reply":row.reply_text}
                finally:
                    db.close()
                return jsonify({"jsonrpc":"2.0","id":rid,"result":{"content":[{"type":"text","text":json.dumps(result, ensure_ascii=False)}]}})
            return rpc_error(rid, -32601, "Unknown tool"), 404
        return rpc_error(rid, -32601, "Unsupported method"), 404

    @bp.post("/bridge/v1/consume")
    def consume_message():
        require_service()
        db = Session()
        try:
            from sqlalchemy import update
            candidate = db.query(BridgeMessage).filter_by(status="queued").order_by(BridgeMessage.created_at.asc()).first()
            if candidate is None:
                return jsonify({"status":"empty"}), 200
            now = datetime.now(timezone.utc)
            claimed = db.execute(update(BridgeMessage).where(BridgeMessage.id == candidate.id, BridgeMessage.status == "queued").values(status="processing", updated_at=now))
            db.commit()
            if claimed.rowcount != 1:
                return jsonify({"status":"empty"}), 200
            row = db.query(BridgeMessage).filter_by(id=candidate.id).one()
            result = {"message_id":row.id,"conversation_id":row.conversation_id,"text":row.message_text}
            return jsonify(result), 200
        finally:
            db.close()

    @bp.post("/bridge/v1/reply")
    def post_reply():
        require_service()
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error":"JSON object required"}), 400
        mid, reply = data.get("message_id"), data.get("reply")
        if not isinstance(mid, str) or not isinstance(reply, str) or not reply.strip() or len(reply) > max_chars * 2:
            return jsonify({"error":"Invalid message_id or reply"}), 400
        db = Session()
        try:
            row = db.query(BridgeMessage).filter_by(id=mid).one_or_none()
            if row is None:
                return jsonify({"error":"message not found"}), 404
            if row.status == "completed":
                return jsonify({"error":"reply already recorded"}), 409
            row.reply_text = reply; row.status = "completed"; row.updated_at = datetime.now(timezone.utc)
            db.commit()
            return jsonify({"message_id":mid,"status":"completed"}), 200
        finally:
            db.close()

    app.register_blueprint(bp)
    return bp
