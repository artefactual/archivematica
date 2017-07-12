import ConfigParser

from django.core.exceptions import ImproperlyConfigured

from env_configparser import EnvConfigParser


class Config(object):
    """Configuration helper for MCPServer, MCPClient and Dashboard.

    It wraps EnvConfigParser. It is used in the following files:

        - MCPClient/lib/settings/common.py
        - MCPServer/lib/settings/common.py
        - Dashboard/src/settings/common.py
    """
    def __init__(self, env_prefix, attrs):
        self.config = EnvConfigParser(prefix=env_prefix)
        self.attrs = attrs

    def read_defaults(self, fp):
        self.config.readfp(fp)

    def read_files(self, files):
        self.config.read(files)

    def get(self, attr, default=None):
        if attr not in self.attrs:
            raise ImproperlyConfigured('Unknown attribute: %s. Make sure the '
                                       'attribute has been included in the '
                                       'attribute list.' % attr)

        attr_opts = self.attrs[attr]
        if not all(k in attr_opts for k in ('section', 'option', 'type')):
            raise ImproperlyConfigured('Invalid attribute: %s. Make sure the '
                                       'entry in the attribute has all the '
                                       'fields needed (section, option, '
                                       'type).' % attr)

        getter = 'get{}'.format('' if attr_opts['type'] == 'string' else attr_opts['type'])
        kwargs = {'section': attr_opts['section'], 'option': attr_opts['option']}
        if default is not None:
            kwargs['fallback'] = default
        elif 'default' in attr_opts:
            kwargs['fallback'] = attr_opts['default']

        try:
            return getattr(self.config, getter)(**kwargs)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            raise ImproperlyConfigured('The following configuration attribute '
                                       'must be defined: %s.' % attr)
