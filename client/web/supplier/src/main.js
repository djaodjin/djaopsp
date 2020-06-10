import Vue from 'vue'
import VueCompositionApi from '@vue/composition-api'

import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'

Vue.use(VueCompositionApi)

Vue.config.productionTip = false

new Vue({
  router,
  vuetify,
  render: (h) => h(App),
}).$mount('#app')
