import logging

from archivematica.search.constants import AIP_FILES_INDEX
from archivematica.search.constants import AIPS_INDEX
from archivematica.search.constants import DOC_TYPE
from archivematica.search.constants import ES_FIELD_STATUS
from archivematica.search.constants import ES_FIELD_UUID
from archivematica.search.constants import STATUS_UPLOADED
from archivematica.search.constants import TRANSFER_FILES_INDEX
from archivematica.search.constants import TRANSFERS_INDEX
from archivematica.search.querying import _document_ids_from_field_query

logger = logging.getLogger("archivematica.search")


def _document_id_from_field_query(client, index, field, value):
    document_id = None
    ids = _document_ids_from_field_query(client, index, field, value)
    if len(ids) == 1:
        document_id = ids[0]
    return document_id


def _update_field(client, index, uuid, field, value):
    document_id = _document_id_from_field_query(client, index, ES_FIELD_UUID, uuid)

    if document_id is None:
        logger.error(f"Unable to find document with UUID {uuid} in index {index}")
        return

    client.update(
        body={"doc": {field: value}}, index=index, doc_type=DOC_TYPE, id=document_id
    )


def mark_aip_stored(client, uuid):
    _update_field(client, AIPS_INDEX, uuid, ES_FIELD_STATUS, STATUS_UPLOADED)


def _update_field_for_package_and_files(
    client, package_index, files_index, package_uuid_field, package_uuid, field, value
):
    """Update the specified field for a package and its related files

    :param client: ES client.
    :param package_index: Name of package index to update.
    :param files_index: Name of files index to update.
    :param package_uuid_field: Name of ES field for package UUID in package_index.
    :param package_uuid: UUID of package to update.
    :param field: Field in indices to update.
    :param value: Value to set in updated field.
    :return: None.
    """
    _update_field(client, package_index, package_uuid, field, value)

    files = _document_ids_from_field_query(
        client, files_index, package_uuid_field, package_uuid
    )
    for file_id in files:
        client.update(
            body={"doc": {field: value}},
            index=files_index,
            doc_type=DOC_TYPE,
            id=file_id,
        )


def mark_aip_deletion_requested(client, uuid):
    """Update AIP package and file indices to reflect AIP deletion request.

    :param client: ES client.
    :param uuid: AIP UUID.
    :return: None.
    """
    _update_field_for_package_and_files(
        client, AIPS_INDEX, AIP_FILES_INDEX, "AIPUUID", uuid, ES_FIELD_STATUS, "DEL_REQ"
    )


def mark_backlog_deletion_requested(client, uuid):
    """Update transfer package and file indices to reflect backlog deletion request.

    :param client: ES client.
    :param uuid: Transfer UUID.
    :return: None.
    """
    _update_field_for_package_and_files(
        client,
        TRANSFERS_INDEX,
        TRANSFER_FILES_INDEX,
        "sipuuid",
        uuid,
        "pending_deletion",
        True,
    )


def revert_aip_deletion_request(client, uuid):
    """Update AIP indices to reflect rejected deletion request

    :param client: ES client.
    :param uuid: AIP UUID.
    :returns: None.
    """
    _update_field_for_package_and_files(
        client,
        AIPS_INDEX,
        AIP_FILES_INDEX,
        "AIPUUID",
        uuid,
        ES_FIELD_STATUS,
        STATUS_UPLOADED,
    )


def revert_backlog_deletion_request(client, uuid):
    """Update transfer indices to reflect rejected deletion request

    :param client: ES client.
    :param uuid: Transfer UUID.
    :returns: None.
    """
    _update_field_for_package_and_files(
        client,
        TRANSFERS_INDEX,
        TRANSFER_FILES_INDEX,
        "sipuuid",
        uuid,
        "pending_deletion",
        False,
    )
