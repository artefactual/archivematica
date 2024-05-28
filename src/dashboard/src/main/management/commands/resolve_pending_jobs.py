"""Resolve pending jobs.

This is an interactive command used to resolve processing jobs
awaiting user decisions. It interacts with the workflow engine RPC
interface directly meaning that it can operate independently to the
Archivematica Dashboard or its API.

It impersonates the admin user, or the first match when multiple
exist.

Not recommended for general use, i.e. if Archivematica provides an
interactive command-line interface in the future it will rely on
public APIs. This is an alternative to the old mcp-rpc-cli command.
"""

from contrib.mcp.client import MCPClient
from django.contrib.auth import get_user_model
from django.core.management.base import CommandError
from lxml import etree
from main.management.commands import DashboardCommand


class Command(DashboardCommand):
    help = __doc__

    def handle(self, *args, **options):
        try:
            self.loop(*args, **options)
        except KeyboardInterrupt:
            self.stdout.write("")
            self.warning("Bye!")

    def loop(self, *args, **options):
        admin_user = self.admin_user()
        if not admin_user:
            raise CommandError("Cannot find a superuser.")
        client = MCPClient(admin_user)

        while True:
            self.success("Fetching packages awaiting decisions...")
            packages = etree.fromstring(client.list())
            if not len(packages):
                self.error("No packages!")

            self.print_pending_packages(packages)

            choice = self.prompt_package_choice()
            if choice == "q":
                self.warning("Bye!")
                break
            elif choice == "u":
                continue
            try:
                choice = int(choice)
                if choice < 1:
                    raise ValueError()
            except ValueError:
                self.warning("Not a valid choice. Try again!")
                continue
            try:
                package = packages[choice - 1]
            except IndexError:
                self.warning("Number not found. Try again!")
                continue

            package_id = package.find("./unit/unitXML/UUID").text
            package_type = package.find("./unit/type").text
            decisions = package.find("./choices")
            job_id = package.find("./UUID").text
            job = {
                job["id"]: job["description"]
                for job in client.get_unit_status(package_id)["jobs"]
            }.get(job_id)

            while True:
                self.print_pending_job_decisions(
                    package_type, package_id, job, decisions
                )

                choice = self.prompt_decision_choice(decisions)
                if choice == "q":
                    break
                try:
                    choice = int(choice)
                    if choice < 1:
                        raise ValueError()
                except ValueError:
                    self.warning("Not a valid choice. Try again!")
                    continue
                try:
                    selected = decisions[choice - 1]
                except IndexError:
                    self.warning("Number not found. Try again!")
                    continue

                chain_id = selected.find("./chainAvailable").text

                try:
                    client.execute_unit(package_id, chain_id)
                    break
                except Exception:
                    self.error("There was a problem executing the selected choice")

    def admin_user(self):
        UserModel = get_user_model()
        return UserModel.objects.filter(is_superuser=True).first()

    def prompt_package_choice(self):
        """Prompts the user to choose a package."""
        self.stdout.write("╔═════════════════════════════════════╗")
        self.stdout.write("║ [q] to quit                         ║")
        self.stdout.write("║ [u] to update                       ║")
        self.stdout.write("║     or number to choose a package.  ║")
        self.stdout.write("╚═════════════════════════════════════╝")
        return input("Please enter your choice: ")

    def prompt_decision_choice(self, decision):
        """Prompts the user to resolve a pending package."""
        self.stdout.write("╔═════════════════════════════════════╗")
        self.stdout.write("║ [q] to quit                         ║")
        self.stdout.write("║     or number to choose a decision. ║")
        self.stdout.write("╚═════════════════════════════════════╝")
        return input("Please enter your choice: ")

    def print_pending_packages(self, packages):
        for idx, choice in enumerate(packages.getchildren(), 1):
            package_type = choice.find("./unit/type").text
            package_id = choice.find("./unit/unitXML/UUID").text
            self.stdout.write(f" [{idx}] {package_type} {package_id}")

    def print_pending_job_decisions(self, package_type, package_id, job, decisions):
        self.stdout.write(f"{package_type}: {package_id}")
        self.stdout.write(f"Job: {job}")
        for idx, choice in enumerate(decisions.getchildren(), 1):
            description = choice.find("./description").text
            self.stdout.write(f" [{idx}] {description}")
