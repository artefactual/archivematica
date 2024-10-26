#!/usr/bin/env python
"""
Tests for XML metadata management on the METS creation process:

archivematicaCreateMETSMetadataXML.process_xml_metadata()
"""

from pathlib import Path
from unittest import mock
from uuid import uuid4

import metsrw
import pytest
import requests
from archivematicaCreateMETSMetadataXML import process_xml_metadata
from importlib_metadata import version
from lxml.etree import parse
from main.models import File

METADATA_DIR = Path("objects") / "metadata"
TRANSFER_METADATA_DIR = METADATA_DIR / "transfers" / "transfer_a"
TRANSFER_SOURCE_METADATA_CSV = TRANSFER_METADATA_DIR / "source-metadata.csv"
VALID_XML = '<?xml version="1.0" encoding="UTF-8"?><foo><bar/></foo>'
INVALID_XML = '<?xml version="1.0" encoding="UTF-8"?><foo/>'
SCHEMAS = {
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
}
IMPORTED_SCHEMA = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns="http://foo.com/1.0" targetNamespace="http://foo.com/1.0">
</xs:schema>"""


@pytest.fixture
def make_schema_file(tmp_path):
    def _make_schema_file(schema_type):
        schema_path = tmp_path / (schema_type + "." + schema_type)
        schema_path.write_text(SCHEMAS[schema_type])
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
        "archivematicaCreateMETSMetadataXML.insertIntoEvents",
        return_value="fake_event",
    ) as result:
        yield result


@pytest.fixture
def create_event_mock():
    with mock.patch(
        "archivematicaCreateMETSMetadataXML.createmets2.createEvent",
        return_value="fake_element",
    ) as result:
        yield result


@pytest.fixture
def requests_get():
    # Return a mock response good enough to be parsed as an XML schema.
    with mock.patch(
        "requests.get",
        return_value=mock.Mock(text=IMPORTED_SCHEMA),
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
        "archivematicaCreateMETSMetadataXML.etree.parse",
        mock_parse(),
    ):
        yield


@pytest.fixture
def schema_with_remote_import(tmp_path):
    # Create a schema that imports a remote schema.
    schema = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:import namespace="http://foo.com/1.0" schemaLocation="http://foo.com/my.xsd" />
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
    local_schema.write_text(IMPORTED_SCHEMA)

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
        # Use ANY to avoid comparision with etree.Element, but confirm element tag.
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
    # Use ANY to avoid comparision with etree.Element, but confirm element tag.
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
    # Use ANY to avoid comparision with etree.Element, but confirm element tag.
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
    requests_get.assert_called_once_with("http://foo.com/my.xsd")


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
