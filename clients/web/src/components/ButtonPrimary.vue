<template>
  <v-btn
    :to="to"
    :depressed="$vuetify.breakpoint.xs"
    :block="!display || display !== 'inline'"
    :type="!type ? 'button' : type"
    large
    color="primary"
  >
    <slot></slot>
  </v-btn>
</template>

<script>
export default {
  name: 'ButtonPrimary',
  props: ['to', 'display', 'type'],
}
</script>
