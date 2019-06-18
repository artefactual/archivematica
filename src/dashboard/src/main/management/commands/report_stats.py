import csv

from django.core.management.base import BaseCommand
from django.db.models import Count, F, Func, IntegerField, Max, Min, TimeField, Sum

from main.models import File, Job


class TimeToSec(Func):
    function = "TIME_TO_SEC"
    output_field = IntegerField()


class Timediff(Func):
    function = "TIMEDIFF"
    output_field = TimeField()


class Command(BaseCommand):
    help = "Prints recent processing performance stats"

    base_processing_time_qs = (
        Job.objects.values("sipuuid", "unittype")
        .annotate(
            job_start_time=Min("createdtime"),
            processing_duration=Sum(
                TimeToSec(Timediff(F("task__endtime"), F("task__starttime")))
            ),
            absolute_duration=TimeToSec(
                Timediff(Max(F("task__endtime")), Min(F("task__starttime")))
            ),
            task_count=Count("task"),
        )
        .order_by("-job_start_time")
    )

    sip_processing_time_qs = base_processing_time_qs.filter(unittype="unitSIP")
    transfer_processing_time_qs = base_processing_time_qs.filter(
        unittype="unitTransfer"
    )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

        self.csv_writer = csv.writer(self.stdout, delimiter="\t")

    def add_arguments(self, parser):
        parser.add_argument(
            "report", choices=["sip-processing-times"], help="Report type to generate"
        )
        parser.add_argument(
            "--limit", default=100, type=int, help="Number of rows to include in output"
        )
        parser.add_argument(
            "--exclude-transfer-times",
            action="store_false",
            dest="include_transfers",
            help="Exclude transfer processing times from output",
        )

    def handle(self, *args, **options):
        if options["report"] == "sip-processing-times":
            self.report_sip_processing_times(**options)

    def report_sip_processing_times(self, **options):
        row_values = self.sip_processing_time_qs.values_list(
            "sipuuid",
            "job_start_time",
            "processing_duration",
            "absolute_duration",
            "task_count",
        )[: options["limit"]]

        self.stdout.write(
            (20 * "*")
            + " Processing time for most recent {0: <3} SIPs *********".format(
                options["limit"]
            )
            + (20 * "*")
        )
        if options["include_transfers"]:
            self.stdout.write((31 * "*") + " (including transfer times) " + (32 * "*"))
        self.stdout.write("\n")

        self.csv_writer.writerow(
            (
                "                            SIP UUID",
                "        SIP Submission Timestamp",
                "CPU Time",
                "User Time",
                "Tasks executed",
            )
        )
        for sip_uuid, job_start_time, processing, absolute, task_count in row_values:
            if options["include_transfers"]:
                transfer_uuids = File.objects.filter(sip_id=sip_uuid).values_list(
                    "transfer_id", flat=True
                )
                transfer_processing_times = self.transfer_processing_time_qs.filter(
                    sipuuid__in=transfer_uuids
                ).values_list(
                    "sipuuid", "processing_duration", "absolute_duration", "task_count"
                )
                for transfer_row in transfer_processing_times:
                    processing += transfer_row[1]
                    absolute += transfer_row[2]
                    task_count += transfer_row[3]

            self.csv_writer.writerow(
                (
                    sip_uuid,
                    job_start_time,
                    "{0: >8}".format(processing),
                    "{0: >9}".format(absolute),
                    "{0: >14}".format(task_count),
                )
            )

        self.stdout.write("\n")
        self.stdout.write("*" * 91)
