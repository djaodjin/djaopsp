# Envconnect webapp

This Django project contains the web application for the enviro-connect project.

## Prerequisites

    $ make require

## Install

    $ make install
    $ make initdb


## Development setup: Step-by-step

### Install prerequisites and configurations

    $ python -m venv envconnect
    $ source envconnect/bin/activate
    $ mkdir -p envconnect/reps
    $ cd envconnect/reps
    $ git clone https://github.com/djaodjin/envconnect.git
    $ cd envconnect

    $ ../../bin/pip install -r requirements.txt -r dev-requirements.txt
    $ make install
    $ make initdb
    $ make vendor-assets-prerequisites
    $ make build-assets
    $ diff -u ../../etc/envconnect/site.conf
    -DEBUG=False
    +DEBUG=True

### Launching and debugging the full webserver

    $ supervisord
    # browse http://localhost:8000/envconnect/


### Running the new Vue client by itself

```
$ cd clients/web
$ VUE_APP_STANDALONE=1 VUE_APP_API_HOST=http://localhost:8080 yarn serve
# browse http://localhost:8080/envconnect/app/supplier-1/
```

### Lints and fixes files

```
$ cd clients/web
$ yarn lint
```

### <a name="stand-alone-mode"></a>Client stand-alone mode

The client (Vue app) has its own navigation which can be enabled using the `VUE_APP_STANDALONE` flag in the `.env` file at the client root (`clients/web`). In stand-alone mode, the app will also make calls to a mock server and make changes to an in-memory database.

### Client locales

The client app uses [vue-i18n](https://www.codeandweb.com/babeledit/tutorials/how-to-translate-your-vue-app-with-vue-i18n) to manage the translations of its content strings. Additionally, the UI framework (vuetify) has its own translations. This means that when changing locales for the app, remember to: 
- Add the locale file for the content in `src/locales`
- Update the locales list in `LocaleChanger.vue`
- Update the imports and the `lang.locales` option in `src/plugins/vuetify.js`

The app's default locale and fallback locale are set via the environment variables `VUE_APP_I18N_LOCALE` and `VUE_APP_I18N_FALLBACK_LOCALE` respectively in the `.env` file at the client root (`clients/web`)


## Testing

    supplier user account: steve, yoyo
    supplier manager user account: alice, yoyo
    website administrator: donny, yoyo

### Testing the client app

When running the client app in [stand-alone mode](#stand-alone-mode), a list of scenarios have already been set up to test the functionality of the app. These same scenarios are also used by tests in Cypress.

`/clients/web/src/mocks/scenarios`: List of scenarios

`yarn run cy:run` : run the complete test suite in Cypress from the command line

`yarn run cy:open` : launches the [Cypress Test Runner](https://docs.cypress.io/guides/core-concepts/test-runner.html), where groups of tests or the entire test suite can be run. To run the tests, make sure the local development server is up and running (`yarn serve`).
