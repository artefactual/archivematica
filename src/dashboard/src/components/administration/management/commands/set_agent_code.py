from __future__ import absolute_import
from django.core.management.base import BaseCommand

from installer.steps import set_agent_code
from main.models import Agent


class Command(BaseCommand):
    help = """Set the code of an agent.

    By default it updates the agent code of the Archivematica preservation
    system (pk=1). Use the argument `--pk=` to select a different agent.
    """

    def add_arguments(self, parser):
        parser.add_argument("agent-code")
        parser.add_argument("--pk", default=1, type=int)

    def handle(self, *args, **options):
        try:
            set_agent_code(options["agent-code"], options["pk"])
        except Agent.DoesNotExist:
            self.stderr.write("Agent not found")
