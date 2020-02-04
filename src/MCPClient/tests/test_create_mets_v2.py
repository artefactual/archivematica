# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(THIS_DIR, "../lib/clientScripts")))

from create_mets_v2 import createDMDIDsFromCSVMetadata


def test_createDMDIDsFromCSVMetadata_finds_non_ascii_paths(mocker):
    dmd_secs_creator_mock = mocker.patch(
        "create_mets_v2.createDmdSecsFromCSVParsedMetadata", return_value=[]
    )
    state_mock = mocker.Mock(
        **{
            "CSV_METADATA": {
                "montréal".encode("utf8"): "montreal metadata",
                "dvořák".encode("utf8"): "dvorak metadata",
            }
        }
    )

    createDMDIDsFromCSVMetadata(None, "montréal", state_mock)
    createDMDIDsFromCSVMetadata(None, "toronto", state_mock)
    createDMDIDsFromCSVMetadata(None, "dvořák", state_mock)

    dmd_secs_creator_mock.assert_has_calls(
        [
            mocker.call(None, "montreal metadata", state_mock),
            mocker.call(None, {}, state_mock),
            mocker.call(None, "dvorak metadata", state_mock),
        ]
    )
