from shibboleth.backends import ShibbolethRemoteUserBackend
from tastypie.models import ApiKey


class CustomShibbolethRemoteUserBackend(ShibbolethRemoteUserBackend):
    def configure_user(self, user):
        api_key = ApiKey.objects.create(user=user)
        api_key.key = api_key.generate_key()
        api_key.save()
        return user
