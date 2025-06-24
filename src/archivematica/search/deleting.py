import logging

from django.db.models import Q

from archivematica.dashboard.main.models import File
from archivematica.search.constants import AIP_FILES_INDEX
from archivematica.search.constants import AIPS_INDEX
from archivematica.search.constants import DOC_TYPE
from archivematica.search.constants import ES_FIELD_UUID
from archivematica.search.constants import TRANSFER_FILES_INDEX
from archivematica.search.constants import TRANSFERS_INDEX
from archivematica.search.querying import _document_ids_from_field_query

logger = logging.getLogger("archivematica.search")


def remove_backlog_transfer(client, uuid):
    _delete_matching_documents(client, TRANSFERS_INDEX, ES_FIELD_UUID, uuid)


def remove_backlog_transfer_files(client, uuid):
    _remove_transfer_files(client, uuid, "transfer")


def remove_sip_transfer_files(client, uuid):
    _remove_transfer_files(client, uuid, "sip")


def _remove_transfer_files(client, uuid, unit_type=None):
    if unit_type == "transfer":
        transfers = {uuid}
    else:
        condition = Q(transfer_id=uuid) | Q(sip_id=uuid)
        transfers = {
            f[0] for f in File.objects.filter(condition).values_list("transfer_id")
        }

    if len(transfers) > 0:
        for transfer in transfers:
            files = _document_ids_from_field_query(
                client, TRANSFER_FILES_INDEX, "sipuuid", transfer
            )
            if len(files) > 0:
                for file_id in files:
                    client.delete(
                        index=TRANSFER_FILES_INDEX, doc_type=DOC_TYPE, id=file_id
                    )
    else:
        if not unit_type:
            unit_type = "transfer or SIP"
        logger.warning("No transfers found for %s %s", unit_type, uuid)


def delete_aip(client, uuid):
    _delete_matching_documents(client, AIPS_INDEX, ES_FIELD_UUID, uuid)


def delete_aip_files(client, uuid):
    _delete_matching_documents(client, AIP_FILES_INDEX, "AIPUUID", uuid)


def _delete_matching_documents(client, index, field, value):
    """Deletes all documents in index where field = value

    :param Elasticsearch client: Elasticsearch client
    :param str index: Name of the index. E.g. 'aips'
    :param str field: Field to query when deleting. E.g. 'uuid'
    :param str value: Value of the field to query when deleting. E.g. 'cd0bb626-cf27-4ca3-8a77-f14496b66f04'
    """
    query = {"query": {"term": {field: value}}}
    logger.info("Deleting with query %s", query)
    results = client.delete_by_query(index=index, body=query)
    logger.info("Deleted by query %s", results)
