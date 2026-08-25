from session_store import SessionStore


def test_expired_at_boundary_is_invalid() -> None:
    store = SessionStore()
    store.issue("s1", "u1", ["read"], now=10.0, ttl=5.0)
    assert not store.validate("s1", now=15.0)


def test_caller_scope_mutation_does_not_change_authorization() -> None:
    store = SessionStore()
    scopes = ["read"]
    session = store.issue("s1", "u1", scopes, now=10.0, ttl=5.0)
    scopes.append("admin")
    assert session.scopes == ["read"]


def test_touch_cannot_restore_a_revoked_session() -> None:
    # The production failure occurs when revoke runs between touch's two lock
    # sections. A correct implementation makes the lookup/update atomic.
    store = SessionStore()
    store.issue("s1", "u1", ["read"], now=10.0, ttl=5.0)
    store.revoke("s1")
    assert not store.touch("s1", now=11.0)
