from django.apps import AppConfig


class MainAppConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "archivematica.dashboard.main"

    def ready(self):
        import archivematica.dashboard.main.signals  # noqa: F401
