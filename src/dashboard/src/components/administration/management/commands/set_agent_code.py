from django.core.management.base import BaseCommand

from installer.steps import set_agent_code


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--agent-code', required=True)

    def handle(self, *args, **options):
        set_agent_code(options['agent_code'])
