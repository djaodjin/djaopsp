# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE

-include $(buildTop)/share/dws/prefix.mk

APP_NAME      ?= $(notdir $(abspath $(srcDir)))
APP_PORT      ?= 8000

srcDir        ?= .
installTop    ?= $(VIRTUAL_ENV)
binDir        ?= $(installTop)/bin
libDir        ?= $(installTop)/lib
SYSCONFDIR    := $(installTop)/etc
LOCALSTATEDIR := $(installTop)/var
CONFIG_DIR    := $(SYSCONFDIR)/$(APP_NAME)
ASSETS_DIR    := $(srcDir)/htdocs/static

installDirs   ?= /usr/bin/install -d
installFiles  ?= /usr/bin/install -p -m 644
DOCKER        ?= docker
ESCHECK       ?= es-check
NPM           ?= npm
PIP           ?= pip
PYTHON        ?= python
SASSC         ?= sassc
SQLITE        ?= sqlite3
WEBPACK       ?= NODE_PATH=$(libDir)/node_modules webpack --stats-error-details
#WEBPACK       ?= webpack --stats verbose
#WEBPACK       ?= webpack --profile --json > build.json

# Django 1.7,1.8 sync tables without migrations by default while Django 1.9
# requires a --run-syncdb argument.
# Implementation Note: We have to wait for the config files to be installed
# before running the manage.py command (else missing SECRECT_KEY).
MANAGE        := DJAOPSP_SETTINGS_LOCATION=$(CONFIG_DIR) $(PYTHON) manage.py
RUNSYNCDB     = $(if $(findstring --run-syncdb,$(shell cd $(srcDir) && $(MANAGE) migrate --help 2>/dev/null)),--run-syncdb,)


ifneq ($(wildcard $(CONFIG_DIR)/site.conf),)
# `make initdb` will install site.conf but only after `grep` is run
# and DB_FILNAME set to "". We use the default value in the template site.conf
# here to prevent that issue.
DB_FILENAME   := $(shell grep ^DB_NAME $(CONFIG_DIR)/site.conf | cut -f 2 -d '"')
endif

DOCKER_DB_FILENAME := $(abspath $(srcDir)/db.sqlite)
ifeq ($(DB_FILENAME),)
DB_FILENAME        := $(DOCKER_DB_FILENAME)
endif

MY_EMAIL          ?= $(shell cd $(srcDir) && git config user.email)
EMAIL_FIXTURE_OPT := $(if $(MY_EMAIL),--email="$(MY_EMAIL)",)

# We generate the SECRET_KEY this way so it can be overriden
# in test environments.
SECRET_KEY ?= $(shell $(PYTHON) -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@\#$%^*-_=+") for i in range(50)]))' )

DJAODJIN_SECRET_KEY ?= $(shell $(PYTHON) -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@\#$%^*-_=+") for i in range(50)]))' )


.PHONY: build-assets doc generateschema initdb makemessages package-docker vendor-assets-prerequisites

all:
	@echo "Nothing to be done for 'make'."


# We are installing the overridden vendor files along with the ones installed
# from node_modules.
#	cd $(srcDir) && cp -rf htdocs htdocs-backups
#	cd $(srcDir) && $(MANAGE) collectstatic --noinput
build-assets: $(ASSETS_DIR)/cache/app.css \
              $(ASSETS_DIR)/cache/email.css \
              $(ASSETS_DIR)/cache/assess.js
	$(installFiles) $(srcDir)/djaopsp/static/vendor/djaodjin-dashboard.js $(ASSETS_DIR)/vendor
	$(installFiles) $(srcDir)/djaopsp/static/vendor/djaodjin-menubar.js $(ASSETS_DIR)/vendor
	$(installFiles) $(srcDir)/djaopsp/static/vendor/hallo.js $(ASSETS_DIR)/vendor
	$(installFiles) $(srcDir)/djaopsp/static/vendor/jquery-ui.js $(ASSETS_DIR)/vendor
	$(installFiles) $(srcDir)/djaopsp/static/vendor/djaoapp-i18n.js $(ASSETS_DIR)/vendor
	cd $(srcDir) && $(ESCHECK) es5 htdocs/static/cache/*.js htdocs/static/vendor/*.js -v


clean: clean-dbs
	[ ! -f $(srcDir)/package-lock.json ] || rm $(srcDir)/package-lock.json
	find $(srcDir) -name '__pycache__' -exec rm -rf {} +
	find $(srcDir) -name '*~' -exec rm -rf {} +


doc: schema.yml
	$(installDirs) build/docs
	cd $(srcDir) && sphinx-build -b html ./docs $(PWD)/build/docs


generateschema: schema.yml


# We add a `load_test_transactions` because the command will set the current
# site and thus need the rules.App table.
initdb:
	-[ -f $(DB_FILENAME) ] && rm -f $(DB_FILENAME)
	$(installDirs) $(dir $(DB_FILENAME))
	cd $(srcDir) && $(MANAGE) migrate $(RUNSYNCDB) --noinput
	cd $(srcDir) && $(MANAGE) loadfixtures $(EMAIL_FIXTURE_OPT) \
		djaopsp/fixtures/accounts.json \
		djaopsp/fixtures/content.json \
		djaopsp/fixtures/practices.json \
		djaopsp/fixtures/practices_custom_choices.json \
		djaopsp/fixtures/matrices.json \
		djaopsp/fixtures/samples.json \
		djaopsp/fixtures/100-completed-notshared.json


# We build a local sqlite3 database to be packaged with the Docker image
# such that the container can be started without prior configuration.
package-docker-initdb:
	-[ -f $(DOCKER_DB_FILENAME) ] && rm -f $(DOCKER_DB_FILENAME)
	cd $(srcDir) && DB_LOCATION=sqlite3://$(DOCKER_DB_FILENAME) $(MANAGE) migrate $(RUNSYNCDB) --noinput
	cd $(srcDir) && DB_LOCATION=sqlite3://$(DOCKER_DB_FILENAME) $(MANAGE) loadfixtures djaopsp/fixtures/default-db.json


install:: install-conf


makemessages:
	cd $(srcDir) && $(MANAGE) makemessages -l fr -l es -l pt --symlinks --no-wrap
	cd $(srcDir) && $(MANAGE) makemessages -d djangojs -l fr -l es -l pt --symlinks --no-wrap


package-docker: build-assets package-docker-initdb
	cd $(srcDir) && echo $(DOCKER) build .


package-theme: build-assets
	cd $(srcDir) && DEBUG=0 FEATURES_REVERT_TO_DJANGO=0 \
		$(MANAGE) package_theme \
		--build_dir=$(objDir) --install_dir=htdocs/themes \
		--exclude='_form.html' --exclude='.*/' \
		--include='accounts/' --include='docs/' \
		--include='notification/'
	zip -d $(srcDir)/htdocs/themes/$(APP_NAME).zip "$(APP_NAME)/templates/accounts/base.html"


# Once tests are completed, run 'coverage report'.
run-coverage: initdb
	cd $(srcDir) && coverage run --source='.,deployutils,pages,survey,' \
		manage.py runserver $(APP_PORT) --noreload


# Download prerequisites specified in package.json and install relevant files
# in the directory assets are served from.
vendor-assets-prerequisites: $(installTop)/.npm/$(APP_NAME)-packages


# --------- intermediate targets

clean-dbs:
	[ ! -f $(DB_FILENAME) ] || rm $(DB_FILENAME)

# The chart.js in node_modules/chart.js/dist/chart.js does not pass
# `es-check es5`. The webpack.config.js file rules loader excludes
# `node_modules` from babel, so we install chart.js in $srcDir here.
$(installTop)/.npm/$(APP_NAME)-packages: $(srcDir)/package.json
	$(installFiles) $^ $(libDir)
	$(NPM) install --loglevel verbose --cache $(installTop)/.npm --tmp $(installTop)/tmp --prefix $(libDir)
	install -d $(ASSETS_DIR)/fonts $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/bootstrap/dist/js/bootstrap.js $(ASSETS_DIR)/vendor
	cp -rf $(libDir)/node_modules/chart.js $(srcDir)/djaopsp/static/vendor
	$(installFiles) $(libDir)/node_modules/chartjs-plugin-annotation/dist/chartjs-plugin-annotation.js $(srcDir)/djaopsp/static/vendor
	$(installFiles) $(libDir)/node_modules/dropzone/dist/dropzone.css $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/dropzone/dist/dropzone.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/font-awesome/css/font-awesome.css $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/font-awesome/fonts/* $(ASSETS_DIR)/fonts
	$(installFiles) $(libDir)/node_modules/jquery/dist/jquery.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/moment/moment.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/moment-timezone/builds/moment-timezone-with-data.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/popper.js/dist/umd/popper.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/popper.js/dist/umd/popper-utils.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/vue/dist/vue.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/lodash/lodash.js $(ASSETS_DIR)/vendor
	[ -f $(binDir)/es-check ] || (cd $(binDir) && ln -s ../lib/node_modules/.bin/es-check es-check)
	[ -f $(binDir)/sassc ] || (cd $(binDir) && ln -s ../lib/node_modules/.bin/sass sassc)
	[ -f $(binDir)/swagger-cli ] || (cd $(binDir) && ln -s ../lib/node_modules/.bin/swagger-cli swagger-cli)
	[ -f $(binDir)/webpack ] || (cd $(binDir) && ln -s ../lib/node_modules/.bin/webpack webpack)
	touch $@


schema.yml:
	cd $(srcDir) && $(MANAGE) generateschema > $@
	cd $(srcDir) && swagger-cli validate $@


$(ASSETS_DIR)/cache/assess.js: $(srcDir)/webpack.config.js \
                               webpack-conf-paths.json \
                               $(installTop)/.npm/$(APP_NAME)-packages \
                               $(wildcard $(srcDir)/djaopsp/static/js/*.js)
	cd $(srcDir) && $(WEBPACK) -c $<


webpack-conf-paths.json: $(srcDir)/djaopsp/settings.py
	cd $(srcDir) && $(MANAGE) generate_webpack_paths -o $@


$(ASSETS_DIR)/cache/app.css: \
        $(wildcard $(srcDir)/djaopsp/static/scss/vendor/bootstrap/*.scss) \
        $(wildcard $(srcDir)/djaopsp/static/scss/vendor/djaodjin/*.scss) \
        $(wildcard $(srcDir)/djaopsp/static/scss/vendor/*.scss) \
        $(wildcard $(srcDir)/djaopsp/static/scss/base/*.scss)
	cd $(srcDir) && $(binDir)/sassc --source-map-urls absolute djaopsp/static/scss/base/base.scss $@

$(ASSETS_DIR)/cache/email.css: \
        $(wildcard $(srcDir)/djaopsp/static/scss/email/*.scss)
	cd $(srcDir) && $(binDir)/sassc djaopsp/static/scss/email/email.scss $@


$(srcDir)/djaopsp/locale/fr/LC_MESSAGES/django.mo: \
				$(wildcard $(srcDir)/djaopsp/locale/es/LC_MESSAGES/*.po) \
				$(wildcard $(srcDir)/djaopsp/locale/fr/LC_MESSAGES/*.po) \
				$(wildcard $(srcDir)/djaopsp/locale/pt/LC_MESSAGES/*.po)
	cd $(srcDir) && $(MANAGE) compilemessages


install-conf:: $(DESTDIR)$(CONFIG_DIR)/credentials \
				$(DESTDIR)$(CONFIG_DIR)/site.conf \
				$(DESTDIR)$(CONFIG_DIR)/gunicorn.conf \
				$(DESTDIR)$(SYSCONFDIR)/sysconfig/$(APP_NAME) \
				$(DESTDIR)$(SYSCONFDIR)/logrotate.d/$(APP_NAME) \
				$(DESTDIR)$(SYSCONFDIR)/monit.d/$(APP_NAME) \
				$(DESTDIR)$(SYSCONFDIR)/systemd/system/$(APP_NAME).service \
				$(DESTDIR)$(SYSCONFDIR)/usr/lib/tmpfiles.d/$(APP_NAME).conf
	install -d $(DESTDIR)$(LOCALSTATEDIR)/db
	install -d $(DESTDIR)$(LOCALSTATEDIR)/log/gunicorn
	[ -d $(DESTDIR)$(LOCALSTATEDIR)/run ] || install -d $(DESTDIR)$(LOCALSTATEDIR)/run

# Implementation Note:
# We use [ -f file ] before install here such that we do not blindly erase
# already present configuration files with template ones.
$(DESTDIR)$(CONFIG_DIR)/site.conf: $(srcDir)/etc/site.conf
	install -d $(dir $@)
	[ -f $@ ] || \
		sed -e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' \
			-e 's,%(SYSCONFDIR)s,$(SYSCONFDIR),' \
			-e 's,%(APP_NAME)s,$(APP_NAME),' \
			-e "s,%(ADMIN_EMAIL)s,$(MY_EMAIL)," \
			-e 's,%(installTop)s,$(installTop),' \
			-e "s,%(DB_NAME)s,$(APP_NAME)," \
			-e "s,%(binDir)s,$(binDir)," $< > $@

$(DESTDIR)$(CONFIG_DIR)/credentials: $(srcDir)/etc/credentials
	install -d $(dir $@)
	[ -e $@ ] || sed \
		-e "s,\%(SECRET_KEY)s,`$(PYTHON) -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^*-_=+") for i in range(50)]))'`," \
			$< > $@

$(DESTDIR)$(CONFIG_DIR)/gunicorn.conf: $(srcDir)/etc/gunicorn.conf
	install -d $(dir $@)
	[ -e $@ ] || sed \
		-e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' \
		-e 's,%(APP_NAME)s,$(APP_NAME),' \
		-e 's,%(APP_PORT)s,$(APP_PORT),' $< > $@

$(DESTDIR)$(SYSCONFDIR)/systemd/system/%.service: \
			   $(srcDir)/etc/service.conf
	install -d $(dir $@)
	[ -e $@ ] || sed \
		-e 's,%(srcDir)s,$(srcDir),' \
		-e 's,%(APP_NAME)s,$(APP_NAME),g' \
		-e 's,%(binDir)s,$(binDir),' \
		-e 's,%(SYSCONFDIR)s,$(SYSCONFDIR),' \
		-e 's,%(CONFIG_DIR)s,$(CONFIG_DIR),' \
		-e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' $< > $@

$(DESTDIR)$(SYSCONFDIR)/logrotate.d/%: $(srcDir)/etc/logrotate.conf
	install -d $(dir $@)
	[ -e $@ ] || sed \
		-e 's,%(APP_NAME)s,$(APP_NAME),g' \
		-e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' $< > $@

$(DESTDIR)$(SYSCONFDIR)/monit.d/%: $(srcDir)/etc/monit.conf
	install -d $(dir $@)
	[ -e $@ ] || sed \
		-e 's,%(APP_NAME)s,$(APP_NAME),g' \
		-e 's,%(APP_PORT)s,$(APP_NAME),g' \
		-e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' $< > $@

$(DESTDIR)$(SYSCONFDIR)/sysconfig/%: $(srcDir)/etc/sysconfig.conf
	install -d $(dir $@)
	[ -e $@ ] || install -p -m 644 $< $@

$(DESTDIR)$(SYSCONFDIR)/usr/lib/tmpfiles.d/$(APP_NAME).conf: $(srcDir)/etc/tmpfiles.conf
	install -d $(dir $@)
	[ -e $@ ] || sed \
		-e 's,%(APP_NAME)s,$(APP_NAME),g' $< > $@
