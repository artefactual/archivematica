from __future__ import absolute_import
from django.core.management.base import BaseCommand
from django.utils.six.moves import input
from six.moves import input


class DashboardCommand(BaseCommand):
    def success(self, message):
        self.stdout.write(self.style.MIGRATE_SUCCESS(message))

    def error(self, message):
        self.stdout.write(self.style.ERROR(message))

    def warning(self, message):
        self.stdout.write(self.style.WARNING(message))

    def info(self, message):
        self.stdout.write(message)


def boolean_input(question, default=None):
    question += '\n\nType "yes" to continue, or "no" to cancel: '
    result = eval(input("%s " % question))
    if not result and default is not None:
        return default
    while len(result) < 1 or result.lower() not in ("yes", "no"):
        result = eval(input('Please answer "yes" or "no": '))
    return result.lower() == "yes"
