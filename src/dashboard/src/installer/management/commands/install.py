# -*- coding: utf-8 -*-
# This file is part of Archivematica.
#
# Copyright 2010-2016 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import, print_function, unicode_literals

from django.core.management.base import BaseCommand, CommandError
from django.http import QueryDict
from django.utils import termcolors

from components import helpers
from components.administration.forms import StorageSettingsForm
from installer.steps import create_super_user, setup_pipeline, setup_pipeline_in_ss


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--api-key", required=True)
        parser.add_argument("--org-name", required=True)
        parser.add_argument("--org-id", required=True)
        parser.add_argument("--ss-url", required=True)
        parser.add_argument("--ss-user", required=True)
        parser.add_argument("--ss-api-key", required=True)
        parser.add_argument(
            "--whitelist",
            required=False,
            help="Deprecated. Please use --allowlist instead.",
        )
        parser.add_argument("--allowlist", required=False)
        parser.add_argument("--site-url", required=False)

    def save_ss_settings(self, options):
        POST = QueryDict("", mutable=True)
        POST.update(
            {
                "storage_service_url": options["ss_url"],
                "storage_service_user": options["ss_user"],
                "storage_service_apikey": options["ss_api_key"],
            }
        )
        form = StorageSettingsForm(POST)
        if not form.is_valid():
            raise CommandError("SS attributes are invalid")
        form.save()

    def handle(self, *args, **options):
        # Not needed in Django 1.9+.
        self.style.SUCCESS = termcolors.make_style(opts=("bold",), fg="green")

        setup_pipeline(options["org_name"], options["org_id"], options["site_url"])
        create_super_user(
            options["username"],
            options["email"],
            options["password"],
            options["api_key"],
        )
        self.save_ss_settings(options)
        setup_pipeline_in_ss(use_default_config=True)
        helpers.set_api_allowlist(options["whitelist"] or options["allowlist"])
        self.stdout.write(self.style.SUCCESS("Done!\n"))
