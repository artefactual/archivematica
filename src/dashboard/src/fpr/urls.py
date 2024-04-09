from django.urls import path
from django.urls import re_path
from fpr import views

app_name = "fpr"
urlpatterns = [
    path("", views.home, name="fpr_index"),
    re_path(
        r"^(?P<category>format|formatgroup|idrule|idcommand|fprule|fpcommand)/<uuid:uuid>/toggle_enabled/$",
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
    path(
        "formatgroup/<slug:slug>/",
        views.formatgroup_edit,
        name="formatgroup_edit",
    ),
    path(
        "formatgroup/delete/<slug:slug>/",
        views.formatgroup_delete,
        name="formatgroup_delete",
    ),
    # ID Tools
    path("idtool/", views.idtool_list, name="idtool_list"),
    path("idtool/create/", views.idtool_edit, name="idtool_create"),
    path("idtool/<slug:slug>/", views.idtool_detail, name="idtool_detail"),
    path("idtool/<slug:slug>/edit/", views.idtool_edit, name="idtool_edit"),
    # ID Rules
    path("idrule/", views.idrule_list, name="idrule_list"),
    path("idrule/create/", views.idrule_edit, name="idrule_create"),
    path(
        "idrule/<uuid:uuid>/edit/",
        views.idrule_edit,
        name="idrule_edit",
    ),
    path(
        "idrule/<uuid:uuid>/",
        views.idrule_detail,
        name="idrule_detail",
    ),
    path(
        "idrule/<uuid:uuid>/delete/",
        views.idrule_delete,
        name="idrule_delete",
    ),
    # ID Commands
    path("idcommand/", views.idcommand_list, name="idcommand_list"),
    path("idcommand/create/", views.idcommand_edit, name="idcommand_create"),
    path(
        "idcommand/<uuid:uuid>/",
        views.idcommand_detail,
        name="idcommand_detail",
    ),
    path(
        "idcommand/<uuid:uuid>/edit/",
        views.idcommand_edit,
        name="idcommand_edit",
    ),
    path(
        "idcommand/<uuid:uuid>/delete/",
        views.idcommand_delete,
        name="idcommand_delete",
    ),
    # FP Rules
    path(
        "fprule/<uuid:uuid>/",
        views.fprule_detail,
        name="fprule_detail",
    ),
    path("fprule/create/", views.fprule_edit, name="fprule_create"),
    path("fprule/", views.fprule_list, name="fprule_list"),
    path("fprule/<usage>/", views.fprule_list, name="fprule_list"),
    path(
        "fprule/<uuid:uuid>/edit/",
        views.fprule_edit,
        name="fprule_edit",
    ),
    path(
        "fprule/<uuid:uuid>/delete/",
        views.fprule_delete,
        name="fprule_delete",
    ),
    # FP Tools
    path("fptool/", views.fptool_list, name="fptool_list"),
    path("fptool/create/", views.fptool_edit, name="fptool_create"),
    path("fptool/<slug>)/", views.fptool_detail, name="fptool_detail"),
    path("fptool/<slug>/edit/", views.fptool_edit, name="fptool_edit"),
    # FP Commands
    path(
        "fpcommand/<uuid:uuid>/",
        views.fpcommand_detail,
        name="fpcommand_detail",
    ),
    path("fpcommand/create/", views.fpcommand_edit, name="fpcommand_create"),
    path("fpcommand/<usage>/", views.fpcommand_list, name="fpcommand_list"),
    path("fpcommand/", views.fpcommand_list, name="fpcommand_list"),
    path(
        "fpcommand/<uuid:uuid>/edit/",
        views.fpcommand_edit,
        name="fpcommand_edit",
    ),
    path(
        "fpcommand/<uuid:uuid>/delete/",
        views.fpcommand_delete,
        name="fpcommand_delete",
    ),
    # Revisions
    path(
        "revisions/<entity_name>/<uuid:uuid>/",
        views.revision_list,
        name="revision_list",
    ),
]
