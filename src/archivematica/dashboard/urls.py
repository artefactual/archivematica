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
    path("mcp/", include("components.mcp.urls")),
    path("installer/", include("installer.urls")),
    path("administration/accounts/", include("components.accounts.urls")),
    path("archival-storage/", include("components.archival_storage.urls")),
    path("fpr/", include("fpr.urls")),
    re_path(
        r"^(?P<unit_type>transfer|ingest)/", include("components.unit.urls")
    ),  # URLs common to transfer & ingest
    re_path(
        r"^transfer/(?P<uuid>" + settings.UUID_REGEX + ")/rights/",
        include("components.rights.transfer_urls"),
    ),
    path("transfer/", include("components.transfer.urls")),
    path("appraisal/", include("components.appraisal.urls")),
    re_path(
        r"^ingest/(?P<uuid>" + settings.UUID_REGEX + ")/rights/",
        include("components.rights.ingest_urls"),
    ),
    path("ingest/", include("components.ingest.urls")),
    path("administration/", include("components.administration.urls")),
    path("filesystem/", include("components.filesystem_ajax.urls")),
    path("api/", include("components.api.urls")),
    path("file/", include("components.file.urls")),
    path("access/", include("components.access.urls")),
    path("backlog/", include("components.backlog.urls")),
    path("", include("main.urls")),
]

if settings.PROMETHEUS_ENABLED:
    # Include prometheus metrics at /metrics
    urlpatterns += [path("", include("django_prometheus.urls"))]

if settings.OIDC_AUTHENTICATION:
    urlpatterns += [path("oidc/", include("mozilla_django_oidc.urls"))]

if "shibboleth" in settings.INSTALLED_APPS:
    urlpatterns += [path("shib/", include("shibboleth.urls"))]
