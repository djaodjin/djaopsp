<template>
  <v-btn
    :to="to"
    :depressed="$vuetify.breakpoint.xs"
    block
    large
    color="primary"
  >
    <slot></slot>
  </v-btn>
</template>

<script>
export default {
  name: 'ButtonPrimary',
  props: ['to'],
}
</script>
