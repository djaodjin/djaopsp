"""
WSGI config for the project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""
import os
from django.core.wsgi import get_wsgi_application

#pylint: disable=invalid-name

def save_coverage(*args):
    sys.stderr.write("saving coverage\n")
    cov.stop()
    cov.save()

if os.getenv('DJANGO_COVERAGE'):
    import atexit, sys
    import coverage
    data_file=os.path.join(os.getenv('DJANGO_COVERAGE'),
        ".coverage.%d" % os.getpid())
    cov = coverage.coverage(data_file=data_file)
    sys.stderr.write("start recording coverage in %s\n" % str(data_file))
    cov.set_option("run:relative_files", True)
    cov.start()
    atexit.register(save_coverage)

# We defer to a DJANGO_SETTINGS_MODULE already in the environment. This breaks
# if running multiple sites in the same mod_wsgi process. To fix this, use
# mod_wsgi daemon mode with each site in its own daemon process, or use:
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djaopsp.settings")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
application = get_wsgi_application() #pylint: disable=invalid-name
