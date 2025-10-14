FROM python:3.10-slim-bookworm
#2025-04-15: python:3.10-slim-bookworm - Python 3.10.17, Debian 12.10 (Bookworm)
#2023-04-21: python:3.10-slim-bullseye - Python 3.10.11, Debian 11.0 (Bullseye)

LABEL org.opencontainers.image.source https://github.com/djaodjin/djaopsp

# Print version info for build log
RUN echo "Building with" `python --version` '('`which python`')' "on Debian" `cat /etc/debian_version` "..."

#     Without the following line we have trouble fetching libxml2
RUN apt-get clean all
#     Loads the list of native packages
RUN apt-get update -y
#     Installs required native packages
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install libpangoft2-1.0-0 sqlite3

RUN /usr/local/bin/python3 -m venv --upgrade-deps /app --system-site-packages
#    If we attempt to upgrade from pip 21.2.3 to 22.0.4,
#    installing requests>=2.22.0 fails ("cannot find package").
#RUN /app/bin/pip install pip setuptools --upgrade

#    Installs the preprequisites used for debugging (DEBUG=1, API_DEBUG=1)
#    so we don't have to rebuild a container to investigate when something
#    goes wrong.
RUN /app/bin/pip install cairocffi==1.7.1 coverage==6.3.2 psycopg2-binary==2.9.3 setproctitle==1.2.3
RUN /app/bin/pip install Django==4.2.23 djangorestframework==3.15.2 djaodjin-deployutils==0.14.1 djaodjin-extended-templates==0.4.9 djaodjin-pages==0.8.6 djaodjin-survey==0.17.3 docutils==0.20.1 drf-spectacular==0.27.2 gunicorn==23.0.0 jinja2==3.1.6 html5lib==1.1 monotonic==1.6 openpyxl==3.1.5 python-pptx==0.6.21 pytz==2025.2 django-debug-toolbar==3.8.1 django-extensions==3.2.3 Faker==2.0.0 sqlparse==0.5.3

#    Bundle app source
COPY . /app/reps/djaopsp
WORKDIR /app/reps/djaopsp

# Create local configuration files
RUN /bin/mkdir -p /etc/djaopsp /var/run/djaopsp
RUN /bin/sed -e "s,\%(SECRET_KEY)s,`/app/bin/python -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^*-_=+") for i in range(50)]))'`," -e "s,\%(DJAODJIN_SECRET_KEY)s,`/app/bin/python -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@#%^*-_=+") for i in range(50)]))'`," etc/credentials > /etc/djaopsp/credentials
RUN /bin/sed -e "s,^DB_SECRET_LOCATION *= *\".*\",DB_SECRET_LOCATION = \"sqlite3:///app/reps/djaopsp/db.sqlite\"," -e "s,DB_NAME *= *\".*\.sqlite\",DB_NAME = \"/app/reps/djaopsp/db.sqlite\"," -e 's,%(DB_NAME)s,db,g' \
   -e 's,%(APP_NAME)s,djaopsp,g' -e 's,%(LOCALSTATEDIR)s,/var,g'\
   etc/site.conf > /etc/djaopsp/site.conf
RUN /bin/sed -e 's,%(APP_NAME)s,djaopsp,g' -e 's,%(LOCALSTATEDIR)s,/var,g'\
  -e 's,%(PID_FILE)s,/var/run/djaopsp.pid,g'\
  -e 's,bind="127.0.0.1:%(APP_PORT)s",bind="0.0.0.0:80",'\
  etc/gunicorn.conf > /etc/djaopsp/gunicorn.conf

# Expose application http port
Expose 80/tcp

# Run
ENTRYPOINT ["/app/bin/gunicorn", "-c", "/etc/djaopsp/gunicorn.conf", "djaopsp.wsgi"]
