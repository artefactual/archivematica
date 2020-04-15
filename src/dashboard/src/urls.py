# -*- coding: utf-8 -*-
# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
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
from __future__ import absolute_import

from django.urls import re_path, include
from django.conf import settings


urlpatterns = [
    re_path(r"^mcp/", include("components.mcp.urls")),
    re_path(r"^installer/", include("installer.urls")),
    re_path(r"^administration/accounts/", include("components.accounts.urls")),
    re_path(r"^archival-storage/", include("components.archival_storage.urls")),
    re_path(r"^fpr/", include("fpr.urls")),
    re_path(
        r"^(?P<unit_type>transfer|ingest)/", include("components.unit.urls")
    ),  # URLs common to transfer & ingest
    re_path(
        r"^transfer/(?P<uuid>" + settings.UUID_REGEX + ")/rights/",
        include("components.rights.transfer_urls"),
    ),
    re_path(r"^transfer/", include("components.transfer.urls")),
    re_path(r"^appraisal/", include("components.appraisal.urls")),
    re_path(
        r"^ingest/(?P<uuid>" + settings.UUID_REGEX + ")/rights/",
        include("components.rights.ingest_urls"),
    ),
    re_path(r"^ingest/", include("components.ingest.urls")),
    re_path(r"^administration/", include("components.administration.urls")),
    re_path(r"^filesystem/", include("components.filesystem_ajax.urls")),
    re_path(r"^api/", include("components.api.urls")),
    re_path(r"^file/", include("components.file.urls")),
    re_path(r"^access/", include("components.access.urls")),
    re_path(r"^backlog/", include("components.backlog.urls")),
    re_path(r"", include("main.urls")),
]

if settings.PROMETHEUS_ENABLED:
    # Include prometheus metrics at /metrics
    urlpatterns.append(re_path("", include("django_prometheus.urls")))
