import Vue from 'vue'
// Decrease compilation time per:
// https://vuetifyjs.com/en/customization/presets/#compilation-time
import Vuetify from 'vuetify/lib/framework'
import { preset } from 'vue-cli-plugin-vuetify-preset-rally/preset'

Vue.use(Vuetify)

export default new Vuetify({ preset })
