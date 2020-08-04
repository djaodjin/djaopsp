<template>
  <v-btn
    v-on="$listeners"
    v-bind="$attrs"
    :to="to"
    :depressed="$vuetify.breakpoint.xs"
    :block="!display || display !== 'inline'"
    :type="!type ? 'button' : type"
    :color="!color ? 'secondary' : color"
    large
  >
    <slot></slot>
  </v-btn>
</template>

<script>
export default {
  name: 'ButtonPrimary',
  props: ['color', 'to', 'display', 'type'],
}
</script>
