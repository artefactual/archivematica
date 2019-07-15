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

from django.http import HttpResponse
from lxml import etree

import rpc


def execute(request):
    if request.POST.get("uuid"):
        rpc.approve_job(
            request.POST.get("uuid"), request.POST.get("choice", ""), request.user.pk
        )

    return HttpResponse("", content_type="text/plain")


def list(request):
    response_xml = etree.Element("MCP")
    awaiting_approval = rpc.list_jobs_awaiting_approval()
    for element_str in awaiting_approval.job_xml:
        element = etree.fromstring(element_str)
        response_xml.append(element)

    response_str = etree.tostring(response_xml, pretty_print=True)
    return HttpResponse(response_str, content_type="text/xml")
