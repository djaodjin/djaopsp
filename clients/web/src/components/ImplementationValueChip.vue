<template>
  <v-chip
    class="implementation-value"
    v-bind="$attrs"
    :dark="theme"
    :color="bgColor"
  >
    {{ value }}%
  </v-chip>
</template>

<script>
export default {
  name: 'ImplementationValueChip',

  props: ['value'],

  computed: {
    // Material colors reference:
    // https://vuetifyjs.com/en/styles/colors/#material-colors
    bgColor() {
      let bgColor = '#37474F'
      if (this.value <= 25) {
        bgColor = '#ECEFF1'
      } else if (this.value <= 50) {
        bgColor = '#B0BEC5'
      } else if (this.value <= 75) {
        bgColor = '#78909C'
      }
      return bgColor
    },
    theme() {
      return this.value > 75
    },
  },
}
</script>

<style lang="scss" scoped>
.implementation-value {
  font-size: 1rem;
}
</style>
