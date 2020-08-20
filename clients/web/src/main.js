import Vue from 'vue'
import VueCompositionApi from '@vue/composition-api'
import { Server, Response } from 'miragejs'

import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import i18n from './plugins/i18n'
import Context from './mixins/context'

import { makeServer } from './mocks/server'

Vue.use(VueCompositionApi)

Vue.config.productionTip = false

if (process.env.NODE_ENV !== 'production') {
  require('dotenv').config()

  if (process.env.VUE_APP_STANDALONE) {
    // Proxy your app's network requests
    // https://miragejs.com/quickstarts/cypress/#step-4-proxy-your-apps-network-requests
    if (window.Cypress) {
      new Server({
        environment: 'test',
        routes() {
          let methods = ['get', 'put', 'patch', 'post', 'delete']
          methods.forEach((method) => {
            this[method]('/*', async (schema, request) => {
              let [status, headers, body] = await window.handleFromCypress(
                request
              )
              return new Response(status, headers, body)
            })
          })
        },
      })
    } else {
      makeServer({
        environment: process.env.NODE_ENV,
        apiBasePath: `${process.env.VUE_APP_ROOT}${process.env.VUE_APP_API_BASE}`,
      })
    }
  }
}

new Vue({
  context: new Context(),
  router,
  vuetify,
  i18n,
  render: (h) => h(App),
}).$mount('#app')
