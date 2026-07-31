import dataclasses
import hashlib
import json
import re
from collections.abc import Callable
from datetime import timedelta
from typing import Any

from django.db import IntegrityError
from django.db import transaction
from django.utils import timezone

from archivematica.dashboard.main import models

IDEMPOTENCY_KEY_REGEX = re.compile(r"[\x21-\x7e]{1,255}")


class IdempotencyKeyConflictError(ValueError):
    """An idempotency key was reused with a different request."""


class IdempotencyRequestInProgressError(RuntimeError):
    """An identical request is still establishing its operation result."""


@dataclasses.dataclass(frozen=True)
class IdempotencyReservation:
    record_id: int
    result: Any
    created: bool


def is_valid_key(value: object) -> bool:
    return isinstance(value, str) and IDEMPOTENCY_KEY_REGEX.fullmatch(value) is not None


def fingerprint(payload: object) -> str:
    """Return a stable digest of a JSON-serializable request payload."""
    serialized = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(serialized.encode("utf8")).hexdigest()


def reserve_or_replay(
    *,
    user_id: int,
    operation: str,
    key: str,
    request_fingerprint: str,
    retention: timedelta,
    create_result: Callable[[], Any],
) -> IdempotencyReservation:
    """Create a pending result or replay one completed by its operation."""
    if retention <= timedelta(0):
        raise ValueError("Idempotency key retention must be greater than zero.")

    key_hash = hashlib.sha256(key.encode("utf8")).hexdigest()
    now = timezone.now()
    lookup = {
        "user_id": user_id,
        "operation": operation,
        "key_hash": key_hash,
    }

    def existing_record():
        return models.IdempotencyRecord.objects.filter(
            **lookup,
            expires_at__gt=now,
        ).first()

    def replay(record):
        if record.request_fingerprint != request_fingerprint:
            raise IdempotencyKeyConflictError(
                "Idempotency key has already been used with a different request."
            )
        if record.state == models.IdempotencyRecord.State.PENDING:
            raise IdempotencyRequestInProgressError(
                "A request with this idempotency key is still in progress."
            )
        return IdempotencyReservation(
            record_id=record.pk,
            result=record.result,
            created=False,
        )

    try:
        with transaction.atomic():
            models.IdempotencyRecord.objects.filter(
                **lookup,
                expires_at__lte=now,
            ).delete()
            record = existing_record()
            if record is not None:
                return replay(record)

            record = models.IdempotencyRecord.objects.create(
                **lookup,
                request_fingerprint=request_fingerprint,
                result={},
                expires_at=now + retention,
            )
            result = create_result()
            record.result = result
            record.save(update_fields=["result"])
            return IdempotencyReservation(
                record_id=record.pk,
                result=result,
                created=True,
            )
    except IntegrityError:
        # A concurrent request won the unique (user, operation, key)
        # reservation. Any work performed by this transaction was rolled back.
        record = existing_record()
        if record is None:
            raise
        return replay(record)


def complete(reservation: IdempotencyReservation) -> None:
    """Make a newly created reservation available for future replays."""
    updated = models.IdempotencyRecord.objects.filter(
        pk=reservation.record_id,
        state=models.IdempotencyRecord.State.PENDING,
    ).update(state=models.IdempotencyRecord.State.COMPLETED)
    if updated != 1:
        raise RuntimeError("Idempotency reservation could not be completed.")


def release(reservation: IdempotencyReservation) -> None:
    """Release a pending reservation after its operation failed to start."""
    deleted, _ = models.IdempotencyRecord.objects.filter(
        pk=reservation.record_id,
        state=models.IdempotencyRecord.State.PENDING,
    ).delete()
    if deleted != 1:
        raise RuntimeError("Idempotency reservation could not be released.")
