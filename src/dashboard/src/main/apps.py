from django.apps import AppConfig


class MainAppConfig(AppConfig):
    name = "main"

    def ready(self):
        import main.signals  # noqa: F401
