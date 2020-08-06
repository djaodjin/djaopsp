import Vue from 'vue'
import VueCompositionApi from '@vue/composition-api'

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
    // Proxy app's network requests to mirage server
    makeServer({
      environment: process.env.NODE_ENV,
    })
  }
}

new Vue({
  context: new Context(),
  router,
  vuetify,
  i18n,
  render: (h) => h(App),
}).$mount('#app')
