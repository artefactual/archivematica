import uuid

import pytest

from archivematica.archivematicaCommon import bindpid

VALID_ARG_DICT = {
    "entity_type": "file",
    "resolve_url_template_file": "https://access.my.org/access/{{ naming_authority }}/{{ pid }}",
    "desired_pid": str(uuid.uuid4()),
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
    "desired_pid": str(uuid.uuid4()),
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
    "desired_pid": str(uuid.uuid4()),
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


def test_validate_requires_resolve_url_template_file_for_files() -> None:
    with pytest.raises(
        bindpid.BindPIDException,
        match=(
            "To request a PID for a file, you must also supply a value for"
            " resolve_url_template_file"
        ),
    ):
        bindpid._validate(INVALID_ET_REQUIRED_ARG_DICT)


def test_validate_rejects_unknown_entity_type() -> None:
    with pytest.raises(
        bindpid.BindPIDException,
        match="The value for parameter entity_type must be one of",
    ):
        bindpid._validate(INVALID_ARG_DICT)


def test_validate_accepts_valid_params() -> None:
    assert bindpid._validate(VALID_ARG_DICT) is None
