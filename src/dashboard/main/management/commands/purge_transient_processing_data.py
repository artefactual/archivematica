"""Purge transient processing data.

This command purges package-related data that is generated during processing
from the Archivematica database. In some user workflows, this type of data is
considered discardable as long as the AIPs are successfully stored by the
Archivematica Storage Service.

It can be safely executed on active Archivematica instances since it only
targets packages that have completed processing.

An optional parameter ``--purge-unknown`` may be passed to also purge packages
in unknown state.

An optional parameter ``--keep-failed`` may be passed to prevent failed packages
from being purged.

An optional parameter ``--keep-searches`` may be passed to retain search
documents.

By default, this command only purges packages of a certain age. It uses
``--age='0 06:00:00'``, meaning that no packages will be removed if they have
not completed processing more than six hours ago. Optionally, users can pass
other values.

``/manage.py purge_transient_processing_data --age='0 12:00:00'`` purges
packages that completed processing at least twelve hours ago.

``/manage.py purge_transient_processing_data --age=0`` can be used to target
all packages that completed processing regardless their age. This form is
generally not recommended because it can affect SIPs being created from
recently purged transfers.
"""

import logging
import traceback

import elasticSearchFunctions as es
from django.conf import settings as django_settings
from django.core.management.base import CommandError
from django.utils import timezone
from django.utils.dateparse import parse_duration
from elasticsearch import ElasticsearchException
from main import models
from main.management.commands import DashboardCommand


class Command(DashboardCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print packages but do not purge.",
        )
        parser.add_argument(
            "--purge-unknown",
            action="store_true",
            help="Purge packages in unknown state.",
        )
        parser.add_argument(
            "--keep-failed",
            action="store_true",
            help="Do not purge failed packages.",
        )
        parser.add_argument(
            "--keep-searches",
            action="store_true",
            help="Do not purge search documents.",
        )
        parser.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="Reduce verbosity.",
        )
        parser.add_argument(
            "--age",
            default="0 06:00:00",
            help=(
                "Only purge packages of a certain age (completion date). "
                "Supported formats are: "
                '"%%d %%H:%%M:%%S.%%f" or ISO 8601 durations. '
                'E.g. express "36 hours" as "1 12:00:00" or "P1DT12H". '
                'Default value is "0 06:00:00", i.e. "6 hours".'
            ),
        )

    def handle(self, *args, **options):
        if not options["keep_searches"] and django_settings.SEARCH_ENABLED:
            # Ignore elasticsearch-py logging events unless they're errors.
            logging.getLogger("elasticsearch").setLevel(logging.ERROR)
            logging.getLogger("archivematica.common").setLevel(logging.ERROR)
            try:
                es.setup_reading_from_conf(django_settings)
                es_client = es.get_client()
            except ElasticsearchException as err:
                raise CommandError(f"Unable to connect to Elasticsearch: {err}")

        # Build look-up options.
        kwargs = {
            "include_unknown": options["purge_unknown"],
            "include_failed": not options["keep_failed"],
        }
        if options["age"] != "0":
            duration = parse_duration(options["age"])
            if duration is None:
                raise CommandError("Age could not be parsed.")
            kwargs["completed_before"] = timezone.now() - duration

        self.info("Purging SIPs...")
        sips = models.SIP.objects.done(**kwargs)
        for sip in sips:
            package_id = sip.pk
            if not options["quiet"]:
                self.warning(f"» SIP {package_id} with status {sip.status_str}")
            if options["dry_run"]:
                continue
            try:
                self.delete_queryset(
                    models.Access.objects.filter(sipuuid=package_id),
                    options["quiet"],
                )
                self.delete_queryset(
                    models.UnitVariable.objects.filter(
                        unittype="SIP", unituuid=package_id
                    ),
                    options["quiet"],
                )
                self.delete_queryset(
                    models.Job.objects.filter(sipuuid=package_id, unittype="unitSIP"),
                    options["quiet"],
                )
                self.delete_queryset(
                    models.SIP.objects.filter(pk=package_id),
                    options["quiet"],
                )
                if (
                    not options["keep_searches"]
                    and es.AIPS_INDEX in django_settings.SEARCH_ENABLED
                ):
                    if not options["quiet"]:
                        self.info("  Purging search documents...")
                    es.delete_aip(es_client, package_id)
                    es.delete_aip_files(es_client, package_id)
            except Exception as err:
                self.error(f"  Error: {err}")
                self.stdout.write(traceback.print_exc())

        self.info("Purging transfers...")
        transfers = models.Transfer.objects.done(**kwargs)
        for transfer in transfers:
            package_id = transfer.pk
            if not options["quiet"]:
                self.warning(
                    f"» Transfer {package_id} with status {transfer.status_str}"
                )
            if options["dry_run"]:
                continue
            try:
                self.delete_queryset(
                    models.UnitVariable.objects.filter(
                        unittype="Transfer", unituuid=package_id
                    ),
                    options["quiet"],
                )
                self.delete_queryset(
                    models.Job.objects.filter(
                        sipuuid=package_id, unittype="unitTransfer"
                    ),
                    options["quiet"],
                )
                self.delete_queryset(
                    models.Transfer.objects.filter(pk=package_id),
                    options["quiet"],
                )
                if (
                    not options["keep_searches"]
                    and es.TRANSFERS_INDEX in django_settings.SEARCH_ENABLED
                ):
                    if not options["quiet"]:
                        self.info("  Purging search documents...")
                    es.remove_backlog_transfer(es_client, package_id)
                    es.remove_backlog_transfer_files(es_client, package_id)
            except Exception as err:
                self.error(f"  Error: {err}")
                self.stdout.write(traceback.format_exc())

    def delete_queryset(self, queryset, quiet):
        result = queryset.delete()
        if not quiet and result and len(result) == 2:
            matches = result[1]
            for model, count in matches.items():
                self.info(f"  Purging {model} objects: {count} rows deleted.")
