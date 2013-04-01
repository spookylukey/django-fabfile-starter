"""
Starter fabfile for deploying a Django project.

Designed for Webfaction, but should work on any similar hosting system.

Change all the things marked CHANGEME. Other things can be left at their
defaults if you are happy with the default layout.
"""

import posixpath

from fabric.api import run, local, abort, env, put, settings, cd, task
from fabric.decorators import runs_once
from fabric.contrib.files import exists
from fabric.context_managers import cd, lcd, settings, hide

# CHANGEME:

USER = 'foo'
HOST = 'foo.com'
APP_NAME = 'myapp'
APP_PORT = 30123
GUNICORN_WORKERS = 1

# Host and login username:
env.hosts = ['%s@%s' % (USER, HOST)]

# Directory where everything to do with this app will be stored on the server.
DJANGO_APP_ROOT = '/home/%s/webapps/%s_django' % (USER, APP_NAME)

# Directory where static sources should be collected.  This must equal the value
# of STATIC_ROOT in the settings.py that is used on the server.
STATIC_ROOT = '/home/%s/webapps/%s_static/' % (USER, APP_NAME)

# Subdirectory of DJANGO_APP_ROOT in which project sources will be stored
SRC_SUBDIR = 'src'

# Subdirectory of DJANGO_APP_ROOT in which virtualenv will be stored
VENV_SUBDIR = 'venv'

# Python version
PYTHON_BIN = "python2.7"
PYTHON_PREFIX = "" # e.g. /usr/local  Use "" for automatic
PYTHON_FULL_PATH = "%s/bin/%s" % (PYTHON_PREFIX, PYTHON_BIN) if PYTHON_PREFIX else PYTHON_BIN

GUNICORN_PIDFILE = "%s/gunicorn.pid" % DJANGO_APP_ROOT
GUNICORN_LOGFILE = "/home/%s/logs/user/gunicorn_%s.log" % (USER, APP_NAME)

SRC_DIR = posixpath.join(DJANGO_APP_ROOT, SRC_SUBDIR)
VENV_DIR = posixpath.join(DJANGO_APP_ROOT, VENV_SUBDIR)

WSGI_MODULE = '%s.wsgi' % APP_NAME


def virtualenv(venv_dir):
    """
    Context manager that establishes a virtualenv to use.
    """
    return settings(venv=venv_dir)


def run_venv(command, **kwargs):
    """
    Runs a command in a virtualenv (which has been specified using
    the virtualenv context manager
    """
    run("source %s/bin/activate" % env.venv + " && " + command, **kwargs)


def install_dependencies():
    ensure_virtualenv()
    with virtualenv(VENV_DIR):
        with cd(SRC_DIR):
            run_venv("pip install -r requirements.txt")


def ensure_virtualenv():
    if exists(VENV_DIR):
        return

    with cd(DJANGO_APP_ROOT):
        run("virtualenv --no-site-packages --python=%s %s" %
            (PYTHON_BIN, VENV_SUBDIR))
        run("echo %s > %s/lib/%s/site-packages/projectsource.pth" %
            (SRC_DIR, VENV_SUBDIR, PYTHON_BIN))


def ensure_src_dir():
    if not exists(SRC_DIR):
        run("mkdir -p %s" % SRC_DIR)
    with cd(SRC_DIR):
        if not exists(posixpath.join(SRC_DIR, '.hg')):
            run("hg init")


@task
def push_rev(rev):
    """
    Use the specified revision for deployment, instead of the current revision.
    """
    env.push_rev = rev


def push_sources():
    """
    Push source code to server.
    """
    ensure_src_dir()
    push_rev = getattr(env, 'push_rev', None)
    if push_rev is None:
        push_rev = local("hg id", capture=True).split(" ")[0].strip().strip("+")

    local("hg push -f ssh://%(user)s@%(host)s/%(path)s || true" %
          dict(host=env.host,
               user=env.user,
               path=SRC_DIR,
               ))
    with cd(SRC_DIR):
        run("hg update %s" % push_rev)


@task
def webserver_stop():
    """
    Stop the webserver that is running the Django instance
    """
    run("kill $(cat %s)" % GUNICORN_PIDFILE)


def _webserver_command():
    return ("%(venv_dir)s/bin/gunicorn --log-file=%(logfile)s -b 127.0.0.1:%(port)s -D -w %(workers)s --pid %(pidfile)s %(wsgimodule)s:application" %
            {'venv_dir': VENV_DIR,
             'pidfile': GUNICORN_PIDFILE,
             'wsgimodule': WSGI_MODULE,
             'port': APP_PORT,
             'workers': GUNICORN_WORKERS,
             'logfile': GUNICORN_LOGFILE,
             }
            )


@task
def webserver_start():
    """
    Starts the webserver that is running the Django instance
    """
    run(_webserver_command())


@task
def local_webserver_start():
    """
    Starts the webserver that is running the Django instance, on the local machine
    """
    local(_webserver_command())


@task
def webserver_restart():
    """
    Restarts the webserver that is running the Django instance
    """
    try:
        run("kill -HUP $(cat %s)" % GUNICORN_PIDFILE)
    except:
        webserver_start()


def build_static():
    with virtualenv(VENV_DIR):
        with cd(SRC_DIR):
            run_venv("./manage.py collectstatic -v 0 --noinput --clear")

    run("chmod -R ugo+r %s" % STATIC_ROOT)


@task
def first_deployment_mode():
    """
    Use before first deployment to switch on fake south migrations.
    """
    env.initial_deploy = True


def update_database():
    with virtualenv(VENV_DIR):
        with cd(SRC_DIR):
            if getattr(env, 'initial_deploy', False):
                run_venv("./manage.py syncdb --all")
                run_venv("./manage.py migrate --fake --noinput")
            else:
                run_venv("./manage.py syncdb --noinput")
                run_venv("./manage.py migrate --noinput")


@task
def deploy():
    """
    Deploy project.
    """
    with settings(warn_only=True):
        webserver_stop()
    push_sources()
    install_dependencies()
    update_database()
    build_static()

    webserver_start()

