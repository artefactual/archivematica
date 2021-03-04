# -*- coding: utf-8 -*-
from __future__ import absolute_import

import time

from django.conf import settings as django_settings
from django.core.management.base import BaseCommand, CommandError
from elasticsearch import ElasticsearchException
from six.moves import input

import elasticSearchFunctions as es


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
    if es.AIPS_INDEX not in django_settings.SEARCH_ENABLED:
        raise CommandError(
            "The AIPs indexes are not enabled. Please, make sure to "
            "set the *_SEARCH_ENABLED environment variables to `true` "
            "to enable the AIPs and Transfers indexes, or to `aips` "
            "to only enable the AIPs indexes."
        )

    try:
        es.setup_reading_from_conf(django_settings)
        es_client = es.get_client()
    except ElasticsearchException as err:
        raise CommandError("Unable to connect to Elasticsearch: {}".format(err))

    if delete_all:
        cmd.info("Deleting all AIPs in the 'aips' and 'aipfiles' indices")
        time.sleep(3)  # Time for the user to panic and kill the process.
        indices = [es.AIPS_INDEX, es.AIP_FILES_INDEX]
        es_client.indices.delete(",".join(indices), ignore=404)
        es.create_indexes_if_needed(es_client, indices)

    return es_client
