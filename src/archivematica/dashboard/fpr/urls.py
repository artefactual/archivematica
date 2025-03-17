from django.urls import path
from django.urls import re_path
from fpr import views

UUID_REGEX = r"[\w]{8}(-[\w]{4}){3}-[\w]{12}"

app_name = "fpr"
urlpatterns = [
    path("", views.home, name="fpr_index"),
    re_path(
        r"^(?P<category>format|formatgroup|idrule|idcommand|fprule|fpcommand)/(?P<uuid>"
        + UUID_REGEX
        + ")/toggle_enabled/$",
        views.toggle_enabled,
        name="toggle_enabled",
    ),
    # Formats
    path("format/", views.format_list, name="format_list"),
    path("format/create/", views.format_edit, name="format_create"),
    re_path(r"^format/(?P<slug>[-\w]+)/$", views.format_detail, name="format_detail"),
    re_path(r"^format/(?P<slug>[-\w]+)/edit/$", views.format_edit, name="format_edit"),
    # Format Versions
    re_path(
        r"^format/(?P<format_slug>[-\w]+)/create/$",
        views.formatversion_edit,
        name="formatversion_create",
    ),
    re_path(
        r"^format/(?P<format_slug>[-\w]+)/(?P<slug>[-\w]+)/$",
        views.formatversion_detail,
        name="formatversion_detail",
    ),
    re_path(
        r"^format/(?P<format_slug>[-\w]+)/(?P<slug>[-\w]+)/edit/$",
        views.formatversion_edit,
        name="formatversion_edit",
    ),
    re_path(
        r"^format/(?P<format_slug>[-\w]+)/(?P<slug>[-\w]+)/delete/$",
        views.formatversion_delete,
        name="formatversion_delete",
    ),
    # Format groups
    path("formatgroup/", views.formatgroup_list, name="formatgroup_list"),
    path("formatgroup/create/", views.formatgroup_edit, name="formatgroup_create"),
    re_path(
        r"^formatgroup/(?P<slug>[-\w]+)/$",
        views.formatgroup_edit,
        name="formatgroup_edit",
    ),
    re_path(
        r"^formatgroup/delete/(?P<slug>[-\w]+)/$",
        views.formatgroup_delete,
        name="formatgroup_delete",
    ),
    # ID Tools
    path("idtool/", views.idtool_list, name="idtool_list"),
    path("idtool/create/", views.idtool_edit, name="idtool_create"),
    re_path(r"^idtool/(?P<slug>[-\w]+)/$", views.idtool_detail, name="idtool_detail"),
    re_path(r"^idtool/(?P<slug>[-\w]+)/edit/$", views.idtool_edit, name="idtool_edit"),
    # ID Rules
    path("idrule/", views.idrule_list, name="idrule_list"),
    path("idrule/create/", views.idrule_edit, name="idrule_create"),
    re_path(
        r"^idrule/(?P<uuid>" + UUID_REGEX + ")/edit/$",
        views.idrule_edit,
        name="idrule_edit",
    ),
    re_path(
        r"^idrule/(?P<uuid>" + UUID_REGEX + ")/$",
        views.idrule_detail,
        name="idrule_detail",
    ),
    re_path(
        r"^idrule/(?P<uuid>" + UUID_REGEX + ")/delete/$",
        views.idrule_delete,
        name="idrule_delete",
    ),
    # ID Commands
    path("idcommand/", views.idcommand_list, name="idcommand_list"),
    path("idcommand/create/", views.idcommand_edit, name="idcommand_create"),
    re_path(
        r"^idcommand/(?P<uuid>" + UUID_REGEX + ")/$",
        views.idcommand_detail,
        name="idcommand_detail",
    ),
    re_path(
        r"^idcommand/(?P<uuid>" + UUID_REGEX + ")/edit/$",
        views.idcommand_edit,
        name="idcommand_edit",
    ),
    re_path(
        r"^idcommand/(?P<uuid>" + UUID_REGEX + ")/delete/$",
        views.idcommand_delete,
        name="idcommand_delete",
    ),
    # FP Rules
    re_path(
        r"^fprule/(?P<uuid>" + UUID_REGEX + ")/$",
        views.fprule_detail,
        name="fprule_detail",
    ),
    path("fprule/create/", views.fprule_edit, name="fprule_create"),
    path("fprule/", views.fprule_list, name="fprule_list"),
    re_path(r"^fprule/(?P<usage>[-\w]+)/$", views.fprule_list, name="fprule_list"),
    re_path(
        r"^fprule/(?P<uuid>" + UUID_REGEX + ")/edit/$",
        views.fprule_edit,
        name="fprule_edit",
    ),
    re_path(
        r"^fprule/(?P<uuid>" + UUID_REGEX + ")/delete/$",
        views.fprule_delete,
        name="fprule_delete",
    ),
    # FP Tools
    path("fptool/", views.fptool_list, name="fptool_list"),
    path("fptool/create/", views.fptool_edit, name="fptool_create"),
    re_path(r"^fptool/(?P<slug>[-\w]+)/$", views.fptool_detail, name="fptool_detail"),
    re_path(r"^fptool/(?P<slug>[-\w]+)/edit/$", views.fptool_edit, name="fptool_edit"),
    # FP Commands
    re_path(
        r"^fpcommand/(?P<uuid>" + UUID_REGEX + ")/$",
        views.fpcommand_detail,
        name="fpcommand_detail",
    ),
    path("fpcommand/create/", views.fpcommand_edit, name="fpcommand_create"),
    re_path(
        r"^fpcommand/(?P<usage>[-\w]+)/$", views.fpcommand_list, name="fpcommand_list"
    ),
    path("fpcommand/", views.fpcommand_list, name="fpcommand_list"),
    re_path(
        r"^fpcommand/(?P<uuid>" + UUID_REGEX + ")/edit/$",
        views.fpcommand_edit,
        name="fpcommand_edit",
    ),
    re_path(
        r"^fpcommand/(?P<uuid>" + UUID_REGEX + ")/delete/$",
        views.fpcommand_delete,
        name="fpcommand_delete",
    ),
    # Revisions
    re_path(
        r"^revisions/(?P<entity_name>[-\w]+)/(?P<uuid>" + UUID_REGEX + ")/$",
        views.revision_list,
        name="revision_list",
    ),
]
