from datetime import datetime
from decimal import Decimal
from uuid import UUID

import pytest
from django.core.exceptions import FieldDoesNotExist


@pytest.mark.django_db(transaction=True)
def test_0088_backfills_createdtime_microseconds(migrate_apps):
    from django.db import connection

    if connection.vendor != "mysql":
        pytest.skip("MySQL-specific migration")

    apps = migrate_apps(("main", "0086_remove_appraisal"))
    Job = apps.get_model("main", "Job")

    job_a = Job.objects.create(
        createdtime=datetime(2020, 1, 1, 10, 0, 0),
        createdtimedec=Decimal("0.123456"),
    )
    job_b = Job.objects.create(
        createdtime=datetime(2020, 1, 1, 10, 0, 0),
        createdtimedec=Decimal("0"),
    )
    job_c = Job.objects.create(
        createdtime=datetime(2020, 1, 1, 10, 0, 0, 654321),
        createdtimedec=Decimal("0.123456"),
    )

    apps = migrate_apps(("main", "0088_job_createdtime_microseconds"))
    Job = apps.get_model("main", "Job")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DATETIME_PRECISION
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'Jobs'
              AND COLUMN_NAME = 'createdTime'
            """
        )
        row = cursor.fetchone()
    assert row is not None
    assert int(row[0]) == 6

    job_a = Job.objects.get(jobuuid=job_a.jobuuid)
    job_b = Job.objects.get(jobuuid=job_b.jobuuid)
    job_c = Job.objects.get(jobuuid=job_c.jobuuid)

    assert job_a.createdtime.microsecond == 123456
    assert job_b.createdtime.microsecond == 0
    assert job_c.createdtime.microsecond == 654321

    with pytest.raises(FieldDoesNotExist):
        apps.get_model("main", "Job")._meta.get_field("createdtimedec")


@pytest.mark.django_db(transaction=True)
def test_0088_preserves_timestamp_ordering(migrate_apps):
    from django.db import connection

    if connection.vendor != "mysql":
        pytest.skip("MySQL-specific migration")

    apps = migrate_apps(("main", "0086_remove_appraisal"))
    Job = apps.get_model("main", "Job")

    job_a = Job.objects.create(
        jobuuid=UUID("00000000-0000-0000-0000-000000000002"),
        createdtime=datetime(2020, 1, 1, 10, 0, 0),
        createdtimedec=Decimal("0.100000"),
    )
    job_b = Job.objects.create(
        jobuuid=UUID("00000000-0000-0000-0000-000000000001"),
        createdtime=datetime(2020, 1, 1, 10, 0, 0),
        createdtimedec=Decimal("0.200000"),
    )

    apps = migrate_apps(("main", "0088_job_createdtime_microseconds"))
    Job = apps.get_model("main", "Job")

    jobs = list(Job.objects.order_by("-createdtime", "-jobuuid"))

    assert jobs[0].jobuuid == job_b.jobuuid
    assert jobs[1].jobuuid == job_a.jobuuid
