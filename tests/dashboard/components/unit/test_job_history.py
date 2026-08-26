import uuid

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from archivematica.dashboard.components.unit.views import JOB_HISTORY_PAGE_SIZE
from archivematica.dashboard.main import models


@pytest.fixture
def transfer(db):
    return models.Transfer.objects.create(status=models.PACKAGE_STATUS_DONE)


@pytest.fixture
def link_uuid():
    return uuid.uuid4()


def history_url(unit, link_uuid, unit_type="transfer"):
    return reverse(
        "unit:job_history",
        kwargs={
            "unit_type": unit_type,
            "unit_uuid": unit.pk,
            "link_uuid": link_uuid,
        },
    )


def create_job(unit, link_uuid, **kwargs):
    fields = {
        "sipuuid": unit.pk,
        "unittype": "unitTransfer",
        "microservicechainlink": link_uuid,
        "createdtime": timezone.now(),
        "currentstep": models.Job.STATUS_COMPLETED_SUCCESSFULLY,
        "jobtype": "Normalize for preservation",
        "directory": "/shared/Example/",
    }
    fields.update(kwargs)
    return models.Job.objects.create(**fields)


def test_history_requires_a_dashboard_session(
    dashboard_uuid, client, transfer, link_uuid
):
    response = client.get(history_url(transfer, link_uuid))

    assert response.status_code == 302


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_history_only_accepts_get(
    dashboard_uuid, admin_client, transfer, link_uuid, method
):
    response = getattr(admin_client, method)(history_url(transfer, link_uuid))

    assert response.status_code == 405
    assert response.headers["Allow"] == "GET"


@pytest.mark.parametrize("missing", ["unit", "link", "hidden", "wrong_type"])
def test_history_rejects_inaccessible_scope(
    dashboard_uuid, admin_client, transfer, link_uuid, missing
):
    create_job(transfer, link_uuid)
    url = history_url(transfer, link_uuid)
    if missing == "unit":
        transfer.delete()
    elif missing == "link":
        url = history_url(transfer, uuid.uuid4())
    elif missing == "hidden":
        transfer.hidden = True
        transfer.save(update_fields=["hidden"])
    elif missing == "wrong_type":
        url = history_url(transfer, link_uuid, "ingest")

    response = admin_client.get(url)

    assert response.status_code == 404


@pytest.mark.parametrize("segment", ["unit", "link"])
def test_history_rejects_malformed_uuids(
    dashboard_uuid, admin_client, transfer, link_uuid, segment
):
    unit_id = "invalid" if segment == "unit" else transfer.pk
    link_id = "invalid" if segment == "link" else link_uuid

    response = admin_client.get(f"/transfer/{unit_id}/job-history/{link_id}/")

    assert response.status_code == 404


def test_history_exposes_tasks_from_every_attempt_and_status(
    dashboard_uuid, admin_client, transfer, link_uuid
):
    jobs = [
        create_job(transfer, link_uuid, currentstep=status)
        for status in (
            models.Job.STATUS_COMPLETED_SUCCESSFULLY,
            models.Job.STATUS_COMPLETED_SUCCESSFULLY,
            models.Job.STATUS_FAILED,
            models.Job.STATUS_EXECUTING_COMMANDS,
        )
    ]
    for index, job in enumerate(jobs):
        models.Task.objects.create(
            job=job,
            createdtime=timezone.now(),
            stdout=f"Output from attempt {index}",
        )
    other_link_job = create_job(transfer, uuid.uuid4())
    other_unit_job = create_job(models.Transfer.objects.create(), link_uuid)
    wrong_type_job = create_job(transfer, link_uuid, unittype="unitSIP")

    response = admin_client.get(history_url(transfer, link_uuid))

    assert response.status_code == 200
    assert list(response.context["page"]) == list(reversed(jobs))
    content = response.content.decode()
    assert "Job history" in content
    assert "including every status" in content
    for index, job in enumerate(jobs):
        tasks_url = f"/tasks/{job.pk}/"
        assert f'href="{tasks_url}"' in content
        tasks_response = admin_client.get(tasks_url)
        assert tasks_response.status_code == 200
        assert f"Output from attempt {index}" in tasks_response.content.decode()
    for excluded in (other_link_job, other_unit_job, wrong_type_job):
        assert str(excluded.pk) not in content
    assert "Output from attempt" not in content


def test_ingest_history_includes_sip_and_dip_jobs(
    dashboard_uuid, admin_client, db, link_uuid
):
    sip = models.SIP.objects.create()
    sip_job = create_job(sip, link_uuid, unittype="unitSIP")
    dip_job = create_job(sip, link_uuid, unittype="unitDIP")
    create_job(sip, link_uuid, unittype="unitTransfer")

    response = admin_client.get(history_url(sip, link_uuid, "ingest"))

    assert response.status_code == 200
    assert list(response.context["page"]) == [dip_job, sip_job]
    assert "No tasks" in response.content.decode()


def test_history_paginates_before_loading_jobs_with_stable_tie_ordering(
    dashboard_uuid, admin_client, transfer, link_uuid
):
    timestamp = timezone.now()
    jobs = models.Job.objects.bulk_create(
        [
            models.Job(
                jobuuid=uuid.UUID(int=index + 1),
                sipuuid=transfer.pk,
                unittype="unitTransfer",
                microservicechainlink=link_uuid,
                createdtime=timestamp,
                jobtype="Repeated job",
            )
            for index in range(JOB_HISTORY_PAGE_SIZE + 3)
        ]
    )
    url = history_url(transfer, link_uuid)

    with CaptureQueriesContext(connection) as captured:
        response = admin_client.get(url)

    page = response.context["page"]
    assert page.paginator.count == JOB_HISTORY_PAGE_SIZE + 3
    assert [job.pk for job in page] == [job.pk for job in reversed(jobs[3:])]
    job_queries = [
        query["sql"]
        for query in captured.captured_queries
        if "FROM `Jobs`" in query["sql"] and "COUNT(" not in query["sql"]
    ]
    assert len(job_queries) == 1
    assert f"LIMIT {JOB_HISTORY_PAGE_SIZE}" in job_queries[0]
    assert "stdOut" not in job_queries[0]
    assert 'href="?page=2"' in response.content.decode()

    response = admin_client.get(url, {"page": 2})

    assert [job.pk for job in response.context["page"]] == [
        job.pk for job in reversed(jobs[:3])
    ]
    assert 'href="?page=1"' in response.content.decode()


@pytest.mark.parametrize("page_number", ["invalid", "0", "999"])
def test_history_handles_invalid_page_numbers(
    dashboard_uuid, admin_client, transfer, link_uuid, page_number
):
    job = create_job(transfer, link_uuid)

    response = admin_client.get(history_url(transfer, link_uuid), {"page": page_number})

    assert response.status_code == 200
    assert list(response.context["page"]) == [job]
