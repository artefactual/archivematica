#!/usr/bin/env python
# -*- coding: utf8

"""test_validate_mets.py."""

import os
import sys

import pytest

from job import Job

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))

from validate_mets import load_and_validate_mets, ValidateMETSException

FIXTURES = os.path.join(THIS_DIR, "fixtures", "mets_validation")


@pytest.mark.parametrize(
    "fixture,is_valid",
    [
        ("valid_standard_transfer.xml", True),
        ("invalid_without_baginfo.xml", False),
        ("valid_aic_aip_mets.xml", True),
    ],
)
def test_validate_mets(fixture, is_valid):
    mets_file = os.path.join(FIXTURES, fixture)
    job = Job("stub", "stub", ["", ""])
    job.args[1] = mets_file
    if not is_valid:
        with pytest.raises(
            ValidateMETSException, message="'NoneType' object has no attribute 'tag'"
        ):
            load_and_validate_mets(job)
    else:
        assert load_and_validate_mets(job) is None
