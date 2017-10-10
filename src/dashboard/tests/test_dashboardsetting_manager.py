from main.models import DashboardSetting

import pytest


@pytest.mark.django_db
def test_dashboardsetting_set_simple_dict():
    scope = 'test_simple_dict'
    data = {'url': 'https://archivematica.org', 'key': 'OhZei6ne8boh'}

    DashboardSetting.objects.set_dict(scope, data)

    assert DashboardSetting.objects.filter(scope=scope).count() == len(data)
    assert DashboardSetting.objects.get(scope=scope, name='url').value == unicode(data['url'])
    assert DashboardSetting.objects.get(scope=scope, name='key').value == unicode(data['key'])

    with pytest.raises(DashboardSetting.DoesNotExist):
        DashboardSetting.objects.get(scope=scope, name='unknown')


@pytest.mark.django_db
def test_dashboardsetting_set_complex_dict():

    class Point(object):
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def __unicode__(self):
            return u'POINT (x={},y={})'.format(self.x, self.y)

    scope = 'test_complex_dict'
    data = {'hidden': False, 'hours': 15.20, 'path': [Point(1, 2), Point(1, 4)]}

    DashboardSetting.objects.set_dict(scope, data)

    assert DashboardSetting.objects.get(scope=scope, name='hidden').value == unicode(data['hidden'])
    assert DashboardSetting.objects.get(scope=scope, name='hours').value == unicode(data['hours'])
    assert DashboardSetting.objects.get(scope=scope, name='path').value == unicode(data['path'])


@pytest.mark.django_db
def test_dashboardsetting_get_dict():
    scope = 'test_simple_dict'
    data = {'url': 'https://archivematica.org', 'key': 'OhZei6ne8boh'}

    DashboardSetting.objects.set_dict(scope, data)
    ret = DashboardSetting.objects.get_dict(scope)

    assert isinstance(ret, dict)
    assert len(ret) == len(data)
    assert u'url' in ret.keys()
    assert u'key' in ret.keys()
    assert ret['url'] == unicode(data['url'])
    assert ret['key'] == unicode(data['key'])


@pytest.mark.django_db
def test_dashboardsetting_get_unknown_dict():
    ret = DashboardSetting.objects.get_dict('unknown_dict')

    assert isinstance(ret, dict)
    assert bool(ret) is False


@pytest.mark.django_db
def test_dashboardsetting_unset_dict():
    scope = 'test_translations_es_dict'
    data = {'Polish': 'Polaco', 'Italian': 'Italiano'}

    DashboardSetting.objects.set_dict(scope, data)
    DashboardSetting.objects.unset_dict(scope)

    assert DashboardSetting.objects.filter(scope=scope).count() == 0
