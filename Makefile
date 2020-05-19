# Copyright (c) 2019, DjaoDjin inc.
# see LICENSE.

-include $(buildTop)/share/dws/prefix.mk

srcDir        ?= $(realpath .)
objDir        ?= $(realpath .)/build
installTop    ?= $(VIRTUAL_ENV)
binDir        ?= $(installTop)/bin
SYSCONFDIR    := $(installTop)/etc
LOCALSTATEDIR := $(installTop)/var
APP_NAME      := $(notdir $(srcDir))
CONFIG_DIR    := $(SYSCONFDIR)/$(APP_NAME)

ASSETS_DIR    := $(srcDir)/htdocs/static

NPM           := $(binBuildDir)/npm
PIP           := $(binDir)/pip
PYTHON        := $(binDir)/python
installFiles  := install -p -m 644
MANAGE        := ENVCONNECT_SETTINGS_LOCATION=$(CONFIG_DIR) $(PYTHON) manage.py

DB_FILENAME   := $(shell grep ^DB_NAME $(CONFIG_DIR)/site.conf | cut -f 2 -d '"')
EMAIL_FIXTURE_OPT := $(if $(shell git config user.email),--email="$(shell git config user.email)",)

# Django 1.7,1.8 sync tables without migrations by default while Django 1.9
# requires a --run-syncdb argument.
# Implementation Note: We have to wait for the config files to be installed
# before running the manage.py command (else missing SECRECT_KEY).
RUNSYNCDB     = $(if $(findstring --run-syncdb,$(shell cd $(srcDir) && $(MANAGE) migrate --help 2>/dev/null)),--run-syncdb,)

# We generate the SECRET_KEY this way so it can be overriden
# in test environments.
SECRET_KEY ?= $(shell $(PYTHON) -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@\#$%^*-_=+") for i in range(50)]))' )

DJAODJIN_SECRET_KEY ?= $(shell $(PYTHON) -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@\#$%^*-_=+") for i in range(50)]))' )


all:
	@echo "Nothing to be done for 'make'."


# Delete and create a clean database anew
# Implementation Note: We implicitely rely on installing conf before resources
install:: install-conf


clean:
	rm -rf $(objDir)/envconnect
	-cd $(srcDir) && rm -rf htdocs/static/.webassets-cache htdocs/static/cache


package-theme: build-assets
	cd $(srcDir) && DEBUG=0 FEATURES_REVERT_TO_DJANGO=0 \
		$(MANAGE) package_theme \
		--build_dir=$(objDir) --install_dir=htdocs/themes \
		--exclude='_form.html' --exclude='.*/' \
		--include='accounts/' --include='docs/' \
		--include='saas/' --include='notification/' \
		--include='euissca/' --include='about.html'
	zip -d $(srcDir)/htdocs/themes/envconnect.zip "envconnect/templates/accounts/base.html"

build-assets: htdocs/static/cache/_base.css \
                htdocs/static/cache/_email.css
	cd $(srcDir) && DEBUG=1 $(PYTHON) manage.py assets build

htdocs/static/cache/_base.css: \
                $(wildcard $(srcDir)/assets/scss/vendor/bootstrap/*.scss) \
                $(wildcard $(srcDir)/assets/scss/vendor/djaodjin/*.scss) \
                $(wildcard $(srcDir)/assets/scss/base/*.scss)
	cd $(srcDir) && $(binDir)/sassc assets/scss/base/base.scss $@

htdocs/static/cache/_email.css: \
                $(wildcard $(srcDir)/assets/scss/email/*.scss)
	cd $(srcDir) && $(binDir)/sassc assets/scss/email/email.scss $@


# download and install prerequisites then create the db.
require: require-pip require-resources initdb

# XXX streetsidelite is necessary for account field in pages_element.
initdb: install-conf
	-[ -f $(DB_FILENAME) ] && rm -f $(DB_FILENAME)
	cd $(srcDir) && $(MANAGE) migrate $(RUNSYNCDB) --noinput
	cd $(srcDir) && $(MANAGE) loadfixtures $(EMAIL_FIXTURE_OPT) \
			envconnect/fixtures/streetsidelite.json \
			envconnect/fixtures/default-db.json \
			envconnect/fixtures/measures.json


# Once tests are completed, run 'coverage report'.
run-coverage: initdb
	cd $(srcDir) && ENVCONNECT_SETTINGS_LOCATION=$(CONFIG_DIR) \
		coverage run --source='.,survey,answers' manage.py runserver 8040 --noreload


require-pip:
	$(PIP) install -r $(srcDir)/requirements.txt --upgrade

require-resources: vendor-assets-prerequisites build-assets

# Download prerequisites specified in package.json and install relevant files
# in the directory assets are served from.
vendor-assets-prerequisites: $(srcDir)/package.json
	$(installFiles) $^ $(installTop)
	$(NPM) install --loglevel verbose --cache $(installTop)/.npm --tmp $(installTop)/tmp --prefix $(installTop)
	install -d $(ASSETS_DIR)/fonts $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/angular/angular.min.js* $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/angular/angular.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/angular-animate/angular-animate.min.js* $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/ui-bootstrap4/dist/ui-bootstrap-tpls.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/angular-dragdrop/src/angular-dragdrop.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/angular-route/angular-route.min.js* $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/angular-sanitize/angular-sanitize.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/angular-touch/angular-touch.min.js* $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/bootbox/bootbox.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/bootstrap/dist/js/bootstrap.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/bootstrap-toggle/js/bootstrap-toggle.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/c3/c3.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/c3/c3.css $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/d3/d3.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/dropzone/dist/dropzone.css $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/dropzone/dist/dropzone.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/font-awesome/css/font-awesome.css $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/font-awesome/fonts/* $(ASSETS_DIR)/fonts
	$(installFiles) $(installTop)/node_modules/jquery/dist/jquery.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/jquery-ui-touch-punch/jquery.ui.touch-punch.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/moment/moment.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/nvd3/build/nv.d3.css $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/nvd3/build/nv.d3.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/popper.js/dist/umd/popper.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/popper.js/dist/umd/popper-utils.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/rangy/lib/rangy-core.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/respond.js/src/respond.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/trip.js/dist/trip.css $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/trip.js/dist/trip.js $(ASSETS_DIR)/vendor
	$(installFiles) $(installTop)/node_modules/typeahead.js/dist/typeahead.bundle.js $(ASSETS_DIR)/vendor
	$(installFiles) $(srcDir)/envconnect/static/vendor/PIE.htc $(ASSETS_DIR)/vendor
	[ -f $(binDir)/sassc ] || (cd $(binDir) && ln -s ../node_modules/.bin/sass sassc)


install-conf:: $(DESTDIR)$(CONFIG_DIR)/credentials \
                $(DESTDIR)$(CONFIG_DIR)/site.conf \
                $(DESTDIR)$(CONFIG_DIR)/gunicorn.conf \
                $(DESTDIR)$(SYSCONFDIR)/sysconfig/$(APP_NAME) \
                $(DESTDIR)$(SYSCONFDIR)/logrotate.d/$(APP_NAME) \
                $(DESTDIR)$(SYSCONFDIR)/monit.d/$(APP_NAME) \
                $(DESTDIR)$(SYSCONFDIR)/systemd/system/$(APP_NAME).service
	install -d $(DESTDIR)$(LOCALSTATEDIR)/db
	install -d $(DESTDIR)$(LOCALSTATEDIR)/run
	install -d $(DESTDIR)$(LOCALSTATEDIR)/log/nginx

# Implementation Note:
# We use [ -f file ] before install here such that we do not blindly erase
# already present configuration files with template ones.
$(DESTDIR)$(SYSCONFDIR)/%/site.conf: $(srcDir)/etc/site.conf
	install -d $(dir $@)
	[ -f $@ ] || \
		sed -e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' \
			-e 's,%(SYSCONFDIR)s,$(SYSCONFDIR),' \
			-e "s,%(ADMIN_EMAIL)s,`cd $(srcDir) && git config user.email`," \
			-e "s,%(DB_NAME)s,$(notdir $(patsubst %/,%,$(dir $@)))," \
			-e "s,%(binDir)s,$(binDir)," $< > $@

$(DESTDIR)$(SYSCONFDIR)/%/credentials: $(srcDir)/etc/credentials
	install -d $(dir $@)
	[ -f $@ ] || \
		sed -e "s,\%(SECRET_KEY)s,$(SECRET_KEY)," \
			-e "s,\%(DJAODJIN_SECRET_KEY)s,$(DJAODJIN_SECRET_KEY)," \
			$< > $@

$(DESTDIR)$(SYSCONFDIR)/%/gunicorn.conf: $(srcDir)/etc/gunicorn.conf
	install -d $(dir $@)
	[ -f $@ ] || \
		sed -e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' $< > $@

$(DESTDIR)$(SYSCONFDIR)/systemd/system/%.service: \
               $(srcDir)/etc/service.conf
	install -d $(dir $@)
	[ -f $@ ] || sed -e 's,%(srcDir)s,$(srcDir),' \
		-e 's,%(APP_NAME)s,$(APP_NAME),g' \
		-e 's,%(binDir)s,$(binDir),' \
		-e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' \
		-e 's,%(SYSCONFDIR)s,$(SYSCONFDIR),' $< > $@

$(DESTDIR)$(SYSCONFDIR)/logrotate.d/%: $(srcDir)/etc/logrotate.conf
	install -d $(dir $@)
	[ -f $@ ] || sed \
		-e 's,%(APP_NAME)s,$(APP_NAME),' \
		-e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' $< > $@

$(DESTDIR)$(SYSCONFDIR)/monit.d/%: $(srcDir)/etc/monit.conf
	install -d $(dir $@)
	[ -f $@ ] || sed \
		-e 's,%(APP_NAME)s,$(APP_NAME),g' \
		-e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' $< > $@

$(DESTDIR)$(SYSCONFDIR)/sysconfig/%: $(srcDir)/etc/sysconfig.conf
	install -d $(dir $@)
	[ -f $@ ] || install -p -m 644 $< $@
