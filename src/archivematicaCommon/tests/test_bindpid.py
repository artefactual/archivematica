# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.test import TestCase
import pytest

import bindpid


VALID_ARG_DICT = {
    "entity_type": "file",
    "resolve_url_template_file": "https://access.my.org/access/{{ naming_authority }}/{{ pid }}",
    "desired_pid": "3d6383a3-eafb-410e-b00f-77c33eb0b31b",
    "naming_authority": "12345",
    "pid_web_service_endpoint": "https://my.pid.endpoint.org/secure",
    "pid_web_service_key": "https://my.pid.endpoint.org/secure",
    "handle_resolver_url": "http://197.160.160.197:8015/",
    "pid_request_body_template": """<?xml version='1.0' encoding='UTF-8'?>
    <soapenv:Envelope
        xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/'
        xmlns:pid='http://pid.my.org/'>
        <soapenv:Body>
            <pid:UpsertPidRequest>
                <pid:na>{{ naming_authority }}</pid:na>
                <pid:handle>
                    <pid:pid>{{ naming_authority }}/{{ pid }}</pid:pid>
                    <pid:locAtt>
                        <pid:location weight='1' href='{{ base_resolve_url }}'/>
                        {%% for qrurl in qualified_resolve_urls %%}
                            <pid:location
                                weight='0'
                                href='{{ qrurl.url }}'
                                view='{{ qrurl.qualifier }}'/>
                        {%% endfor %%}
                    </pid:locAtt>
                </pid:handle>
            </pid:UpsertPidRequest>
        </soapenv:Body>
    </soapenv:Envelope>""",
}

# Bind PID params with for a file lacking a key for resolve_url_template_file
INVALID_ET_REQUIRED_ARG_DICT = {
    "entity_type": "file",
    "desired_pid": "3d6383a3-eafb-410e-b00f-77c33eb0b31b",
    "naming_authority": "12345",
    "pid_web_service_endpoint": "https://my.pid.endpoint.org/secure",
    "pid_web_service_key": "https://my.pid.endpoint.org/secure",
    "handle_resolver_url": "http://197.160.160.197:8015/",
    "pid_request_body_template": """<?xml version='1.0' encoding='UTF-8'?>
    <soapenv:Envelope
        xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/'
        xmlns:pid='http://pid.my.org/'>
        <soapenv:Body>
            <pid:UpsertPidRequest>
                <pid:na>{{ naming_authority }}</pid:na>
                <pid:handle>
                    <pid:pid>{{ naming_authority }}/{{ pid }}</pid:pid>
                    <pid:locAtt>
                        <pid:location weight='1' href='{{ base_resolve_url }}'/>
                        {%% for qrurl in qualified_resolve_urls %%}
                            <pid:location
                                weight='0'
                                href='{{ qrurl.url }}'
                                view='{{ qrurl.qualifier }}'/>
                        {%% endfor %%}
                    </pid:locAtt>
                </pid:handle>
            </pid:UpsertPidRequest>
        </soapenv:Body>
    </soapenv:Envelope>""",
}

# Invalid bind PID params: entity_type is wrong
INVALID_ARG_DICT = {
    "entity_type": "godzilla",
    "desired_pid": "3d6383a3-eafb-410e-b00f-77c33eb0b31b",
    "naming_authority": "12345",
    "pid_web_service_endpoint": "https://my.pid.endpoint.org/secure",
    "pid_web_service_key": "https://my.pid.endpoint.org/secure",
    "handle_resolver_url": "http://197.160.160.197:8015/",
    "pid_request_body_template": """<?xml version='1.0' encoding='UTF-8'?>
    <soapenv:Envelope
        xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/'
        xmlns:pid='http://pid.my.org/'>
        <soapenv:Body>
            <pid:UpsertPidRequest>
                <pid:na>{{ naming_authority }}</pid:na>
                <pid:handle>
                    <pid:pid>{{ naming_authority }}/{{ pid }}</pid:pid>
                    <pid:locAtt>
                        <pid:location weight='1' href='{{ base_resolve_url }}'/>
                        {%% for qrurl in qualified_resolve_urls %%}
                            <pid:location
                                weight='0'
                                href='{{ qrurl.url }}'
                                view='{{ qrurl.qualifier }}'/>
                        {%% endfor %%}
                    </pid:locAtt>
                </pid:handle>
            </pid:UpsertPidRequest>
        </soapenv:Body>
    </soapenv:Envelope>""",
}


class TestBindPID(TestCase):
    def test__validate(self):
        """Test the _validate function"""

        with pytest.raises(bindpid.BindPIDException) as excinfo:
            bindpid._validate(INVALID_ET_REQUIRED_ARG_DICT)
        assert (
            "To request a PID for a file, you must also supply a value for"
            " resolve_url_template_file" in str(excinfo.value)
        )

        with pytest.raises(bindpid.BindPIDException) as excinfo:
            bindpid._validate(INVALID_ARG_DICT)
        assert "The value for parameter entity_type must be one of" in str(
            excinfo.value
        )

        assert bindpid._validate(VALID_ARG_DICT) is None
