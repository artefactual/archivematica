# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf.urls import url

from fpr import views

UUID_REGEX = r"[\w]{8}(-[\w]{4}){3}-[\w]{12}"

app_name = "fpr"
urlpatterns = [
    url(r"^$", views.home, name="fpr_index"),
    url(
        r"^(?P<category>format|formatgroup|idrule|idcommand|fprule|fpcommand)/(?P<uuid>"
        + UUID_REGEX
        + ")/toggle_enabled/$",
        views.toggle_enabled,
        name="toggle_enabled",
    ),
    # Formats
    url(r"^format/$", views.format_list, name="format_list"),
    url(r"^format/create/$", views.format_edit, name="format_create"),
    url(r"^format/(?P<slug>[-\w]+)/$", views.format_detail, name="format_detail"),
    url(r"^format/(?P<slug>[-\w]+)/edit/$", views.format_edit, name="format_edit"),
    # Format Versions
    url(
        r"^format/(?P<format_slug>[-\w]+)/create/$",
        views.formatversion_edit,
        name="formatversion_create",
    ),
    url(
        r"^format/(?P<format_slug>[-\w]+)/(?P<slug>[-\w]+)/$",
        views.formatversion_detail,
        name="formatversion_detail",
    ),
    url(
        r"^format/(?P<format_slug>[-\w]+)/(?P<slug>[-\w]+)/edit/$",
        views.formatversion_edit,
        name="formatversion_edit",
    ),
    url(
        r"^format/(?P<format_slug>[-\w]+)/(?P<slug>[-\w]+)/delete/$",
        views.formatversion_delete,
        name="formatversion_delete",
    ),
    # Format groups
    url(r"^formatgroup/$", views.formatgroup_list, name="formatgroup_list"),
    url(r"^formatgroup/create/$", views.formatgroup_edit, name="formatgroup_create"),
    url(
        r"^formatgroup/(?P<slug>[-\w]+)/$",
        views.formatgroup_edit,
        name="formatgroup_edit",
    ),
    url(
        r"^formatgroup/delete/(?P<slug>[-\w]+)/$",
        views.formatgroup_delete,
        name="formatgroup_delete",
    ),
    # ID Tools
    url(r"^idtool/$", views.idtool_list, name="idtool_list"),
    url(r"^idtool/create/$", views.idtool_edit, name="idtool_create"),
    url(r"^idtool/(?P<slug>[-\w]+)/$", views.idtool_detail, name="idtool_detail"),
    url(r"^idtool/(?P<slug>[-\w]+)/edit/$", views.idtool_edit, name="idtool_edit"),
    # ID Rules
    url(r"^idrule/$", views.idrule_list, name="idrule_list"),
    url(r"^idrule/create/$", views.idrule_edit, name="idrule_create"),
    url(
        r"^idrule/(?P<uuid>" + UUID_REGEX + ")/edit/$",
        views.idrule_edit,
        name="idrule_edit",
    ),
    url(
        r"^idrule/(?P<uuid>" + UUID_REGEX + ")/$",
        views.idrule_detail,
        name="idrule_detail",
    ),
    url(
        r"^idrule/(?P<uuid>" + UUID_REGEX + ")/delete/$",
        views.idrule_delete,
        name="idrule_delete",
    ),
    # ID Commands
    url(r"^idcommand/$", views.idcommand_list, name="idcommand_list"),
    url(r"^idcommand/create/$", views.idcommand_edit, name="idcommand_create"),
    url(
        r"^idcommand/(?P<uuid>" + UUID_REGEX + ")/$",
        views.idcommand_detail,
        name="idcommand_detail",
    ),
    url(
        r"^idcommand/(?P<uuid>" + UUID_REGEX + ")/edit/$",
        views.idcommand_edit,
        name="idcommand_edit",
    ),
    url(
        r"^idcommand/(?P<uuid>" + UUID_REGEX + ")/delete/$",
        views.idcommand_delete,
        name="idcommand_delete",
    ),
    # FP Rules
    url(
        r"^fprule/(?P<uuid>" + UUID_REGEX + ")/$",
        views.fprule_detail,
        name="fprule_detail",
    ),
    url(r"^fprule/create/$", views.fprule_edit, name="fprule_create"),
    url(r"^fprule/$", views.fprule_list, name="fprule_list"),
    url(r"^fprule/(?P<usage>[-\w]+)/$", views.fprule_list, name="fprule_list"),
    url(
        r"^fprule/(?P<uuid>" + UUID_REGEX + ")/edit/$",
        views.fprule_edit,
        name="fprule_edit",
    ),
    url(
        r"^fprule/(?P<uuid>" + UUID_REGEX + ")/delete/$",
        views.fprule_delete,
        name="fprule_delete",
    ),
    # FP Tools
    url(r"^fptool/$", views.fptool_list, name="fptool_list"),
    url(r"^fptool/create/$", views.fptool_edit, name="fptool_create"),
    url(r"^fptool/(?P<slug>[-\w]+)/$", views.fptool_detail, name="fptool_detail"),
    url(r"^fptool/(?P<slug>[-\w]+)/edit/$", views.fptool_edit, name="fptool_edit"),
    # FP Commands
    url(
        r"^fpcommand/(?P<uuid>" + UUID_REGEX + ")/$",
        views.fpcommand_detail,
        name="fpcommand_detail",
    ),
    url(r"^fpcommand/create/$", views.fpcommand_edit, name="fpcommand_create"),
    url(r"^fpcommand/(?P<usage>[-\w]+)/$", views.fpcommand_list, name="fpcommand_list"),
    url(r"^fpcommand/$", views.fpcommand_list, name="fpcommand_list"),
    url(
        r"^fpcommand/(?P<uuid>" + UUID_REGEX + ")/edit/$",
        views.fpcommand_edit,
        name="fpcommand_edit",
    ),
    url(
        r"^fpcommand/(?P<uuid>" + UUID_REGEX + ")/delete/$",
        views.fpcommand_delete,
        name="fpcommand_delete",
    ),
    # Revisions
    url(
        r"^revisions/(?P<entity_name>[-\w]+)/(?P<uuid>" + UUID_REGEX + ")/$",
        views.revision_list,
        name="revision_list",
    ),
]
