import ast
from contextlib import contextmanager
from pathlib import Path

import pytest

from archivematica.MCPClient.client import transactions


class FakeConnection:
    in_atomic_block = False


def test_client_scripts_do_not_import_django_transactions() -> None:
    client_scripts = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "archivematica"
        / "MCPClient"
        / "clientScripts"
    )
    direct_imports = []

    for path in client_scripts.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module == "django.db" and any(
                alias.name == "transaction" for alias in node.names
            ):
                direct_imports.append(path.name)
            if node.module == "django.db.transaction" and any(
                alias.name == "atomic" for alias in node.names
            ):
                direct_imports.append(path.name)

    assert direct_imports == []


def test_atomic_observes_only_outer_transaction(monkeypatch) -> None:
    connection = FakeConnection()
    observations = []
    times = iter([10.0, 11.5])

    @contextmanager
    def fake_atomic(**kwargs: object):
        del kwargs
        was_in_atomic_block = connection.in_atomic_block
        connection.in_atomic_block = True
        try:
            yield
        finally:
            connection.in_atomic_block = was_in_atomic_block

    monkeypatch.setattr(
        transactions.transaction, "get_connection", lambda using: connection
    )
    monkeypatch.setattr(transactions.transaction, "atomic", fake_atomic)
    monkeypatch.setattr(transactions.time, "monotonic", lambda: next(times))
    monkeypatch.setattr(
        transactions.metrics,
        "database_transaction_observed",
        observations.append,
    )

    with transactions.atomic():
        with transactions.atomic():
            pass

    assert observations == [pytest.approx(1.5)]
