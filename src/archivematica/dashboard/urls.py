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
from django.conf import settings
from django.urls import include
from django.urls import path
from django.urls import re_path

urlpatterns = [
    path("mcp/", include("archivematica.dashboard.components.mcp.urls")),
    path("installer/", include("archivematica.dashboard.installer.urls")),
    path(
        "administration/accounts/",
        include("archivematica.dashboard.components.accounts.urls"),
    ),
    path(
        "archival-storage/",
        include("archivematica.dashboard.components.archival_storage.urls"),
    ),
    path("fpr/", include("archivematica.dashboard.fpr.urls")),
    re_path(
        r"^(?P<unit_type>transfer|ingest)/",
        include("archivematica.dashboard.components.unit.urls"),
    ),  # URLs common to transfer & ingest
    re_path(
        r"^transfer/(?P<uuid>" + settings.UUID_REGEX + ")/rights/",
        include("archivematica.dashboard.components.rights.transfer_urls"),
    ),
    path("transfer/", include("archivematica.dashboard.components.transfer.urls")),
    path("appraisal/", include("archivematica.dashboard.components.appraisal.urls")),
    re_path(
        r"^ingest/(?P<uuid>" + settings.UUID_REGEX + ")/rights/",
        include("archivematica.dashboard.components.rights.ingest_urls"),
    ),
    path("ingest/", include("archivematica.dashboard.components.ingest.urls")),
    path(
        "administration/",
        include("archivematica.dashboard.components.administration.urls"),
    ),
    path(
        "filesystem/",
        include("archivematica.dashboard.components.filesystem_ajax.urls"),
    ),
    path("api/", include("archivematica.dashboard.components.api.urls")),
    path("file/", include("archivematica.dashboard.components.file.urls")),
    path("access/", include("archivematica.dashboard.components.access.urls")),
    path("backlog/", include("archivematica.dashboard.components.backlog.urls")),
    path("", include("archivematica.dashboard.main.urls")),
]

if settings.PROMETHEUS_ENABLED:
    # Include prometheus metrics at /metrics
    urlpatterns += [path("", include("django_prometheus.urls"))]

if settings.OIDC_AUTHENTICATION:
    urlpatterns += [path("oidc/", include("mozilla_django_oidc.urls"))]

if "shibboleth" in settings.INSTALLED_APPS:
    urlpatterns += [path("shib/", include("shibboleth.urls"))]
