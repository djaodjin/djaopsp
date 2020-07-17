import Vue from 'vue'
import VueCompositionApi from '@vue/composition-api'
import Vuex from 'vuex'

import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import i18n from './plugins/i18n'
import storeConfig from './config/store'

Vue.use(VueCompositionApi)
Vue.use(Vuex)

Vue.config.productionTip = false

const store = new Vuex.Store(storeConfig)

if (process.env.NODE_ENV !== 'production') {
  require('dotenv').config()
}

new Vue({
  router,
  vuetify,
  i18n,
  store,
  render: (h) => h(App),
}).$mount('#app')
