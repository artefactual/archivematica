#!/usr/bin/env python
"""
Tests for XML metadata management on the METS creation process:

archivematicaCreateMETSMetadataXML.process_xml_metadata()
"""

import re
from importlib.metadata import version
from os.path import abspath
from pathlib import Path
from unittest import mock
from uuid import uuid4

import metsrw
import pytest
import requests
from lxml.etree import parse

from archivematica.dashboard.main.models import File
from archivematica.MCPClient.clientScripts.archivematicaCreateMETSMetadataXML import (
    process_xml_metadata,
)

METADATA_DIR = Path("objects") / "metadata"
TRANSFER_METADATA_DIR = METADATA_DIR / "transfers" / "transfer_a"
TRANSFER_SOURCE_METADATA_CSV = TRANSFER_METADATA_DIR / "source-metadata.csv"
PLACEHOLDER_LOCAL_DIR = "INJECT_LOCAL_DIR_HERE"

DUMMY_EXTERNAL_SCHEMA_URI = "http://foo.com/my.xsd"
DUMMY_EXTERNAL_SCHEMA_URI_0 = "http://foo.com/layer0.xsd"
DUMMY_EXTERNAL_SCHEMA_URI_1 = "http://foo.com/layer1.xsd"
DUMMY_EXTERNAL_SCHEMA_URI_2 = "http://foo.com/layer2.xsd"
DUMMY_EXTERNAL_SCHEMA_URI_3 = "http://foo.com/layer3.xsd"
DUMMY_SCHEMA_NAMESPACE = "http://foo.com/1.0"
DUMMY_SCHEMA_NAMESPACE_0 = "http://foo.com/layer0"
DUMMY_SCHEMA_NAMESPACE_1 = "http://foo.com/layer1"
DUMMY_SCHEMA_NAMESPACE_2 = "http://foo.com/layer2"
DUMMY_SCHEMA_NAMESPACE_3 = "http://foo.com/layer3"

DUMMY_SCHEMAS = {
    "xsd": """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="foo">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="bar" type="xs:string"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
""",
    "dtd": """<!ELEMENT foo (bar)>
<!ELEMENT bar (#PCDATA)>
""",
    "rng": """<element name="foo" xmlns="http://relaxng.org/ns/structure/1.0">
  <oneOrMore>
    <element name="bar">
      <text/>
    </element>
  </oneOrMore>
</element>
""",
    "xsd_imported": f"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns="{DUMMY_SCHEMA_NAMESPACE}" targetNamespace="{DUMMY_SCHEMA_NAMESPACE}">
</xs:schema>
""",
    "xsd_with_ns": f"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="{DUMMY_SCHEMA_NAMESPACE}" elementFormDefault="qualified">
  <xs:element name="foo">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="bar" type="xs:string"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
""",
    "xsd_with_ns_v2": f"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="{DUMMY_SCHEMA_NAMESPACE}" elementFormDefault="qualified">
  <xs:element name="foo">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="bar2" type="xs:string"/>    <!-- modified for v2: simulate a breaking change -->
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
""",
    "xsd_with_nested_imports_layer0": f"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema targetNamespace="{DUMMY_SCHEMA_NAMESPACE_0}"
           xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:layer1="{DUMMY_SCHEMA_NAMESPACE_1}"
           elementFormDefault="qualified">
  <xs:import namespace="{DUMMY_SCHEMA_NAMESPACE_1}" schemaLocation="file://{PLACEHOLDER_LOCAL_DIR}/layer1.xsd"/>
  <xs:element name="foo">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="layer1:bar1"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
""",
    "xsd_with_nested_imports_layer1": f"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema targetNamespace="{DUMMY_SCHEMA_NAMESPACE_1}"
           xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:layer2="{DUMMY_SCHEMA_NAMESPACE_2}"
           elementFormDefault="qualified">
  <xs:import namespace="{DUMMY_SCHEMA_NAMESPACE_2}" schemaLocation="file://{PLACEHOLDER_LOCAL_DIR}/layer2.xsd"/>
  <xs:element name="bar1">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="layer2:bar2"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
""",
    "xsd_with_nested_imports_layer2": f"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema targetNamespace="{DUMMY_SCHEMA_NAMESPACE_2}"
           xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:layer3="{DUMMY_SCHEMA_NAMESPACE_3}"
           elementFormDefault="qualified">
  <xs:import namespace="{DUMMY_SCHEMA_NAMESPACE_3}" schemaLocation="file://{PLACEHOLDER_LOCAL_DIR}/layer3.xsd"/>
  <xs:element name="bar2">
    <xs:complexType>
      <xs:sequence>
        <xs:element ref="layer3:bar3"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
""",
    "xsd_with_nested_imports_layer3": f"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema targetNamespace="{DUMMY_SCHEMA_NAMESPACE_3}"
           xmlns:xs="http://www.w3.org/2001/XMLSchema"
           elementFormDefault="qualified">
  <xs:element name="bar3" type="xs:string"/>
</xs:schema>
""",
    "xsd_with_nested_imports_layer3_circular": f"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema targetNamespace="{DUMMY_SCHEMA_NAMESPACE_3}"
           xmlns:xs="http://www.w3.org/2001/XMLSchema"
           elementFormDefault="qualified">
  <xs:import namespace="{DUMMY_SCHEMA_NAMESPACE_1}" schemaLocation="file://{PLACEHOLDER_LOCAL_DIR}/layer1.xsd"/>
  <xs:element name="bar3" type="xs:string"/>
</xs:schema>
""",
}

VALID_XML = '<?xml version="1.0" encoding="UTF-8"?><foo><bar/></foo>'
INVALID_XML = '<?xml version="1.0" encoding="UTF-8"?><foo/>'
XML_WITHOUT_NAMESPACE = VALID_XML
XML_WITH_NAMESPACE_NO_SCHEMALOCATION = f"""<?xml version="1.0" encoding="UTF-8"?>
<foo xmlns="{DUMMY_SCHEMA_NAMESPACE}">
  <bar/>
</foo>"""
INVALID_XML_WITH_NAMESPACE_NO_SCHEMALOCATION = f"""<?xml version="1.0" encoding="UTF-8"?>
<foo xmlns="{DUMMY_SCHEMA_NAMESPACE}">
  <foofoo/>
</foo>"""
XML_WITH_NAMESPACE_AND_SCHEMALOCATION = f"""<?xml version="1.0" encoding="UTF-8"?>
<foo xmlns="{DUMMY_SCHEMA_NAMESPACE}"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="{DUMMY_SCHEMA_NAMESPACE} {DUMMY_EXTERNAL_SCHEMA_URI}">
  <bar/>
</foo>"""
BROKEN_XML_WITH_NAMESPACE_AND_SCHEMALOCATION = f"""<?xml version="1.0" encoding="UTF-8"?>
<foo xmlns="{DUMMY_SCHEMA_NAMESPACE}"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="{DUMMY_SCHEMA_NAMESPACE} {DUMMY_EXTERNAL_SCHEMA_URI}">
  <-- simulate broken xml: metadata got truncated, structure not well-formed -->
  <bar>
"""
XML_WITH_NESTED_SCHEMA_IMPORTS = f"""<?xml version="1.0" encoding="UTF-8"?>
<layer0:foo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xmlns:layer0="{DUMMY_SCHEMA_NAMESPACE_0}"
     xmlns:layer1="{DUMMY_SCHEMA_NAMESPACE_1}"
     xmlns:layer2="{DUMMY_SCHEMA_NAMESPACE_2}"
     xmlns:layer3="{DUMMY_SCHEMA_NAMESPACE_3}"
     xsi:schemaLocation="{DUMMY_SCHEMA_NAMESPACE} {DUMMY_EXTERNAL_SCHEMA_URI}">
  <layer1:bar1>
    <layer2:bar2>
      <layer3:bar3>foo</layer3:bar3>
    </layer2:bar2>
  </layer1:bar1>
</layer0:foo>
"""
INVALID_XML_WITH_NESTED_SCHEMA_IMPORTS = f"""<?xml version="1.0" encoding="UTF-8"?>
<layer0:foo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xmlns:layer0="{DUMMY_SCHEMA_NAMESPACE_0}"
     xmlns:layer1="{DUMMY_SCHEMA_NAMESPACE_1}"
     xmlns:layer2="{DUMMY_SCHEMA_NAMESPACE_2}"
     xmlns:layer3="{DUMMY_SCHEMA_NAMESPACE_3}"
     xsi:schemaLocation="{DUMMY_SCHEMA_NAMESPACE} {DUMMY_EXTERNAL_SCHEMA_URI}">
  <layer1:bar1>
    <layer2:bar2>
      <!-- simulate invalid nested metadata -->
      <layer3:invalid_node/>
    </layer2:bar2>
  </layer1:bar1>
</layer0:foo>
"""


@pytest.fixture
def make_schema_file(tmp_path):
    def _make_schema_file(schema_type):
        schema_path = tmp_path / (schema_type + "." + schema_type)
        schema_path.write_text(DUMMY_SCHEMAS[schema_type])
        return schema_path

    return _make_schema_file


@pytest.fixture
def sip_directory_path(sip_directory_path):
    transfer_metadata_dir = sip_directory_path / TRANSFER_METADATA_DIR
    transfer_metadata_dir.mkdir(parents=True)
    (transfer_metadata_dir / "valid.xml").write_text(VALID_XML)
    (transfer_metadata_dir / "invalid.xml").write_text(INVALID_XML)

    return sip_directory_path


@pytest.fixture
def make_metadata_file(sip, sip_directory_path):
    def _make_metadata_file(rel_path):
        return File.objects.create(
            uuid=uuid4(),
            sip=sip,
            currentlocation=f"%SIPDirectory%{rel_path}".encode(),
        )

    return _make_metadata_file


@pytest.fixture
def make_mock_fsentry():
    def _make_mock_fsentry(**kwargs):
        mock_fsentry = metsrw.FSEntry(**kwargs)
        mock_fsentry.add_dmdsec = mock.Mock()
        mock_fsentry.delete_dmdsec = mock.Mock()
        mock_fsentry.add_premis_event = mock.Mock()
        return mock_fsentry

    return _make_mock_fsentry


@pytest.fixture
def make_mock_mets(make_mock_fsentry):
    def _make_mock_mets(metadata_file_uuids=None):
        if metadata_file_uuids is None:
            metadata_file_uuids = []
        sip = make_mock_fsentry(label="sip", type="Directory")
        objects = make_mock_fsentry(label="objects", type="Directory")
        directory = make_mock_fsentry(label="directory", type="Directory")
        file_txt = make_mock_fsentry(label="file.txt")
        sip.add_child(objects).add_child(directory).add_child(file_txt)
        files = [sip, objects, directory, file_txt]
        for uuid in metadata_file_uuids:
            files.append(make_mock_fsentry(file_uuid=uuid, use="metadata"))
        mock_mets = mock.Mock()
        mock_mets.all_files.return_value = files
        mock_mets.get_file.side_effect = lambda **kwargs: next(
            (
                f
                for f in files
                if all(v == getattr(f, k, None) for k, v in kwargs.items())
            ),
            None,
        )
        return mock_mets

    return _make_mock_mets


@pytest.fixture
def insert_into_events_mock():
    with mock.patch(
        "archivematica.MCPClient.clientScripts.archivematicaCreateMETSMetadataXML.insertIntoEvents",
        return_value="fake_event",
    ) as result:
        yield result


@pytest.fixture
def create_event_mock():
    with mock.patch(
        "archivematica.MCPClient.clientScripts.archivematicaCreateMETSMetadataXML.createmets2.createEvent",
        return_value="fake_element",
    ) as result:
        yield result


@pytest.fixture
def requests_get():
    # Return a mock response good enough to be parsed as an XML schema.
    with mock.patch(
        "requests.get",
        return_value=mock.Mock(text=DUMMY_SCHEMAS["xsd_imported"]),
    ) as result:
        yield result


@pytest.fixture
def requests_get_error():
    # Simulate an error retrieving an imported schema.
    with mock.patch(
        "requests.get",
        side_effect=requests.RequestException("error"),
    ) as result:
        yield result


@pytest.fixture
def etree_parse():
    # Mocked etree.parse used in the resolver tests that returns None before the first
    # XMLSchema call, which triggers an etree.XMLSchemaParseError exception
    # and forces reparsing the validation schema with a custom etree.Resolver.
    class mock_parse:
        def __init__(self, *args, **kwargs):
            self.call_count = 0

        def __call__(self, *args, **kwargs):
            self.call_count += 1
            # Parse is called first with the metadata XML file
            # and then with the XML validation schema.
            if self.call_count == 2:
                return
            return parse(*args, **kwargs)

    with mock.patch(
        "archivematica.MCPClient.clientScripts.archivematicaCreateMETSMetadataXML.etree.parse",
        mock_parse(),
    ):
        yield


@pytest.fixture
def schema_with_remote_import(tmp_path):
    # Create a schema that imports a remote schema.
    schema = f"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:import namespace="{DUMMY_SCHEMA_NAMESPACE}" schemaLocation="{DUMMY_EXTERNAL_SCHEMA_URI}" />
  <xs:element name="foo">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="bar" type="xs:string"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
"""
    schema_path = tmp_path / "schema.xsd"
    schema_path.write_text(schema)
    return schema_path


@pytest.fixture
def schema_with_local_import(tmp_path):
    # Create a schema that imports a local schema.
    schema = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:import namespace="http://foo.com/1.0" schemaLocation="my.xsd" />
  <xs:element name="foo">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="bar" type="xs:string"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
"""
    schema_path = tmp_path / "schema.xsd"
    schema_path.write_text(schema)

    local_schema = tmp_path / "my.xsd"
    local_schema.write_text(DUMMY_SCHEMAS["xsd_imported"])

    return schema_path


def test_disabled_settings(make_mock_mets):
    mock_mets = make_mock_mets()
    mock_mets, errors = process_xml_metadata(
        mock_mets, "sip_uuid", "sip_path", "sip_type", False
    )
    assert not errors
    mock_mets.all_files.assert_not_called()


@pytest.mark.django_db
def test_no_source_metadata_csv(settings, make_mock_mets, sip, sip_directory_path):
    settings.METADATA_XML_VALIDATION_ENABLED = True
    xml_validation = {"foo": None}
    mock_mets = make_mock_mets()
    mock_mets, errors = process_xml_metadata(
        mock_mets,
        str(sip_directory_path),
        sip.uuid,
        "sip_type",
        xml_validation,
    )
    assert not errors
    mock_mets.all_files.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "xml_file, schema, should_pass",
    [
        ("valid.xml", "xsd", True),
        ("valid.xml", "dtd", True),
        ("valid.xml", "rng", True),
        ("invalid.xml", "xsd", False),
        ("invalid.xml", "dtd", False),
        ("invalid.xml", "rng", False),
    ],
)
def test_validation(
    settings,
    make_metadata_file,
    make_mock_mets,
    make_schema_file,
    sip,
    sip_directory_path,
    insert_into_events_mock,
    create_event_mock,
    xml_file,
    schema,
    should_pass,
):
    schema_uri = str(make_schema_file(schema))
    settings.METADATA_XML_VALIDATION_ENABLED = True
    xml_validation = {"foo": schema_uri}
    source_metadata_csv_contents = f"filename,metadata,type\nobjects,{xml_file},mdtype"
    metadata_csv_path = sip_directory_path / TRANSFER_SOURCE_METADATA_CSV
    metadata_csv_path.write_text(source_metadata_csv_contents)
    metadata_file_rel_path = TRANSFER_METADATA_DIR / xml_file
    metadata_file = make_metadata_file(metadata_file_rel_path)
    mock_mets = make_mock_mets([str(metadata_file.uuid)])
    mock_mets, errors = process_xml_metadata(
        mock_mets,
        sip_directory_path,
        sip.uuid,
        "sip_type",
        xml_validation,
    )
    objects_fsentry = mock_mets.get_file(label="objects")
    metadata_fsentry = mock_mets.get_file(file_uuid=str(metadata_file.uuid))
    if should_pass:
        # Use ANY to avoid comparison with etree.Element, but confirm element tag.
        objects_fsentry.add_dmdsec.assert_called_once_with(
            mock.ANY, "OTHER", othermdtype="mdtype", status="original"
        )
        assert objects_fsentry.add_dmdsec.call_args[0][0].tag == "foo"
    else:
        objects_fsentry.add_dmdsec.assert_not_called()
    event_detail = {
        "type": "metadata",
        "validation-source-type": schema,
        "validation-source": schema_uri,
        "program": "lxml",
        "version": version("lxml"),
    }
    insert_into_events_mock.assert_called_with(
        str(metadata_file.uuid),
        **{
            "eventType": "validation",
            "eventDetail": "; ".join([f'{k}="{v}"' for k, v in event_detail.items()]),
            "eventOutcome": "pass" if should_pass else "fail",
            "eventOutcomeDetailNote": "\n".join([str(err) for err in errors]),
        },
    )
    create_event_mock.assert_called_once_with("fake_event")
    metadata_fsentry.add_premis_event.assert_called_once_with("fake_element")


@pytest.mark.django_db
def test_skipped_validation(
    settings, make_metadata_file, make_mock_mets, sip, sip_directory_path
):
    settings.METADATA_XML_VALIDATION_ENABLED = True
    xml_validation = {"foo": None}
    source_metadata_csv_contents = "filename,metadata,type\nobjects,invalid.xml,mdtype"
    metadata_csv_path = sip_directory_path / TRANSFER_SOURCE_METADATA_CSV
    metadata_csv_path.write_text(source_metadata_csv_contents)
    metadata_file_rel_path = TRANSFER_METADATA_DIR / "invalid.xml"
    metadata_file = make_metadata_file(metadata_file_rel_path)
    mock_mets = make_mock_mets([str(metadata_file.uuid)])
    mock_mets, errors = process_xml_metadata(
        mock_mets,
        sip_directory_path,
        sip.uuid,
        "sip_type",
        xml_validation,
    )
    objects_fsentry = mock_mets.get_file(label="objects")
    metadata_fsentry = mock_mets.get_file(file_uuid=str(metadata_file.uuid))
    assert not errors
    # Use ANY to avoid comparison with etree.Element, but confirm element tag.
    objects_fsentry.add_dmdsec.assert_called_once_with(
        mock.ANY, "OTHER", othermdtype="mdtype", status="original"
    )
    assert objects_fsentry.add_dmdsec.call_args[0][0].tag == "foo"
    metadata_fsentry.add_premis_event.assert_not_called()


@pytest.mark.django_db
def test_validation_schema_errors(
    settings,
    make_metadata_file,
    make_mock_mets,
    make_schema_file,
    sip,
    sip_directory_path,
):
    settings.METADATA_XML_VALIDATION_ENABLED = True
    xml_validation = {"foo": "bad_path.xsd"}
    source_metadata_csv_contents = "filename,metadata,type\nobjects,valid.xml,mdtype"
    metadata_csv_path = sip_directory_path / TRANSFER_SOURCE_METADATA_CSV
    metadata_csv_path.write_text(source_metadata_csv_contents)
    metadata_file_rel_path = TRANSFER_METADATA_DIR / "valid.xml"
    metadata_file = make_metadata_file(metadata_file_rel_path)
    mock_mets = make_mock_mets([str(metadata_file.uuid)])
    mock_mets, errors = process_xml_metadata(
        mock_mets,
        sip_directory_path,
        sip.uuid,
        "sip_type",
        xml_validation,
    )
    assert "XML schema local path bad_path.xsd must be absolute" in errors[0]
    schema_file = make_schema_file("xsd")
    schema_file.write_text("")
    xml_validation = {"foo": str(schema_file)}
    mock_mets, errors = process_xml_metadata(
        mock_mets,
        sip_directory_path,
        sip.uuid,
        "sip_type",
        xml_validation,
    )
    assert "Could not parse schema file" in errors[0]
    unk_schema_file = schema_file.with_suffix(".unk")
    unk_schema_file.write_text("")
    xml_validation = {"foo": str(unk_schema_file)}
    mock_mets, errors = process_xml_metadata(
        mock_mets,
        sip_directory_path,
        sip.uuid,
        "sip_type",
        xml_validation,
    )
    assert "Unknown XML validation schema type: unk" in errors[0]


@pytest.mark.django_db
def test_source_metadata_errors(settings, make_mock_mets, sip, sip_directory_path):
    settings.METADATA_XML_VALIDATION_ENABLED = True
    xml_validation = {"foo": None}
    mock_mets = make_mock_mets()
    metadata_csv_path = sip_directory_path / TRANSFER_SOURCE_METADATA_CSV
    source_metadata_csv_contents = (
        "filename,metadata,type\n"
        + "valid.xml,none\n"
        + ",valid.xml,none\n"
        + "objects,valid.xml\n"
        + "objects,valid.xml,"
    )
    metadata_csv_path.write_text(source_metadata_csv_contents)
    mock_mets, errors = process_xml_metadata(
        mock_mets,
        sip_directory_path,
        sip.uuid,
        "sip_type",
        xml_validation,
    )
    assert len(errors) == 4
    for error in errors:
        assert "missing the filename and/or type" in error
    source_metadata_csv_contents = "filename,metadata,type\nobjects,valid.xml,CUSTOM"
    metadata_csv_path.write_text(source_metadata_csv_contents)
    mock_mets, errors = process_xml_metadata(
        mock_mets,
        sip_directory_path,
        sip.uuid,
        "sip_type",
        xml_validation,
    )
    assert "is using CUSTOM, a reserved type" in errors[0]
    source_metadata_csv_contents = (
        "filename,metadata,type\n"
        + "objects,valid.xml,mdtype\n"
        + "objects,invalid.xml,mdtype"
    )
    metadata_csv_path.write_text(source_metadata_csv_contents)
    mock_mets, errors = process_xml_metadata(
        mock_mets,
        sip_directory_path,
        sip.uuid,
        "sip_type",
        xml_validation,
    )
    assert (
        f"More than one entry in {metadata_csv_path} for path objects and type mdtype"
        in errors[0]
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "validation_key, should_error",
    [
        ("http://foo.com/foo_no_namespace_schema.xsd", False),
        ("http://foo.com/foo_schema.xsd", False),
        ("http://foo.com/foo_namespace.xsd", False),
        ("foo", False),
        ("bar", True),
    ],
)
def test_schema_uri_retrieval(
    settings,
    make_metadata_file,
    make_mock_mets,
    make_schema_file,
    sip,
    sip_directory_path,
    validation_key,
    should_error,
):
    schema_path = str(make_schema_file("xsd"))
    settings.METADATA_XML_VALIDATION_ENABLED = True
    xml_validation = {validation_key: schema_path}
    source_metadata_csv_contents = "filename,metadata,type\nobjects,valid.xml,mdtype"
    metadata_csv_path = sip_directory_path / TRANSFER_SOURCE_METADATA_CSV
    metadata_csv_path.write_text(source_metadata_csv_contents)
    metadata_file_contents = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        + '<foo:foo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        + 'xmlns:foo="http://foo.com/foo_namespace.xsd" '
        + 'xsi:schemaLocation="http://foo.com/foo http://foo.com/foo_schema.xsd" '
        + 'xsi:noNamespaceSchemaLocation="http://foo.com/foo_no_namespace_schema.xsd"/>'
    )
    metadata_file_rel_path = TRANSFER_METADATA_DIR / "valid.xml"
    metadata_file = make_metadata_file(metadata_file_rel_path)
    metadata_file_path = sip_directory_path / metadata_file_rel_path
    metadata_file_path.write_text(metadata_file_contents)
    mock_mets = make_mock_mets([str(metadata_file.uuid)])
    mock_mets, errors = process_xml_metadata(
        mock_mets,
        sip_directory_path,
        sip.uuid,
        "sip_type",
        xml_validation,
    )
    metadata_fsentry = mock_mets.get_file(file_uuid=str(metadata_file.uuid))
    if should_error:
        assert "XML validation schema not found for keys:" in str(errors[0])
        metadata_fsentry.add_premis_event.assert_not_called()
    else:
        metadata_fsentry.add_premis_event.assert_called()


@pytest.mark.django_db
def test_multiple_dmdsecs(
    settings, make_metadata_file, make_mock_mets, sip, sip_directory_path
):
    mdkeys = ["foo", "foo_2", "foo_3"]
    settings.METADATA_XML_VALIDATION_ENABLED = True
    xml_validation = {}
    csv_contents = "filename,metadata,type\n"
    metadata_file_uuids = []
    for mdkey in mdkeys:
        xml_validation[mdkey] = None
        csv_contents += f"objects,{mdkey}.xml,{mdkey}\n"
        csv_contents += f"objects/directory,{mdkey}.xml,{mdkey}\n"
        csv_contents += f"objects/directory/file.txt,{mdkey}.xml,{mdkey}\n"
        metadata_file_rel_path = TRANSFER_METADATA_DIR / f"{mdkey}.xml"
        metadata_file = make_metadata_file(metadata_file_rel_path)
        metadata_file_path = sip_directory_path / metadata_file_rel_path
        metadata_file_path.write_text(
            f'<?xml version="1.0" encoding="UTF-8"?><{mdkey}/>'
        )
        metadata_file_uuids.append(str(metadata_file.uuid))
    metadata_csv_path = sip_directory_path / TRANSFER_SOURCE_METADATA_CSV
    metadata_csv_path.write_text(csv_contents)
    mock_mets = make_mock_mets(metadata_file_uuids)
    mock_mets, errors = process_xml_metadata(
        mock_mets,
        sip_directory_path,
        sip.uuid,
        "sip_type",
        xml_validation,
    )
    assert not errors
    for label in ["objects", "directory", "file.txt"]:
        fsentry = mock_mets.get_file(label=label)
        assert fsentry.add_dmdsec.call_count == 3


@pytest.mark.django_db
def test_reingest(
    settings,
    make_schema_file,
    make_metadata_file,
    make_mock_mets,
    sip,
    sip_directory_path,
):
    settings.METADATA_XML_VALIDATION_ENABLED = True
    xml_validation = {"foo": str(make_schema_file("xsd"))}
    source_metadata_csv_contents = "filename,metadata,type\nobjects,valid.xml,mdtype"
    metadata_csv_path = sip_directory_path / METADATA_DIR / "source-metadata.csv"
    metadata_csv_path.write_text(source_metadata_csv_contents)
    metadata_file_rel_path = METADATA_DIR / "valid.xml"
    metadata_file = make_metadata_file(metadata_file_rel_path)
    (sip_directory_path / metadata_file_rel_path).write_text(VALID_XML)
    mock_mets = make_mock_mets([str(metadata_file.uuid)])
    mock_mets, errors = process_xml_metadata(
        mock_mets, sip_directory_path, sip.uuid, "REIN", xml_validation
    )
    objects_fsentry = mock_mets.get_file(label="objects")
    metadata_fsentry = mock_mets.get_file(file_uuid=str(metadata_file.uuid))
    assert not errors
    # Use ANY to avoid comparison with etree.Element, but confirm element tag.
    objects_fsentry.add_dmdsec.assert_called_once_with(
        mock.ANY, "OTHER", othermdtype="mdtype", status="update"
    )
    assert objects_fsentry.add_dmdsec.call_args[0][0].tag == "foo"
    metadata_fsentry.add_premis_event.assert_called()
    source_metadata_csv_contents = "filename,metadata,type\nobjects,,mdtype"
    metadata_csv_path.write_text(source_metadata_csv_contents)
    mock_mets, errors = process_xml_metadata(
        mock_mets, sip_directory_path, sip.uuid, "REIN", xml_validation
    )
    assert not errors
    objects_fsentry.delete_dmdsec.assert_called_with("OTHER", "mdtype")


@pytest.mark.django_db
def test_resolver(
    settings,
    make_metadata_file,
    make_mock_mets,
    sip,
    sip_directory_path,
    etree_parse,
    requests_get,
    schema_with_remote_import,
):
    settings.METADATA_XML_VALIDATION_ENABLED = True
    xml_validation = {"foo": str(schema_with_remote_import)}
    source_metadata_csv_contents = "filename,metadata,type\nobjects,valid.xml,mdtype"
    metadata_csv_path = sip_directory_path / TRANSFER_SOURCE_METADATA_CSV
    metadata_csv_path.write_text(source_metadata_csv_contents)
    metadata_file_rel_path = TRANSFER_METADATA_DIR / "valid.xml"
    metadata_file = make_metadata_file(metadata_file_rel_path)
    mock_mets = make_mock_mets([str(metadata_file.uuid)])
    mock_mets, errors = process_xml_metadata(
        mock_mets,
        sip_directory_path,
        sip.uuid,
        "sip_type",
        xml_validation,
    )
    assert not errors
    requests_get.assert_called_once_with(DUMMY_EXTERNAL_SCHEMA_URI)


@pytest.mark.django_db
def test_resolver_with_requests_error(
    settings,
    make_metadata_file,
    make_mock_mets,
    sip,
    sip_directory_path,
    etree_parse,
    requests_get_error,
    schema_with_remote_import,
):
    settings.METADATA_XML_VALIDATION_ENABLED = True
    xml_validation = {"foo": str(schema_with_remote_import)}
    source_metadata_csv_contents = "filename,metadata,type\nobjects,valid.xml,mdtype"
    metadata_csv_path = sip_directory_path / TRANSFER_SOURCE_METADATA_CSV
    metadata_csv_path.write_text(source_metadata_csv_contents)
    metadata_file_rel_path = TRANSFER_METADATA_DIR / "valid.xml"
    metadata_file = make_metadata_file(metadata_file_rel_path)
    mock_mets = make_mock_mets([str(metadata_file.uuid)])
    mock_mets, errors = process_xml_metadata(
        mock_mets,
        sip_directory_path,
        sip.uuid,
        "sip_type",
        xml_validation,
    )
    assert not errors


@pytest.mark.django_db
def test_resolver_with_local_import(
    settings,
    make_metadata_file,
    make_mock_mets,
    sip,
    sip_directory_path,
    etree_parse,
    requests_get,
    schema_with_local_import,
):
    settings.METADATA_XML_VALIDATION_ENABLED = True
    xml_validation = {"foo": str(schema_with_local_import)}
    source_metadata_csv_contents = "filename,metadata,type\nobjects,valid.xml,mdtype"
    metadata_csv_path = sip_directory_path / TRANSFER_SOURCE_METADATA_CSV
    metadata_csv_path.write_text(source_metadata_csv_contents)
    metadata_file_rel_path = TRANSFER_METADATA_DIR / "valid.xml"
    metadata_file = make_metadata_file(metadata_file_rel_path)
    mock_mets = make_mock_mets([str(metadata_file.uuid)])
    mock_mets, errors = process_xml_metadata(
        mock_mets,
        sip_directory_path,
        sip.uuid,
        "sip_type",
        xml_validation,
    )
    assert not errors
    requests_get.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "xml, schemas, xml_validation_factory, should_pass, expected_error",
    [
        # scenario 01 - XML metadata without namespace
        #               XML_VALIDATION provides schema based on root element node
        (
            XML_WITHOUT_NAMESPACE,
            {"custom.xsd": DUMMY_SCHEMAS["xsd"]},
            lambda schema_paths: {"foo": str(schema_paths["custom.xsd"])},
            True,
            None,
        ),
        # scenario 02: XML metadata with namespace, but no schemaLocation hint
        #              XML_VALIDATION provides schema based on namespace
        (
            XML_WITH_NAMESPACE_NO_SCHEMALOCATION,
            {"custom.xsd": DUMMY_SCHEMAS["xsd_with_ns"]},
            lambda schema_paths: {
                f"{DUMMY_SCHEMA_NAMESPACE}": str(schema_paths["custom.xsd"])
            },
            True,
            None,
        ),
        # scenario 03: XML metadata with namespace & schemaLocation hint
        #              XML_VALIDATION provides schema based on namespace, overrules schemaLocation hint
        (
            XML_WITH_NAMESPACE_AND_SCHEMALOCATION,
            {"custom.xsd": DUMMY_SCHEMAS["xsd_with_ns"]},
            lambda schema_paths: {
                f"{DUMMY_SCHEMA_NAMESPACE}": str(schema_paths["custom.xsd"])
            },
            True,
            None,
        ),
        # scenario 04: XML metadata with namespace & schemaLocation hint, but metadata is invalid
        #              XML_VALIDATION forces validation skip, overrules schemaLocation hint
        (
            XML_WITH_NAMESPACE_AND_SCHEMALOCATION,
            {},
            lambda schema_paths: {f"{DUMMY_SCHEMA_NAMESPACE}": None},
            True,
            None,
        ),
        # scenario 05: XML metadata is missing, empty file
        #              parsing metadata should fail gracefully
        (
            "",
            {},
            lambda schema_paths: True,  # just enable xml validation
            False,
            "Could not parse metadata file",
        ),
        # scenario 06: XML metadata is broken, structure not well-formed
        #              parsing metadata should fail gracefully
        (
            BROKEN_XML_WITH_NAMESPACE_AND_SCHEMALOCATION,
            {"custom.xsd": DUMMY_SCHEMAS["xsd_with_ns"]},
            lambda schema_paths: {
                f"{DUMMY_SCHEMA_NAMESPACE}": str(schema_paths["custom.xsd"])
            },
            False,
            "Could not parse metadata file",
        ),
        # scenario 07: XML metadata with namespace, but no schemaLocation hint, metadata is invalid
        #              XML_VALIDATION provides schema based on namespace, metadata invalid against user provided schema
        (
            INVALID_XML_WITH_NAMESPACE_NO_SCHEMALOCATION,
            {"custom.xsd": DUMMY_SCHEMAS["xsd_with_ns"]},
            lambda schema_paths: {
                f"{DUMMY_SCHEMA_NAMESPACE}": str(schema_paths["custom.xsd"])
            },
            False,
            "foofoo.*element is not expected",
        ),
        # scenario 08: XML metadata with namespace & schemaLocation hint, metadata is valid against schemaLocation hint
        #              XML_VALIDATION overrules schemaLocation hint, metadata invalid against user provided schema
        (
            XML_WITH_NAMESPACE_AND_SCHEMALOCATION,
            {"custom.xsd": DUMMY_SCHEMAS["xsd_with_ns_v2"]},
            lambda schema_paths: {
                f"{DUMMY_SCHEMA_NAMESPACE}": str(schema_paths["custom.xsd"])
            },
            False,
            "bar[^2].*element is not expected",
        ),
        # scenario 09: XML metadata with namespace
        #              XML_VALIDATION provides schema based on namespace, but schema path is not absolute
        (
            XML_WITH_NAMESPACE_NO_SCHEMALOCATION,
            {"custom.xsd": DUMMY_SCHEMAS["xsd_with_ns"]},
            lambda schema_paths: {f"{DUMMY_SCHEMA_NAMESPACE}": "relative_path.xsd"},
            False,
            "schema local path.*must be absolute",
        ),
        # scenario 10: XML metadata with namespace
        #              XML_VALIDATION provides schema based on namespace, but schema path is not accessable, parsing schema should fail gracefully
        (
            XML_WITH_NAMESPACE_NO_SCHEMALOCATION,
            {"custom.xsd": DUMMY_SCHEMAS["xsd_with_ns"]},
            lambda schema_paths: {
                f"{DUMMY_SCHEMA_NAMESPACE}": abspath("does_not_exist.xsd")
            },
            False,
            "Could not parse schema file|No such file or directory",
        ),
        # scenario 11: XML metadata without namespace
        #              XML_VALIDATION does not provide a schema matching the root node
        (
            VALID_XML,
            {"custom.xsd": DUMMY_SCHEMAS["xsd_with_ns"]},
            lambda schema_paths: {
                "not_dummy_schema_namespace": str(schema_paths["custom.xsd"])
            },
            False,
            "XML validation schema not found for keys",
        ),
        # scenario 12: XML metadata with namespace, but namespace has multiple levels of imports
        #              XML_VALIDATION does only provide schema for the initial namespace, missing schemas are handled by lxml using schemaLocation
        (
            XML_WITH_NESTED_SCHEMA_IMPORTS,
            {
                "layer0.xsd": DUMMY_SCHEMAS["xsd_with_nested_imports_layer0"],
                "layer1.xsd": DUMMY_SCHEMAS["xsd_with_nested_imports_layer1"],
                "layer2.xsd": DUMMY_SCHEMAS["xsd_with_nested_imports_layer2"],
                "layer3.xsd": DUMMY_SCHEMAS["xsd_with_nested_imports_layer3"],
            },
            lambda schema_paths: {
                f"{DUMMY_SCHEMA_NAMESPACE_0}": str(schema_paths["layer0.xsd"])
            },  # XML_VALIDATION only handles layer 0 schema
            True,
            None,
        ),
        # scenario 13: XML metadata with namespace, but namespace has multiple layers of imports, some circular
        #              XML_VALIDATION does only provide schema for the initial namespace, missing schemas are handled by lxml using schemaLocation
        (
            XML_WITH_NESTED_SCHEMA_IMPORTS,
            {
                "layer0.xsd": DUMMY_SCHEMAS["xsd_with_nested_imports_layer0"],
                "layer1.xsd": DUMMY_SCHEMAS["xsd_with_nested_imports_layer1"],
                "layer2.xsd": DUMMY_SCHEMAS["xsd_with_nested_imports_layer2"],
                "layer3.xsd": DUMMY_SCHEMAS["xsd_with_nested_imports_layer3_circular"],
            },
            lambda schema_paths: {
                f"{DUMMY_SCHEMA_NAMESPACE_0}": str(schema_paths["layer0.xsd"])
            },  # XML_VALIDATION only handles layer0
            True,
            None,
        ),
        # scenario 14: XML metadata with namespace, but namespace has multiple layers of imports, metadata is invalid
        #              XML_VALIDATION does only provide schema for the initial namespace, missing schemas are handled by lxml using schemaLocation
        (
            INVALID_XML_WITH_NESTED_SCHEMA_IMPORTS,
            {
                "layer0.xsd": DUMMY_SCHEMAS["xsd_with_nested_imports_layer0"],
                "layer1.xsd": DUMMY_SCHEMAS["xsd_with_nested_imports_layer1"],
                "layer2.xsd": DUMMY_SCHEMAS["xsd_with_nested_imports_layer2"],
                "layer3.xsd": DUMMY_SCHEMAS["xsd_with_nested_imports_layer3"],
            },
            lambda schema_paths: {
                f"{DUMMY_SCHEMA_NAMESPACE_0}": str(schema_paths["layer0.xsd"])
            },  # XML_VALIDATION only handles layer0
            False,
            "invalid_node.*element is not expected",
        ),
    ],
)
def test_validation_in_additional_xml_scenarios(
    settings,
    make_metadata_file,
    make_mock_mets,
    sip,
    sip_directory_path,
    tmp_path,
    xml,
    schemas,
    xml_validation_factory,
    should_pass,
    expected_error,
):
    # create xml metadata file to be validated
    xml_file = "custom.xml"
    xml_file_path = sip_directory_path / TRANSFER_METADATA_DIR / xml_file
    xml = re.sub(
        f"{PLACEHOLDER_LOCAL_DIR}", f"{tmp_path}", xml
    )  # inject tmp_path if placeholder was set
    xml_file_path.write_text(xml)

    # create local schema files required for scenario
    schema_paths = {}
    for name, content in schemas.items():
        schema_path = tmp_path / f"{name}"
        content = re.sub(
            f"{PLACEHOLDER_LOCAL_DIR}", f"{tmp_path}", content
        )  # inject tmp_path into <import/> nodes, so lxml can find it
        schema_path.write_text(content)
        schema_paths[name] = (
            schema_path  # map schema name to its path for xml_validation_factory
        )

    # generate XML_VALIDATION dictionary utilizing the created schema files
    xml_validation = xml_validation_factory(schema_paths)

    # enable internal xml validation with lxml
    settings.METADATA_XML_VALIDATION_ENABLED = True

    # create source-metadata.csv
    source_metadata_csv_contents = f"filename,metadata,type\nobjects,{xml_file},mdtype"
    metadata_csv_path = sip_directory_path / TRANSFER_SOURCE_METADATA_CSV
    metadata_csv_path.write_text(source_metadata_csv_contents)

    # mock package METS
    metadata_file_rel_path = TRANSFER_METADATA_DIR / xml_file
    metadata_file = make_metadata_file(metadata_file_rel_path)
    mock_mets = make_mock_mets([str(metadata_file.uuid)])

    # test
    mock_mets, errors = process_xml_metadata(
        mock_mets,
        sip_directory_path,
        sip.uuid,
        "sip_type",
        xml_validation,
    )
    if should_pass:
        assert not errors, (
            f"Scenario should have passed without errors, but: '{errors}'"
        )
    else:
        assert errors, "Scenario should have failed with errors, but has none."
        error_found = any(re.search(expected_error, str(err)) for err in errors)
        assert error_found, (
            f"Scenario did not contain expected error '{expected_error}', only: '{errors}'"
        )
