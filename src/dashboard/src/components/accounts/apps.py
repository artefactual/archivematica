from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "components.accounts"
    verbose_name = "Dashboard Accounts"

    def ready(self):
        try:
            import components.accounts.signals  # noqa
        except ImportError:
            pass
