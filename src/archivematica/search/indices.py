import logging
import sys

from archivematica.search.constants import DEPTH_LIMIT
from archivematica.search.constants import DOC_TYPE
from archivematica.search.constants import ES_FIELD_ACCESSION_IDS
from archivematica.search.constants import ES_FIELD_AICID
from archivematica.search.constants import ES_FIELD_CREATED
from archivematica.search.constants import ES_FIELD_FILECOUNT
from archivematica.search.constants import ES_FIELD_LOCATION
from archivematica.search.constants import ES_FIELD_NAME
from archivematica.search.constants import ES_FIELD_SIZE
from archivematica.search.constants import ES_FIELD_STATUS
from archivematica.search.constants import ES_FIELD_UUID
from archivematica.search.constants import INDEXES
from archivematica.search.constants import TOTAL_FIELDS_LIMIT

logger = logging.getLogger("archivematica.search")


def create_indexes_if_needed(client, indexes):
    """Checks if the indexes passed exist in the client.

    Otherwise, creates the missing ones with their settings and mappings.
    """
    if client.indices.exists(index=",".join(indexes)):
        logger.info("All indexes already created.")
        return
    for index in indexes:
        if index not in INDEXES:
            logger.warning('Index "%s" not recognized. Skipping.', index)
            continue
        # Call get index body functions below for each index
        body = getattr(sys.modules[__name__], "_get_%s_index_body" % index)()
        logger.info('Creating "%s" index ...', index)
        client.indices.create(index, body=body, ignore=400)
        logger.info("Index created.")


def _get_index_settings():
    """Returns a dictionary with the settings used in all indexes."""
    return {
        "index": {
            "mapping": {
                "total_fields": {"limit": TOTAL_FIELDS_LIMIT},
                "depth": {"limit": DEPTH_LIMIT},
            },
            "analysis": {
                "analyzer": {
                    # Use the char_group tokenizer to split paths and filenames,
                    # including file extensions, which avoids the overhead of
                    # the pattern tokenizer.
                    "file_path_and_name": {
                        "tokenizer": "char_tokenizer",
                        "filter": ["lowercase"],
                    }
                },
                "tokenizer": {
                    "char_tokenizer": {
                        "type": "char_group",
                        "tokenize_on_chars": ["-", "_", ".", "/", "\\"],
                    }
                },
            },
        }
    }


def _get_aips_index_body():
    """Get settings and mappings for `aips` index.

    The mapping is dynamic and not a full representation of the final documents.
    For example, the AIP directories AMD and DMD sections are parsed from the
    METS file and added to a `transferMetadata` field.
    """
    return {
        "settings": _get_index_settings(),
        "mappings": {
            DOC_TYPE: {
                "date_detection": False,
                "properties": {
                    ES_FIELD_NAME: {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "file_path_and_name",
                    },
                    ES_FIELD_SIZE: {"type": "double"},
                    ES_FIELD_UUID: {"type": "keyword"},
                    ES_FIELD_ACCESSION_IDS: {"type": "keyword"},
                    ES_FIELD_STATUS: {"type": "keyword"},
                    ES_FIELD_FILECOUNT: {"type": "integer"},
                    ES_FIELD_LOCATION: {"type": "keyword"},
                },
            }
        },
    }


def _get_aipfiles_index_body():
    """Get settings and mappings for `aipfiles` index.

    The mapping is dynamic and not a full representation of the final documents.
    For example, the files AMD and DMD sections are parsed from the METS file
    and added to a `METS` field.
    """
    return {
        "settings": _get_index_settings(),
        "mappings": {
            DOC_TYPE: {
                "date_detection": False,
                "properties": {
                    "sipName": {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "file_path_and_name",
                    },
                    "AIPUUID": {"type": "keyword"},
                    "FILEUUID": {"type": "keyword"},
                    "isPartOf": {"type": "keyword"},
                    ES_FIELD_AICID: {"type": "keyword"},
                    "indexedAt": {"type": "double"},
                    "filePath": {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "file_path_and_name",
                    },
                    "fileExtension": {"type": "text"},
                    "origin": {"type": "text"},
                    "identifiers": {"type": "keyword"},
                    "accessionid": {"type": "keyword"},
                    ES_FIELD_STATUS: {"type": "keyword"},
                },
            }
        },
    }


def _get_transfers_index_body():
    return {
        "settings": _get_index_settings(),
        "mappings": {
            DOC_TYPE: {
                "properties": {
                    ES_FIELD_NAME: {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "file_path_and_name",
                    },
                    ES_FIELD_STATUS: {"type": "text"},
                    "ingest_date": {"type": "date", "format": "dateOptionalTime"},
                    ES_FIELD_SIZE: {"type": "long"},
                    ES_FIELD_FILECOUNT: {"type": "integer"},
                    ES_FIELD_UUID: {"type": "keyword"},
                    "accessionid": {"type": "keyword"},
                    "pending_deletion": {"type": "boolean"},
                }
            }
        },
    }


def _get_transferfiles_index_body():
    return {
        "settings": _get_index_settings(),
        "mappings": {
            DOC_TYPE: {
                "properties": {
                    "filename": {
                        "type": "text",
                        "fields": {"raw": {"type": "keyword"}},
                        "analyzer": "file_path_and_name",
                    },
                    "relative_path": {"type": "text", "analyzer": "file_path_and_name"},
                    "fileuuid": {"type": "keyword"},
                    "sipuuid": {"type": "keyword"},
                    "accessionid": {"type": "keyword"},
                    ES_FIELD_STATUS: {"type": "keyword"},
                    "origin": {"type": "keyword"},
                    "ingestdate": {"type": "date", "format": "dateOptionalTime"},
                    # METS.xml files in transfers sent to backlog will have ''
                    # as their modification_date value. This can cause a
                    # failure in certain cases, see:
                    # https://github.com/artefactual/archivematica/issues/719.
                    # For this reason, we specify the type and format here and
                    # ignore malformed values like ''.
                    "modification_date": {
                        "type": "date",
                        "format": "dateOptionalTime",
                        "ignore_malformed": True,
                    },
                    ES_FIELD_CREATED: {"type": "double"},
                    ES_FIELD_SIZE: {"type": "double"},
                    "tags": {"type": "keyword"},
                    "file_extension": {"type": "keyword"},
                    "bulk_extractor_reports": {"type": "keyword"},
                    "format": {
                        "type": "nested",
                        "properties": {
                            "puid": {"type": "keyword"},
                            "format": {"type": "text"},
                            "group": {"type": "text"},
                        },
                    },
                    "pending_deletion": {"type": "boolean"},
                }
            }
        },
    }
