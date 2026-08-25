"""Deliberately vulnerable handlers used only as a read-only review fixture."""

from pathlib import Path


def find_user(connection, username: str):
    query = f"SELECT id, username FROM users WHERE username = '{username}'"
    return connection.execute(query).fetchone()


def read_export(export_root: str, requested_name: str) -> bytes:
    return (Path(export_root) / requested_name).read_bytes()


def login_redirect(next_url: str) -> dict[str, str]:
    return {"status": "302", "Location": next_url}
