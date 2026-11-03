"""Compatibility entry point for the central Flask application.

Legacy shell-based pull endpoints are intentionally not exposed here.
"""
from app import app

__all__ = ["app"]
