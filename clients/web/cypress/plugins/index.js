/// <reference types="cypress" />
// ***********************************************************
// This example plugins/index.js can be used to load plugins
//
// You can change the location of this file or turn off loading
// the plugins file with the 'pluginsFile' configuration option.
//
// You can read more here:
// https://on.cypress.io/plugins-guide
// ***********************************************************

// This function is called when a project is opened or re-opened (e.g. due to
// the project's config changing)

/**
 * @type {Cypress.PluginConfig}
 */
module.exports = (on, config) => {
  // `on` is used to hook into various events Cypress emits
  // `config` is the resolved Cypress config
}

// Grab some process environment variables and stick them into config.env
module.exports = (on, config) => {
  require('dotenv').config()
  config.env = config.env || {}
  config.env.ROOT = process.env.VUE_APP_ROOT
  config.env.API_BASE = process.env.VUE_APP_API_BASE
  config.baseUrl = `http://127.0.0.1:8080${process.env.VUE_APP_ROOT}${process.env.VUE_APP_CLIENT_BASE}`
  return config
}
