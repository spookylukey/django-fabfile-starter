Django starter fabfile
======================

The provided fabfile.py is a basic starter fabfile for use with the deployment
tool 'fabric' and Django projects. It has been used successfully to deploy to a
site hosted on webfaction.com.

Put this fabfile.py in the directory that contains all your project sources, and
customize to suit.


Requirements
------------

The fabfile assumes:

- you are using Django 1.4 or greater

- you have your development environment already setup, including
  having 'fabric' installed.

- your server is basically 'provisioned' i.e.

  - SSH setup for logging in (and you've set up your developer machine
    for passwordless login).

  - database server installed etc., and database created

  - Python is installed

- use of virtualenv to isolate the environment. You will need to have virtualenv
  available on your server. For maximum isolation, virtualenv is run with
  '--no-site-packages'.

- use of 'south' for migrations.

- a project layout like this:

  - some_dir/  - directory containing all sources, under source control

    - fabfile.py

    - manage.py

    - top level Python package directories. For example:

      - myproject/

      - myproject/__init__.py

      - myproject/wsgi.py

      - myapp/

      - etc.

- settings.py on the server that correctly defines and separates STATIC_ROOT and
  MEDIA_ROOT. STATIC_ROOT is populated by the Django 'collectstatic' command,
  and files already there are cleared out.

- manage.py loads the correct settings.py when run on the server.

- use of a pip 'requirements.txt' for installation of Python packages, in the
  same directory as the fabfile. It should contain at least:

  * Django
  * south
  * gunicorn
  * psutil
  * fabric

- use of Mercurial for source control, requiring hg to be installed on
  your server. (This could be easily modified to use git).

- deployment to a POSIX server. (Uses posixpath for path manipulation)

- you can cope with some downtime when deploying, which is needed to update
  sources, dependencies and run migrations.


Usage
-----

Copy the fabfile.py to your top level of your project, and modify.

Use 'fab deploy' to deploy.

You might want to do 'fab first_deployment_mode deploy' for the first deployment.

Use 'fab -l' to see other commands

You should probably create a cronjob to ensure that the Gunicorn webserver is
running. This can use fabric on the server and the command 'local_webserver_start':

*/10     * * * *    /home/myuser/webapps/myapp_django/venv/bin/fab -f /home/myuser/webapps/myapp_django/src/fabfile.py local_webserver_start

Tips
----

To extend for a staging/production system:

1) Change the constants at the top to None where these constants
   are different for the two environments.

2) Create tasks 'staging' and 'production' which set these globals.
   These commands must be run before the 'deploy' command.
