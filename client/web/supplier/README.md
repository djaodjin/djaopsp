# Supplier app

## Project setup

```
yarn install
```

### Compiles and hot-reloads for development

```
yarn serve
```

### Compiles and minifies for production

```
yarn build
```

### Lints and fixes files

```
yarn lint
```

### Customize configuration

See [Configuration Reference](https://cli.vuejs.org/config/).

### Locales

The app uses [vue-i18n](https://www.codeandweb.com/babeledit/tutorials/how-to-translate-your-vue-app-with-vue-i18n) to manage the translations of its content strings. Additionally, the UI framework (vuetify) has its own translations. This means that when changing locales for the app, remember to: 
- Add the locale file for the content in `src/locales`
- Update the locales list in `LocaleChanger.vue`
- Update the imports and the `lang.locales` option in `src/plugins/vuetify.js`

The app's default locale and fallback locale are set via the environment variables `VUE_APP_I18N_LOCALE` and `VUE_APP_I18N_FALLBACK_LOCALE` respectively.
