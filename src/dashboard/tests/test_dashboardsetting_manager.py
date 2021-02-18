# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from main.models import DashboardSetting

import pytest
import six


@pytest.mark.django_db
def test_dashboardsetting_set_simple_dict():
    scope = "test_simple_dict"
    data = {"url": "https://archivematica.org", "key": "OhZei6ne8boh"}

    DashboardSetting.objects.set_dict(scope, data)

    assert DashboardSetting.objects.filter(scope=scope).count() == len(data)
    assert DashboardSetting.objects.get(scope=scope, name="url").value == six.text_type(
        data["url"]
    )
    assert DashboardSetting.objects.get(scope=scope, name="key").value == six.text_type(
        data["key"]
    )

    with pytest.raises(DashboardSetting.DoesNotExist):
        DashboardSetting.objects.get(scope=scope, name="unknown")


@pytest.mark.django_db
def test_dashboardsetting_set_complex_dict():
    @six.python_2_unicode_compatible
    class Point(object):
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def __str__(self):
            return "POINT (x={},y={})".format(self.x, self.y)

    scope = "test_complex_dict"
    data = {"hidden": False, "hours": 15.20, "path": [Point(1, 2), Point(1, 4)]}

    DashboardSetting.objects.set_dict(scope, data)

    assert DashboardSetting.objects.get(
        scope=scope, name="hidden"
    ).value == six.text_type(data["hidden"])
    assert DashboardSetting.objects.get(
        scope=scope, name="hours"
    ).value == six.text_type(data["hours"])
    assert DashboardSetting.objects.get(
        scope=scope, name="path"
    ).value == six.text_type(data["path"])


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
    assert ret["url"] == six.text_type(data["url"])
    assert ret["key"] == six.text_type(data["key"])


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
