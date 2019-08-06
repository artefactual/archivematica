# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.contrib import messages
from django.shortcuts import render
from django.utils.translation import ugettext as _

from components.administration.forms_dip_upload import (
    ArchivesSpaceConfigForm,
    AtomConfigForm,
)
from main.models import DashboardSetting


_AS_DICTNAME = "upload-archivesspace_v0.0"
_ATOM_DICTNAME = "upload-qubit_v0.0"


def admin_as(request):
    """ View to configure ArchivesSpace DIP upload. """
    if request.method == "POST":
        form = ArchivesSpaceConfigForm(request.POST)
        if form.is_valid():
            DashboardSetting.objects.set_dict(_AS_DICTNAME, form.cleaned_data)
            messages.info(request, _("Saved."))
    else:
        form = ArchivesSpaceConfigForm(
            initial=DashboardSetting.objects.get_dict(_AS_DICTNAME)
        )
    return render(request, "administration/dips_as_edit.html", {"form": form})


def admin_atom(request):
    """ View to configure AtoM DIP upload. """
    if request.method == "POST":
        form = AtomConfigForm(request.POST)
        if form.is_valid():
            DashboardSetting.objects.set_dict(_ATOM_DICTNAME, form.cleaned_data)
            messages.info(request, _("Saved."))
    else:
        form = AtomConfigForm(initial=DashboardSetting.objects.get_dict(_ATOM_DICTNAME))
    return render(request, "administration/dips_atom_edit.html", {"form": form})
