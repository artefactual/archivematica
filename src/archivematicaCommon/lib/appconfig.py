import ConfigParser

from django.core.exceptions import ImproperlyConfigured

from env_configparser import EnvConfigParser


class Config(object):
    """Configuration helper for MCPServer, MCPClient and Dashboard.

    It wraps EnvConfigParser. It is used in the following files:

        - MCPClient/lib/settings/common.py
        - MCPServer/lib/settings/common.py
        - Dashboard/src/settings/base.py
    """
    def __init__(self, env_prefix, attrs):
        self.config = EnvConfigParser(prefix=env_prefix)
        self.attrs = attrs

    INVALID_ATTR_MSG = ('Invalid attribute: %s. Make sure the entry in the'
                        ' attribute has all the fields needed (section, option,'
                        ' type).')

    UNDEFINED_ATTR_MSG = (
        'The following configuration attribute must be defined: %s.')

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
        if isinstance(attr_opts, list):
            return self.get_from_opts_list(attr, attr_opts, default=default)
        if not all(k in attr_opts for k in ('section', 'option', 'type')):
            raise ImproperlyConfigured(self.INVALID_ATTR_MSG % attr)

        getter = 'get{}'.format('' if attr_opts['type'] == 'string' else attr_opts['type'])
        kwargs = {'section': attr_opts['section'], 'option': attr_opts['option']}
        if default is not None:
            kwargs['fallback'] = default
        elif 'default' in attr_opts:
            kwargs['fallback'] = attr_opts['default']

        try:
            return getattr(self.config, getter)(**kwargs)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            raise ImproperlyConfigured(self.UNDEFINED_ATTR_MSG % attr)

    def get_from_opts_list(self, attr, attr_opts_list, default=None):
        if not all(all(
                k in attr_opts for k in ('section', 'option', 'type'))
                for attr_opts in attr_opts_list):
            raise ImproperlyConfigured(self.INVALID_ATTR_MSG % attr)
        opts = []
        for attr_opts in attr_opts_list:
            opt_type = attr_opts['type']
            getter = 'get{}'.format({'string': ''}.get(opt_type, opt_type))
            kwargs = {'section': attr_opts['section'],
                      'option': attr_opts['option']}
            if default is not None:
                kwargs['fallback'] = default
            elif 'default' in attr_opts:
                kwargs['fallback'] = attr_opts['default']
            try:
                opt = getattr(self.config, getter)(**kwargs)
            except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
                pass
            else:
                opts.append(opt)
        if opts:
            return opts[0]
        raise ImproperlyConfigured(self.UNDEFINED_ATTR_MSG % attr)
