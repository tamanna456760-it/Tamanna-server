"""Tamanna service-to-service protocol v1: timestamped HMAC authentication."""
import hashlib
import hmac
import os
import re
import threading
import time

PROTOCOL_VERSION = "1"
CLOCK_SKEW_SECONDS = int(os.getenv("TAMANNA_PROTOCOL_CLOCK_SKEW_SECONDS", "300"))
SHARED_SECRET = os.getenv("TAMANNA_SERVICE_SHARED_SECRET", "")
KEY_ID = os.getenv("TAMANNA_SERVICE_KEY_ID", "tamanna-ai")
REDIS_URL = os.getenv("TAMANNA_PROTOCOL_REDIS_URL", "").strip()
_NONCES = {}
_LOCK = threading.Lock()
_NONCE_RE = re.compile(r"^[A-Za-z0-9_-]{16,128}$")


def canonical_message(method: str, path: str, timestamp: str, nonce: str, body: bytes) -> bytes:
    digest = hashlib.sha256(body).hexdigest()
    return "\\n".join((PROTOCOL_VERSION, method.upper(), path, timestamp, nonce, digest)).encode("utf-8")


def sign_request(method: str, path: str, timestamp: str, nonce: str, body: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), canonical_message(method, path, timestamp, nonce, body), hashlib.sha256).hexdigest()


def _claim_nonce(key_id: str, nonce: str, now: int) -> bool:
    if REDIS_URL:
        try:
            import redis
            client = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2, socket_timeout=2, decode_responses=True)
            # SET NX is atomic across workers and hosts; TTL exceeds accepted clock skew.
            return bool(client.set(f"tamanna:protocol:nonce:{key_id}:{nonce}", "1", nx=True, ex=max(1, CLOCK_SKEW_SECONDS * 2)))
        except Exception:
            # Fail closed: never fall back to a process-local replay cache when Redis is configured.
            return False
    # Local development fallback only. Configure TAMANNA_PROTOCOL_REDIS_URL in production.
    with _LOCK:
        cutoff = now - CLOCK_SKEW_SECONDS
        for old_nonce, seen_at in list(_NONCES.items()):
            if seen_at < cutoff:
                _NONCES.pop(old_nonce, None)
        replay_key = f"{key_id}:{nonce}"
        if replay_key in _NONCES or len(_NONCES) >= 50000:
            return False
        _NONCES[replay_key] = now
        return True


def verify_request(method: str, path: str, headers, body: bytes) -> bool:
    if len(SHARED_SECRET) < 32:
        return False
    version = headers.get("X-Tamanna-Protocol", "")
    key_id = headers.get("X-Tamanna-Key-Id", "")
    timestamp = headers.get("X-Tamanna-Timestamp", "")
    nonce = headers.get("X-Tamanna-Nonce", "")
    signature = headers.get("X-Tamanna-Signature", "")
    if version != PROTOCOL_VERSION or key_id != KEY_ID:
        return False
    if not timestamp.isdigit() or not _NONCE_RE.fullmatch(nonce):
        return False
    if not re.fullmatch(r"[0-9a-f]{64}", signature):
        return False
    now = int(time.time())
    if abs(now - int(timestamp)) > CLOCK_SKEW_SECONDS:
        return False
    expected = sign_request(method, path, timestamp, nonce, body, SHARED_SECRET)
    if not hmac.compare_digest(expected, signature):
        return False
    return _claim_nonce(key_id, nonce, now)
