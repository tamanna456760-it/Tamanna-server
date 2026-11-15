"""Regression tests for concurrent SQLite bridge schema initialization."""
from concurrent.futures import ThreadPoolExecutor

from flask import Flask
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from bridge import register_bridge


def test_bridge_schema_initialization_is_safe_for_concurrent_workers(tmp_path):
    database_path = tmp_path / "bridge-startup.sqlite3"
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False, "timeout": 30},
        pool_pre_ping=True,
    )
    session_factory = sessionmaker(bind=engine)

    def register_worker(worker_number):
        app = Flask(f"bridge-startup-{worker_number}")
        register_bridge(app, engine, session_factory)
        return app

    try:
        with ThreadPoolExecutor(max_workers=8) as executor:
            apps = list(executor.map(register_worker, range(16)))

        assert len(apps) == 16
        inspector = inspect(engine)
        assert "bridge_messages" in inspector.get_table_names()
        indexes = {
            item["name"] for item in inspector.get_indexes("bridge_messages")
        }
        assert "ix_bridge_messages_conversation_id" in indexes
        assert "ix_bridge_messages_status" in indexes
    finally:
        engine.dispose()
