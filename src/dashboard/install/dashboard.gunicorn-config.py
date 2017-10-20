# Documentation: http://docs.gunicorn.org/en/stable/configure.html
# Example: https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py

import os

# http://docs.gunicorn.org/en/stable/settings.html#user
user = os.environ.get('AM_GUNICORN_USER', 'archivematica')

# http://docs.gunicorn.org/en/stable/settings.html#group
group = os.environ.get('AM_GUNICORN_GROUP', 'archivematica')

# http://docs.gunicorn.org/en/stable/settings.html#bind
bind = os.environ.get('AM_GUNICORN_BIND', '127.0.0.1:8002')

# http://docs.gunicorn.org/en/stable/settings.html#workers
workers = os.environ.get('AM_GUNICORN_WORKERS', '1')

# http://docs.gunicorn.org/en/stable/settings.html#worker-class
worker_class = os.environ.get('AM_GUNICORN_WORKER_CLASS', 'gevent')

# http://docs.gunicorn.org/en/stable/settings.html#timeout
timeout = os.environ.get('AM_GUNICORN_TIMEOUT', '172800')

# http://docs.gunicorn.org/en/stable/settings.html#reload
reload = os.environ.get('AM_GUNICORN_RELOAD', 'false')

# http://docs.gunicorn.org/en/stable/settings.html#reload-engine
reload_engine = os.environ.get('AM_GUNICORN_RELOAD_ENGINE', 'auto')

# http://docs.gunicorn.org/en/stable/settings.html#chdir
chdir = os.environ.get('AM_GUNICORN_CHDIR', '/usr/share/archivematica/dashboard')

# http://docs.gunicorn.org/en/stable/settings.html#accesslog
accesslog = os.environ.get('AM_GUNICORN_ACCESSLOG', '/dev/null')

# http://docs.gunicorn.org/en/stable/settings.html#errorlog
errorlog = os.environ.get('AM_GUNICORN_ERRORLOG', '-')

# http://docs.gunicorn.org/en/stable/settings.html#loglevel
loglevel = os.environ.get('AM_GUNICORN_LOGLEVEL', 'info')

# http://docs.gunicorn.org/en/stable/settings.html#proc-name
proc_name = os.environ.get('AM_GUNICORN_PROC_NAME', 'archivematica-dashboard')

# http://docs.gunicorn.org/en/stable/settings.html#sendfile
sendfile = os.environ.get('AM_GUNICORN_SENDFILE', 'false')
