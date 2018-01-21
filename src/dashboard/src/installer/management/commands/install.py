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

from __future__ import print_function
from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError
from django.http import QueryDict

from components import helpers
from components.administration.forms import StorageSettingsForm
from installer.steps import create_super_user, download_fpr_rules, setup_pipeline, setup_pipeline_in_ss, submit_fpr_agent


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--email', required=True)
        parser.add_argument('--password', required=True)
        parser.add_argument('--api-key', required=True)
        parser.add_argument('--org-name', required=True)
        parser.add_argument('--org-id', required=True)
        parser.add_argument('--ss-url', required=True)
        parser.add_argument('--ss-user', required=True)
        parser.add_argument('--ss-api-key', required=True)
        parser.add_argument('--whitelist', required=False)

    def save_ss_settings(self, options):
        POST = QueryDict('', mutable=True)
        POST.update({
            'storage_service_url': options['ss_url'],
            'storage_service_user': options['ss_user'],
            'storage_service_apikey': options['ss_api_key'],
        })
        form = StorageSettingsForm(POST)
        if not form.is_valid():
            raise CommandError('SS attributes are invalid')
        form.save()

    def handle(self, *args, **options):
        setup_pipeline(options['org_name'], options['org_id'])
        create_super_user(options['username'], options['email'], options['password'], options['api_key'])
        submit_fpr_agent()
        download_fpr_rules()
        self.save_ss_settings(options)
        setup_pipeline_in_ss(use_default_config=True)
        helpers.set_setting('api_whitelist', options['whitelist'])
