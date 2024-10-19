from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "components.accounts"
    verbose_name = "Dashboard Accounts"

    def ready(self):
        try:
            import components.accounts.signals  # noqa
        except ImportError:
            pass
