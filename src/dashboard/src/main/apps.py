# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.apps import AppConfig


class MainAppConfig(AppConfig):
    name = "main"

    def ready(self):
        import main.signals  # noqa: F401
