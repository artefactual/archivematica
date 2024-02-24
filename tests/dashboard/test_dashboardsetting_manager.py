import pytest
from main.models import DashboardSetting


@pytest.mark.django_db
def test_dashboardsetting_set_simple_dict():
    scope = "test_simple_dict"
    data = {"url": "https://archivematica.org", "key": "OhZei6ne8boh"}

    DashboardSetting.objects.set_dict(scope, data)

    assert DashboardSetting.objects.filter(scope=scope).count() == len(data)
    assert DashboardSetting.objects.get(scope=scope, name="url").value == str(
        data["url"]
    )
    assert DashboardSetting.objects.get(scope=scope, name="key").value == str(
        data["key"]
    )

    with pytest.raises(DashboardSetting.DoesNotExist):
        DashboardSetting.objects.get(scope=scope, name="unknown")


@pytest.mark.django_db
def test_dashboardsetting_set_complex_dict():
    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def __str__(self):
            return f"POINT (x={self.x},y={self.y})"

    scope = "test_complex_dict"
    data = {"hidden": False, "hours": 15.20, "path": [Point(1, 2), Point(1, 4)]}

    DashboardSetting.objects.set_dict(scope, data)

    assert DashboardSetting.objects.get(scope=scope, name="hidden").value == str(
        data["hidden"]
    )
    assert DashboardSetting.objects.get(scope=scope, name="hours").value == str(
        data["hours"]
    )
    assert DashboardSetting.objects.get(scope=scope, name="path").value == str(
        data["path"]
    )


@pytest.mark.django_db
def test_dashboardsetting_get_dict():
    scope = "test_simple_dict"
    data = {"url": "https://archivematica.org", "key": "OhZei6ne8boh"}

    DashboardSetting.objects.set_dict(scope, data)
    ret = DashboardSetting.objects.get_dict(scope)

    assert isinstance(ret, dict)
    assert len(ret) == len(data)
    assert "url" in list(ret.keys())
    assert "key" in list(ret.keys())
    assert ret["url"] == str(data["url"])
    assert ret["key"] == str(data["key"])


@pytest.mark.django_db
def test_dashboardsetting_get_unknown_dict():
    ret = DashboardSetting.objects.get_dict("unknown_dict")

    assert isinstance(ret, dict)
    assert bool(ret) is False


@pytest.mark.django_db
def test_dashboardsetting_unset_dict():
    scope = "test_translations_es_dict"
    data = {"Polish": "Polaco", "Italian": "Italiano"}

    DashboardSetting.objects.set_dict(scope, data)
    DashboardSetting.objects.unset_dict(scope)

    assert DashboardSetting.objects.filter(scope=scope).count() == 0
