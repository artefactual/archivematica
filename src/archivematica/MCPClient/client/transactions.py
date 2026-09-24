import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Optional

from django.db import transaction

from archivematica.MCPClient.client import metrics


@contextmanager
def atomic(
    using: Optional[str] = None,
    savepoint: bool = True,
    durable: bool = False,
) -> Iterator[None]:
    """Open an atomic block and measure outer transaction duration."""
    connection = transaction.get_connection(using)
    is_outermost = not connection.in_atomic_block
    entered = False
    started_at = time.monotonic() if is_outermost else None

    try:
        with transaction.atomic(using=using, savepoint=savepoint, durable=durable):
            entered = True
            yield
    finally:
        if started_at is not None and entered:
            metrics.database_transaction_observed(time.monotonic() - started_at)
