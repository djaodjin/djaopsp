import Vue from 'vue'
// Decrease compilation time per:
// https://vuetifyjs.com/en/customization/presets/#compilation-time
import Vuetify from 'vuetify/lib/framework'
import { preset } from 'vue-cli-plugin-vuetify-preset-rally/preset'

import en from 'vuetify/es5/locale/en'
import es from 'vuetify/es5/locale/es'

const options = {
  lang: {
    current: process.env.VUE_APP_I18N_LOCALE,
    locales: { en, es },
  },
  theme: {
    dark: true,
  },
}

Vue.use(Vuetify)

export default new Vuetify({ preset, ...options })
