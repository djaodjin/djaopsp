import Vue from 'vue'
// Decrease compilation time per:
// https://vuetifyjs.com/en/customization/presets/#compilation-time
import Vuetify from 'vuetify/lib/framework'
import { preset } from 'vue-cli-plugin-vuetify-preset-rally/preset'

const options = {
  theme: {
    dark: true,
  },
}

Vue.use(Vuetify)

export default new Vuetify({ preset, ...options })
