import time

from django.conf import settings as django_settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

import archivematica.search.constants
from archivematica.search.service import SearchServiceError
from archivematica.search.service import setup_search_service_from_conf


class DashboardCommand(BaseCommand):
    def success(self, message):
        self.stdout.write(self.style.SUCCESS(message))

    def error(self, message):
        self.stdout.write(self.style.ERROR(message))

    def warning(self, message):
        self.stdout.write(self.style.WARNING(message))

    def info(self, message):
        self.stdout.write(message)


def boolean_input(question, default=None):
    question += '\n\nType "yes" to continue, or "no" to cancel: '
    result = input("%s " % question)
    if not result and default is not None:
        return default
    while len(result) < 1 or result.lower() not in ("yes", "no"):
        result = input('Please answer "yes" or "no": ')
    return result.lower() == "yes"


def setup_es_for_aip_reindexing(cmd, delete_all=False):
    """Setup for reindexing AIPs.

    :param cmd: Command object.
    :param delete_all: Optional arg to delete AIP indices.

    :returns: ES client.
    """
    if archivematica.search.constants.AIPS_INDEX not in django_settings.SEARCH_ENABLED:
        raise CommandError(
            "The AIPs indexes are not enabled. Please, make sure to "
            "set the *_SEARCH_ENABLED environment variables to `true` "
            "to enable the AIPs and Transfers indexes, or to `aips` "
            "to only enable the AIPs indexes."
        )

    try:
        search_service = setup_search_service_from_conf(django_settings)
    except SearchServiceError as err:
        raise CommandError(f"Unable to connect to the search service: {err}")

    if delete_all:
        cmd.info("Deleting all AIPs in the 'aips' and 'aipfiles' indices")
        time.sleep(3)  # Time for the user to panic and kill the process.
        indices = [
            archivematica.search.constants.AIPS_INDEX,
            archivematica.search.constants.AIP_FILES_INDEX,
        ]
        search_service.delete_indexes(indices)
        search_service.ensure_indexes_exist(indices)

    return search_service
