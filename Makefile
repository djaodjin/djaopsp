# Copyright (c) 2022, DjaoDjin inc.
# see LICENSE

-include $(buildTop)/share/dws/prefix.mk

APP_NAME      ?= $(notdir $(abspath $(srcDir)))
APP_PORT      ?= 8000

srcDir        ?= .
installTop    ?= $(VIRTUAL_ENV)
binDir        ?= $(installTop)/bin
SYSCONFDIR    := $(installTop)/etc
LOCALSTATEDIR := $(installTop)/var
CONFIG_DIR    := $(SYSCONFDIR)/$(APP_NAME)
ASSETS_DIR    := $(srcDir)/htdocs/static

installDirs   ?= /usr/bin/install -d
installFiles  ?= /usr/bin/install -p -m 644
NPM           ?= npm
PIP           := $(binDir)/pip
PYTHON        := $(binDir)/python
SASSC         := $(binDir)/sassc
SQLITE        ?= sqlite3
WEBPACK       ?= $(libDir)/node_modules/.bin/webpack

# Django 1.7,1.8 sync tables without migrations by default while Django 1.9
# requires a --run-syncdb argument.
# Implementation Note: We have to wait for the config files to be installed
# before running the manage.py command (else missing SECRECT_KEY).
RUNSYNCDB     = $(if $(findstring --run-syncdb,$(shell cd $(srcDir) && SETTINGS_LOCATION=$(CONFIG_DIR) $(PYTHON) manage.py migrate --help 2>/dev/null)),--run-syncdb,)
MANAGE        := SETTINGS_LOCATION=$(CONFIG_DIR) $(PYTHON) manage.py


ifneq ($(wildcard $(CONFIG_DIR)/site.conf),)
# `make initdb` will install site.conf but only after `grep` is run
# and DB_FILNAME set to "". We use the default value in the template site.conf
# here to prevent that issue.
DB_FILENAME   := $(shell grep ^DB_NAME $(CONFIG_DIR)/site.conf | cut -f 2 -d '"')
else
DB_FILENAME   := $(srcDir)/db.sqlite
endif

MY_EMAIL          ?= $(shell cd $(srcDir) && git config user.email)
EMAIL_FIXTURE_OPT := $(if $(MY_EMAIL),--email="$(MY_EMAIL)",)

# We generate the SECRET_KEY this way so it can be overriden
# in test environments.
SECRET_KEY ?= $(shell $(PYTHON) -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@\#$%^*-_=+") for i in range(50)]))' )

DJAODJIN_SECRET_KEY ?= $(shell $(PYTHON) -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@\#$%^*-_=+") for i in range(50)]))' )


.PHONY: initdb

all:
	@echo "Nothing to be done for 'make'."


build-assets: $(ASSETS_DIR)/cache/base.css \
                $(ASSETS_DIR)/cache/email.css \
                webpack-conf-paths.json
	cd $(srcDir) && $(WEBPACK)


clean: clean-dbs
	[ ! -f $(srcDir)/package-lock.json ] || rm $(srcDir)/package-lock.json
	find $(srcDir) -name '__pycache__' -exec rm -rf {} +
	find $(srcDir) -name '*~' -exec rm -rf {} +

clean-dbs:
	[ ! -f $(DB_FILENAME) ] || rm $(DB_FILENAME)

install:: install-conf

doc: schema.yml
	$(installDirs) build/docs
	cd $(srcDir) && sphinx-build -b html ./docs $(PWD)/build/docs


# We add a `load_test_transactions` because the command will set the current
# site and thus need the rules.App table.
initdb:
	-[ -f $(DB_FILENAME) ] && rm -f $(DB_FILENAME)
	$(installDirs) $(dir $(DB_FILENAME))
	cd $(srcDir) && $(MANAGE) migrate $(RUNSYNCDB) --noinput
	cd $(srcDir) && $(MANAGE) loadfixtures $(EMAIL_FIXTURE_OPT) \
		djaopsp/fixtures/default-db.json


makemessages:
	cd $(srcDir) && $(PYTHON) manage.py makemessages -l fr -l es -l pt --symlinks --no-wrap
	cd $(srcDir) && $(PYTHON) manage.py makemessages -d djangojs -l fr -l es -l pt --symlinks --no-wrap


package-theme: build-assets
	cd $(srcDir) && DEBUG=0 FEATURES_REVERT_TO_DJANGO=0 \
		$(MANAGE) package_theme \
		--build_dir=$(objDir) --install_dir=htdocs/themes \
		--exclude='_form.html' --exclude='.*/' \
		--include='accounts/' --include='docs/' \
		--include='notification/'
	zip -d $(srcDir)/htdocs/themes/$(APP_NAME).zip "$(APP_NAME)/templates/accounts/base.html"


# Download prerequisites specified in package.json and install relevant files
# in the directory assets are served from.
vendor-assets-prerequisites: $(installTop)/.npm/$(APP_NAME)-packages


$(installTop)/.npm/$(APP_NAME)-packages: $(srcDir)/package.json
	$(installFiles) $^ $(libDir)
	$(NPM) install --loglevel verbose --cache $(installTop)/.npm --tmp $(installTop)/tmp --prefix $(libDir)
	install -d $(ASSETS_DIR)/fonts $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/bootstrap/dist/js/bootstrap.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/chart.js/dist/chart.js $(ASSETS_DIR)/vendor
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
	$(installFiles) $(libDir)/node_modules/vue-infinite-loading/dist/vue-infinite-loading.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/vue-resource/dist/vue-resource.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/lodash/lodash.js $(ASSETS_DIR)/vendor
	[ -f $(binDir)/sassc ] || (cd $(binDir) && ln -s ../lib/node_modules/.bin/sass sassc)
	[ -f $(binDir)/swagger-cli ] || (cd $(binDir) && ln -s ../lib/node_modules/.bin/swagger-cli swagger-cli)


schema.yml:
	cd $(srcDir) && $(PYTHON) manage.py generateschema > $@
	cd $(srcDir) && swagger-cli validate $@


$(ASSETS_DIR)/cache/base.css: \
                $(wildcard $(srcDir)/assets/scss/vendor/bootstrap/*.scss) \
                $(wildcard $(srcDir)/assets/scss/vendor/djaodjin/*.scss) \
                $(wildcard $(srcDir)/assets/scss/vendor/*.scss) \
                $(wildcard $(srcDir)/assets/scss/base/*.scss)
	cd $(srcDir) && $(binDir)/sassc assets/scss/base/base.scss $@

$(ASSETS_DIR)/cache/email.css: \
                $(wildcard $(srcDir)/assets/scss/email/*.scss)
	cd $(srcDir) && $(binDir)/sassc assets/scss/email/email.scss $@


webpack.config.js: $(srcDir)/webpack.config.js
	$(installFiles) $< $@


webpack-conf-paths.json: webpack.config.js
	cd $(srcDir) && $(PYTHON) manage.py generate_webpack_paths -o $@


$(srcDir)/djaopsp/locale/fr/LC_MESSAGES/django.mo: \
				$(wildcard $(srcDir)/djaopsp/locale/es/LC_MESSAGES/*.po) \
				$(wildcard $(srcDir)/djaopsp/locale/fr/LC_MESSAGES/*.po) \
				$(wildcard $(srcDir)/djaopsp/locale/pt/LC_MESSAGES/*.po)
	cd $(srcDir) && \
		SETTINGS_LOCATION=$(CONFIG_DIR) $(PYTHON) manage.py compilemessages


install-conf:: $(DESTDIR)$(CONFIG_DIR)/credentials \
				$(DESTDIR)$(CONFIG_DIR)/site.conf \
				$(DESTDIR)$(CONFIG_DIR)/gunicorn.conf \
				$(DESTDIR)$(SYSCONFDIR)/sysconfig/$(APP_NAME) \
				$(DESTDIR)$(SYSCONFDIR)/logrotate.d/$(APP_NAME) \
				$(DESTDIR)$(SYSCONFDIR)/monit.d/$(APP_NAME) \
				$(DESTDIR)$(SYSCONFDIR)/systemd/system/$(APP_NAME).service
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
		-e 's,%(APP_NAME)s,$(APP_NAME),' \
		-e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' $< > $@

$(DESTDIR)$(SYSCONFDIR)/monit.d/%: $(srcDir)/etc/monit.conf
	install -d $(dir $@)
	[ -e $@ ] || sed \
		-e 's,%(APP_NAME)s,$(APP_NAME),g' \
		-e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' $< > $@

$(DESTDIR)$(SYSCONFDIR)/sysconfig/%: $(srcDir)/etc/sysconfig.conf
	install -d $(dir $@)
	[ -e $@ ] || install -p -m 644 $< $@
