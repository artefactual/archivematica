# Documentation: http://docs.gunicorn.org/en/stable/configure.html
# Example: https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py

# http://docs.gunicorn.org/en/stable/settings.html#user
user = "archivematica"

# http://docs.gunicorn.org/en/stable/settings.html#group
group = "archivematica"

# http://docs.gunicorn.org/en/stable/settings.html#bind
bind = "127.0.0.1:8002"

# http://docs.gunicorn.org/en/stable/settings.html#workers
workers = "4"

# http://docs.gunicorn.org/en/stable/settings.html#timeout
timeout = "172800"

# http://docs.gunicorn.org/en/stable/settings.html#reload
reload = False

# http://docs.gunicorn.org/en/stable/settings.html#chdir
chdir = "/usr/share/archivematica/dashboard"

# http://docs.gunicorn.org/en/stable/settings.html#raw-env
raw_env = [
    "DJANGO_SETTINGS_MODULE=settings.common",
]

# http://docs.gunicorn.org/en/stable/settings.html#accesslog
accesslog = "/var/log/archivematica/dashboard/gunicorn.access_log"

# http://docs.gunicorn.org/en/stable/settings.html#errorlog
errorlog = "/var/log/archivematica/dashboard/gunicorn.error_log"

# http://docs.gunicorn.org/en/stable/settings.html#loglevel
loglevel = "info"

# http://docs.gunicorn.org/en/stable/settings.html#proc-name
proc_name = "archivematica-dashboard"

# http://docs.gunicorn.org/en/stable/settings.html#pythonpath
pythonpath = "/usr/share/archivematica/dashboard,/usr/lib/archivematica/archivematicaCommon"
