FROM python:3.10-slim-bullseye
# As of 2023-04-21: Python 3.10.11, Debian 11.0 (Bullseye)

LABEL org.opencontainers.image.source https://github.com/djaodjin/djaopsp

# Print version info for build log
RUN echo "Building with" `python --version` '('`which python`')' "on Debian" `cat /etc/debian_version` "(Bullseye Slim)..."

#     Without the following line we have trouble fetching libxml2
RUN apt-get clean all
#     Loads the list of native packages
RUN apt-get update -y
#     Installs required native packages
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install libpangoft2-1.0-0

RUN /usr/local/bin/python3 -m venv /app --system-site-packages
#    If we attempt to upgrade from pip 21.2.3 to 22.0.4,
#    installing requests>=2.22.0 fails ("cannot find package").
#RUN /app/bin/pip install pip setuptools --upgrade

#    Bundle app source
COPY . /app/reps/djaopsp
WORKDIR /app/reps/djaopsp
#    Installs the preprequisites used for debugging (DEBUG=1, API_DEBUG=1)
#    so we don't have to rebuild a container to investigate when something
#    goes wrong.
RUN /app/bin/pip install -r requirements.txt -r dev-requirements.txt

# Create local configuration files
RUN /bin/mkdir -p /etc/djaopsp
RUN /bin/sed -e "s,\%(SECRET_KEY)s,`/app/bin/python -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^*-_=+") for i in range(50)]))'`," -e "s,\%(DJAODJIN_SECRET_KEY)s,`/app/bin/python -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^*-_=+") for i in range(50)]))'`," etc/credentials > /etc/djaopsp/credentials
RUN /bin/sed -e "s,^DB_LOCATION *= *\".*\",DB_LOCATION = \"sqlite3:///app/reps/djaopsp/db.sqlite\"," etc/site.conf > /etc/djaopsp/site.conf
RUN /bin/sed -e 's,%(APP_NAME)s,djaopsp,g' -e 's,%(LOCALSTATEDIR)s,/var,g'\
  -e 's,%(PID_FILE)s,/var/run/djaopsp.pid,g'\
  -e 's,bind="127.0.0.1:%(APP_PORT)s",bind="0.0.0.0:80",'\
  etc/gunicorn.conf > /etc/djaopsp/gunicorn.conf

# Expose application http port
Expose 80

# Run
CMD ["/app/bin/gunicorn", "-c", "/etc/djaopsp/gunicorn.conf", "djaopsp.wsgi"]
