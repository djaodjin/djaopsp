FROM python:3.9-slim-bullseye
# As of 2021-10-04: Python 3.9.7, Debian 11.0 (Bullseye)
# RUN which python3
# RUN python3 --version
# RUN cat /etc/debian_version

#     Loads the list of native packages
RUN apt-get update -y
#     Installs required native packages
RUN DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get -y install libpangoft2-1.0-0

RUN /usr/local/bin/python3 -m venv /app --system-site-packages
RUN /app/bin/pip install pip setuptools --upgrade

# Bundle app source
COPY . /app/reps/djaopsp
WORKDIR /app/reps/djaopsp
RUN /app/bin/pip install -r requirements.txt

# Create local configuration files
RUN /bin/mkdir -p /etc/djaopsp
RUN /bin/sed -e "s,\%(SECRET_KEY)s,`/app/bin/python -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^*-_=+") for i in range(50)]))'`," etc/credentials > /etc/djaopsp/credentials
RUN /bin/sed -e "s,^DB_LOCATION *= *\".*\",DB_LOCATION = \"sqlite3:///app/reps/djaopsp/db.sqlite\"," etc/site.conf > /etc/djaopsp/site.conf
RUN /bin/sed -e 's,%(APP_NAME)s,djaopsp,g' -e 's,%(LOCALSTATEDIR)s,/var,g'\
  -e 's,%(PID_FILE)s,/var/run/djaopsp.pid,g'\
  -e 's,bind="127.0.0.1:%(APP_PORT)s",bind="0.0.0.0:80",'\
  etc/gunicorn.conf > /etc/djaopsp/gunicorn.conf

# Expose application http port
Expose 80

# Run
CMD ["/app/bin/gunicorn", "-c", "/etc/djaopsp/gunicorn.conf", "djaopsp.wsgi"]
