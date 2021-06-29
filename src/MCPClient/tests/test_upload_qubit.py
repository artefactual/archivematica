# -*- coding: utf8
from __future__ import unicode_literals
import os
import uuid

import pytest
import six.moves.cPickle

from main import models

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

import upload_qubit


@pytest.fixture
def sip(db):
    return models.SIP.objects.create(uuid=str(uuid.uuid4()))


@pytest.fixture
def job(sip, tmp_path):
    job_dir = tmp_path / "job"
    job_dir.mkdir()
    return models.Job.objects.create(
        sipuuid=sip.uuid,
        jobtype="Upload DIP",
        directory=str(job_dir),
        createdtime="2021-06-29T00:00:00Z",
    )


@pytest.fixture
def access(db, sip):
    return models.Access.objects.create(
        sipuuid=sip.uuid,
        target=six.moves.cPickle.dumps({"target": "atom-description-id"}, protocol=0),
    )


def test_start_synchronously(db, mocker, sip, job, access):
    mocker.patch(
        "requests.request",
        return_value=mocker.Mock(
            status_code=200, headers={"Location": "http://example.com"}
        ),
    )

    job = mocker.Mock()
    opts = mocker.Mock(
        uuid=sip.uuid,
        rsync_target=False,
        rsync_command=None,
        version=2,
        url="http://example.com",
        email="",
        password="",
        debug=True,
    )

    assert upload_qubit.start(job, opts) == 0

    access = models.Access.objects.get(sipuuid=sip.uuid)
    assert access.statuscode == 14
    assert access.resource == "{}/atom-description-id".format(opts.url)
    assert access.status == "Deposited synchronously"
