import Vue from 'vue'
import VueCompositionApi from '@vue/composition-api'

import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import i18n from './plugins/i18n'

Vue.use(VueCompositionApi)

Vue.config.productionTip = false

if (process.env.NODE_ENV !== 'production') {
  require('dotenv').config()
}

new Vue({
  router,
  vuetify,
  i18n,
  render: (h) => h(App),
}).$mount('#app')
