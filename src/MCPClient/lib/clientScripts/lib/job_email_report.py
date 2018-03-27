"""Generate and send failing jobs email report."""

from django.conf import settings as mcpclient_settings
from django.contrib.auth.models import User
from django.core.mail.message import EmailMessage
from django.utils.translation import ugettext as _

from contrib import utils

from custom_handlers import get_script_logger
from main import models
from email.mime.text import MIMEText

logger = get_script_logger('archivematica.mcp.client.emailOnCompletion')


# Maximum size of the task details text stream in bytes.
MAX_ATTACHMENT_SIZE = 100000


def get_recipients():
    """Get the active users to send emails to.

    TODO: for Jisc, we want to send to administrative users only.
    """
    return User.objects \
        .filter(is_active=True).values_list('email', flat=True) \
        .exclude(email__in=['demo@example.com', ''])


def send_email(subject, to, content, attachment_text):
    """Send the email with the given parameters.

    If attachment_text is empty no attachment will be sent.
    """
    try:
        logger.info('Sending workflow completion email')
        mail = EmailMessage(subject, content,
                            mcpclient_settings.DEFAULT_FROM_EMAIL, to)
        if attachment_text:
            attachment = MIMEText(attachment_text)
            attachment.add_header('Content-Disposition', 'attachment; '
                                  'filename=TaskDetails.txt')
            mail.attach(attachment)
        return mail.send()
    except Exception:
        logger.exception('Report email was not delivered')
        raise
    else:
        logger.info('Report sent successfully!')


def get_workflow_details(unit_uuid):
    """Get basic details about the ended workflow for sending in an email.

    If there any any jobs that have failed, get a general message about the
    failure. Task details from each failed job are added as an attachment.
    """
    jobs = models.Job.objects \
        .filter(sipuuid=unit_uuid).order_by('-createdtime')
    if not jobs:
        raise ValueError('There are no job with the given SIP of '
                         'Transfer UUID %s', unit_uuid)

    email_content = _('Completion report for job with directory '
                      '%s.\n\n' % utils.get_directory_name_from_job(jobs))

    general_failure = _('Internal Processing Error. '
                        'Contact your administrator for help.')
    job_details = task_details = ''
    whole_flow_success = True
    for job in jobs:
        if job.currentstep == models.Job.STATUS_FAILED:
            job_details += _('Job failed: (%s)\n') % job.jobtype
            messages = job.microservicechainlink.jobfailmessage_set.all()
            job_details += '        {0}\n'.format(
                messages[0].message if messages.exists() else general_failure)

            # TODO This check is done in the UI but looks unreliable to me. Is
            # it better to check the microservicechainlink ID, or some other
            # measure of failure?
            if job.microservicechainlink.microservicegroup in \
                    ('Failed SIP', 'Failed transfer'):
                whole_flow_success = False

            for task in job.task_set.all():
                if len(task_details) < MAX_ATTACHMENT_SIZE and \
                        task.stderror.strip():
                    task_details += _('Task %(execution)s: %(stderr)s' % {
                        'execution': task.execution,
                        'stderr': task.stderror,
                    })

    if whole_flow_success:
        email_content += _('The preservation workflow succeeded. The jobs '
                           'below (if any) failed but did not cause the '
                           'preservation to fail.\n\n')
    else:
        email_content += _('The preservation workflow failed. The problems '
                           'below caused the preservation to fail.\n\n')

    email_content += job_details

    attachment = ""
    if task_details:
        attachment = _("Detailed messages\n\n") + task_details

    return email_content, attachment


def run_report(unit_uuid):
    """Generate and send job email report."""
    to = get_recipients()
    if not to:
        raise Exception('Nobody to send it to. Please add users with valid '
                        'email addresses in the dashboard.')
    # Generate email message and send it.
    subject = _('Archivematica Completion Report for %s') % (unit_uuid)
    content, attachment = get_workflow_details(unit_uuid)
    send_email(subject, to, content, attachment)
