Working with the code base
===========================

Installing dependencies
-----------------------

To run djaopsp locally, you will need to install 3 types of dependencies

- Javascript dependencies (see package.json)
- Pure Python dependencies (see requirements.txt)
- Python bindings and native libraries (see requirements-native.txt)

CSS
---

The css files are built through saasc.

To rebuild the css files run the following make command:

.. code-block:: shell

    make build-assets

As it is inconvienient to edit/build/reload every time you make a change,
the ``AssetView`` class is used to detect changes and rebuild
``/static/cache/base.css`` as necessary on page load.
For that you need to make sure ``DEBUG`` is ``True`` and the ``--nostatic``
flag is passed to the runserver command line.

.. code-block:: shell

    DEBUG=1 python manage.py runserver --nostatic


So make your .sccs updates and reload the page!


HTML templates
--------------

The website is built as a Multi-Page Application (MPA). As much as possible
the template filenames follow the URL on which the template is used.
For example: you can find the template for ``/app/{profile}/assess/{sample}/``
in ``djaopsp/templates/app/assess/index.html``.

Django reads and re-compiles the template on page load.

So make your .html template updates and reload the page!


Javascript
----------

Because the site is using a Multi-Page Application (MPA) architecture, there
are no complex business logic and/or dependency logic in the Javascript code.
The order of the ``<script>`` HTML elements in the templates is pretty
straightforward.

Most developers will work with a very recent browser with the latest
EcmaScript features available. So in DEBUG mode, all we really want to
do is to be able to inclde the .js files through ``<script>`` HTML
elements in one of the ``base.html`` template.

Because we want to be able to work when no Internet connection is available,
we serve local copies of 3rd party vendor scripts in development mode.
The static assets are served by Django so they must be found through
the ``STATICFILES_FINDERS`` settings. The following make target insures that.

.. code-block:: shell

    make vendor-assets-prerequisites


Then make your .js updates and reload the page!


To support production mode (i.e. ``DEBUG=False``), we would like:

1. 3rd party vendor scripts loaded through the official CDN whenever possible
   to take advantage of browser caching.
2. Transpile and optimize the Vue components native to the website so they
   work on target browsers.

That is why we use a Universal Module Definition (UMD)] format as a wrapper
and specific webpack plugins (Technically we only need to append to an
``exports`` variable it is exists).

Typically npm, webpack and other Javascript tools will install and expect
a node_modules directory in your source tree. That is just ugly, bloats
your backups and really cramp your style when you are working with command
line tools such as ``grep``. Furthermore we have .js files present in
static directories of Django app installed in the virtual env ``site-packages``
directory that must be imported.

The ``generate_webpack_paths`` Django command creates a
``webpack-conf-paths.json`` file that contains the same search path
as set in ``settings.STATICFILES_FINDERS`` (followed by
``VIRTUAL_ENV/lib/node_modules/`` for vendor modules). That
webpack-conf-paths.json file is then loaded in ``webpack.config.js``
to set the modules search path for webpack.

To compile .js production asset files run the following make command:

.. code-block:: shell

    make build-assets


Python/Django
-------------

Updating the Python code and debugging changes works as expected. Three
noticeable prerequisites are the following Django apps:

- `djaodjin-deployutils`_ for encoding/decoding sessions
- `djaodjin-pages`_ for content management
- `djaodjin-survey`_ for surveys and assessments


Translation
-----------

Whenever possible translated strings should be written in the HTML templates
within ``{% trans %}{% endtrans %}`` markers.

We initially `generated translation units for the Vue components <https://www.djaodjin.com/blog/integrating-django-i18-with-jinja2-and-vuejs.blog>`_
but it had many drawbacks:

1. It required to load a djaoapp-i18n.js file at runtime.

2. It required to re-bundle the assets to fix a typo.

3. Translation strings were in two separate ``.po`` files (one for the Python/HTML templates and one for the Javascript).

Since then we made it a policy that there should not be any translation
strings within the .js files. If it is necessary to pass translatable text
to a component, do so through a component configuration variable and
initialize that component with the default text value in the HTML template.

To add another language, generate a new translation unit with the following
command:

.. code-block:: shell

    python manage.py makemessages -l {locale_name}


Edit the generated djaopsp/locale/{locale_name}/LC_MESSAGES/django.po file with
appropriate translations. Then compile the messages into a ``.mo`` file.

.. code-block:: shell

    python manage.py compilemessages



Generating API Documentation
----------------------------

Run the the server using the following command, the browse
http://localhost:8000/docs/api/

.. code-block:: shell

    DEBUG=0 API_DEBUG=1 python manage.py runserver

The ``APIDocView`` view will spit out warning and error messages whenever
examples provided do not match the API definition.

When the API reference documentation looks reasonnably well, generate
an OpenAPI schema.

.. code-block:: shell

    make generateschema


Building the Docker container
-----------------------------

Run the following command

.. code-block:: shell

    make package-docker


Running djaopsp behind djaoapp locally
--------------------------------------

Follow the `instructions to install djaoapp`_
and `instructions to install djaopsp`_
source repositories on your local machine.

To run djaopsp and djaoapp together on localhost, you need to insure:

1. Both djaoapp and djaopsp databases are populated with matching fixtures
2. djaoapp is setup to forward HTTP requests to djaopsp
3. djaopsp decodes the forwarded authenticated user session properly


djaoapp will for can access both
databases, and that the multitier entry in the djaoapp database has settings
matching the djaopsp server configuration (credentials and site.conf).

To populate the djaopsp database with livedemo fixtures, run the following
command in the djaopsp source directory.

.. code-block:: shell

    make initdb


To populate the djaoapp database with livedemo fixtures, and forward
HTTP requests properly, run the following command in the djaoapp source
directory.

.. code-block:: shell

    make setup-livedemo
    sqlite3 db.sqlite "UPDATE rules_rule set is_forward=1 WHERE app_id=(select id FROM rules_app WHERE slug='djaopsp');"
    sqlite3 db.sqlite "UPDATE rules_app SET enc_key='$(grep DJAODJIN_SECRET_KEY ../djaopsp/.venv/etc/djaopsp/credentials | cut -d \" -f 2)' WHERE id=(select id FROM rules_app WHERE slug='djaopsp');"

You will most likely want to run both servers in `DEBUG` mode. To do that,
change the settings in both site.conf file.
In `DEBUG` mode, the djaopsp server is configured to use a `djaopsp` path
prefix, so you will also need to update the djaoapp `multitier_site` entry
to reflect that:

In djaopsp source directory:

.. code-block:: shell

    $ diff -u .venv/etc/djaopsp/site.conf
    -DEBUG = False
    +DEBUG = True

    $ python manage.py runserver 8040

In djaoapp source directory:

.. code-block:: shell

    $ sqlite3 db.sqlite "UPDATE multitier_site set is_path_prefix=1 WHERE slug='djaopsp';"
    $ diff -u .venv/etc/djaoapp/site.conf
    -DEBUG = False
    +DEBUG = True

    $ python manage.py runserver

Browse to URL `http://localhost:8000/djaopsp/`, and click the user account
to login with on the livedemo site.


.. _djaodjin-deployutils: https://github.com/djaodjin/djaodjin-deployutils/

.. _djaodjin-pages: https://github.com/djaodjin/djaodjin-pages/

.. _djaodjin-survey: https://djaodjin-survey.readthedocs.io/

.. _instructions to install djaoapp: https://github.com/djaodjin/djaoapp/#install

.. _instructions to install djaopsp: https://github.com/djaodjin/djaopsp/#install
