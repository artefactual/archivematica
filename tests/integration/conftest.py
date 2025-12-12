import pytest
from django.contrib.auth.models import AbstractUser


@pytest.fixture
def user(django_user_model: type[AbstractUser]) -> AbstractUser:
    user = django_user_model.objects.create(
        username="foobar",
        email="foobar@example.com",
        first_name="Foo",
        last_name="Bar",
    )
    user.set_password("foobar1A,")
    user.save()

    return user
