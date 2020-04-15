# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.urls import re_path

from components.appraisal import views

app_name = "appraisal"
urlpatterns = [re_path(r"^$", views.appraisal, name="appraisal_index")]
