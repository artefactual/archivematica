from django.apps import AppConfig


class MainAppConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "main"

    def ready(self):
        import main.signals  # noqa: F401
