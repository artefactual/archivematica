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
import django.contrib.auth.views
from components.accounts import views
from django.conf import settings
from django.urls import path

app_name = "accounts"
urlpatterns = [
    path("", views.list, name="accounts_index"),
    path("add/", views.add, name="add"),
    path("<int:id>/delete/", views.delete, name="delete"),
    path("<int:id>/edit/", views.edit, name="edit"),
    path("profile/", views.profile, name="profile"),
    path("list/", views.list),
]

if "django_cas_ng" in settings.INSTALLED_APPS:
    import django_cas_ng.views

    urlpatterns += [
        path("login/", django_cas_ng.views.LoginView.as_view(), name="login"),
        path("logout/", django_cas_ng.views.LogoutView.as_view(), name="logout"),
    ]

elif "mozilla_django_oidc" in settings.INSTALLED_APPS:
    from components.accounts.views import CustomOIDCLogoutView

    urlpatterns += [
        path(
            "login/",
            django.contrib.auth.views.LoginView.as_view(
                template_name="accounts/login.html"
            ),
            name="login",
        ),
        path(
            "logout/",
            CustomOIDCLogoutView.as_view(),
            name="logout",
        ),
    ]

else:
    urlpatterns += [
        path(
            "login/",
            django.contrib.auth.views.LoginView.as_view(
                template_name="accounts/login.html"
            ),
            name="login",
        ),
        path("logout/", django.contrib.auth.views.logout_then_login, name="logout"),
    ]
