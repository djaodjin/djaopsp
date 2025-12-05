# Copyright (c) 2025, DjaoDjin inc.
# see LICENSE

-include $(buildTop)/share/dws/prefix.mk

APP_NAME      ?= $(notdir $(abspath $(srcDir)))
APP_PORT      ?= 8000

srcDir        ?= .
installTop    ?= $(if $(VIRTUAL_ENV),$(VIRTUAL_ENV),$(abspath $(srcDir))/.venv)
binDir        ?= $(installTop)/bin
libDir        ?= $(installTop)/lib
SYSCONFDIR    ?= $(installTop)/etc
LOCALSTATEDIR ?= $(installTop)/var
CONFIG_DIR    ?= $(SYSCONFDIR)/$(APP_NAME)
ASSETS_DIR    ?= $(srcDir)/htdocs/static
# because we are not loading DB_NAME from site.conf
RUN_DIR       ?= $(abspath $(srcDir))

installDirs   ?= /usr/bin/install -d
installFiles  ?= /usr/bin/install -p -m 644
DOCKER        ?= docker
ESCHECK       ?= eslint es5
NPM           ?= npm
PIP           ?= pip
PYTHON        ?= python
SASSC         ?= sassc --style=compressed --source-map-urls absolute
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
NOIMPORTS     = $(if $(findstring --no-imports,$(shell $(MANAGE) shell --help 2>/dev/null)),--no-imports,)


ifneq ($(wildcard $(CONFIG_DIR)/site.conf),)
# `make initdb` will install site.conf but only after `grep` is run
# and DB_FILENAME set to "". We use the default value in the template site.conf
# here to prevent that issue.
DB_FILENAME   ?= $(shell grep ^DB_NAME $(CONFIG_DIR)/site.conf | cut -f 2 -d '"')
else
DB_FILENAME   ?= $(RUN_DIR)/db.sqlite
endif

MY_EMAIL           ?= $(shell cd $(srcDir) && git config user.email)
EMAIL_FIXTURE_OPT  := $(if $(MY_EMAIL),--email="$(MY_EMAIL)",)
APP_VERSION_SUFFIX ?= $(shell grep 'APP_VERSION =' $(srcDir)/$(APP_NAME)/settings.py | sed -e 's/APP_VERSION = "\(.*\)"/-\1/')

# We generate the SECRET_KEY this way so it can be overriden
# in test environments.
SECRET_KEY ?= $(shell $(PYTHON) -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@\#$%^*-_=+") for i in range(50)]))' )

DJAODJIN_SECRET_KEY ?= $(shell $(PYTHON) -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@\#$%^*-_=+") for i in range(50)]))' )


.PHONY: build-assets doc generateschema initdb makemessages setup-livedemo vendor-assets-prerequisites

all:
	@echo "Nothing to be done for 'make'."


# We are installing the overridden vendor files along with the ones installed
# from node_modules.
# Implementation note: chart.js is a directory. chartjs-plugin-annotation.js
# is not ES5 compatible.
build-assets: $(ASSETS_DIR)/cache/app.css \
              $(ASSETS_DIR)/cache/email.css \
              $(ASSETS_DIR)/cache/assess.js
	$(installFiles) $(ASSETS_DIR)/cache/app.css $(ASSETS_DIR)/cache/app$(APP_VERSION_SUFFIX).css
	$(installFiles) $(ASSETS_DIR)/cache/app.css.map $(ASSETS_DIR)/cache/app$(APP_VERSION_SUFFIX).css.map
	$(installFiles) $(ASSETS_DIR)/cache/email.css $(ASSETS_DIR)/cache/email$(APP_VERSION_SUFFIX).css
	$(installFiles) $(ASSETS_DIR)/cache/email.css.map $(ASSETS_DIR)/cache/email$(APP_VERSION_SUFFIX).css.map
	$(installFiles) $(ASSETS_DIR)/cache/assess.js $(ASSETS_DIR)/cache/assess$(APP_VERSION_SUFFIX).js
	$(installFiles) $(ASSETS_DIR)/cache/editors.js $(ASSETS_DIR)/cache/editors$(APP_VERSION_SUFFIX).js
	$(installFiles) $(ASSETS_DIR)/cache/reporting.js $(ASSETS_DIR)/cache/reporting$(APP_VERSION_SUFFIX).js
	cd $(srcDir) && DEBUG=0 $(MANAGE) collectstatic --noinput
	rm -rf $(ASSETS_DIR)/rest_framework $(ASSETS_DIR)/scss $(ASSETS_DIR)/css
	$(installFiles) $(srcDir)/djaopsp/static/vendor/djaodjin-dashboard.js $(ASSETS_DIR)/vendor
	$(installFiles) $(srcDir)/djaopsp/static/vendor/djaodjin-menubar.js $(ASSETS_DIR)/vendor
	$(installFiles) $(srcDir)/djaopsp/static/vendor/djaoapp-i18n.js $(ASSETS_DIR)/vendor
	rm -rf $(srcDir)/htdocs/static/vendor/chart.js $(srcDir)/htdocs/static/vendor/chartjs-plugin-annotation.js
	cd $(srcDir) && $(ESCHECK) htdocs/static/cache/*.js htdocs/static/vendor/*.js -v


clean: clean-dbs
	rm -rf $(ASSETS_DIR)/rest_framework $(ASSETS_DIR)/scss $(ASSETS_DIR)/css $(ASSETS_DIR)/js $(ASSETS_DIR)/data
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
		djaopsp/fixtures/engineering-si-units.json \
		djaopsp/fixtures/engineering-alt-units.json \
		djaopsp/fixtures/accounts.json \
		djaopsp/fixtures/content.json \
		djaopsp/fixtures/practices.json \
		djaopsp/fixtures/practices_custom_choices.json \
		djaopsp/fixtures/matrices.json \
		djaopsp/fixtures/samples.json \
		djaopsp/fixtures/100-completed-notshared.json \
		djaopsp/fixtures/101-onboarding.json \
		djaopsp/fixtures/800-data-series.json

setup-livedemo: initdb

install:: install-conf


makemessages:
	cd $(srcDir) && $(MANAGE) makemessages -l fr -l es -l pt --symlinks --no-wrap
	cd $(srcDir) && $(MANAGE) makemessages -d djangojs -l fr -l es -l pt --symlinks --no-wrap


ifeq ($(MY_EMAIL),)

.PHONY: package-docker

# We build a local sqlite3 database to be packaged with the Docker image
# such that the container can be started without prior configuration.
package-docker: build-assets initdb
	[[ -f $(srcDir)/db.sqlite ]] || cp $(DB_FILENAME) $(srcDir)/db.sqlite
	cd $(srcDir) && $(DOCKER) build $(DOCKER_OPTS) .

endif

# we remove the build directory to make sure we don't have extra files remaining
# when we excluded them in the package_theme command line. We also insures
# we are not removing important directories in the src tree by running
# the condition: `[ "$(abspath $(objDir))" != "$(abspath $(srcDir))" ]`.
package-theme: build-assets
	[ "$(abspath $(objDir))" != "$(abspath $(srcDir))" ] && rm -rf $(objDir)/$(APP_NAME)
	cd $(srcDir) && DEBUG=0 FEATURES_REVERT_TO_DJANGO=0 \
		$(MANAGE) package_theme \
		--build_dir=$(objDir) --install_dir=$(srcDir)/dist \
		--exclude='_form.html' --exclude='_form_fields.html' \
		--exclude='_params_start_at_field.html' \
		--exclude='_params_ends_at_field.html' --exclude='_filter.html' \
		--exclude='_pagination.html' --exclude='.*/'


# Once tests are completed, run 'coverage report'.
run-coverage: initdb
	cd $(srcDir) && coverage run --source='.,deployutils,pages,survey,' \
		manage.py runserver $(APP_PORT) --noreload


# Download prerequisites specified in package.json and install relevant files
# in the directory assets are served from.
vendor-assets-prerequisites: $(libDir)/.npm/$(APP_NAME)-packages


# --------- intermediate targets

clean-dbs:
	[ ! -f $(DB_FILENAME) ] || rm $(DB_FILENAME)

# The chart.js in node_modules/chart.js/dist/chart.js does not pass
# `es-check es5`. The webpack.config.js file rules loader excludes
# `node_modules` from babel, so we install chart.js in $srcDir here.
$(libDir)/.npm/$(APP_NAME)-packages: $(srcDir)/package.json
	$(installDirs) $(libDir)/tmp
	$(installFiles) $^ $(libDir)/tmp
	$(NPM) install --cache $(libDir)/.npm --tmp $(libDir)/tmp --prefix $(libDir)
	$(installDirs) $(ASSETS_DIR)/fonts $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/bootstrap/dist/js/bootstrap.min.js $(ASSETS_DIR)/vendor
	cp -rf $(libDir)/node_modules/chart.js $(srcDir)/djaopsp/static/vendor
	$(installFiles) $(libDir)/node_modules/chartjs-plugin-annotation/dist/chartjs-plugin-annotation.js $(srcDir)/djaopsp/static/vendor
	$(installFiles) $(libDir)/node_modules/dropzone/dist/dropzone.css $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/dropzone/dist/dropzone.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/easymde/dist/easymde.min.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/font-awesome/css/font-awesome.css $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/font-awesome/fonts/* $(ASSETS_DIR)/fonts
	$(installFiles) $(libDir)/node_modules/jquery/dist/jquery.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/marked/marked.min.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/moment/moment.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/moment-timezone/builds/moment-timezone-with-data.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/@popperjs/core/dist/umd/popper.min.js* $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/vue/dist/vue.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/lodash/lodash.js $(ASSETS_DIR)/vendor
	$(installFiles) $(libDir)/node_modules/@yaireo/tagify/dist/tagify.js $(libDir)/node_modules/@yaireo/tagify/dist/tagify.js.map $(ASSETS_DIR)/vendor
	[ -e $(binDir)/eslint ] || (cd $(binDir) && ln -s ../lib/node_modules/.bin/eslint eslint)
	[ -f $(binDir)/sassc ] || (cd $(binDir) && ln -s ../lib/node_modules/.bin/sass sassc)
	[ -f $(binDir)/swagger-cli ] || (cd $(binDir) && ln -s ../lib/node_modules/.bin/swagger-cli swagger-cli)
	[ -f $(binDir)/webpack ] || (cd $(binDir) && ln -s ../lib/node_modules/.bin/webpack webpack)
	touch $@


schema.yml:
	cd $(srcDir) && DEBUG=0 API_DEBUG=1 OPENAPI_SPEC_COMPLIANT=1 \
		$(MANAGE) spectacular --color --file $@ --validate
	cd $(srcDir) && swagger-cli validate $@


$(ASSETS_DIR)/cache/assess.js: $(srcDir)/webpack.config.js \
                               webpack-conf-paths.json \
                               $(wildcard $(srcDir)/djaopsp/static/js/*.js)
	cd $(srcDir) && $(WEBPACK) -c $<


webpack-conf-paths.json: $(srcDir)/djaopsp/settings.py
	cd $(srcDir) && $(MANAGE) generate_webpack_paths -o $@


$(ASSETS_DIR)/cache/app.css: $(srcDir)/djaopsp/static/scss/base/base.scss \
        $(wildcard $(srcDir)/djaopsp/static/scss/base/*.scss) \
        $(wildcard $(srcDir)/djaopsp/static/scss/vendor/*.scss) \
        $(wildcard $(srcDir)/djaopsp/static/scss/vendor/bootstrap/*.scss) \
        $(wildcard $(srcDir)/djaopsp/static/scss/vendor/djaodjin/*.scss)
	cd $(srcDir) && $(SASSC) $< $@

$(ASSETS_DIR)/cache/email.css: $(srcDir)/djaopsp/static/scss/email/email.scss \
        $(wildcard $(srcDir)/djaopsp/static/scss/email/*.scss)
	cd $(srcDir) && $(SASSC) $< $@


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
				$(DESTDIR)$(libDir)/tmpfiles.d/$(APP_NAME).conf
	$(installDirs) $(DESTDIR)$(LOCALSTATEDIR)/db
	$(installDirs) $(DESTDIR)$(LOCALSTATEDIR)/log/gunicorn
	[ -d $(DESTDIR)$(LOCALSTATEDIR)/run ] || $(installDirs) $(DESTDIR)$(LOCALSTATEDIR)/run

# Implementation Note:
# We use [ -f file ] before install here such that we do not blindly erase
# already present configuration files with template ones.
$(DESTDIR)$(CONFIG_DIR)/site.conf: $(srcDir)/etc/site.conf
	$(installDirs) $(dir $@)
	[ -f $@ ] || \
		sed -e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' \
			-e 's,%(SYSCONFDIR)s,$(SYSCONFDIR),' \
			-e 's,%(APP_NAME)s,$(APP_NAME),' \
			-e "s,%(ADMIN_EMAIL)s,$(MY_EMAIL)," \
			-e 's,%(installTop)s,$(installTop),' \
			-e "s,%(DB_NAME)s,$(APP_NAME)," \
			-e "s,%(DB_FILENAME)s,$(DB_FILENAME)," \
			-e "s,%(binDir)s,$(binDir)," $< > $@

$(DESTDIR)$(CONFIG_DIR)/credentials: $(srcDir)/etc/credentials
	$(installDirs) $(dir $@)
	[ -e $@ ] || sed \
		-e "s,\%(SECRET_KEY)s,`$(PYTHON) -c 'import sys ; from random import choice ; sys.stdout.write("".join([choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^*-_=+") for i in range(50)]))'`," \
			$< > $@

$(DESTDIR)$(CONFIG_DIR)/gunicorn.conf: $(srcDir)/etc/gunicorn.conf
	$(installDirs) $(dir $@)
	[ -e $@ ] || sed \
		-e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' \
		-e 's,%(APP_NAME)s,$(APP_NAME),g' \
		-e 's,%(APP_PORT)s,$(APP_PORT),' $< > $@

$(DESTDIR)$(SYSCONFDIR)/systemd/system/%.service: \
			   $(srcDir)/etc/service.conf
	$(installDirs) $(dir $@)
	[ -e $@ ] || sed \
		-e 's,%(srcDir)s,$(srcDir),' \
		-e 's,%(APP_NAME)s,$(APP_NAME),g' \
		-e 's,%(binDir)s,$(binDir),' \
		-e 's,%(SYSCONFDIR)s,$(SYSCONFDIR),' \
		-e 's,%(CONFIG_DIR)s,$(CONFIG_DIR),' \
		-e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' $< > $@

$(DESTDIR)$(SYSCONFDIR)/logrotate.d/%: $(srcDir)/etc/logrotate.conf
	$(installDirs) $(dir $@)
	[ -e $@ ] || sed \
		-e 's,%(APP_NAME)s,$(APP_NAME),g' \
		-e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' $< > $@

$(DESTDIR)$(SYSCONFDIR)/monit.d/%: $(srcDir)/etc/monit.conf
	$(installDirs) $(dir $@)
	[ -e $@ ] || sed \
		-e 's,%(APP_NAME)s,$(APP_NAME),g' \
		-e 's,%(APP_PORT)s,$(APP_NAME),g' \
		-e 's,%(LOCALSTATEDIR)s,$(LOCALSTATEDIR),' $< > $@

$(DESTDIR)$(SYSCONFDIR)/sysconfig/%: $(srcDir)/etc/sysconfig.conf
	$(installDirs) $(dir $@)
	[ -e $@ ] || install -p -m 644 $< $@

$(DESTDIR)$(libDir)/tmpfiles.d/$(APP_NAME).conf: $(srcDir)/etc/tmpfiles.conf
	$(installDirs) $(dir $@)
	[ -e $@ ] || sed \
		-e 's,%(APP_NAME)s,$(APP_NAME),g' $< > $@
