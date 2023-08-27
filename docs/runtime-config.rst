Container runtime configuration
===============================

The basic command to run the Docker container on port 8000 looks like this:

    .. code-block:: shell

        $ docker run -d -p 8000:80 -t ghcr.io/djaodjin/djaopsp/djaopsp:main

The container is meant to be run behind
a `DjaoApp <https://github.com/djaodjin/djaoapp>`_ Web/API Gateway for user
authentication and permission checks.

When accessed directly, the mockup accounts to login
(see ``settings.DEPLOYUTILS['MOCKUP_SESSIONS''])`` are:

- "donny", a profile manager of the site (`broker <https://www.djaodjin.com/docs/guides/accounts/#broker>`_)
- "kathryn", a profile manager of an alliance profile on the site.
- "alice", a profile manager of an organization member of the alliance above.
- "steve", a profile manager for an organization with no special affiliations.


Using a local database
----------------------

The djaopsp Docker container is meant to be started with a ``site.conf``
and ``credentials`` configuration files.
Typically site-specific configurations, like feature flags, pathnames and
URI location of third-party services are stored in ``site.conf``, whereas
identification and encryption keys are stored in the ``credentials`` file.

To keep things simple, we are going to create the database and ``site.conf``
configuration file in a directory on the local filesystem.

    .. code-block:: shell

        $ mkdir -p mounted_config

We can create such database by running the commands:

    .. code-block:: shell

        $ python manage.py migrate --run-syncdb
        $ python manage.py createsuperuser
        $ mv db.sqlite3 mounted_config

With a db.sqlite3 file created, we then create a ``site.conf`` configuration
file and define the necessary variables to use our newly created database.

We are going to mount the host directory where the database resides
as /app/var in the container, so we set ``DB_ENGINE`` and ``DB_NAME`` as such:

    .. code-block:: shell

        $ cat mounted_config/site.conf
        ...
        DB_ENGINE="django.db.backends.sqlite3"
        DB_NAME="/app/var/db.sqlite3"

Now when we start the container, we mount the host directory where the database
and configuration file reside, as we define the environment variable
``DJAOPSP_SETTINGS_LOCATION`` to find such configuration files.

    .. code-block:: shell

        $ sudo docker run -d -p 8000:80 -v "${PWD}"/mounted_config:/app/var:z -e DJAOPSP_SETTINGS_LOCATION=/app/var -t ghcr.io/djaodjin/djaopsp/djaopsp:main


Configuring the SMTP settings to send email
-------------------------------------------

If you have setup a local database as explained in the previous section,
you will guess correctly that we define the e-mail settings in ``site.conf``.

For example, if we want to use the Django internal in-memory SMTP server
instead of an actual SMTP server, thus preventing both 500 errors because of
SMTP misconfiguration and e-mails ending up in an inbox, we can use
the following definitions:

    .. code-block:: shell

        $ cat mounted_config/site.conf
        ...
        EMAIL_HOST    = "localhost"
        EMAIL_PORT    = 1025    # matches SMTP_PORT in test driver
        EMAIL_USE_TLS = False
        EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

Then, as usual, we start the Docker container as:

    .. code-block:: shell

        $ sudo docker run -d -p 8000:80 -v "${PWD}"/mounted_config:/app/var:z -e DJAOPSP_SETTINGS_LOCATION=/app/var -t ghcr.io/djaodjin/djaopsp/djaopsp:main


Configuring where assets are stored
-----------------------------------

    .. code-block:: shell

        $ cat mounted_config/site.conf
        ...
        DEFAULT_FILE_STORAGE    = "storages.backends.s3boto3.S3Boto3Storage"
        AWS_STORAGE_BUCKET_NAME = "*bucket_name*"

Then, as usual, we start the Docker container as:

    .. code-block:: shell

        $ sudo docker run -d -p 8000:80 -v "${PWD}"/mounted_config:/app/var:z -e DJAOPSP_SETTINGS_LOCATION=/app/var -t ghcr.io/djaodjin/djaopsp/djaopsp:main


Reference for configuration variables
-------------------------------------

There exists templates for both ``credentials`` and ``site.conf`` in the source
repository inside the ``etc`` directory.

General behavior

+---------------------+------------+------------------------------------------+
| Name                | Default    | Description                              |
+=====================+============+==========================================+
| SECRET_KEY          | random     | Key for CSRF protection                  |
+---------------------+------------+------------------------------------------+
| DEBUG               | False      | Enables debug mode when ``True``         |
+---------------------+------------+------------------------------------------+
| FEATURES_DEBUG      | False      | Enable features not quite ready yet      |
+---------------------+------------+------------------------------------------+


Variable for database connection

+--------------------+------------+--------------------------------------------+
|Name                | Default    | Description                                |
+====================+============+============================================+
|DB_ENGINE           |"sqlite3"   | Database engine (sqlite3, postgresql)      |
+--------------------+------------+--------------------------------------------+
|DB_NAME             |"db.sqlite" | Name of the database                       |
+--------------------+------------+--------------------------------------------+
|DB_HOST             |            | Hostname where the database is located     |
+--------------------+------------+--------------------------------------------+
|DB_PORT             |            | Port number (on host) to connect to the db |
+--------------------+------------+--------------------------------------------+
|DB_USER             |""          | Username to identify with the database     |
+--------------------+------------+--------------------------------------------+
|DB_PASSWORD         |""          | Password to identify with the database     |
+--------------------+------------+--------------------------------------------+


Variables to send notification e-mails

+--------------------+------------+--------------------------------------------+
|Name                | Default    | Description                                |
+====================+============+============================================+
|SEND_EMAIL          |True        | Disable notification e-mails altogether    |
|                    |            | when ``False``                             |
+--------------------+------------+--------------------------------------------+
|EMAIL_BACKEND       |            | Django e-mail backend to use               |
+--------------------+------------+--------------------------------------------+
|EMAIL_HOST          |"localhost" | Hostname where the SMTP server is located  |
+--------------------+------------+--------------------------------------------+
|EMAIL_PORT          |25          | Port number on the host to connect         |
|                    |            | to the SMTP server                         |
+--------------------+------------+--------------------------------------------+
|EMAIL_HOST_USER     | ""         | Username to identify with the SMTP server  |
+--------------------+------------+--------------------------------------------+
|EMAIL_HOST_PASSWORD | ""         | Password to identify with the SMTP server  |
+--------------------+------------+--------------------------------------------+
|EMAIL_USE_TLS       | False      | Uses TLS encryption when ``True``          |
+--------------------+------------+--------------------------------------------+
|DEFAULT_FROM_EMAIL  |""          | Default e-mail used to send notification   |
|                    |            | e-mails                                    |
+--------------------+------------+--------------------------------------------+
