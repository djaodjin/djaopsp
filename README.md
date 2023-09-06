DjaoDjin Practices Survey Platform
==================================

[![Documentation Status](https://readthedocs.org/projects/djaopsp/badge/?version=latest)](https://djaopsp.readthedocs.io/en/latest/?badge=latest)

This repository contains the code for DjaoDjin practices sharing platform.
To learn more visit [DjaoDjin's Website](https://www.djaodjin.com/).

The practices sharing platform is built on
[Django](https://www.djangoproject.com/),
[Vue.js](https://vuejs.org/), [Bootstrap](https://getbootstrap.com/)
frameworks and many more Open Source projects. Thank you for the support!

<p align="center">
<img src="https://static.djangoproject.com/img/logos/django-logo-positive.png" height="75">
<img src="https://vuejs.org/images/logo.png" height="75">
<img src="https://getbootstrap.com/docs/4.3/assets/brand/bootstrap-solid.svg" height="75">
</p>

If you are looking to add features, this project integrates
- [djaodjin-pages](https://github.com/djaodjin/djaodjin-pages/) for content management
- [djaodjin-survey](https://github.com/djaodjin/djaodjin-survey/) for assessments

Tested with

- **Python:** 3.10, **Django:** 3.2 ([LTS](https://www.djangoproject.com/download/))


Install
-------

First you will need to create a workspace environment, download the 3rd party
vendor prerequisite packages and build the static assets.

<pre><code>
    $ python -m venv <em>installTop</em>
    $ source <em>installTop</em>/bin/activate
    $ pip install -r requirements.txt
    $ make vendor-assets-prerequisites
    $ make install-conf
    $ make build-assets
</code></pre>

At this point, all the 3rd party vendor prerequisite packages (Python and
Javascript) have been downloaded and installed in the environment.

Then create the database, and start the built-in webserver

    $ python manage.py migrate --run-syncdb
    $ python manage.py createsuperuser
    $ python manage.py runserver


Development
-----------

You will want to toggle `DEBUG` on in the site.conf file.

<pre><code>
    $ diff -u <em>installTop</em>/etc/djaoapp/site.conf
    -DEBUG = False
    +DEBUG = True

    # Create the tests databases and load test datasets.
    $ make initdb

    # To generate some sample data, disable emailing of receipts and run:
    $ python manage.py load_test_transactions

    # Spins up a dev server that re-compiles the `.css` files
    # on page reload whenever necessary.
    $ python manage.py runserver --nostatic
</code></pre>


Release Notes
=============

See [release notes](https://www.djaodjin.com/docs/djaopsp/releases/)
