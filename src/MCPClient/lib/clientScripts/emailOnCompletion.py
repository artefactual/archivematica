
import argparse
import sys

import django
from django.conf import settings as mcpclient_settings
from django.contrib.auth.models import User
from django.core.mail.message import EmailMessage
from django.utils.translation import ugettext as _

from contrib import utils

from custom_handlers import get_script_logger
from main import models
from email.mime.text import MIMEText

django.setup()

logger = get_script_logger('archivematica.mcp.client.emailOnCompletion')

FAILED_JOB_STEP = 4
MAX_ATTACHMENT_SIZE = 100000  # Bytes. Attachment can have messages from every file so limit this.
GENERAL_FAILURE = _('Internal Processing Error. Contact your administrator for help.')


def get_recipients():
    """ Gets the active users to send emails to. If the setting TEST_EMAIL is defined, the email will
    be sent to that user.
    TODO For Jisc, we want to send to administrative users only.
    """
    email_to = getattr(mcpclient_settings, 'TEST_EMAIL', '')
    if not email_to:
        return User.objects.filter(is_active=True).values_list('email', flat=True).exclude(email__in=['demo@example.com', ''])
    else:
        return [email_to]


def send_email(subject, to, content, attachmentText):
    """ Send the email with the given parameters. If attachmentText is empty no attachment
    will be sent
    """
    try:
        logger.info('Sending workflow completion email')
        mail = EmailMessage(subject, content, mcpclient_settings.DEFAULT_FROM_EMAIL, to)
        if attachmentText:
            attachment = MIMEText(attachmentText)
            attachment.add_header('Content-Disposition', 'attachment; filename=TaskDetails.txt')
            mail.attach(attachment)

        return mail.send()
    except:
        logger.exception('Report email was not delivered')
        raise
    else:
        logger.info('Report sent successfully!')


def get_workflow_details(unit_uuid):
    """ Get basic details about the ended workflow with the given uuid for sending in an email.
    If there any any jobs that have failed, get a general message about the failure.
    Task details from each failed job are added as an attachment.
    """
    jobs = models.Job.objects.filter(sipuuid=unit_uuid).order_by('-createdtime')
    if not jobs:
        raise ValueError('There are no job with the given SIP of Transfer UUID %s', unit_uuid)

    email_content = "Completion report for job with directory {0}\n\n".format(utils.get_directory_name_from_job(jobs))

    job_details = ""
    task_details = ""
    whole_flow_success = True
    for job in jobs:
        if job.currentstep == models.Job.STATUS_FAILED:
            job_details += _('Job failed: (%s)\n') % job.jobtype
            messages = job.microservicechainlink.jobfailmessage_set.all()
            job_details += '        {0}\n'.format(messages[0].message if messages.exists() else GENERAL_FAILURE)

            # TODO This check is done in the UI but looks unreliable to me. Is it better to
            # check the microservicechainlink ID, or some other measure of failure?
            if (job.microservicechainlink.microservicegroup == 'Failed SIP' or
                    job.microservicechainlink.microservicegroup == 'Failed transfer'):
                whole_flow_success = False

            for task in job.task_set.all():
                if len(task_details) < MAX_ATTACHMENT_SIZE and task.stderror.strip():
                    task_details += 'Task {0}: {1}'.format(task.execution, task.stderror)

    email_content += _("The preservation workflow %s.\n\n") % ("succeeded" if whole_flow_success else "failed")
    if whole_flow_success:
        email_content += _("The jobs below failed but did not cause the preservation to fail.\n\n")
    else:
        email_content += _("The problems below caused the preservation to fail.\n\n")

    email_content += job_details

    attachment = ""
    if task_details:
        attachment = _("Detailed Messages\n\n") + task_details

    return email_content, attachment


def run_job(unit_uuid, stdout):
    to = get_recipients()
    if not to:
        logger.error('Nobody to send it to. Please add users with valid email addresses in the dashboard.')
        return 1

    subject = _('Archivematica Completion Report for %s') % (unit_uuid)

    # Generate email message and send it.
    content, attachment = get_workflow_details(unit_uuid)
    send_email(subject, to, content, attachment)

    if stdout:
        print(content)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--unitIdentifier', action='store', dest='unit_uuid', required=True)
    parser.add_argument('-f', '--from', action='store', dest='from', default='ArchivematicaSystem@archivematica.org')
    parser.add_argument('--stdout', action='store_true', dest='stdout', default=False)
    args = parser.parse_args()

    sys.exit(run_job(args.unit_uuid, args.stdout))
