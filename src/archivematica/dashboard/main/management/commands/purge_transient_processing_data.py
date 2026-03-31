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

An optional parameter ``--hidden-transfers-only`` may be passed to only purge
packages hidden in the dashboard. In this mode, SIPs are filtered by
``SIP.hidden=True`` and transfers are selected when either
``Transfer.hidden=True`` or they are linked to a hidden SIP.

An optional parameter ``--batch-size`` may be passed to cap how many SIPs and
how many transfers are purged per run. ``--batch-size=0`` means no cap.

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

from django.conf import settings as django_settings
from django.core.management.base import CommandError
from django.utils import timezone
from django.utils.dateparse import parse_duration

import archivematica.search.constants
from archivematica.dashboard.main import models
from archivematica.dashboard.main.management.commands import DashboardCommand
from archivematica.search.service import SearchServiceError
from archivematica.search.service import setup_search_service_from_conf


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
        parser.add_argument(
            "--hidden-transfers-only",
            action="store_true",
            help="Only purge packages tied to hidden SIPs.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=0,
            help=(
                "Process package deletions in batches. "
                "Lower values can reduce lock duration at the expense of runtime. "
                "Use 0 to process all matching packages at once. "
                "Default is 0."
            ),
        )

    def handle(self, *args, **options):
        if options["batch_size"] < 0:
            raise CommandError("--batch-size must be greater than or equal to 0.")

        search_service = None
        if (
            not options["keep_searches"]
            and archivematica.search.constants.AIPS_INDEX
            in django_settings.SEARCH_ENABLED
        ):
            # Ignore elasticsearch-py logging events unless they're errors.
            logging.getLogger("elasticsearch").setLevel(logging.ERROR)
            logging.getLogger("archivematica.common").setLevel(logging.ERROR)
            try:
                search_service = setup_search_service_from_conf(django_settings)
            except SearchServiceError as err:
                raise CommandError(f"Unable to connect to the search service: {err}")

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

        selected_transfer_ids = None
        if options["hidden_transfers_only"]:
            hidden_sips = models.SIP.objects.done(**kwargs).filter(hidden=True)
            hidden_transfer_ids = list(
                models.Transfer.objects.done(**kwargs)
                .filter(hidden=True)
                .order_by("pk")
                .values_list("pk", flat=True)
            )
            linked_transfer_ids = list(
                models.Transfer.objects.done(**kwargs)
                .filter(file__sip_id__in=hidden_sips.values("pk"))
                .order_by("pk")
                .distinct()
                .values_list("pk", flat=True)
            )
            batch_limit = options["batch_size"] or None
            selected_transfer_ids = hidden_transfer_ids
            selected_transfer_ids.extend(
                transfer_id
                for transfer_id in linked_transfer_ids
                if transfer_id not in selected_transfer_ids
            )
            if batch_limit is not None:
                selected_transfer_ids = selected_transfer_ids[:batch_limit]

        self.info("Purging SIPs...")
        sips = models.SIP.objects.done(**kwargs)
        if options["hidden_transfers_only"]:
            sips = sips.filter(hidden=True)
        sips = sips.order_by("pk")
        batch_limit = options["batch_size"] or None
        if batch_limit is not None:
            sips = sips[:batch_limit]
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
                    and archivematica.search.constants.AIPS_INDEX
                    in django_settings.SEARCH_ENABLED
                ):
                    if not options["quiet"]:
                        self.info("  Purging search documents...")
                    search_service.delete_aip(str(package_id))
                    search_service.delete_aip_files(str(package_id))
            except Exception as err:
                self.error(f"  Error: {err}")
                self.stdout.write(traceback.print_exc())

        self.info("Purging transfers...")
        if selected_transfer_ids is not None:
            transfers = models.Transfer.objects.filter(pk__in=selected_transfer_ids)
            transfers = transfers.order_by("pk")
        else:
            transfers = models.Transfer.objects.done(**kwargs).order_by("pk")
            batch_limit = options["batch_size"] or None
            if batch_limit is not None:
                transfers = transfers[:batch_limit]
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
            except Exception as err:
                self.error(f"  Error: {err}")
                self.stdout.write(traceback.format_exc())

    def delete_queryset(self, queryset, quiet):
        result = queryset.delete()
        if not quiet and result and len(result) == 2:
            matches = result[1]
            for model, count in matches.items():
                self.info(f"  Purging {model} objects: {count} rows deleted.")
