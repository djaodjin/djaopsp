<template>
  <component v-if="TESTING" :duration="0" :is="name" v-bind="$attrs">
    <slot></slot>
  </component>
  <component v-else :is="name" v-bind="$attrs">
    <slot></slot>
  </component>
</template>

<script>
/*
 * Why this component exists: animated transitions were causing Cypress tests to fail
 *
 * Transition duration of vuetify's transition components depends on the global
 * SASS variable $primary-transition:
 * https://dev.vuetifyjs.com/en/styles/transitions/#slide-y-transitions
 * https://github.com/vuetifyjs/vuetify/blob/8c650e48a53ac32ba44bd16d3f853a8b07810ff3/packages/vuetify/src/styles/settings/_variables.scss#L246
 *
 * Per vuetify's documentation:
 * https://vuetifyjs.com/en/customization/sass-variables/#sass-variables
 * Global SASS variables can be overriden; however, we need to control the
 * behaviour of $primary-transition depending on whether Cypress tests are
 * running or not.
 *
 * Instead of changing the value of $primary-transition, this component
 * wraps transition components and removes their transition duration in
 * run-time.
 */
import { VSlideXTransition, VFadeTransition } from 'vuetify/lib'

export default {
  name: 'TspTransition',

  props: ['name'],

  data() {
    return {
      TESTING: !!window.Cypress,
    }
  },

  components: {
    VSlideXTransition,
    VFadeTransition,
  },
}
</script>
