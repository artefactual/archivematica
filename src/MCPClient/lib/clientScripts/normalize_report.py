#!/usr/bin/env python2

from argparse import ArgumentParser
import logging
import os.path

import django
from django.conf import settings as mcpclient_settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.template import Context, Template

from main.models import File, Job, Report, SIP, Task
import components.helpers as helpers

from custom_handlers import get_script_logger


django.setup()

logger = get_script_logger("archivematica.mcp.client.normalizeReport")

# Based on http://leemunroe.github.io/responsive-html-email-template/email.html
EMAIL_TEMPLATE = """
    <!doctype html>
    <html>
        <head>
            <meta name="viewport" content="width=device-width">
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            <title>Normalization failure report - failures detected!</title>
        </head>
        <body>
            <table cellpadding="10" width="100%">
                <tr>
                    <td></td>
                    <td>
                        <h1>Archivematica</h1>
                        <p>
                            Pipeline: {{ pipeline_uuid }}<br />
                            SIP: <strong>{{ name }}</strong> ({{ uuid }})
                        </p>
                        <hr />
                        <h3>Normalization failure report - failures detected!</h3>
                        <table cellpadding="10" border="1" width="100%">
                            <thead>
                                <tr>
                                    <th>File name</th>
                                    <th>File UUID</th>
                                    <th>Exit code</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for type, tasks in failed_tasks.items %}
                                    <tr>
                                        <td colspan="3" style="background-color: #aaa; font-weight: bold;">
                                            {{ type }} (total = {{ tasks.count }})
                                        </td>
                                    </tr>
                                    {% for item in tasks %}
                                        <tr>
                                            <td>{{ item.location }}</td>
                                            <td>{{ item.fileuuid }}</td>
                                            <td>{{ item.exitcode }}</td>
                                        </tr>
                                    {% endfor %}
                                {% endfor %}
                            </tbody>
                        </table>
                    </td>
                    <td></td>
                </tr>
            </table>
            <table class="footer-wrap">
                <tr>
                    <td></td>
                    <td class="container">
                        <div class="content">
                            <table>
                                <tr>
                                    <td align="center">
                                        <p>Archivematica</p>
                                    </td>
                                </tr>
                            </table>
                        </div>
                    </td>
                    <td></td>
                </tr>
            </table>
        </body>
    </html>
"""


def report(uuid):
    """
    Generate normalization report using Django's template module and send it to
    every active user.
    """
    recipient_list = User.objects.filter(
        is_active=True, userprofile__system_emails=True
    ).values_list("email", flat=True)
    if not recipient_list:
        logger.info(
            "Normalization report is not being sent because the recipient list is empty."
        )
        return 0

    logger.info("Sending report to %s.", ", ".join(recipient_list))

    try:
        sip = SIP.objects.get(uuid=uuid)
    except SIP.DoesNotExist:
        logger.error("SIP with UUID %s not found.", uuid)
        return 1

    failed_tasks = {}
    for jobtype in ("Normalize for preservation", "Normalize for access"):
        try:
            job = Job.objects.filter(sipuuid=uuid, jobtype=jobtype).order_by(
                "-createdtime"
            )[0]
        except IndexError:
            logger.info(
                'No normalization failures have been detected in type "%s"', jobtype
            )
            continue
        tasks = Task.objects.filter(job=job).exclude(exitcode__in=[0, 2])
        if not tasks.exists():
            logger.info(
                'No normalization failures have been detected in type "%s"', jobtype
            )
            continue
        failed_tasks[jobtype] = tasks.values("filename", "fileuuid", "exitcode")
        for item in failed_tasks[jobtype]:
            try:
                item["location"] = File.objects.get(
                    uuid=item["fileuuid"]
                ).currentlocation.replace("%SIPDirectory%", "")
            except File.DoesNotExist:
                pass

    if not len(failed_tasks):
        logger.info(
            "Normalization report is not being sent because no failures have been detected."
        )
        return 0

    ctxdict = {
        "uuid": uuid,
        "name": os.path.basename(sip.currentpath.rstrip("/")).replace(
            "-" + sip.uuid, ""
        ),
        "pipeline_uuid": helpers.get_setting("dashboard_uuid"),
        "failed_tasks": failed_tasks,
    }

    logger.info("Building HTML message")
    ctx = Context(ctxdict)
    tmpl = Template(EMAIL_TEMPLATE)
    html_message = tmpl.render(ctx)

    logger.info("Storing report in database")
    Report.objects.create(
        content=html_message,
        unittype="SIP",
        unitname=ctxdict["name"],
        unitidentifier=ctxdict["uuid"],
    )

    try:
        logger.info("Sending email...")
        send_mail(
            subject="Normalization failure report for {} ({})".format(
                ctxdict["name"], ctxdict["uuid"]
            ),
            message="Please see the attached HTML document",
            from_email=mcpclient_settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
        )
    except:
        logger.exception("Report email was not delivered")
        return 1
    else:
        logger.info("Report sent successfully!")

    return 0


def call(jobs):
    parser = ArgumentParser()
    parser.add_argument("--uuid", required=True)
    parser.add_argument("--debug", action="store_true", default=False)

    with transaction.atomic():
        for job in jobs:
            with job.JobContext(logger=logger):
                args = parser.parse_args(job.args[1:])

                logging_stream_handler = None
                if args.debug:
                    logger.setLevel(logging.DEBUG)
                    logging_stream_handler = logger.addHandler(logging.StreamHandler())
                else:
                    logger.setLevel(logging.NOTSET)

                job.set_status(report(args.uuid))

                if logging_stream_handler is not None:
                    logger.removeHandler(logging_stream_handler)
