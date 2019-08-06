# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from prometheus_client import Counter

from main.models import RightsStatementRightsGranted, RightsStatement


@receiver(post_delete, sender=RightsStatementRightsGranted)
def delete_rights_statement(sender, **kwargs):
    """
    Delete a RightsStatement if it has no RightsGranted.

    Rights are displayed in the GUI based on their RightsGranted, but the RightsStatement tracks their reingest status.
    When a RightsGranted is deleted, also delete the RightsStatement if this was the last RightsGranted.
    """
    instance = kwargs.get("instance")
    try:
        # If the statement has no other RightsGranted delete the RightsStatement
        if not instance.rightsstatement.rightsstatementrightsgranted_set.all():
            instance.rightsstatement.delete()
    except RightsStatement.DoesNotExist:
        # The RightsGranted is being deleted as part of a cascasde delete from the RightsStatement
        pass


if settings.PROMETHEUS_ENABLED:
    # Count saves and deletes via Prometheus.
    # This is a bit of a flawed way to do it (it doesn't include bulk create,
    # update, etc), but is a good starting point.
    # django-prometheus provides these counters via a model mixin, but signals
    # are less invasive.

    model_save_count = Counter(
        "django_model_save_total",
        "Total model save calls labeled by model class",
        ["model"],
    )
    model_delete_count = Counter(
        "django_model_delete_total",
        "Total model delete labeled by model class",
        ["model"],
    )

    @receiver(post_save)
    def increment_model_save_count(sender, **kwargs):
        model_save_count.labels(model=sender.__name__).inc()

    @receiver(post_delete)
    def increment_model_delete_count(sender, **kwargs):
        model_delete_count.labels(model=sender.__name__).inc()
