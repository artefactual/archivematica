"""Helpers for updating FPRule execution counters.

The helpers in this module only aggregate and persist counter increments. Callers
remain responsible for deciding which workflow outcomes should count and when
the accumulated updates should be flushed.
"""

from django.db.models import F

from archivematica.dashboard.fpr.models import FPRule


class DeferredFPRuleCounter:
    """Batch FPRule counter increments and flush them with short updates."""

    def __init__(self) -> None:
        self._counts: dict[str, dict[str, int]] = {}

    def _get_counts(self, fprule: FPRule) -> dict[str, int]:
        return self._counts.setdefault(
            str(fprule.uuid),
            {
                "count_attempts": 0,
                "count_okay": 0,
                "count_not_okay": 0,
            },
        )

    def record_attempt(self, fprule: FPRule) -> None:
        self._get_counts(fprule)["count_attempts"] += 1

    def record_success(self, fprule: FPRule) -> None:
        self._get_counts(fprule)["count_okay"] += 1

    def record_failure(self, fprule: FPRule) -> None:
        self._get_counts(fprule)["count_not_okay"] += 1

    def flush(self) -> None:
        """Persist recorded increments and clear the in-memory batch."""
        for rule_uuid in sorted(self._counts):
            counts = self._counts[rule_uuid]
            updates = {
                field: F(field) + count for field, count in counts.items() if count
            }
            if not updates:
                continue

            FPRule.objects.filter(uuid=rule_uuid).update(**updates)

        self._counts.clear()
