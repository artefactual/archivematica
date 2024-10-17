#!/usr/bin/env python
#
# This file is part of Archivematica.
#
# Copyright 2010-2021 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica. If not, see <http://www.gnu.org/licenses/>.
"""Management of XML metadata files."""

import csv
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

import create_mets_v2 as createmets2
import namespaces as ns
import requests
from databaseFunctions import insertIntoEvents
from django.core.exceptions import ValidationError
from importlib_metadata import version
from lxml import etree
from main import models


def process_xml_metadata(mets, sip_dir, sip_uuid, sip_type, xml_validation):
    if not xml_validation:
        return mets, []
    xml_metadata_mapping, xml_metadata_errors = _get_xml_metadata_mapping(
        sip_dir, reingest="REIN" in sip_type
    )
    if not xml_metadata_mapping:
        return mets, xml_metadata_errors
    for fsentry in mets.all_files():
        if fsentry.use != "original" and fsentry.type != "Directory":
            continue
        path = fsentry.get_path()
        if path not in xml_metadata_mapping:
            continue
        for xml_type, xml_path in xml_metadata_mapping[path].items():
            if not xml_path:
                fsentry.delete_dmdsec("OTHER", xml_type)
                continue
            tree = etree.parse(str(xml_path))
            try:
                schema_uri = _get_schema_uri(tree, xml_validation)
            except ValueError as err:
                xml_metadata_errors.append(err)
                continue
            if schema_uri:
                xml_rel_path = xml_path.relative_to(sip_dir)
                try:
                    metadata_file = models.File.objects.get(
                        sip_id=sip_uuid,
                        currentlocation=f"%SIPDirectory%{xml_rel_path}".encode(),
                    )
                except (models.File.DoesNotExist, ValidationError):
                    xml_metadata_errors.append(f"No uuid for file: {xml_rel_path}")
                    continue
                valid, errors = _validate_xml(tree, schema_uri)
                _add_validation_event(
                    mets, str(metadata_file.uuid), schema_uri, valid, errors
                )
                if not valid:
                    xml_metadata_errors += errors
                    continue
            fsentry.add_dmdsec(
                tree.getroot(),
                "OTHER",
                othermdtype=xml_type,
                status="update" if "REIN" in sip_type else "original",
            )
    return mets, xml_metadata_errors


def _get_xml_metadata_mapping(sip_path, reingest=False):
    """Get a mapping of files/dirs in the SIP and their related XML files.

    On initial ingests, it looks for such mapping in source-metadata.csv
    files located on each transfer metadata folder. On reingest it only
    considers the source-metadata.csv file in the main metadata folder.

    Example source-metadata.csv:

    filename,metadata,type
    objects,objects_metadata.xml,metadata_type
    objects/dir,dir_metadata.xml,metadata_type
    objects/dir/file.pdf,file_metadata_a.xml,metadata_type_a
    objects/dir/file.pdf,file_metadata_b.xml,metadata_type_b

    Example dict returned:

    {
        "objects": {"metadata_type": Path("/path/to/objects_metadata.xml")},
        "objects/dir": {"metadata_type": Path("/path/to/dir_metadata.xml")},
        "objects/dir/file.pdf": {
            "metadata_type_a": Path("/path/to/file_metadata_a.xml"),
            "metadata_type_b": Path("/path/to/file_metadata_b.xml"),
        },
    }

    :param str sip_path: Absolute path to the SIP.
    :param bool reingest: Boolean to indicate if it's a reingest.
    :return dict, list: Dictionary with File/dir path -> dict of type -> metadata
    file pathlib Path, and list with errors (if a CSV row is missing the filename
    or type, or if there is more than one entry for the same filename and type).
    """
    mapping = {}
    errors = []
    source_metadata_paths = []
    metadata_path = Path(sip_path) / "objects" / "metadata"
    transfers_metadata_path = metadata_path / "transfers"
    if reingest:
        source_metadata_paths.append(metadata_path / "source-metadata.csv")
    elif transfers_metadata_path.is_dir():
        for dir_ in transfers_metadata_path.iterdir():
            source_metadata_paths.append(dir_ / "source-metadata.csv")
    for source_metadata_path in source_metadata_paths:
        if not source_metadata_path.is_file():
            continue
        with source_metadata_path.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not all(k in row and row[k] for k in ["filename", "type"]):
                    errors.append(
                        f"A row in {source_metadata_path} is missing the filename and/or type"
                    )
                    continue
                if row["type"] == "CUSTOM":
                    errors.append(
                        f"A row in {source_metadata_path} is using CUSTOM, a reserved type"
                    )
                    continue
                if row["filename"] not in mapping:
                    mapping[row["filename"]] = {}
                elif row["type"] in mapping[row["filename"]]:
                    errors.append(
                        "More than one entry in {} for path {} and type {}".format(
                            source_metadata_path, row["filename"], row["type"]
                        )
                    )
                    continue
                if row["metadata"]:
                    row["metadata"] = source_metadata_path.parent / row["metadata"]
                mapping[row["filename"]][row["type"]] = row["metadata"]
    return mapping, errors


def _get_schema_uri(tree, xml_validation):
    key = None
    checked_keys = []
    schema_location = tree.xpath(
        "/*/@xsi:noNamespaceSchemaLocation", namespaces={"xsi": ns.xsiNS}
    )
    if schema_location:
        key = schema_location[0].strip()
        checked_keys.append(key)
    if not key or key not in xml_validation:
        schema_location = tree.xpath(
            "/*/@xsi:schemaLocation", namespaces={"xsi": ns.xsiNS}
        )
        if schema_location:
            key = schema_location[0].strip().split()[-1]
            checked_keys.append(key)
    if not key or key not in xml_validation:
        key = tree.xpath("namespace-uri(.)")
        checked_keys.append(key)
    if not key or key not in xml_validation:
        key = tree.xpath("local-name(.)")
        checked_keys.append(key)
    if not key or key not in xml_validation:
        raise ValueError(f"XML validation schema not found for keys: {checked_keys}")
    return xml_validation[key]


class Resolver(etree.Resolver):
    def resolve(self, url, id, context):
        url_scheme = urlparse(url).scheme
        if url_scheme in ("http", "https"):
            try:
                response = requests.get(url)
            except requests.RequestException:
                return super().resolve(url, id, context)
            else:
                return self.resolve_string(response.text, context)
        else:
            return super().resolve(url, id, context)


def _validate_xml(tree, schema_uri):
    schema_type = schema_uri.split(".")[-1]
    parse_result = urlparse(schema_uri)
    if not parse_result.scheme and schema_uri == parse_result.path:
        # URI is a local file
        try:
            schema_uri = Path(schema_uri).as_uri()
        except ValueError:
            return False, [f"XML schema local path {schema_uri} must be absolute"]
    try:
        with urlopen(schema_uri) as f:
            if schema_type == "dtd":
                schema = etree.DTD(f)
            elif schema_type == "xsd":
                schema_contents = etree.parse(f)
                try:
                    schema = etree.XMLSchema(schema_contents)
                except etree.XMLSchemaParseError:
                    # Try parsing the schema again with a custom resolver
                    parser = etree.XMLParser()
                    resolver = Resolver()
                    parser.resolvers.add(resolver)
                    with urlopen(schema_uri) as f2:
                        schema_contents = etree.parse(f2, parser)
                    schema = etree.XMLSchema(schema_contents)
            elif schema_type == "rng":
                schema_contents = etree.parse(f)
                schema = etree.RelaxNG(schema_contents)
            else:
                return False, [f"Unknown XML validation schema type: {schema_type}"]
    except etree.LxmlError as err:
        return False, [f"Could not parse schema file: {schema_uri}", err]
    if not schema.validate(tree):
        return False, schema.error_log
    return True, []


def _add_validation_event(mets, file_uuid, schema_uri, valid, errors):
    event_detail = {
        "type": "metadata",
        "validation-source-type": schema_uri.split(".")[-1],
        "validation-source": schema_uri,
        "program": "lxml",
        "version": version("lxml"),
    }
    event_data = {
        "eventType": "validation",
        "eventDetail": "; ".join([f'{k}="{v}"' for k, v in event_detail.items()]),
        "eventOutcome": "pass" if valid else "fail",
        "eventOutcomeDetailNote": "\n".join([str(err) for err in errors]),
    }
    event_object = insertIntoEvents(file_uuid, **event_data)
    metadata_fsentry = mets.get_file(file_uuid=str(file_uuid))
    metadata_fsentry.add_premis_event(createmets2.createEvent(event_object))
